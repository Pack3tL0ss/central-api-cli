#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import base64
from contextlib import asynccontextmanager
from enum import Enum
import hashlib
import hmac
import json
import sys
from collections import Counter
from pathlib import Path
import time
from typing import Any, Literal, Sequence

import pendulum
import typer
import uvicorn
from fastapi import FastAPI, Header, Request, Response as FastAPIResponse, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request  # NoQA
from starlette.responses import FileResponse
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from centralcli import APIClients, Config, config, render, utils, common as _common, log
from centralcli.clicommon import BuiltRequests, CLICommon
from centralcli.constants import GenericDeviceTypes
from centralcli.models.webhook import HookResponse, MonitoringWebHook, wh_resp_schema
from centralcli.models.alerts import Alerts
from centralcli.response import BatchResponse, Response, RateLimit
from centralcli.strings import emoji
from centralcli.cache import Cache
from centralcli.client import BatchRequest
from centralcli.cache import DBAction
from centralcli.objects import DateTime
from centralcli.objects.cache import CacheDevice, CacheSite
from centralcli.environment import env, env_var


COLLECT = False
TEST_MODE = False  # TEST MODE does not do any signature verification.  (Makes sending hooks via curl or the like easier)
CON_UPDATE_NIDS = [3, 4, 201, 203, 301, 303]
RAW_CAPTURE_FILE = config.outdir / "wh_watcher_raw.json"
RESPONSE_OUT_FILE = config.outdir / "wh_watcher_responses"


# log_file = Path(config.dir / "logs" / f"wh_{Path(__file__).stem}.log")
# log_file.parent.mkdir(exist_ok=True)
# log = MyLogger(log_file, debug=config.debug, show=True, verbose=config.debugv, prefix=LOG_PFX)
log.show = True
log.prefix = "[WH WATCHER] "


class ExecutionResults:
    def __init__(self, move: BatchResponse = None, delete: BatchResponse = None, site_delete: BatchResponse = None):
        self.move = move
        self.delete = delete
        self.site_delete = site_delete

    @property
    def ok(self) -> bool:
        if self.move is not None and self.move.failed:
            return False
        if self.delete is not None and self.delete.failed:
            return False
        if self.site_delete is not None and self.site_delete.failed:
            return False
        return True

    @property
    def passed(self) -> list[Response]:
        return [
            *([] if self.move is None else self.move.passed),
            *([] if self.delete is None else self.delete.passed),
            *([] if self.site_delete is None else self.site_delete.passed),
        ]

    @property
    def failed(self) -> list[Response]:
        return [
            *([] if self.move is None else self.move.failed),
            *([] if self.delete is None else self.delete.failed),
            *([] if self.site_delete is None else self.site_delete.failed),
        ]

    def __len__(self):
        return sum([len(self.passed), len(self.failed)])

    def display(self, outfile: Path = None) -> None:
        file_sfx = ["moves", "dev_deletes", "site_deletes"]
        for sfx, (_type, r) in zip(file_sfx, {"Group & Site Moves": self.move, "Device Deletions": self.delete, "Site Deletions": self.site_delete}.items()):
            if r is None:
                continue
            render.display_results(
                [*r.passed, *r.failed],
                tablefmt="action",
                title=f"WebHook Watcher Results {_type}",
                caption=f"[dark_olive_green2]Counts[/]: Total: [cyan]{len(r)}[/], [bright_green]Passed[/]: [bright_green]{len(r.passed)}[/], [red]Failed[/]: [red]{len(r.failed)}[/]",
                outfile=outfile and outfile.parent / f"{outfile.stem}{sfx}{outfile.suffix}",
                suppress_rl=True,
                exit_on_fail=False,
            )
        delete_rl = min([RateLimit(), *[r.last_rl for r in [self.delete, self.site_delete] if r is not None]])
        if self.move:
            render.econsole.print(f"[italic]{wh_common.move_ws} [dark_olive_green2]{self.move.last_rl}[/][/]")
        if delete_rl:
            render.econsole.print(f"[italic]{wh_common.delete_ws} [dark_olive_green2]{self.delete.last_rl}[/][/]")
        render.econsole.print(f"[dark_olive_green3]Counts All Calls[/]: Total: [cyan]{len(self)}[/], [bright_green]Passed[/]: [bright_green]{len(self.passed)}[/], [red]Failed[/]: [red]{len(self.failed)}[/]")
        render.econsole.print("\nUse [cyan]cencli batch verify[/] to verify final status.")

    def __add__(self, other: "ExecutionResults"):
        if other.move is not None:
            if self.move is not None:
                self.move.responses += other.move.responses
                self.move.cache_clear()
            else:
                self.move = other.move
        if other.delete is not None:
            if self.delete is not None:
                self.delete.responses += other.delete.responses
                self.delete.cache_clear()
            else:
                self.delete = other.delete
        if other.site_delete is not None:
            if self.site_delete is not None:
                self.site_delete.responses += other.site_delete.responses
                self.site_delete.cache_clear()
            else:
                self.site_delete = other.site_delete
        return self


class WorkSpace:
    def __init__(self, workspace_name: str = None):
        self.name = workspace_name
        self.config = self.name and Config(workspace=self.name)
        self.config.debugv = config.debugv
        self.config.debug = config.debug
        self.api_clients = self.name and APIClients(self.config, limit_per_host=7, total_timeout=None)
        self.cache = self.name and Cache(self.config)
        self.common = CLICommon(workspace=self.name, cache=self.cache, raw_out=_common.raw_out)

    def __str__(self) -> str:
        return f"[medium_spring_green]{self.name}[/] workspace"

    def __repr__(self):  # pragma: no cover
        return f"<{self.__module__}.{type(self).__name__} ({self.name} workspace) object at {hex(id(self))}>"


class MoveType(str, Enum):
    SITE = "SITE"
    GROUP = "GROUP"


class DeleteType(str, Enum):
    DEVICE = "DEVICE"
    SITE = "SITE"


class BuiltTriggerRequests:
    def __init__(self, requests: list[BatchRequest], items: dict[str, list[str]] | list[str], request_type: MoveType | DeleteType):
        self.requests = requests
        self.items = items  # serials by site_id~|~type i.e {"123~|~switch": ["US123ABC9", "TW986ZYX8"]}
        self.req_type = request_type
        if len(self.requests) != len(self.items):
            raise ValueError("Mismatched lens between requests and associated items")
        self.batch_resp: BatchResponse = None


class SiteMoveRequests:
    def __init__(self, requests: list[BatchRequest], items: dict[str, list[str]]):
        self.requests = requests
        self.items = items  # serials by site_id~|~type i.e {"123~|~switch": ["US123ABC9", "TW986ZYX8"]}
        if len(self.requests) != len(self.items):
            raise ValueError("Mismatched lens between requests and associated items")
        self.batch_resp: BatchResponse = None


class GroupMoveRequests:
    def __init__(self, requests: list[BatchRequest], items: dict[str, list[str]]):
        self.requests = requests
        self.items = items  # serials by group i.e {"WadeLab": ["US123ABC9", "TW986ZYX8"]}
        if len(self.requests) != len(self.items):
            raise ValueError("Mismatched lens between requests and associated items")
        self.batch_resp: BatchResponse = None


class DevDeleteRequests:
    def __init__(self, requests: list[BatchRequest], items: dict[str, list[str]]):
        self.requests = requests
        self.items = items  #
        if len(self.requests) != len(self.items):
            raise ValueError("Mismatched lens between requests and associated items")
        self.batch_resp: BatchResponse = None


class SiteDeleteRequests:
    def __init__(self, requests: list[BatchRequest], items: dict[str, list[str]]):
        self.requests = requests
        self.items = items  #
        if len(self.requests) != len(self.items):
            raise ValueError("Mismatched lens between requests and associated items")
        self.batch_resp: BatchResponse = None


class TaskQueue:
    move_tasks: list[BuiltTriggerRequests] = []
    dev_del_tasks: list[BuiltTriggerRequests] = []
    site_del_tasks: list[BuiltTriggerRequests] = []

    def __init__(self, move_ws: WorkSpace = None, delete_ws: WorkSpace = None):
        self.move_ws = move_ws
        self.delete_ws = delete_ws
        self.moved_serials_site: list[str] = []
        self.moved_serials_group: list[str] = []
        self.deleted_serials: list[str] = []
        self.deleted_sites: list[str] = []

    @classmethod
    def add_moves(cls, reqs: list[BatchRequest]):
        cls.move_tasks += reqs

    @classmethod
    def add_dev_del(cls, reqs: list[BatchRequest]):
        cls.dev_del_tasks += reqs

    @classmethod
    def add_site_del(cls, reqs: list[BatchRequest]):
        cls.site_del_tasks += reqs

    # @property
    # def staged_cnt_str(self) -> str:
    #     counts = []
    #     if self.move_ws:
    #         counts += [f"{self.move_ws} [italic]([spring_green3]devics moves[/])[/] [dark_orange3]Staged[/]: {len(self.ready_to_move)}"]
    #         if self.moved_serials_group or self.moved_serials_site:
    #             group_str = '' if not self.moved_serials_group else f'[light_sea_green]Group[/]: {len(self.moved_serials_group)}'
    #             site_str = '' if not self.moved_serials_site else f'[medium_turquoise]Site[/]: {len(self.moved_serials_site)}'
    #             counts += [f"[green]Processed[/]: {group_str}, {site_str}".rstrip(", ")]

    #     if self.delete_ws:
    #         counts += [f"{self.delete_ws} [italic]([red]deletes[/])[/] [dark_orange3]Staged[/]: [light_sea_green]Devices[/]: {len(self.ready_to_delete)}, [medium_turquoise]Sites[/]: {len(self.sites_ready_to_delete)}"]
    #         if self.deleted_serials:
    #             dev_str = '' if not self.deleted_serials else f'[light_sea_green]Devices[/]: {len(self.deleted_serials)}'
    #             site_str = '' if not self.deleted_sites else f'[medium_turquoise]Sites[/]: {len(self.deleted_sites)}'
    #             counts += [f"[green]Processed[/]: {dev_str}, {site_str}".rstrip(", ")]

    #     return ", ".join(counts).replace(" , ", " ")


class WHCommon:
    RUNNING: bool = None
    _test_mode_log_sent: bool = False

    def __init__(
            self,
            move_ws: str = config.workspace,
            *,
            delete_ws: str | None = None,
            watcher_dir: Path = Path.cwd(),
            watcher_prefix: str | Sequence[str] = ("migrate", "devies"),
            update_interval: int = 10,
            refresh: bool = True,
            past: int = 30,
        ):
        self.move_ws = WorkSpace(move_ws)
        self.delete_ws: WorkSpace | None = delete_ws and WorkSpace(delete_ws)
        self.task_queue = TaskQueue(self.move_ws, delete_ws=self.delete_ws)
        self.watcher_dir = watcher_dir
        if self.watcher_dir and not self.watcher_dir.is_dir():
            _common.exit(f"Watcher directory [cyan]{self.watcher_dir}[/], not found or is not a directory.")
        self.watcher_prefix = watcher_prefix
        self.update_interval = update_interval

        self.migrate_data = self.get_migrate_data()
        self.tasks: list[asyncio.Task] = []
        self.trigger_results = ExecutionResults()
        self._ready_to_move: list[dict[str, Any]] = []
        self._ready_to_delete: list[dict[str, str | int | MonitoringWebHook]] = []
        self.deleted_serials: list[str] = []
        self.deleted_sites: list[str] = []
        self.moved_serials_group: list[str] = []
        self.moved_serials_site: list[str] = []
        self.sites_ready_to_delete: list[str] = []
        self.count_per_site = Counter()
        self.deleted_devs_count_per_site: dict[str, int] = {}
        start: pendulum.DateTime = pendulum.now()
        self.next_update: pendulum.DateTime = start + pendulum.duration(seconds=update_interval)
        self._refresh = refresh
        self._past = past

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

    @property
    def next_update_pretty(self):
        return DateTime(self.next_update.int_timestamp - pendulum.now().int_timestamp, format='durwords').durwords

    @property
    def ready_to_move(self) -> list[dict[str, str | int | MonitoringWebHook]]:
        return self._ready_to_move

    @ready_to_move.setter
    def ready_to_move(self, ready_to_move: list[dict[str, Any]]):
        _begin_len = len(ready_to_move)
        ready_by_serial = {d["serial"]: d for d in ready_to_move}
        dups = _begin_len - len(ready_by_serial)
        if dups:
            log.warning(f"Removed {dups} duplicate entries from move queue.  [italic]Webhooks can arrive more than once on occasion[/]")
        self._ready_to_move = [d for d in ready_to_move if (d.get("site") and d["serial"] not in self.moved_serials_site) or (d.get("group") and d["serial"] not in self.moved_serials_group)]

    @property
    def ready_to_delete(self) -> list[dict[str, Any]]:
        return self._ready_to_delete

    @ready_to_delete.setter
    def ready_to_delete(self, ready_to_delete: list[dict[str, Any]]):
        self._ready_to_delete = [d for d in ready_to_delete if d["serial"] not in self.deleted_serials]

    @property
    def staged_cnt_str(self) -> str:
        counts = []
        if self.move_ws:
            counts += [f"{self.move_ws} [italic]([spring_green3]devics moves[/])[/] [dark_orange3]Staged[/]: {len(self.ready_to_move)}"]
            if self.moved_serials_group or self.moved_serials_site:
                group_str = '' if not self.moved_serials_group else f'[light_sea_green]Group[/]: {len(self.moved_serials_group)}'
                site_str = '' if not self.moved_serials_site else f'[medium_turquoise]Site[/]: {len(self.moved_serials_site)}'
                counts += [f"[green]Processed[/]: {group_str}, {site_str}".rstrip(", ")]

        if self.delete_ws:
            counts += [f"{self.delete_ws} [italic]([red]deletes[/])[/] [dark_orange3]Staged[/]: [light_sea_green]Devices[/]: {len(self.ready_to_delete)}, [medium_turquoise]Sites[/]: {len(self.sites_ready_to_delete)}"]
            if self.deleted_serials:
                dev_str = '' if not self.deleted_serials else f'[light_sea_green]Devices[/]: {len(self.deleted_serials)}'
                site_str = '' if not self.deleted_sites else f'[medium_turquoise]Sites[/]: {len(self.deleted_sites)}'
                counts += [f"[green]Processed[/]: {dev_str}, {site_str}".rstrip(", ")]

        return ", ".join(counts).replace(" , ", " ")

    @property
    def has_staged_updates(self) -> bool:
        return any([self.ready_to_delete, self.ready_to_move, self.sites_ready_to_delete])

    @property
    def staged_count(self) -> int:
        return sum(map(len, [self.ready_to_delete, self.ready_to_move, self.sites_ready_to_delete]))

    @property
    def do_updates(self) -> bool:
        cnt_move_update = True if len(self.ready_to_move) > 7 else False
        cnt_delete_update = True if len(self.ready_to_delete) > 7 else False
        cnt_site_delete_update = True if len(self.sites_ready_to_delete) > 7 else False
        time_based = True if pendulum.now() >= self.next_update else False
        return True if any([time_based, cnt_move_update, cnt_delete_update, cnt_site_delete_update]) else False

    async def refresh_cache(self):
        start = time.perf_counter()
        spin_pfx = f"{emoji.cache} Updating Cache"
        tasks = []
        with render.Spinner(spin_pfx) as spinner:
            if self.delete_ws:  # pragma: no cover
                spinner.update(f"{spin_pfx} for {self.delete_ws}")
                # self.delete_ws.api_clients.classic.session.silent = True
                tasks += [await asyncio.create_task(self.delete_ws.cache._check_fresh(dev_db=True, site_db=True))]
                # tasks += [self.loop.create_task(self.delete_ws.cache._check_fresh(dev_db=True, site_db=True))]
            if self.move_ws:  # pragma: no cover
                spinner.update(f"{spin_pfx} for {self.move_ws}")
                # self.move_ws.api_clients.classic.session.silent = True
                # tasks += [self.loop.create_task(self.move_ws.cache._check_fresh(dev_db=True, site_db=True, group_db=True))]
                tasks += [await asyncio.create_task(self.move_ws.cache._check_fresh(dev_db=True, site_db=True, group_db=True))]
        # wh_common.loop.run_until_complete(asyncio.gather(*tasks))
        # await asyncio.gather(*tasks)
        spinner.succeed(f"{spin_pfx} Completed in {round(time.perf_counter() - start, 3)}")

    def get_migrate_data(self) -> dict[str, dict[str, str | int | MonitoringWebHook]]:
        matched_files = []
        migrate_data = {}
        with render.Spinner(f"Importing any existing watcher files in [dark_violet]{self.watcher_dir}[/]", spinner="arrow3") as spinner:
            for file in self.watcher_dir.iterdir():
                if file.is_file() and any([file.name.startswith(pfx) or file.name == Path(pfx).name for pfx in self.watcher_prefix]) and ("retry" not in file.name and ".bak" not in file.name):
                    spinner.update(f"Importing devices to watch for from [dark_violet]{file.name}[/]")
                    this = _common._get_import_file(file, "devices", required_fields=["serial"])
                    migrate_data = {**migrate_data, **{d["serial"]: d for d in this}}
                    matched_files += [file.name]
            if migrate_data:
                self.count_per_site = Counter([d["site"] for d in migrate_data.values() if d.get("site")])
                groups = set([d["group"] for d in migrate_data.values() if d.get("group")])
                spinner.succeed(f"{len(matched_files)} [bright_green]Existing watch file{'s' if len(matched_files) > 1 else ''} found[/] in {self.watcher_dir}. Watching for Webhooks related to {len(migrate_data)} devices / {len(self.count_per_site)} sites / {len(groups)} groups.")
            else:
                spinner.succeed(f"No staged devices at Startup.  Watching {self.watcher_dir} for new files that start with {utils.color(self.watcher_prefix)}")

        return migrate_data

    async def get_current_alerts(self, past: int = 30):
        delete_alerts = []
        delete_alerts = []
        if self.delete_ws:
            delete_alerts = await self.delete_ws.api_clients.classic.session._request(self.delete_ws.api_clients.classic.central.get_alerts, from_time=pendulum.now() - pendulum.duration(minutes=past), ack=False)
            if delete_alerts and delete_alerts.output:
                log.info(f"Processing existing alerts for past {past} minutes from {self.delete_ws}")
                formatted_alerts = Alerts([a for a in delete_alerts.output if a["nid"] in CON_UPDATE_NIDS])
                if formatted_alerts:
                    _ = [asyncio.create_task(self.stage_trigger(alert, api_client=self.delete_ws.api_clients)) for alert in formatted_alerts.model_dump()]
        if self.move_ws:
            move_alerts = await self.move_ws.api_clients.classic.session._request(self.move_ws.api_clients.classic.central.get_alerts, from_time=pendulum.now() - pendulum.duration(minutes=past), ack=False)
            if move_alerts and move_alerts.output:
                log.info(f"Processing existing alerts for past {past} minutes from {self.move_ws}")
                formatted_alerts = Alerts([a for a in move_alerts.output if a["nid"] in CON_UPDATE_NIDS])
                if formatted_alerts:
                    _ = [asyncio.create_task(self.stage_trigger(alert, api_client=self.move_ws.api_clients)) for alert in formatted_alerts.model_dump()]

        log.info(f"\u2714  Fetching notifications (previous webhooks) for past {past} minutes complete.")  # \u2714 is :heavy_check_mark: ✔

    def _build_mon_del_reqs(self, cache_devs: list[CacheDevice], data: list[dict[str, str | int | MonitoringWebHook]]) -> BuiltRequests:
        mon_del_reqs, mon_del_items, _stack_ids = [], [], []
        data_by_serial = {dev["serial"]: dev for dev in data}
        cache_by_serial = {cdev.serial: cdev for cdev in cache_devs}

        api = self.delete_ws.api_clients.classic
        for serial in data_by_serial:
            dev = cache_by_serial.get(serial)
            if dev is None:  # not in cache fallback to using what we know from webhook
                func = data_by_serial[serial]["hook_info"].delete_method and getattr(api.monitoring, data_by_serial[serial]["hook_info"].delete_method)
                if func is None:
                    log.warning(f"[dim][dark_orange3]Ignoring[/] [red]delete[/] for [turquoise2]{serial}[/] in [cyan]{self.delete_ws}[/].  Alert Type: [dark_olive_green2]{data_by_serial[serial]['hook_info'].alert_type}[/][/]")
                    continue
                mon_del_reqs += [BatchRequest(func, serial)]
                mon_del_items += [serial]
                continue
            elif dev.generic_type == "switch" and dev.swack_id is not None:
                dev_type = "stack"
                if dev.swack_id in _stack_ids:
                    continue
                else:
                    items = tuple([d.serial for d in cache_devs if d.swack_id == dev.swack_id])
                    _stack_ids += [dev.swack_id]
            else:
                dev_type = dev.generic_type if dev.generic_type != "gw" else "gateway"
                items = dev.serial

            func = getattr(api.monitoring, f"delete_{dev_type}")
            mon_del_reqs += [BatchRequest(func, dev.serial if dev_type != "stack" else dev.swack_id)]
            mon_del_items += [items]

        return BuiltRequests(mon_del_reqs, items=mon_del_items)

    async def update_site_deleted_devs(self, cache_devs: list[CacheDevice], deleted_serials: list[str] = None, not_found_serials: list[str] = None) -> None:
        _new_ready_site_cnt = 0
        if deleted_serials:
            deleted_devs = [dev for dev in cache_devs if dev.serial in deleted_serials]
            for dev in deleted_devs:
                self.deleted_devs_count_per_site[dev.site] = self.deleted_devs_count_per_site.get(dev.site, 0) + 1

        if not_found_serials:
            for serial in not_found_serials:
                this_dev = self.migrate_data.get(serial)
                _site = this_dev and this_dev.get("site")
                if _site:
                    self.deleted_devs_count_per_site[_site] = self.deleted_devs_count_per_site.get(_site, 0) + 1

        pop_list = []
        for site in self.deleted_devs_count_per_site:
            if self.deleted_devs_count_per_site[site] >= self.count_per_site[site]:  # could be > if devices did not exist in cache at startup
                if site in self.deleted_sites:
                    log.warning(f"[dim][dark_orange3]Ignoring[/] site [red]delete[/] for site [cyan]{site}[/], [italic]it's already been deleted.[/][/]")
                    continue
                self.sites_ready_to_delete += [site]
                pop_list += [site]
                _new_ready_site_cnt += 1
                log.info(f":heavy_plus_sign: [medium_turquoise]Site[/] [turquoise2]{site}[/] added to [red]delete[/] queue for {self.delete_ws} [dim italic]All devices deleted[/].")

        if pop_list:
            self.deleted_devs_count_per_site = {k: v for k, v in self.deleted_devs_count_per_site.items() if k not in pop_list}

    async def _get_site_del_reqs(self, cache_sites: list[CacheSite]) -> list[BatchRequest]:
        site_names = self.sites_ready_to_delete
        log.info(f"delete_sites called for {len(site_names)} sites in {self.delete_ws}")
        not_in_cache_sites = [site for site, cache_site in zip(site_names, cache_sites) if cache_site is None]
        not_found = cache_sites.count(None)
        if not_found:
            log.warning(f"{not_found} sites were [red]not found[/] in {self.delete_ws} cache.  They will be skipped[/].  [dim italic]site id is required to delete sites[/]")
            log.debug(f"Sites not found in Cache: {utils.color(not_in_cache_sites)}")
            [self.deleted_sites.append(s) for s, cache_site in zip(site_names, cache_sites) if cache_site is None and s not in self.deleted_sites]
            cache_sites = utils.strip_none(cache_sites)
        if not cache_sites:
            self.sites_ready_to_delete = [name for name in self.sites_ready_to_delete if name not in not_in_cache_sites]
            return

        return [BatchRequest(self.delete_ws.api_clients.classic.central.delete_site, s.id) for s in cache_sites]

    async def eval_site_del_resp(self, batch_resp: BatchResponse, cache_sites: list[CacheSite]) -> BatchResponse | None:
        not_found_sites = []
        if batch_resp.failed:
            log.error(f"{len(batch_resp.failed)} of {len(batch_resp.responses)} site deletions failed in {self.delete_ws}")
            not_found_sites = [site.name for res, site in zip(batch_resp.responses, cache_sites) if res.status == 404 or (res.status == 400 and "NO_SUCH_SITE_ID" in res.output.get("description", ""))]
            if not_found_sites:
                log.warning(f"{len(not_found_sites)} sites returned [red]SITE_ERR_NO_SUCH_SITE_ID[/] meaning the site [red]does not exist[/] in {self.delete_ws} [dim italic]Removing from queue[/]")
                self.deleted_sites = [*self.deleted_sites, *[s for s in not_found_sites if s not in self.deleted_sites]]

        deleted_sites = [site.name for res, site in zip(batch_resp.responses, cache_sites) if res.ok]
        if deleted_sites:
            self.deleted_sites += deleted_sites
            try:  # cache update
                update_data = [{"name": site} for site in [*deleted_sites, *not_found_sites]]
                asyncio.create_task(self.delete_ws.cache.update_site_db(data=update_data, action=DBAction.DELETE))
            except Exception as e:  # pragma: no cover
                log.exception(f"{repr(e)} occured during attempt to update sites cache in {self.delete_ws}")

        if any([deleted_sites, not_found_sites]):
            self.sites_ready_to_delete = [name for name in self.sites_ready_to_delete if name not in [*deleted_sites, *not_found_sites]]

        render.display_results(
            batch_resp.responses,
            title=f"Site Deletions {len(batch_resp)} sites in {self.delete_ws}",
            tablefmt="action",
            exit_on_fail=False
        )

        return batch_resp

    def get_devs_from_cache(self, data: list[dict[str, Any]], cache: Cache, is_mon_delete: bool = False) -> list[CacheDevice]:
        serials = [d["serial"] for d in data]
        cache_devs = cache.bulk_dev_cache_lookup(serial_numbers=serials, refresh_on_fail=False)  # retry_on_fail is problematic as it uses asyncio.run and that can't be called from a running event_loop, also we are reacting to New Device connected, so the devs will not exist in the cache yet
        not_found = cache_devs.count(None)
        if not_found:
            log.warning(f"{not_found} device{'s were' if not_found > 1 else ' was'} [red]not found in cache[/].  Processing moves based on info from WebHook")
            cache_devs = utils.strip_none(cache_devs)

        return cache_devs

    async def device_move_cache_update(
            self,
            mv_resp: list[Response],
            update_data: dict[str, dict[str, Any]],
            serials_by_site: dict[str, list[str]] = None,  # this needs to be {site_name: ["serial", ...]}
            serials_by_group: dict[str, list[str]] = None,
        ) -> dict[str, list[Literal["site", "group"]]]:
        serials_by_site = serials_by_site or {}
        serials_by_group = serials_by_group or {}
        failures = {}
        serials = set(
            [
                *([s for s_list in serials_by_site.values() for s in s_list]),
                *([g for g_list in serials_by_group.values() for g in g_list]),
            ]
        )
        moves_by_type = {
            "site": serials_by_site or {},
            "group": serials_by_group or {}
        }

        # updates_by_serial = {s: {} for s in serials}
        updates_by_serial = update_data
        for r, (move_type, name, serials) in zip(mv_resp, [(move_type, name, serials) for move_type, v in moves_by_type.items() for name, serials in v.items()]):
            if move_type == "site":
                for s in serials:
                    if r.ok:
                        updates_by_serial[s]["site"] = name
                        self.moved_serials_site += [s]
                    else:
                        site_failures = r.raw.get("failures", [])
                        already_associated_serials = [f.get("device_id") for f in site_failures if f.get("reason", "") == "SITE_ERR_SITE_ID_ALREADY_ASSOCIATED"]
                        if already_associated_serials:
                            for _serial in already_associated_serials:
                                updates_by_serial[_serial]["site"] = name
                                self.moved_serials_site += [_serial]
                        else:
                            utils.update_dict(failures, s, "site")
            if move_type == "group":  # All or none here as far as the response.
                for s in serials:
                    if r.ok:
                        updates_by_serial[s]["group"] = name
                        self.moved_serials_group += [s]
                    else:
                        utils.update_dict(failures, s, "group")

        if [s for s in updates_by_serial if updates_by_serial[s]]:
            asyncio.create_task(
                self.move_ws.cache.update_dev_db(
                    data=[{"serial": s, **updates_by_serial[s]} for s in updates_by_serial if updates_by_serial[s]],
                    action=DBAction.UPSERT
                )
            )
        return failures

    async def _site_moves(self, data: list[dict[str, str | int | MonitoringWebHook]], cache_by_serial: dict[str, CacheDevice], site_name_id_map: dict[str, int]) -> tuple[list[BatchRequest], dict[str, list[str]]]:
        def _get_site_id_dev_type_key(site: str, dev_type: GenericDeviceTypes):
            return f"{site_name_id_map.get(site, f'NOT_FOUND_{site}')}~|~{dev_type}"

        serials_by_site_id_type: dict[str, list[str]] = {}
        for dev in data:
            cache_dev = cache_by_serial.get(dev["serial"])
            if not dev.get("site"):
                continue
            if cache_dev and cache_dev.site == dev["site"]:
                log.warning(f"[dim][turquoise2]{dev['serial']}[/] [dark_orange3]Ignoring[/] move to site {dev['site']} in {self.move_ws}.  [italic]Device already in site {dev['site']}[/][/]")
                continue
            utils.update_dict(serials_by_site_id_type, _get_site_id_dev_type_key(site=dev["site"], dev_type=dev['hook_info'].dev_type), dev["serial"])

        site_mv_reqs = []
        api = self.move_ws.api_clients.classic
        if serials_by_site_id_type:
            for k, v in serials_by_site_id_type.items():
                if k.startswith("NOT_FOUND"):
                    log.warning(f"Skipping site move {k.split('~|~')[0].removeprefix('NOT_FOUND_')}.  Unable to retrieve site_id from cache. [dim italic]Does the site exist?[/]")
                    continue
                site_id, dev_type = k.split("~|~")
                site_mv_reqs += [BatchRequest(api.central.move_devices_to_site, site_id=int(site_id), serials=v, device_type=dev_type)]

        return site_mv_reqs, serials_by_site_id_type

    async def _group_moves(self, data: list[dict[str, str | int | MonitoringWebHook]]) -> tuple[list[BatchRequest], dict[str, list[str]]]:
        move_groups = list(set([d["group"] for d in data if "group" in d]))
        serials_by_group = {group: [] for group in move_groups}
        [utils.update_dict(serials_by_group, dev["group"], dev["serial"]) for dev in data if dev["group"] != dev["hook_info"].details.group_name]
        api = self.move_ws.api_clients.classic
        group_mv_reqs = []
        if serials_by_group:
            group_mv_reqs = [BatchRequest(api.configuration.move_devices_to_group, group=k, serials=chunk, cx_retain_config=True) for k, v in serials_by_group.items() for chunk in utils.chunker(v, 50)]

        return group_mv_reqs, serials_by_group

    async def move_devices(self) -> BatchResponse:
        data = self.ready_to_move
        cache = self.move_ws.cache
        move_sites = [s for s in set([d.get("site") for d in data]) if s is not None]
        cache_sites = cache.bulk_site_cache_lookup(move_sites, refresh_on_fail=False)
        site_name_id_map = {s.name: s.id for s in cache_sites if s is not None}
        cache_devs = self.get_devs_from_cache(self.ready_to_move, cache=cache)
        cache_by_serial = {d.serial: d for d in cache_devs}

        group_mv_task = asyncio.create_task(self._group_moves(data))
        site_mv_task = asyncio.create_task(self._site_moves(data, cache_by_serial=cache_by_serial, site_name_id_map=site_name_id_map))
        (site_mv_reqs, serials_by_site_id_type), (group_mv_reqs, serials_by_group) = await asyncio.gather(site_mv_task, group_mv_task)

        api = self.move_ws.api_clients.classic
        batch_resp = []
        if any([site_mv_reqs, group_mv_reqs]):
            batch_resp = await api.session._batch_request([*site_mv_reqs, *group_mv_reqs], continue_on_fail=True)

        # site_responses = batch_resp[0:len(site_mv_reqs)]
        # group_responses = batch_resp[len(site_mv_reqs):]
        try:
            site_id_name_map = {v: k for k, v in site_name_id_map.items()}
            serials_by_site_name = {site_id_name_map[int(k.split("~|~")[0])]: v for k, v in serials_by_site_id_type.items()}
            update_data_by_serial = {dev["serial"]: {"name": dev["name"], "status": "Up", "type": dev["hook_info"].dev_type, "model": dev.get("model"), "ip": dev.get("ip"), "serial": dev["serial"], "mac": dev["mac"], "group": dev["hook_info"].details.group_name, "version": ""} for dev in self.ready_to_move}
            failures = await self.device_move_cache_update(batch_resp, update_data=update_data_by_serial, serials_by_site=serials_by_site_name, serials_by_group=serials_by_group)
            self.ready_to_move = [d for d in self.ready_to_move if d["serial"] in failures]
        except Exception as e:
            log.exception(f"{repr(e)} during attempt to update devices cache after group/site moves in {self.move_ws}")

        render.display_results(batch_resp, tablefmt="action", title=f"Site/Group moves for {self.move_ws}", exit_on_fail=False)

        return BatchResponse(batch_resp)

    async def _get_dev_delete_reqs(self) -> BuiltRequests:
        cache = self.delete_ws.cache
        cache_devs = self.get_devs_from_cache(self.ready_to_delete, cache=cache, is_mon_delete=True)
        data = self.ready_to_delete

        return self._build_mon_del_reqs(cache_devs, data=data)

    async def eval_dev_del_resp(self, batch_resp: BatchResponse, req_info: BuiltRequests, cache_devs: list[CacheDevice]) -> BatchResponse | None:
        cache = self.delete_ws.cache
        common = self.delete_ws.common
        not_found_serials = []
        deleted_serials = []
        if batch_resp.failed:
            not_found_serials = [res.url.name for res in batch_resp.failed if res.status == 404]  # res.url.name is the serial...
            if len(not_found_serials) != len(batch_resp.failed):
                log.error(f"{len(batch_resp.failed)}  of {len(batch_resp.responses)} failed to delete from monitoring in {self.delete_ws}.")
            if not_found_serials:
                log.warning(f"{len(not_found_serials)} devices returned a 404 meaning the device [red]does not exist[/] in {self.delete_ws} monitoring views.  [dim italic]Removing from queue[/]", caption=True, log=True)
                self.deleted_serials = [*self.deleted_serials, *[s for s in not_found_serials if s not in self.deleted_serials]]
                self.ready_to_delete = [d for d in self.ready_to_delete if d["serial"] not in not_found_serials]

        if batch_resp.passed:
            try:
                update_data = common._extract_serials_from_built_requests_items(req_info.items, batch_resp.responses)  # [{"serial": USABC123XY}, ...]
                if update_data:
                    deleted_serials = [d["serial"] for d in update_data]
                    self.deleted_serials += deleted_serials
                    self.ready_to_delete = [dev for dev in self.ready_to_delete if dev["serial"] not in deleted_serials]
                    asyncio.create_task(cache.update_dev_db(update_data, action=DBAction.DELETE))  # Cache Updates
            except Exception as e:
                log.exception(f"{repr(e)} during attempt to update device monitoring db in clicommon.batch_delete_devices_glp.")

        if any([deleted_serials, not_found_serials]):
            asyncio.create_task(self.update_site_deleted_devs(cache_devs, deleted_serials=deleted_serials, not_found_serials=not_found_serials))

        render.display_results(
            batch_resp.responses,
            title=f"Monitoring UI [red]deletes[/] for {len(batch_resp.responses)} devices in {self.delete_ws}",
            tablefmt="action",
            exit_on_fail=False
        )

        return batch_resp

    async def execute_triggers(self) -> ExecutionResults:
        move_task: asyncio.Task | None = None
        del_task: asyncio.Task | None = None
        del_resp: list[Response] | None = None
        site_del_resp: list[Response] | None = None
        dev_del_resp: list[Response] | None = None
        move_resp: list[Response] | None = None
        dev_del_reqs: list[BatchRequest] = []
        site_del_reqs: list[BatchRequest] = []
        del_cache_devs: list[CacheDevice] = []
        del_cache_sites: list[CacheSite] = []

        try:
            if self.ready_to_move:  # TODO create tasks then gather running the moves and deletes in parallel (with device site deletes sequential)
                log.info(f"Executing [bright_green]moves[/] for {len(self.ready_to_move)} devices in {self.move_ws}")
                move_task = asyncio.create_task(self.move_devices())
            if self.ready_to_delete:
                log.info(f"Executing [red]deletes[/] for {len(self.ready_to_delete)} devices in {self.delete_ws}")
                del_cache_devs = self.get_devs_from_cache(self.ready_to_delete, cache=self.delete_ws.cache, is_mon_delete=True)
                data = self.ready_to_delete
                dev_del_req_info = self._build_mon_del_reqs(del_cache_devs, data=data)
                dev_del_reqs = dev_del_req_info.requests
            if self.sites_ready_to_delete:
                del_cache_sites = self.delete_ws.cache.bulk_site_cache_lookup(self.sites_ready_to_delete, refresh_on_fail=False)  # All pertinent caches refreshed on launch
                log.info(f"Executing [red]deletes[/] for {len(self.sites_ready_to_delete)} sites in {self.delete_ws}")
                site_del_reqs = await self._get_site_del_reqs(del_cache_sites) or []

            del_reqs = [*dev_del_reqs, *site_del_reqs]
            if del_reqs:
                del_task = asyncio.create_task(self.delete_ws.api_clients.classic.session._batch_request(del_reqs))

            tasks = [t for t in [move_task, del_task] if t is not None]
            if tasks:
                responses = await asyncio.gather(*tasks)
                if move_task:  # HACK has to be a more elegant way
                    move_resp = responses[0]
                    if del_task:
                        del_resp = responses[1]
                else:
                    del_resp = responses[0]

            if del_resp:
                if dev_del_reqs:
                    dev_del_resp = await self.eval_dev_del_resp(BatchResponse(del_resp[0:len(dev_del_reqs)]), req_info=dev_del_req_info, cache_devs=del_cache_devs)
                site_del_resp = await self.eval_site_del_resp(BatchResponse(del_resp[len(dev_del_reqs):]), cache_sites=del_cache_sites)

        except Exception as e:
            log.exception(f"{repr(e)} in wh_watcher._execute_triggers()")

        return ExecutionResults(move=move_resp, delete=dev_del_resp, site_delete=site_del_resp)

    async def stage_trigger(self, data: dict[str, Any], api_client: APIClients) -> None:
        """Evaluates Webhook and determines if move / delete should be done based on type of WebHook.

        This method simply updates the ready_to_move / ready_to_delete / sites_ready_to_delete class attributes.
        No action is taken at this stage.

        Args:
            data (dict[str, Any]): The raw data (dict) from WebHook
            api_client (APIClients): The api_client associated with the workspace the WebHook is for.
        """
        skip = False
        hook_info = MonitoringWebHook(**data)
        wh_ts_str = f"WH ts: {DateTime(hook_info.timestamp, format='timediff')}."
        if hook_info.state != "Open":
            skip = True
        if hook_info.type == "OTHER":
            skip = True
        if hook_info.device_id not in wh_common.migrate_data:
            log.info(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace based on [dark_olive_green2]{hook_info.alert_type}[/] event. {wh_ts_str}  [italic]Device not included in migrate data.[/]")
            skip = True

        if not skip:
            if hook_info.type == "CONNECTED" and self.move_ws.config.workspace_object.classic.customer_id == hook_info.cid:
                if env.watcher_no_moves:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_olive_green2]{hook_info.alert_type}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace. {wh_ts_str} [dim italic]{env_var.watcher_no_moves} env var set[/].")
                    return
                _to_site = self.migrate_data[hook_info.device_id].get("site")
                _dev_name = self.migrate_data[hook_info.device_id].get("name")
                _to_group = self.migrate_data[hook_info.device_id].get("group")
                if _to_site and hook_info.device_id in self.moved_serials_site:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] Move to site [cyan]{_to_site}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/]  {wh_ts_str}. [dim italic]Site move already performed[/].")
                elif _to_group and hook_info.device_id in self.moved_serials_group:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] Move to Group [cyan]{_to_group}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace. {wh_ts_str} [dim italic]Group move already performed[/].")
                elif hook_info.device_id in [d["serial"] for d in self.ready_to_move]:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace based on [dark_olive_green2]{hook_info.alert_type}[/] event.  {wh_ts_str}  [dim italic]Device Already queued for move.[/]")
                else:  # STAGE MOVE
                    if _dev_name and _to_site and not _dev_name.startswith(_to_site):  # REMOVE this is specific to dtfd migration
                        log.warning(f"[turquoise2]{hook_info.device_id}[/] Move to site [cyan]{_to_site}[/] device name does not start with site name.  {_dev_name = }  {_to_site = }.")
                    self.ready_to_move += [{**self.migrate_data[hook_info.device_id], "hook_info": hook_info}]
                    log.info(f":heavy_plus_sign: [turquoise2]{hook_info.device_id}[/] added to [bright_green]move[/] queue for [cyan]{api_client.config.workspace}[/] workspace based on [dark_olive_green2]{hook_info.alert_type}[/] event. {wh_ts_str}")
            elif hook_info.type == "DISCONNECTED" and self.delete_ws and self.delete_ws.config.workspace_object.classic.customer_id == hook_info.cid:
                if env.watcher_no_deletes:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_olive_green2]{hook_info.alert_type}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace {wh_ts_str}. [dim italic]{env_var.watcher_no_deletes} env var set[/].")
                    return
                if hook_info.device_id in [d["serial"] for d in self.ready_to_delete]:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace based on [dark_olive_green2]{hook_info.alert_type}[/] event. {wh_ts_str}  Device already queued for delete.[/]")
                elif hook_info.device_id in [s for s in self.deleted_serials]:
                    log.info(f"[dim][turquoise2]{hook_info.device_id}[/] Delete device [dark_orange3]Ignored[/] for [cyan]{api_client.config.workspace}[/] workspace.  {wh_ts_str} [dim italic]Delete already performed[/].")
                elif not hook_info.delete_method:  # this can happen on service restarts if device was already deleted in previous session
                    log.warning(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_orange3]Ignoring[/] [red]delete[/] in {self.delete_ws}. {wh_ts_str} Alert Type: [dark_olive_green2]{hook_info.alert_type}[/][/]")
                else:  # STAGE DELETE
                    self.ready_to_delete += [{**self.migrate_data[hook_info.device_id], "hook_info": hook_info}]
                    log.info(f":heavy_plus_sign: [turquoise2]{hook_info.device_id}[/] added to [red]delete[/] queue for [cyan]{api_client.config.workspace}[/] workspace based on [dark_olive_green2]{hook_info.alert_type}[/] event. {wh_ts_str}")
            else:
                log.info(f"[dim][turquoise2]{hook_info.device_id}[/] [dark_orange3]Ignoring[/]  [dark_olive_green2]{hook_info.alert_type}[/] {wh_ts_str} [dim italic]Alert Type not monitored[/]")
        else:
            log.debug(f"[dark_orange3]Ignored[/] Unrelated WebHook. {wh_ts_str} {hook_info.device_id}|{hook_info.alert_type}", show=config.debug)

    async def collect_task_results(self) -> None:
        if self.tasks:
            log.info(f"Collecting responses for {len(self.tasks)} executed moves/deletes")
            tasks = self.tasks.copy()  # otherwise you'll remove tasks added while this loop is running
            for task in tasks:
                this_res = await task
                self.trigger_results += this_res
            self.tasks = [t for t in self.tasks if t not in tasks]

    async def execution_loop(self) -> None:
        log.info(":arrows_counterclockwise: [green]Execution loop starting[/]")
        half_log_sent = False
        while WHCommon.RUNNING:
            if self.tasks:
                _ = asyncio.create_task(self.collect_task_results())

            if self.has_staged_updates and self.do_updates:
                self.tasks = [asyncio.create_task(self.execute_triggers())]
                log.info(f":play_button: [bright_green]Processing Updates[/] {self.staged_cnt_str}")
            elif (self.ready_to_delete or self.ready_to_move) and pendulum.now() >= self.next_update:
                self.tasks = [asyncio.create_task(self.execute_triggers())]
                log.info(f":play_button: [bright_greenProcessing Updates (secondary eval)[/] {self.staged_cnt_str}")
            else:
                log.debug("No staged updates?", show=config.debug)

            if pendulum.now() > self.next_update:
                self.next_update = pendulum.now() + pendulum.duration(seconds=self.update_interval)
                half_log_sent = False
                if not self.has_staged_updates:
                    log.info(f"No Updates to perform.  Next update in {self.next_update_pretty}. {self.staged_cnt_str}")
            elif not self.has_staged_updates and not half_log_sent and pendulum.now() >= pendulum.now() + pendulum.duration(seconds=int(self.update_interval / 2)):
                log.info(f"[dim]Deffered Updates[/] {self.staged_cnt_str}")
                log.info(f"Next Update in {self.update_interval} minutes or once 7 moves/deletes are collected.")
                half_log_sent = True

            await asyncio.sleep(1)

    def start(self) -> None:
        WHCommon.RUNNING = True
        if self._past:
            _ = asyncio.create_task(self.get_current_alerts(self._past), name="get_current_alerts")
        if self._refresh:
            _ = asyncio.create_task(self.refresh_cache(), name="cache_refresh")
        _ = asyncio.create_task(self.execution_loop(), name="execution_loop")

    def stop(self) -> None:
        WHCommon.RUNNING = False
        if self.tasks:
            with render.Spinner(f"Gathering results from last {len(self.tasks)} executed tasks"):
                task = asyncio.create_task(self.collect_task_results())
                _ = asyncio.gather(task)


class MyEventHandler(FileSystemEventHandler):
    def __init__(self, wh_common: WHCommon):
        self.wh_common = wh_common

    def _is_watch_event(self, event: FileSystemEvent) -> bool:
        if isinstance(event, FileCreatedEvent) or isinstance(event, FileModifiedEvent):
            return any([Path(event.src_path).name.startswith(pfx) and "retry" not in Path(event.src_path).name for pfx in self.wh_common.watcher_prefix])

    def handle_file_change(self, event: FileSystemEvent) -> None:
        if self._is_watch_event(event):
            try:
                this = _common._get_import_file(Path(event.src_path), "devices")
                self.wh_common.migrate_data = {**self.wh_common.migrate_data, **{d["serial"]: d for d in this}}
                self.wh_common.count_per_site = Counter([d["site"] for d in wh_common.migrate_data.values() if "site" in d])
                log.info(f"Captured new trigger data ({len(wh_common.migrate_data)} devices) from {event.src_path}")
            except Exception as e:
                log.exception(f"{repr(e)} while trying to fetch import data from {event.src_path}")  # Modifying a file with nano can cause an transient event where device does not exist

    # when a file is created 2 events are recieved one for create (on_created) and another for modify.  So we will just watch for modify to avoid duplicate
    def on_modified(self, event: FileSystemEvent) -> None:
        self.handle_file_change(event)


async def raw_capture(data: dict):
    with RAW_CAPTURE_FILE.open("a") as rf:
        rf.write(json.dumps(data))


def verify_header_auth(data: dict, svc: str, sig: str, ts: str, del_id: str) -> APIClients | None:
    """
    This method ensures integrity and authenticity of the data
    received from Aruba Central via Webhooks
    """
    # Token obtained from Aruba Central Webhooks page as provided in the input
    for workspace in [wh_common.delete_ws, wh_common.move_ws]:
        if workspace is None:
            continue
        workspace: WorkSpace

        token = workspace.config.webhook.token
        token = token.encode('utf-8')  # TODO they will get NoneType Object has no attribute encode if the workspace or webhook: token is not defined in the config.  Need to verify at launch

        # Construct HMAC digest message
        _data = json.dumps(data)
        sign_data = f"{_data}{svc}{del_id}{ts}"
        sign_data = sign_data.encode('utf-8')

        # Find Message signature using HMAC algorithm and SHA256 digest mod
        dig = hmac.new(token, msg=sign_data, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(dig).decode()

        # Verify if the signature received in header is same as the one found using HMAC
        if sig == signature:
            return workspace.api_clients  # returns either the api_session for the src (delete devices from monitoring UI) workspace or the dest (move devices) workspace

    if wh_common.move_ws and wh_common.move_ws.config and data.get("cid") == wh_common.move_ws.config.workspace_object.classic.customer_id:
        log.error("webhook customer id matched dest_workspace (move operations), but token veifification failed.", show=True)
    elif wh_common.delete_ws and wh_common.delete_ws.config and data.get("cid") == wh_common.delete_ws.config.workspace_object.classic.customer_id:
        log.error("webhook customer id matched src_workspace (delete operations), but token veifification failed.", show=True)


async def log_request(request: Request, route: str):
    log.info(f'[NEW API RQST IN] {request.client.host} {route} via API')


@asynccontextmanager
async def lifespan(app: FastAPI):
    wh_common.start()
    yield

    # Clean up
    wh_common.stop()


app = FastAPI(
    title='Central CLI Migration Webhook Proxy',
    docs_url='/api/docs',
    redoc_url="/api/redoc",
    openapi_url='/api/openapi/openapi.json',
    version="1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=f"{Path(__file__).parent}/static"), name="static")


@app.get('/favicon.ico', include_in_schema=False)
async def _favicon():
    return FileResponse(Path(__file__).parent / "static/favicon.ico")


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title,
        swagger_favicon_url="/static/favicon.ico",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
    )


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.post("/webhook", status_code=200, response_model=HookResponse, responses=wh_resp_schema)
async def webhook(
    data: dict,
    request: Request,
    response: FastAPIResponse,
    content_length: int = Header(...),
    x_central_service: str = Header(None),
    x_central_signature: str = Header(None),
    x_central_delivery_timestamp: str = Header(None),
    x_central_delivery_id: str = Header(None),
):
    if content_length > 1_000_000:
        # To prevent memory allocation attacks
        log.error(f"Incoming wh ignored, Content too long:  content_length: ({content_length})")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"result": "Content too long"}
        )

    # test webhook from central lacks an id... add it to avoid validation error
    if data["nid"] == 1250:
        data["id"] = data.get("id", "TEST-HOOK-IGNORE")

    unauthorized_response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"result": "Unauthorized", "updated": False}
    )

    global wh_common
    raw_input: dict[str, Any] = await request.json()
    if x_central_signature:
        api_client = verify_header_auth(
            raw_input,
            svc=x_central_service,
            sig=x_central_signature,
            ts=x_central_delivery_timestamp,
            del_id=x_central_delivery_id,
        )
        if api_client is not None:
            asyncio.create_task(wh_common.stage_trigger(data, api_client))
            if COLLECT:
                asyncio.create_task(raw_capture(data))
        else:
            log.debug("[dim][dark_orange3]Ignoring[/] POST from Central with [red]invalid signature[/] [italic](check webhook token in config)[/][/]", show=config.debug)
            return unauthorized_response
    elif TEST_MODE:  # This is to facilitate testing with curl and the like, allows payload without the headers needed to validate signature.
        if not WHCommon._test_mode_log_sent:
            log.info("Message received with no signature, [bright_green]TEST MODE ENABLED[/]... Processing message.  Allowing messages without signature. [dim italic]This message will not be repeated[/]", log=config.debug)
            WHCommon._test_mode_log_sent = True
        if str(raw_input.get("cid", "")) == wh_common.delete_ws.config.workspace_object.classic.customer_id:
            api_client = wh_common.delete_ws.api_clients
        else:
            api_client = wh_common.move_ws.api_clients
        asyncio.create_task(wh_common.stage_trigger(data, api_client))
    else:
        log.error("[dim][dark_orange3]Ignoring[/] Message received with no signature", show=True)
        return unauthorized_response

    return {
            "result": "ok",
            "updated": True,  # updated is a relic of the existing ReponseModel created for nms_proxy, doesn't hurt anything here.
        }


def start_webhook_watcher(workspace: str, watcher_dir: Path, watcher_prefix: str | list[str] = ["migrate", "devices"], port: int = config.webhook.port, delete_ws: str = None, test_mode: bool = False, collect: bool = False, update_interval: int = 10, refresh: bool = True, past: int = 30):
    port = port or config.webhook.port
    render.console.print(f"Webhook Proxy [dim italic](hook-watcher)[/] will listen on port {port}")
    move_ws = workspace or config.workspace
    if move_ws == delete_ws:
        render.econsole.print(f"{emoji.warn} Source WorkSpace {delete_ws} ([red]Delete devices[/]) and Destination WorkSpace {move_ws} ([bright_green]Move devices[/]) are the same.")
        sys.exit(1)

    if test_mode:
        global TEST_MODE
        TEST_MODE = True
        log.info(f"{emoji.info} Test mode enabled.", show=True)
    if collect:
        global COLLECT
        COLLECT = True
        log.info("Collection mode enabled.", show=True)

    render.econsole.print(f"Watcher will process [cyan]New device connected[/] Webhooks in [cyan]{move_ws}[/] workspace and process [medium_spring_green]moves[/] (group/site), based on data found in import_files.")
    if delete_ws:
        render.econsole.print(f"Watcher will process [cyan]devices disconnected[/] Webhooks in [cyan]{delete_ws}[/] workspace and process monitoring UI [red]deletes[/], based on data found in import_files.")

    global wh_common
    wh_common = WHCommon(watcher_dir=watcher_dir, watcher_prefix=watcher_prefix, move_ws=move_ws, delete_ws=delete_ws, update_interval=update_interval, refresh=refresh, past=past)

    with render.Spinner(f"Starting Directory Watcher to monitor {watcher_dir} for new files that start with {utils.summarize_list(watcher_prefix, sep=' or ')}.") as spinner:
        event_handler = MyEventHandler(wh_common)
        observer = Observer()
        observer.schedule(event_handler, str(wh_common.watcher_dir), recursive=False)
        observer.start()
        spinner.succeed()

    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        ...
    except KeyboardInterrupt:
        log.info("hook watcher process terminated.  Processing stages tasks...")
    except Exception as e:
        log.exception(f"Exception: {repr(e)}, during attempt to start wh_watcher", show=True)

    observer.stop()
    observer.join()

    if wh_common.trigger_results:
        outfile = config.outdir / "watcher-results"
        wh_common.trigger_results.display(outfile=outfile)


CONTEXT_SETTINGS = {
    "help_option_names": ["?", "--help"]
}

cli_app = typer.Typer(context_settings=CONTEXT_SETTINGS, rich_markup_mode="rich")

watcher_prefix_default = "'migrate' or 'devices'"
@cli_app.command(help="Start WebHook Watcher")  # NoQA
def start(
    port: int = typer.Option(config.webhook.port, "-P", "--port", help="Port to listen on (overrides config value if provided)", show_default=True),
    collect: bool = typer.Option(False, "--collect", "-c", help="Store raw webhooks in local json file", rich_help_panel="Dev Options", hidden=not env.is_dev_user),
    test_mode: bool = typer.Option(False, "--test-mode", help="Enable test mode [dim italic](Allows hooks with no signature)[/]", rich_help_panel="Dev Options", hidden=not env.is_dev_user),
    watcher_dir: Path = typer.Option(
        Path.cwd(),
        "-D",
        "--dir",
        help=f"For [cyan]hook-watcher[/].  Directory to watch for device files defining how to respond to devices going online/offline. {render.help_block(f'current directory ({Path.cwd()})')}",
        show_default=False,
        envvar=env_var.watcher_dir
    ),
    watcher_prefix: str = typer.Option(None, "--prefix", help=f"filename prefix to watch for.  {render.help_block(watcher_prefix_default)}", show_default=False),
    delete_ws: str = typer.Option(
        None,
        envvar=env_var.delete_ws,
        help=f"The Aruba Central [dim italic]([green]GreenLake[/green])[/] WorkSpace for delete operations.  {emoji.warn} Devices found in watch files will be deleted from this workspace once disconnected.",
        autocompletion=_common.cache.workspace_completion,
        show_default=False,
    ),
    update_interval: int = typer.Option(10, "-I", "--update-interval", help="Update interval in seconds.  Device moves are queued and sent periodically to reduce API calls.", show_default=True),
    no_refresh: bool = _common.options.get("no_refresh", help="Do not perform cache update at startup."),
    past: int = typer.Option(30, "--past", help=f"Fetch current alerts.  {render.help_block('30 mins. (specify 0 to skip fetch of current alerts from REST API)')}", envvar=env_var.watcher_current_alerts_past),
    debug: bool = _common.options.debug,
    default: bool = _common.options.default,
    workspace: str = _common.options.get("workspace", "--ws", "--workspace", "--move-ws", default=config.workspace, help=f"The Aruba Central [dim italic]([green]GreenLake[/green])[/] WorkSpace for move operations.  {emoji.info} Devices found in watch files will be moved to defined group/site once connected.",),
) -> None:  # pragma: no cover
    watcher_prefix = watcher_prefix or ["migrate", "devices"]
    start_webhook_watcher(workspace=workspace, watcher_dir=watcher_dir, watcher_prefix=watcher_prefix, port=port, delete_ws=delete_ws, test_mode=test_mode, collect=collect, update_interval=update_interval, refresh=not no_refresh, past=past)


if __name__ == "__main__":
    cli_app()
