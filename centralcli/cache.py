#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Sequence, Set, Union, Generator, Tuple, Callable

import typer
from rich import print
from rich.console import Console
from tinydb import Query, TinyDB
from tinydb.table import Table
from copy import deepcopy

from centralcli import CentralApi, Response, cleaner, config, constants, log, models, render, utils

try:
    import readline  # noqa imported for backspace support during prompt.
except Exception:
    pass

try:
    from fuzzywuzzy import process  # type: ignore noqa
    FUZZ = True
except Exception:
    FUZZ = False

# Used to debug completion
err_console = Console(stderr=True)
emoji_console = Console()
console = Console(emoji=False)
TinyDB.default_table_name = "devices"

# DBType = Literal["dev", "site", "template", "group"]
DEV_COMPLETION = ["move", "device", ""]
SITE_COMPLETION = ["site"]
GROUP_COMPLETION = ["group", "wlan"]
TEMPLATE_COMPLETION = []
EXTRA_COMPLETION = {
    "move": ["site", "group"]
}
LIB_DEV_TYPE = {
    "AOS-CX": "cx",
    "AOS-S": "sw",
    "gateway": "gw"
}


def get_cencli_devtype(dev_type: str) -> str:
    """Convert device type returned by API to consistent cencli types

    Args:
        dev_type(str): device type provided by API response

    Returns:
        str: One of ["ap", "sw", "cx", "gw"]
    """
    return LIB_DEV_TYPE.get(dev_type, dev_type)


class CentralObject:
    def __init__(
        self,
        db: Literal["dev", "site", "template", "group", "label", "mpsk", "portal"],
        data: Union[list, Dict[str, Any]],
    ) -> Union[list, Dict[str, Any]]:
        self.is_dev, self.is_template, self.is_group, self.is_site, self.is_label, self.is_mpsk, self.is_portal = False, False, False, False, False, False, False
        data: Dict | List[dict] = None if not data else data
        setattr(self, f"is_{db}", True)
        self.cache = db

        if isinstance(data, list):
            if len(data) > 1:
                raise ValueError(f"CentralObject expects a single item. Got list of {len(data)}")
            elif data:
                data = data[0]

        self.data = data

        # When building Central Object from Inventory this is necessary
        # TODO maybe pydantic model
        if self.is_dev and self.data:
            self.name = self.data["name"] = self.data.get("name", self.data["serial"])
            self.status = self.data["status"] = self.data.get("status")
            self.ip = self.data["ip"] = self.data.get("ip")
            self.site = self.data["site"] = self.data.get("site")
            self.swack_id = self.data["swack_id"] = self.data.get("swack_id")
            self.serial: str = self.data.get("serial")

    def __bool__(self):
        return bool(self.data)

    def __repr__(self):
        _ = f"<{self.__module__}.{type(self).__name__} ({self.cache}|{self.get('name', bool(self))}) object at {hex(id(self))}>"
        return _

    def __str__(self):
        if isinstance(self.data, dict):
            return "\n".join([f"  {k}: {v}" for k, v in self.data.items()])

        return str(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, name: str) -> Any:
        if hasattr(self, "data") and self.data:
            if name in self.data:
                return self.data[name]

        if hasattr(self, "data") and hasattr(self.data, name):
            return getattr(self.data, name)

        log.exception(f"Cache LookUp Failure: 'CentralObject' has no attribute '{name}'", show=True)
        raise typer.Exit(1)

    def __fields__(self) -> List[str]:
        return [k for k in self.__dir__() if not k.startswith("_") and not callable(k)]

    @property
    def generic_type(self):
        if "type" in self.data:
            return "switch" if self.data["type"].lower() in ["cx", "sw"] else self.data["type"].lower()

    def _get_help_text_parts(self):
        parts = []
        if self.cache == "site":
            parts = [
                "Site",
                *[a for a in [self.city, self.state, self.zipcode] if a]
            ]
        elif self.cache == "template":
            parts = [
                self.device_type,
                self.model,
                f"s:{self.group}",
            ]
        elif self.cache == "dev":
            parts = [
                self.name,
                self.generic_type.upper(),
                self.serial,
                self.mac,
                self.ip,
            ]
            # TODO Inventory only devices don't have group attribute
            if "group" in self.data.keys():
                parts += [self.group]
            if "site" in self.data.keys():
                parts += [self.site]

            parts = utils.strip_none(parts, strip_empty_obj=True)
            if self.site:
                parts[-1] = f"s:{parts[-1]}"
            if "group" in self.data.keys() and self.group:
                parts[-2 if self.site else -1] = f"g:{parts[-2 if self.site else -1]}"
        elif self.cache == "group":
            parts = ["Group", self.name]
        elif self.cache == "label":
            parts = [self.data.get("name"), f"id: {self.data.get('id', 'ERROR')}"]

        return parts

    @property
    def help_text(self):
        parts = self._get_help_text_parts()
        return "|".join(
            [
                typer.style(p, fg="blue" if not idx % 2 == 0 else "cyan") for idx, p in enumerate(parts)
            ]
        )

    @property
    def rich_help_text(self):
        parts = self._get_help_text_parts()
        return "[reset]|".join(
            [
                f'{"[green]" if not idx % 2 == 0 else "[cyan]"}{p}[/]' for idx, p in enumerate(parts)
            ]
        )


    @property
    def summary_text(self):
        if self.is_site:
            parts = [a for a in [self.name, self.city, self.state, self.zipcode] if a]
        elif self.is_dev:
            parts = [p for p in utils.unique([self.name, self.serial, self.mac, self.ip, self.site]) if p]
            if self.site:
                parts[-1] = f"Site:{parts[-1]}"
        else:
            return str(self)

        return "[reset]" + "|".join(
            [
                f"{'[cyan]' if idx in list(range(0, len(parts), 2)) else '[bright_green]'}{p}[/]" for idx, p in enumerate(parts)
            ]
        )



# TODO Not used yet refactor to make consistent Response object available for when using contents of cache to avoid API call
class CacheResponses:
    def __init__(
        self,
        dev: Response = None,
        inv: Response = None,
        site: Response = None,
        template: Response = None,
        group: Response = None,
        label: Response = None,
        mpsk: Response = None,
        portal: Response = None,
    ) -> None:
        self._dev = dev
        self._inv = inv
        self._site = site
        self._template = template
        self._group = group
        self._label = label
        self._mpsk = mpsk
        self._portal = portal

    def update_rl(self, resp: Response) -> Response:
        """Returns provided Response object with the RateLimit info from the most recent API call.
        """
        _last_rl = sorted([r.rl for r in [self._dev, self._inv, self._site, self._template, self._group, self._label, self._mpsk, self._portal] if r is not None], key=lambda k: k.remain_day)
        if _last_rl:
            resp.rl = _last_rl[0]
        return resp

    @property
    def dev(self):
        return self.update_rl(self._dev)

    @dev.setter
    def dev(self, resp: Response):
        self._dev = resp

    @property
    def inv(self):
        return self.update_rl(self._inv)

    @inv.setter
    def inv(self, resp: Response):
        self._inv = resp

    @property
    def site(self):
        return self.update_rl(self._site)

    @site.setter
    def site(self, resp: Response):
        self._site = resp

    @property
    def template(self):
        return self.update_rl(self._template)

    @template.setter
    def template(self, resp: Response):
        self._template = resp

    @property
    def group(self):
        return self.update_rl(self._group)

    @group.setter
    def group(self, resp: Response):
        self._group = resp

    @property
    def label(self):
        return self.update_rl(self._label)

    @label.setter
    def label(self, resp: Response):
        self._label = resp

    @property
    def mpsk(self):
        return self.update_rl(self._mpsk)

    @mpsk.setter
    def mpsk(self, resp: Response):
        self._mpsk = resp

    @property
    def portal(self):
        return self.update_rl(self._portal)

    @portal.setter
    def portal(self, resp: Response):
        self._portal = resp


class Cache:
    def __init__(
        self,
        central: CentralApi = None,
        data: Union[List[dict], dict] = None,
        refresh: bool = False,
    ) -> None:
        """Central-API-CLI Cache object
        """
        self.updated: list = []  # TODO change from list of methods to something easier
        self.central = central
        self.responses = CacheResponses()
        # self.LicenseDB = LicenseDB()  # for the benefit of sphinx
        if config.valid and config.cache_dir.exists():
            self.DevDB: TinyDB = TinyDB(config.cache_file)
            self.InvDB: Table = self.DevDB.table("inventory")
            self.SiteDB: Table = self.DevDB.table("sites")
            self.GroupDB: Table = self.DevDB.table("groups")
            self.TemplateDB: Table = self.DevDB.table("templates")
            self.LabelDB: Table = self.DevDB.table("labels")
            self.LicenseDB: Table = self.DevDB.table("licenses")
            self.ClientDB: Table = self.DevDB.table("clients")  # Updated only when show clients is ran
            # log db is used to provide simple index to get details for logs
            # vs the actual log id in form 'audit_trail_2021_2,...'
            # it is updated anytime show logs is ran.
            self.LogDB: Table = self.DevDB.table("logs")
            self.EventDB: Table = self.DevDB.table("events")
            self.HookConfigDB: Table = self.DevDB.table("wh_config")
            self.HookDataDB: Table = self.DevDB.table("wh_data")
            self.MpskDB: Table = self.DevDB.table("mpsk")  # Only updated when show mpsk networks is ran or as needed when show named-mpsk <SSID> is ran
            self.PortalDB: Table = self.DevDB.table("portal")  # Only updated when show portals is ran or as needed
            self._tables = [self.DevDB, self.InvDB, self.SiteDB, self.GroupDB, self.TemplateDB, self.LabelDB, self.LicenseDB, self.ClientDB]
            self.Q = Query()
            if data:
                self.insert(data)
            if central:
                self.check_fresh(refresh)

    def __call__(self, refresh=False) -> None:
        if refresh:
            self.check_fresh(refresh)

    def __iter__(self) -> Generator[Tuple[str, TinyDB | Table], None, None]:
        for db in self._tables:
            yield db.name(), db.all()

    @property
    def devices(self) -> list:
        return self.DevDB.all()

    @property
    def device_types(self) -> Set[str]:
        db = self.InvDB if self.InvDB else self.DevDB
        return set([d["type"] for d in db.all()])

    @property
    def devices_by_serial(self) -> dict:
        return {d["serial"]: d for d in self.devices}

    @property
    def inventory(self) -> list:
        return self.InvDB.all()

    @property
    def inventory_by_serial(self) -> dict:
        return {d["serial"]: d for d in self.inventory}

    @property
    def sites(self) -> list:
        return self.SiteDB.all()

    @property
    def groups(self) -> list:
        return self.GroupDB.all()

    @property
    def labels(self) -> list:
        return self.LabelDB.all()

    @property
    def licenses(self) -> List[str]:
        if hasattr(self, "LicenseDB"):
            return [lic["name"] for lic in self.LicenseDB.all()]
        else:
            return [lic.value for lic in constants.LicenseTypes]

    @property
    def LicenseTypes(self) -> constants.LicenseTypes:
        if len(self.licenses) > 0:
            return Enum("ValidLicenseTypes", {item: item.replace("_", "-") for item in self.licenses}, type=str)
        else:
            return constants.LicenseTypes

    @property
    def clients(self) -> list:
        return self.ClientDB.all()

    @property
    def mpsk(self) -> list:
        return self.MpskDB.all()

    @property
    def portals(self) -> list:
        return self.PortalDB.all()

    @property
    def logs(self) -> list:
        return self.LogDB.all()

    @property
    def events(self) -> list:
        return self.EventDB.all()

    @property
    def event_ids(self) -> list:
        return [f'{x["id"]}' for x in self.EventDB.all()]

    @property
    def group_names(self) -> list:
        return [g["name"] for g in self.GroupDB.all()]

    @property
    def label_names(self) -> list:
        return [g["name"] for g in self.LabelDB.all()]

    @property
    def license_names(self) -> list:
        return [lic["name"] for lic in self.LicenseDB.all()]

    @property
    def templates(self) -> list:
        return self.TemplateDB.all()

    @property
    def hook_config(self) -> list:
        return self.HookConfigDB.all()

    @property
    def hook_data(self) -> list:
        return self.HookDataDB.all()

    @property
    def hook_active(self) -> list:
        return [h for h in self.HookDataDB.all() if h["state"].lower() == "open"]

    @property
    def all(self) -> dict:
        return {t.name: getattr(self, t.name) for t in self._tables}

    async def get_hooks_by_serial(self, serial):
        return self.HookDataDB.get(self.Q.device_id == serial)


    def get_devices_with_inventory(self, no_refresh=False) -> List[Response]:
        """Returns List of Response objects with data from Inventory and Monitoring

        Args:
            no_refresh(bool, optional): Used currently cached data, skip refresh of cache.
                Defaults to False.

                Refresh will only occur if cache was not updated during this session.
                Setting no_refresh to True means it will not occur regardless.

        Returns:
            List[Response]: Response objects where output is list of dicts with
                            data from Inventory and Monitoring.
        """
        kwargs = {
            "dev_db": self.responses.dev is None,
            "inv_db": self.responses.inv is None
        }
        if any(kwargs.values()) and not no_refresh:
            res = self.check_fresh(**kwargs)
        else:
            res = [self.responses.dev or Response()]

        _inv_by_ser = self.inventory_by_serial
        # Need to use the resp value not what was just stored in cache as we don't store all fields
        dev_res = list(filter(lambda r: r.url.path.startswith("/monitoring"), res))
        if dev_res:
            _dev_by_ser = {d["serial"]: d for d in dev_res[0].output}
        else:
            _dev_by_ser = self.devices_by_serial

        _all_serials = set([*_inv_by_ser.keys(), *_dev_by_ser.keys()])  # TODO need to add clients
        combined = [
            {**_inv_by_ser.get(serial, {}), **_dev_by_ser.get(serial, {})}
            for serial in _all_serials

        ]
        res[-1].output = combined  # TODO this may be an issue if check_fresh has a failure, don't think it returns Response object
        return res[-1]

    # using shell_complete to see if it improves click 8 compat... it does not still have ^M with click 8
    @staticmethod
    def account_completion(ctx: typer.Context, args: List[str], incomplete: str):
        # err_console.print(f'\n\nctx: {ctx.__dict__} \n\n incomplete type: {type(incomplete)}\nincomplete_value: {incomplete}\n\nargs_type: {type(args)}\n value: {args.__dict__}')
        # Works on shell_complete=
        # return [a for a in config.defined_accounts if a.lower().startswith(incomplete.lower())]
        # Works with autocompletion=
        for a in config.defined_accounts:
            if a.lower().startswith(incomplete.lower()):
                yield a

    # TODO maybe build script to gather completion and help text and place in flat file
    def method_test_completion(self, incomplete: str, args: List[str] = []):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        if self.central is not None:
            methods = [
                d for d in self.central.__dir__()
                if not d.startswith("__")
            ]

        import importlib
        bpdir = Path(__file__).parent / "boilerplate"
        all_calls = [
            importlib.import_module(f"centralcli.{bpdir.name}.{f.stem}") for f in bpdir.iterdir()
            if not f.name.startswith("_") and f.suffix == ".py"
        ]
        for m in all_calls:
            methods += [
                d for d in m.AllCalls().__dir__()
                if not d.startswith("__")
            ]

        for m in sorted(methods):
            if m.startswith(incomplete):
                yield m

    def smg_kw_completion(self, ctx: typer.Context, incomplete: str, args: List[str] = []):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        kwds = ["group", "mac", "serial"]
        out = []

        if not args:  # HACK click 8.x work-around now pinned at click 7.2 until resolved
            args = [v for k, v in ctx.params.items() if v and k in ["serial", "mac", "group"]]

        if args[-1].lower() == "group":
            out = [m for m in self.group_completion(incomplete, args)]
            for m in out:
                yield m
        elif args[-1].lower() == "serial":
            out = ["|", "<SERIAL NUMBER>"]
            if incomplete:
                out.append(incomplete)
            for m in out:
                yield m
        elif args[-1].lower() == "mac":
            out = ["|", "<MAC ADDRESS>"]
            for m in out:
                yield m

        else:
            for kw in kwds:
                if kw not in args and kw.lower().startswith(incomplete):
                    yield kw

    def null_completion(self, incomplete: str, args: List[str] = None):
        incomplete = "NULL_COMPLETION"
        _ = incomplete
        for m in ["|", "<cr>"]:
            yield m

    def dev_completion(
        self,
        # ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        # HACK click 8.x broke args being passed to completion functions.
        # if args is not None:
        #     if ctx is not None and ctx.command_path == "cencli delete device":
        #         args = ctx.params["devices"]
        #     else:
        #         _params = [{k: v} for k, v in ctx.params.items() if isinstance(v, tuple)]
        #         args = list(_params[0].values())[-1]

        dev_type = None
        if args:
            if args[-1].lower() in ["gateways", "clients", "server"]:
                dev_type = "gw"
            elif args[-1].lower().startswith("switch"):
                dev_type = "switch"
            elif args[-1].lower() in ["aps", "ap"]:
                dev_type = "ap"

        match = self.get_dev_identifier(
            incomplete,
            dev_type=dev_type,
            completion=True,
        )
        out = []
        args = args or []
        if match:
            # remove devices that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if m.name.startswith(incomplete):
                    out += [tuple([m.name, m.help_text])]
                elif m.serial.startswith(incomplete):
                    out += [tuple([m.serial, m.help_text])]
                elif m.mac.strip(":.-").lower().startswith(incomplete.strip(":.-").lower()):
                    out += [tuple([m.mac, m.help_text])]
                elif m.ip.startswith(incomplete):
                    out += [tuple([m.ip, m.help_text])]
                else:
                    out += [tuple([m.name, m.help_text])]  # failsafe, shouldn't hit

        for m in out:
            yield m

    def dev_switch_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Device completion for returning matches that are switches (AOS-SW or CX)

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(incomplete, dev_type=["switch"], completion=True)

        out = []
        if match:
            out = [
                tuple([m.name, m.help_text]) for m in sorted(match, key=lambda i: i.name)
                if m.name not in args
                ]

        for m in out:
            yield m

    def dev_switch_by_type_completion(
        self,
        incomplete: str,
        args: List[str] = [],
        dev_type: Literal["cx", "sw"] = "cx",
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Device completion for returning matches that are of specific switch type (cx by default)

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(incomplete, dev_type=[dev_type], completion=True)

        out = []
        if match:
            out = [
                tuple([m.name, m.help_text]) for m in sorted(match, key=lambda i: i.name)
                if m.name not in args
                ]

        for m in out:
            yield m

    def dev_cx_completion(
            self,
            incomplete: str,
            args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        for match in self.dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="cx"):
            yield match

    def dev_sw_completion(
            self,
            incomplete: str,
            args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        for match in self.dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="sw"):
            yield match

    def dev_ap_gw_sw_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Device completion for returning matches that are ap, gw, or AOS-SW

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match: List[CentralObject] = self.get_dev_identifier(incomplete, dev_type=["ap", "gw", "sw"], completion=True)

        out = []
        if match:
            out = [
                tuple([m.name, m.help_text]) for m in sorted(match, key=lambda i: i.name)
                if m.name not in args
                ]

        for m in out:
            yield m

    def mpsk_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_mpsk_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or ctx.params.values()  # HACK as args stopped working
        if match:
            # remove items that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if m.name.startswith(incomplete):
                    out += [tuple([m.name, m.id])]
                elif m.id.startswith(incomplete):
                    out += [tuple([m.id, m.name])]
                else:
                    out += [tuple([m.name, m.help_text])]  # failsafe, shouldn't hit

        for m in out:
            yield m

    # TODO one common completion that is referenced by multiple xx_completions passing in ctx and the get__identifier func/args
    def portal_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_name_id_identifier(
            "portal",
            incomplete,
            completion=True,
        )
        out = []
        args = args or ctx.params.values()  # HACK as args stopped working
        if match:
            # remove items that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if m.name.startswith(incomplete):
                    out += [tuple([m.name, m.id])]
                elif m.id.startswith(incomplete):
                    out += [tuple([m.id, m.name])]
                else:
                    out += [tuple([m.name, m.help_text])]  # failsafe, shouldn't hit

        for m in out:
            yield m


    def dev_kwarg_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for commands that allow a list of devices followed by group/site.

        i.e. cencli move dev1 dev2 dev3 site site_name group group_name

        Args:
            ctx (typer.Context): Provided automatically by typer
            incomplete (str): The incomplete word for autocompletion
            args (List[str], optional): The prev args passed into the command.

        Yields:
            Generator[Tuple[str, str], None, None]: Matching completion string, help text, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        if not args:  # HACK resolves click 8.x issue now pinned to 7.2 until fixed upstream
            args = [k for k, v in ctx.params.items() if v and k[:2] not in ["kw", "va"]]
            args += [v for k, v in ctx.params.items() if v and k[:2] in ["kw", "va"]]

        if args and args[-1].lower() == "group":
            out = [m for m in self.group_completion(incomplete, args)]
            for m in out:
                yield m

        elif args and args[-1].lower() == "site":
            out = [m for m in self.site_completion(incomplete, args)]
            for m in out:
                ##  This was required for completion to work in click 8.x when case doesn't match
                ##  i.e. site: WadeLab incomplete: wade in click 7 completes wade -> WadeLab
                ##  in click 8 it returns nothing.
                ##  pinned click back to 7.1.2 until this and the other 2 issues are sorted upstream.
                # if m[0].lower().startswith(incomplete):
                #     # console.print(m[0].lower())
                #     yield m[0].lower(), m[1]
                # else:
                yield m

        elif args and args[-1].lower() == "ap":
            out = [m for m in self.dev_completion(incomplete, args)]
            for m in out:
                yield m

        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    _help = "move device(s) to a different site" if ctx.info_name == "move" else f"{ctx.info_name} ... site"  # TODO the fallback ... need to check which commands use this.
                    out += [("site", _help)]
                if "group" not in args and "group".startswith(incomplete.lower()):
                    _help = "move device(s) to a different group" if ctx.info_name == "move" else f"{ctx.info_name} ... group"  # TODO the fallback ... need to check which commands use this.
                    out += [("group", _help)]

            if "site" not in args and "group" not in args:
                out = [*out, *[m for m in self.dev_completion(incomplete, args)]]
            elif "site" in args and "group" in args:
                incomplete = "NULL_COMPLETION"
                out += ["|", "<cr>"]

            for m in out:
                yield m if isinstance(m, tuple) else (m, f"{ctx.info_name} ... {m}")

    def dev_ap_completion(
        self,
        # ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for argument where only APs are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # if not args:
        #     _last = ctx.command_path.split()[-1]
        #     if _last in ctx.params:
        #         args = ctx.params[_last]
        #     else:
        #         args = [k for k, v in ctx.params.items() if v and k not in ["account", "debug"]]

        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        dev_types = ["ap"]
        match = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)

        # TODO this completion complete using the type of iden they start, and omits any idens already on the command line regardless of iden type
        # so they could put serial then auto-complete name and the name of the device whos serial is already on the cli would not appear.
        # Make others like this.
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                idens = [m.name, m.serial, m.mac, m.ip]
                if all([i not in args for i in idens]):
                    if m.name.startswith(incomplete):
                        out += [tuple([m.name, m.help_text])]
                    elif m.serial.startswith(incomplete):
                        out += [tuple([m.serial, m.help_text])]
                    elif m.mac.strip(":.-").lower().startswith(incomplete.strip(":.-").lower()):
                        out += [tuple([m.mac, m.help_text])]
                    elif m.ip.startswith(incomplete):
                        out += [tuple([m.ip, m.help_text])]

        for m in out:
            yield m

    # TODO put client names with spaces in quotes
    def dev_client_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for client output.

        Returns only devices that apply based on filter provided in command, defaults to clients
        on both APs and switches (wires/wireless), but returns applicable devices if "wireless" or
        "wired" filter is used.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return


        if ctx.params.get("wireless"):
            gen = self.dev_ap_completion
        elif ctx.params.get("wired"):
            gen = self.dev_switch_completion
        else:
            gen = self.dev_switch_ap_completion
            # return

        for m in [dev for dev in gen(incomplete, args)]:
            yield m

    def dev_switch_ap_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Device completion for returning matches that are either switch or AP

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI.

        Yields:
            Generator[Tuple[str, str], None, None]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(incomplete, dev_type=["switch", "ap"], completion=True)

        # TODO fancy map to ensure dev.name, dev.mac, dev.serial, dev.ip are all not in args
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_ap_gw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Device completion that returns only ap and gw.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        # Prevents device completion for cencli show config cencli
        if ctx.command_path == "cencli show config" and ctx.params.get("group_dev", "") == "cencli":
            return

        dev_types = ["ap", "gw"]
        _match = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)

        match = []
        for m in _match:
            if m.name in args or m.serial in args or m.mac in args:
                continue
            else:
                match += [m]

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m[0], m[1]

    def dev_switch_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Device completion that returns only switches and gateways.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        dev_types = ["switch", "gw"]
        match = [m for m in self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True) if m.generic_type in dev_types]

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if match not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for device idens where only gateways are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(incomplete, device_type="gw", completion=True)

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m[0], m[1]

    # FIXME not completing partial serial number is zsh get_dev_completion appears to return as expected
    # works in BASH and powershell
    def group_dev_ap_gw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for argument that can be either group or device.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        # group_match = self.get_group_identifier(incomplete, completion=True)

        dev_types = ["ap", "gw"]
        # match = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)
        match = self.get_identifier(incomplete, ["group", "dev"], device_type=dev_types, completion=True)

        # match = group_match + match


        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]
                # out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])]  # FIXME completion for names with spaces is now broken, used to work.  Change in completion behavior

        if args:
            if " ".join(args).lower() == "show config" and "cencli".lower().startswith(incomplete):
                out += [("cencli", "show cencli configuration")]
            if " ".join(args).lower() == "update config" and "cencli".lower().startswith(incomplete):
                out += [("cencli", "update cencli configuration")]
        elif ctx.command_path == "cencli show config" and ctx.params.get("group_dev") is None:  # typer not sending args fix
            if "cencli".lower().startswith(incomplete):
                out += [("cencli", "update cencli configuration")]



        # partial completion by serial: out appears to have list with expected tuple but does
        # not appear in zsh

        for m in out:
            log.debug(f"yielding to completion {m}")  # FIXME DEBUG remove me serial completion yielding expected tuple but does not appear in zsh
            yield m

    def group_dev_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for argument that can be either group or a gateway.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_identifier(incomplete, ["group", "dev"], device_type="gw", completion=True)

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m[0], m[1]

    # FIXME completion doesn't pop args need ctx: typer.Context and reference ctx.params which is dict?
    def send_cmds_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for argument that can be either group, site, or a gateway or keyword "commands".

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        if ctx.params.get("nodes"):
            yield "commands"
        elif ctx.params.get("kw1") == "all":
            yield "commands"
        elif ctx.params.get("kw1") in ["commands", "file"]:
            yield None  # force shell path completion
        elif ctx.params.get("kw1") not in ["group", "site", "device"]:
            yield "commands"
        else:
            if ctx.params.get("kw1") == "group":
                db = "group"
            elif ctx.params.get("kw1") == "site":
                db = "site"
            else:
                db = "dev"

        # FIXME typer broke this a long time ago
        # if args[-1] == "all":
        #     yield "commands"
        # elif args[-1] in ["commands", "file"]:
        #     yield None
        # elif args[-1] not in ["group", "site", "device"]:
        #     yield "commands"
        # else:
        #     if args[-1] == "group":
        #         db = "group"
        #     elif args[-1] == "site":
        #         db = "site"
        #     else:
        #         db = "dev"

            match = self.get_identifier(incomplete, [db], device_type="gw", completion=True)

            out = []
            if match:
                for m in sorted(match, key=lambda i: i.name):
                    out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])]

                for m in out:
                    yield m[0], m[1]

    def group_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_group_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]
                    # out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])] # FIXME case insensitive and group completion now broken used to work

        for m in out:
            yield m

    def label_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for labels.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]:  Name and help_text for the label, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_label_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])]

        for m in out:
            yield m

    def client_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for clients.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the client, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_client_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or []
        if match:
            # remove clients that are already on the command line
            match = [m for m in match if m.name not in args]
            for c in sorted(match, key=lambda i: i.name):
                if c.name.startswith(incomplete):
                    out += [tuple([c.name, f'{c.ip}|{c.mac} type: {c.type} connected to: {c.connected_name} ~ {c.connected_port}'])]
                elif c.mac.strip(":.-").lower().startswith(incomplete.strip(":.-")):
                    out += [tuple([c.mac, f'{c.name}|{c.ip} type: {c.type} connected to: {c.connected_name} ~ {c.connected_port}'])]
                elif c.ip.startswith(incomplete):
                    out += [tuple([c.mac, f'{c.name}|{c.mac} type: {c.type} connected to: {c.connected_name} ~ {c.connected_port}'])]
                else:
                    # failsafe, shouldn't hit
                    out += [tuple([c.name, f'{c.ip}|{c.mac} type: {c.type} connected to: {c.connected_name} ~ {c.connected_port} (fail-safe match)'])]


        for c in out:  # TODO completion behavior has changed.  This works-around issue bash doesn't complete past 00: and zsh treats each octet as a dev name when : is used.
            yield c[0].replace(":", "-"), c[1]

    def event_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for events.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Generator[Tuple[str, str], None, None]: Value and help_text for the event, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        if incomplete == "":
            out = [("cencli", "Show cencli logs"), *[(x['id'], f"{x['id']}|{x['device'].split('Group:')[0].rstrip()}") for x in self.events]]
            for m in out:
                yield m[0], m[1]

        elif "cencli".startswith(incomplete.lower()):
            yield "cencli", "Show cencli logs"
        else:
            for event in self.events:
                if event["id"].startswith(incomplete):
                    yield event["id"], f"{event['id']}|{event['device'].split('Group:')[0].rstrip()}"

    # TODO add support for zip code city state etc.
    def site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        """Completion for sites.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Generator[Tuple[str, str], None, None]: Name and help_text for the site, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_site_identifier(
            incomplete.replace('"', "").replace("'", ""),
            completion=True,
        )
        out = []
        if match:
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])]

        for m in out:
            yield m

    def template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        match = match or []
        dev_match = self.get_dev_identifier(
            incomplete,
            completion=True,
        )
        match += dev_match or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(
            incomplete,
            completion=True,
        )
        match = match or []
        match += self.get_site_identifier(
            incomplete,
            completion=True,
        ) or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_gw_switch_site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Generator[Tuple[str, str], None, None] | None:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(
            incomplete,
            dev_type=["gw", "switch"],
            completion=True,
        )
        match = match or []
        match += self.get_site_identifier(
            incomplete,
            completion=True,
        ) or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def remove_completion(
        self,
        incomplete: str,
        args: List[str],
    ) -> Generator[Tuple[str, str], None, None] | None:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        if args[-1].lower() == "site":
            out = [m for m in self.site_completion(incomplete)]
            for m in out:
                yield m
        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    out += ("site", )

            if "site" not in args:
                out += [m for m in self.dev_completion(incomplete=incomplete, args=args)]
            else:
                out += [m for m in self.null_completion(incomplete)]

            for m in out:
                yield m

    # TODO double check not used and remove
    def completion(
        self,
        incomplete: str,
        args: List[str],
    ) -> Generator[Tuple[str, str], None, None] | None:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            err_console.print(":warning:  Invalid config")
            return

        cache = ()
        if [True for m in DEV_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["dev"])
        elif [True for m in GROUP_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["group"])
        elif [True for m in SITE_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["site"])
        elif [True for m in TEMPLATE_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["template"])

        if not cache:
            match = self.get_identifier(
                incomplete,
                ("dev", "group", "site", "template"),
                completion=True,
            )
        else:
            match = self.get_identifier(
                incomplete,
                tuple(cache),
                completion=True,
            )

        out = []
        _extra = [e for e in EXTRA_COMPLETION if e in args and args[-1] != e]
        if _extra:
            out += [
                tuple([m, "COMMAND KEYWORD"]) for e in _extra for m in EXTRA_COMPLETION[e]
                if m.startswith(incomplete) and args[-1] != m
                ]

        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    # TODO ??deprecated?? should be able to remove this method. don't remember this note. looks used
    def insert(
        self,
        data: Union[
            List[
                dict,
            ],
            dict,
        ],
    ) -> bool:
        log.warning("DEV WARNING: Cache().insert() is being used.", show=True)
        _data = data
        if isinstance(data, list) and data:
            _data = data[1]

        table = self.DevDB
        if "zipcode" in _data.keys():
            table = self.SiteDB

        data = data if isinstance(data, list) else [data]
        ret = table.insert_multiple(data)

        return len(ret) == len(data)


    # FIXME handle no devices in Central yet exception 837 --> cleaner.py 498
    # TODO if we are updating inventory we only need to get those devices types
    async def update_dev_db(self,  data: Union[str, List[str], List[dict]] = None, remove: bool = False, **kwargs) -> Union[List[int], Response]:
        """Update Device Database (local cache).

        Args:
            data (Union[str, List[str]], List[dict] optional): serial number or list of serials numbers to add or remove. Defaults to None.
            remove (bool, optional): Determines if update is to add or remove from cache. Defaults to False (add devices).

        Raises:
            ValueError: if provided data is of wrong type or does not appear to be a serial number

        Returns:
            Union[Response, None]: returns Response object from inventory api call if no data was provided for add/remove.
                If adding/removing (providing serials) returns None.  Logs errors if any occur during db update.
        """
        if data:
            data = utils.listify(data)
            if not remove:
                upd = [self.DevDB.upsert(dev, cond=self.Q.serial == dev.get("serial")) for dev in data]
                upd = [item for in_list in upd for item in in_list]
                if False in upd:
                    log.error(f"TinyDB DevDB update returned an error.  db_resp: {upd}", show=True)
                return upd
                # db_res = self.DevDB.insert_multiple(data)
                # if False in db_res:
                #     log.error(f"TinyDB DevDB update returned an error.  db_resp: {db_res}", show=True)
            else:
                doc_ids = []
                for qry in data:
                    # allow list of dicts with device data, only interested in serial
                    if isinstance(qry, dict):
                        qry = qry if "data" not in qry else qry["data"]
                        if "serial" not in qry.keys():
                            raise ValueError(f"update_dev_db data is dict but lacks 'serial' key {list(qry.keys())}")
                        qry = qry["serial"]

                    if not isinstance(qry, str):
                        raise ValueError(f"update_dev_db data should be serial number(s) as str or list of str not {type(qry)}")
                    if not utils.isserial(qry):
                        raise ValueError("Provided str does not appear to be a serial number.")
                    else:
                        doc_ids += [self.DevDB.get((self.Q.serial == qry)).doc_id]

                if len(doc_ids) != len(data):
                    log.error(
                        f"Warning update_dev_db: no match found for {len(data) - len(doc_ids)} of the {len(data)} serials provided.",
                        show=True
                    )

                db_res = self.DevDB.remove(doc_ids=doc_ids)
                if False in db_res:
                    log.error(f"Tiny DB returned an error during DevDB update {db_res}", show=True)
        else:
            # TODO update device inventory first then only get details for device types in inventory
            resp = await self.central.get_all_devicesv2(cache=True, **kwargs)
            if resp.ok:
                if resp.output:
                    _update_data = utils.listify(deepcopy(resp.output))
                    _update_data = cleaner.get_devices(_update_data, cache=True)

                    # Cache update  # TODO make own function
                    self.DevDB.truncate()
                    update_res = self.DevDB.insert_multiple(_update_data)
                    if False in update_res:
                        log.error("Tiny DB returned an error during dev db update", caption=True)

                # TODO change updated from  list of funcs to class with bool attributes or something
                self.updated.append(self.central.get_all_devicesv2)
                self.responses.dev = resp
            return resp

    async def update_inv_db(
            self,
            data: Union[str, List[str]] = None,
            *,
            remove: bool = False,
            dev_type: str = "all",
            sub: bool = None
        ) -> Union[List[int], Response]:
        """Update Inventory Database (local cache).

        Args:
            data (Union[str, List[str]], optional): serial number or list of serials numbers to add or remove. Defaults to None.
            remove (bool, optional): Determines if update is to add or remove from cache. Defaults to False.
            dev_type (str, optional): all/iap/switch/controller/gateway/vgw/cap/boc/all_ap/all_controller/others
            sub (str, optional): whether or not to filter return by subscribed / not subscribed. Defaults to None (no filter)

        Raises:
            ValueError: if provided data is of wrong type or does not appear to be a serial number

        Returns:
            Union[Response, None]: returns Response object from inventory api call if no data was provided for add/remove.
                If adding/removing (providing serials) returns None.  Logs errors if any occur during db update.
        """
        if data:
            # provide serial or list of serials to remove
            data = utils.listify(data)
            if not remove:
                db_res = self.InvDB.insert_multiple(data)
                if False in db_res:
                    log.error(f"TinyDB InvDB table update returned an error.  db_resp: {db_res}", show=True)
            else:
                doc_ids = []
                for qry in data:
                    # allow list of dicts with inventory data, only interested in serial
                    if isinstance(qry, dict):
                        qry = qry if "data" not in qry else qry["data"]
                        if "serial" not in qry.keys():
                            raise ValueError(f"update_dev_db data is dict but lacks 'serial' key {list(qry.keys())}")
                        qry = qry["serial"]

                    if not isinstance(qry, str):
                        raise ValueError(f"update_inv_db data should be serial number(s) as str or list of str not {type(qry)}")
                    if not utils.isserial(qry):
                        raise ValueError("Provided str does not appear to be a serial number.")
                    else:
                        match = self.InvDB.get((self.Q.serial == qry))
                        if match:
                            doc_ids += [match.doc_id]
                        else:
                            log.warning(f'Warning update_inv_db: no match found for {qry}', show=True)

                # if len(doc_ids) != len(data):
                #     log.error(
                #         f"Warning update_inv_db: no match found for {len(data) - len(doc_ids)} of the {len(data)} serials provided.",
                #         show=True
                #     )

                db_res = self.InvDB.remove(doc_ids=doc_ids)
                if False in db_res:
                    log.error(f"Tiny DB returned an error during Inventory db update {db_res}", show=True)
        else:
            resp = await self.central.get_device_inventory(sku_type=dev_type)
            if resp.ok:
                if resp.output:
                    resp.output = utils.listify(resp.output)
                    resp.output = cleaner.get_device_inventory(resp.output)
                    if dev_type == "all":
                        self.InvDB.truncate()
                        db_res = self.InvDB.insert_multiple(resp.output)
                    else:
                        db_res = [
                            self.InvDB.upsert(d, self.Q.serial == d.get("serial", "--"))
                            for d in resp.output
                        ]
                    if sub is not None:  # filtered response for display, no filter prior for benefit of cache.
                        resp.output = [dev for dev in resp.output if bool(dev["services"]) is sub]
                    if False in db_res:
                        log.error(f"Tiny DB returned an error during InvDB update {db_res}", show=True)

                # TODO change updated from  list of funcs to class with bool attributes or something
                self.updated.append(self.central.get_device_inventory)
                self.responses.inv = resp
            return resp

    async def update_site_db(self, data: Union[list, dict] = None, remove: bool = False) -> Union[List[int], Response]:
        # cli.cache.SiteDB.search(cli.cache.Q.id == del_list[0])[0].doc_id
        if data:
            data = utils.listify(data)
            if not remove:
                data = [{k.replace("site_", ""): v for k, v in d.items()} for d in data]
                upd = [self.SiteDB.upsert(site, cond=self.Q.id == site.get("id")) for site in data]
                upd = [item for in_list in upd for item in in_list]
                return upd
                # return self.SiteDB.insert_multiple(data)
            else:
                doc_ids = []
                for qry in data:
                    # provided list of site_ids to remove
                    if isinstance(qry, (int, str)) and str(qry).isdigit():
                        doc_ids += [self.SiteDB.get((self.Q.id == qry)).doc_id]
                    else:
                        # list of dicts with {search_key: value_to_search_for}
                        if len(qry.keys()) > 1:
                            raise ValueError(f"cache.update_site_db remove Should only have 1 query not {len(qry.keys())}")
                        q = list(qry.keys())[0]
                        doc_ids += [self.SiteDB.get((self.Q[q] == qry[q])).doc_id]
                return self.SiteDB.remove(doc_ids=doc_ids)
        else:  # update site cache
            resp = await self.central.get_all_sites()
            if resp.ok:
                resp.output = utils.listify(resp.output) if resp.output else []
                resp.output = [{k.replace("site_", ""): v for k, v in d.items()} for d in resp.output]
                self.responses.site = resp
                # TODO time this to see which is more efficient
                # upd = [self.SiteDB.upsert(site, cond=self.Q.id == site.get("id")) for site in site_resp.output]
                # upd = [item for in_list in upd for item in in_list]
                self.updated.append(self.central.get_all_sites)
                self.SiteDB.truncate()
                update_res = self.SiteDB.insert_multiple(resp.output)
                if False in update_res:
                    log.error(f"Tiny DB returned an error during site db update {update_res}", show=True)
            return resp

    async def update_group_db(self, data: Union[list, dict] = None, remove: bool = False) -> Union[List[int], Response]:
        if data:
            data = utils.listify(data)
            if not remove:
                return self.GroupDB.insert_multiple(data)
            else:
                doc_ids = []
                for qry in data:
                    if len(qry.keys()) > 1:
                        raise ValueError(f"cache.update_group_db remove Should only have 1 query not {len(qry.keys())}")
                    q = list(qry.keys())[0]
                    doc_ids += [self.GroupDB.get((self.Q[q] == qry[q])).doc_id]
                return self.GroupDB.remove(doc_ids=doc_ids)
        else:
            resp = await self.central.get_all_groups()
            if resp.ok:
                resp.output = cleaner.get_all_groups(resp.output)
                resp.output = utils.listify(resp.output)
                self.responses.group = resp
                self.updated.append(self.central.get_all_groups)
                self.GroupDB.truncate()
                update_res = self.GroupDB.insert_multiple(resp.output)
                if False in update_res:
                    log.error("Tiny DB returned an error during group db update", caption=True)
            return resp

    async def update_label_db(self, data: Union[list, dict] = None, remove: bool = False) -> Union[List[int], Response]:
        if data:
            data = utils.listify(data)
            if not remove:
                return self.LabelDB.insert_multiple(data)
            else:
                doc_ids = []
                for qry in data:
                    # provided list of label_ids to remove
                    if isinstance(qry, (int, str)) and str(qry).isdigit():
                        doc_ids += [self.LabelDB.get((self.Q.id == qry)).doc_id]
                    else:
                        # list of dicts with {search_key: value_to_search_for}
                        if len(qry.keys()) > 1:
                            raise ValueError(f"cache.update_label_db remove Should only have 1 query not {len(qry.keys())}")
                        q = list(qry.keys())[0]
                        doc_ids += [self.LabelDB.get((self.Q[q] == qry[q])).doc_id]
                return self.LabelDB.remove(doc_ids=doc_ids)
        else:
            resp = await self.central.get_labels()
            if resp.ok:
                resp.output = cleaner.get_labels(resp.output)
                resp.output = utils.listify(resp.output)
                self.responses.label = resp
                self.updated.append(self.central.get_labels)
                self.LabelDB.truncate()
                update_res = self.LabelDB.insert_multiple(resp.output)
                if False in update_res:
                    log.error("Tiny DB returned an error during label db update")
            return resp

    async def update_license_db(self) -> Response:
        """Update License DB

        License DB stores the valid license names accepted by GreenLake/Central

        Returns:
            Response: CentralAPI Response Object
        """
        resp = await self.central.get_valid_subscription_names()
        if resp.ok:
            # licenses starting with enhanced_ or standard_ are compute/storage
            resp.output = [{"name": k} for k in resp.output.keys() if not k.startswith("standard_") and not k.startswith("enhanced_")]
            self.updated.append(self.central.get_valid_subscription_names)
            self.LicenseDB.truncate()
            update_res = self.LicenseDB.insert_multiple(resp.output)
            if False in update_res:
                log.error("Tiny DB returned an error during license db update")
        return resp

    async def update_template_db(self):
        # groups = self.groups if self.central.get_all_groups in self.updated else None
        if self.central.get_all_groups not in self.updated:
            gr_resp = await self.update_group_db()
            if not gr_resp.ok:
                return gr_resp

        groups = self.groups
        resp = await self.central.get_all_templates(groups=groups)
        if resp.ok:
            if len(resp) > 0: # handles initial cache population when none of the groups are template groups
                resp.output = utils.listify(resp.output)
                self.updated.append(self.central.get_all_templates)
                self.responses.template = resp
                self.TemplateDB.truncate()
                update_res = self.TemplateDB.insert_multiple(resp.output)
                if False in update_res:
                    log.error("Tiny DB returned an error during template db update")
        return resp

    # TODO need a reset cache flag in "show clients"
    async def update_client_db(self, *args, truncate: bool = False, **kwargs) -> Response:
        """Update client DB

        This is only updates when the user does a show clients

        It returns the raw data from the API with whatever filters were provided by the user
        then updates the db with the data returned

        Past users are always retained, unless truncate=True
        """
        # TODO running pytest on subsequent tests of show clients this would eval True and return None
        # if self.central.get_clients not in self.updated:
        client_resp = await self.central.get_clients(*args, **kwargs)
        if not client_resp.ok:
            return client_resp
        else:
            if len(client_resp) > 0:
                client_resp.output = utils.listify(client_resp.output)
                self.updated.append(self.central.get_clients)
                data = [
                    {
                        "mac": c.get("macaddr"),
                        "name": c.get("name", c.get("macaddr")),
                        "ip": c.get("ip_address", ""),
                        "type": c["client_type"],
                        "connected_port": c.get("network", c.get("interface_port", "!!ERROR!!")),
                        "connected_serial": c.get("associated_device"),
                        "connected_name": c.get("associated_device_name"),
                        "site": c.get("site"),
                        "group": c.get("group_name"),
                        "last_connected": c.get("last_connection_time")
                    }
                    for c in client_resp.output
                ]
                if truncate:
                    self.ClientDB.truncate()
                    cache_update_res = self.ClientDB.insert_multiple(data)
                else:
                    Client = Query()
                    cache_update_res = [
                        self.ClientDB.upsert(c, Client.mac == c.get("mac", "--"))
                        for c in data
                    ]
                if False in cache_update_res:
                    log.error("Tiny DB returned an error during client db update")
        return client_resp


    def update_log_db(self, log_data: List[Dict[str, Any]]) -> bool:
        self.LogDB.truncate()
        return self.LogDB.insert_multiple(log_data)

    def update_event_db(self, log_data: List[Dict[str, Any]]) -> bool:
        self.EventDB.truncate()
        return self.EventDB.insert_multiple(log_data)

    def update_hook_config_db(self, data: List[Dict[str, Any]], remove: bool = False) -> bool:
        data = utils.listify(data)
        self.HookConfigDB.truncate()
        return self.HookConfigDB.insert_multiple(data)

    async def update_hook_data_db(self, data: List[Dict[str, Any]]) -> bool:
        data = utils.listify(data)
        rem_data = []
        add_data = []
        for d in data:
            if d.get("state", "") == "Close":
                match = self.HookDataDB.get((self.Q.id == d["id"]))
                if match is not None:
                    rem_data += [match.doc_id]
            else:
                add_data += [d]

        if rem_data and add_data:
            log.error("update_hook_data_db called with both open and closed notifications")

        if rem_data:
            log.info(f"Removing {rem_data} from HookDataDB")
            return self.HookDataDB.remove(doc_ids=rem_data)
        elif add_data:
            data = [*self.hook_active, *add_data]
            self.HookDataDB.truncate()
            return self.HookDataDB.insert_multiple(data)
        else:
            data = [*self.hook_active, *data]
            self.HookDataDB.truncate()
            return self.HookDataDB.insert_multiple(data)

    async def update_mpsk_db(self, data: List[Dict[str, Any]] = None) -> bool:
        if data:
            if isinstance(data, list):
                data = {"items": data}
            data = models.CacheMpskNetworks(**data)
            data = data.dict()["items"]
            self.MpskDB.truncate()
            return self.MpskDB.insert_multiple(data)
        else:
            resp = await self.central.cloudauth_get_mpsk_networks()
            if resp.ok:
                if resp.output:
                    _update_data = utils.listify(deepcopy(resp.output))
                    _update_data = models.CacheMpskNetworks(**resp.raw)
                    _update_data = _update_data.dict()["items"]

                    self.MpskDB.truncate()
                    update_res = self.MpskDB.insert_multiple(_update_data)
                    if False in update_res:
                        log.error("Tiny DB returned an error during MPSK db update", caption=True)

                # TODO change updated from  list of funcs to class with bool attributes or something
                self.updated.append(self.central.cloudauth_get_mpsk_networks)
                self.responses.mpsk = resp
            return resp

    async def update_portal_db(self, data: List[Dict[str, Any]] = None) -> bool:
        if data:
            if isinstance(data, list):
                data = {"portals": data}
            data = models.CachePortals(**data)
            data = data.dict()["portals"]
            self.PortalDB.truncate()
            return self.PortalDB.insert_multiple(data)
        else:
            resp = await self.central.get_portals()
            if resp.ok:
                if resp.output:
                    _update_data = utils.listify(deepcopy(resp.output))
                    _update_data = models.CachePortals(**resp.raw)
                    _update_data = _update_data.dict()["portals"]

                    self.PortalDB.truncate()
                    update_res = self.PortalDB.insert_multiple(_update_data)
                    if False in update_res:
                        log.error("Tiny DB returned an error during Portal db update", caption=True)

                self.updated.append(self.central.get_portals)
                self.responses.portal = resp
            return resp

    # TODO cache.groups cache.devices etc change to Response object with data in output.  So they can be leveraged in commands with all attributes
    async def _check_fresh(
        self,
        dev_db: bool = False,
        inv_db: bool = False,
        site_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
        label_db: bool = False,
        license_db: bool = False,
        ):
        update_funcs, db_res = [], []
        if dev_db:
            update_funcs += [self.update_dev_db]
        if inv_db:
            update_funcs += [self.update_inv_db]
        if site_db:
            update_funcs += [self.update_site_db]
        if template_db:
            update_funcs += [self.update_template_db]
        if group_db:
            update_funcs += [self.update_group_db]
        if label_db:
            update_funcs += [self.update_label_db]
        if license_db:
            update_funcs += [self.update_license_db]
        async with self.central.aio_session:
            if update_funcs:
                db_res += [await update_funcs[0]()]
                if db_res[-1]:
                    if len(update_funcs) > 1:
                        db_res = [*db_res, *await asyncio.gather(*[f() for f in update_funcs[1:]])]

            # If all *_db params are false refresh cache for all
            # TODO make more elegant
            else:
                db_res += [await self.update_group_db()]  # update groups first so template update can use the result
                if db_res[-1]:
                    db_res += [await self.update_dev_db()]  # dev_db separate as it uses asyncio.gather/central._batch_request
                    if db_res[-1]:
                        db_res = [
                            *db_res,
                            *await asyncio.gather(
                                self.update_inv_db(),
                                self.update_site_db(),
                                self.update_template_db(),
                                self.update_label_db(),
                                self.update_license_db()
                            )
                        ]
        return db_res

    def check_fresh(
        self,
        refresh: bool = False,
        site_db: bool = False,
        dev_db: bool = False,
        inv_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
        label_db: bool = False,
        license_db: bool = False,
    ) -> List[Response]:
        db_res = None
        if True in [site_db, inv_db, dev_db, group_db, template_db, label_db, license_db]:
            refresh = True

        if refresh or not config.cache_file.is_file() or not config.cache_file.stat().st_size > 0:
            _word = "Refreshing" if refresh else "Populating"
            print(f"[cyan]-- {_word} Identifier mapping Cache --[/cyan]", end="")

            start = time.monotonic()
            db_res = asyncio.run(self._check_fresh(
                dev_db=dev_db, inv_db=inv_db, site_db=site_db, template_db=template_db, group_db=group_db, label_db=label_db, license_db=license_db
                )
            )

            if not all([r.ok for r in db_res]):
                res_map = ["dev_db", "inv_db", "site_db", "template_db", "group_db", "label_db", "license_db"]
                res_map = ", ".join([db for idx, db in enumerate(res_map[0:len(db_res)]) if not db_res[idx]])
                self.central.spinner.fail(f"Cache Refresh Returned an error updating ({res_map})")
            else:
                self.central.spinner.succeed(f"Cache Refresh Completed in {round(time.monotonic() - start, 2)} sec")
            log.info(f"Cache Refreshed in {round(time.monotonic() - start, 2)} seconds", show=False)

        return db_res

    def handle_multi_match(
        self,
        match: List[CentralObject] | List[models.Client],
        query_str: str = None,
        query_type: str = "device",
    ) -> List[Dict[str, Any]]:
        # typer.secho(f" -- Ambiguous identifier provided.  Please select desired {query_type}. --\n", color="cyan")
        typer.echo()
        set_width_cols = {}
        if query_type == "site":
            fields = ("name", "city", "state", "type")
        elif query_type == "template":
            fields = ("name", "group", "model", "device_type", "version")
        elif query_type == "group":
            fields = ("name",)
            set_width_cols = {"name": {"min": 20, "max": None}}
        elif query_type == "label":
            fields = ("name",)
        elif query_type == "inventory":
            fields = ("serial", "mac")
        elif query_type == "client":
            fields = {"name", "mac", "ip", "connected_port", "connected_name", "site"}
        else:  # device
            fields = ("name", "serial", "mac", "type")

        if isinstance(match[0], models.Client):
            data = [{k: d.dict()[k] for k in d.dict() if k in fields} for d in match]
        else:
            data = [{k: d[k] for k in d.data if k in fields} for d in match]

        out = utils.output(
            data,
            title=f"Ambiguous identifier. Select desired {query_type}.",
            set_width_cols=set_width_cols,
        )
        menu = out.menu(data_len=len(match))

        if query_str:
            menu = menu.replace(query_str, typer.style(query_str, fg="bright_cyan"))
            menu = menu.replace(query_str.upper(), typer.style(query_str.upper(), fg="bright_cyan"))
        typer.echo(menu)
        selection = ""
        valid = [str(idx + 1) for idx, _ in enumerate(match)]
        try:
            while selection not in valid:
                selection = typer.prompt(f"Select {query_type.title()}")
                if not selection or selection not in valid:
                    typer.secho(f"Invalid selection {selection}, try again.")
        except KeyboardInterrupt:
            raise typer.Abort()

        return [match.pop(int(selection) - 1)]

    def get_identifier(
        self,
        qry_str: str,
        qry_funcs: Sequence[str],
        device_type: Union[str, List[str]] = None,
        swack: bool = False,
        conductor_only: bool = False,
        group: str = None,
        all: bool = False,
        completion: bool = False,
    ) -> Union[CentralObject, List[CentralObject]]:
        """Get Identifier when iden type could be one of multiple types.  i.e. device or group

        Args:
            qry_str (str): The query string provided by user.
            qry_funcs (Sequence[str]): Sequence of strings "dev", "group", "site", "template"
            device_type (Union[str, List[str]], optional): Restrict matches to specific dev type(s).
                Defaults to None.
            swack (bool, optional): Restrict matches to only the stack commanders matching query (filter member switches).
                Defaults to False.
            conductor_only (bool, optional): Similar to swack, but only filters member switches of stacks, but will also return any standalone switches that match.
                Does not filter non stacks, the way swack option does. Defaults to False.
            group (str, optional): applies to get_template_identifier, Only match if template is in this group.
                Defaults to None.
            all (bool, optional): For use in completion, adds keyword "all" to valid completion.
            completion (bool, optional): If function is being called for AutoCompletion purposes. Defaults to False.
                When called for completion it will fail silently and will return multiple when multiple matches are found.

        Raises:
            typer.Exit: If not ran for completion, and there is no match, exit with code 1.

        Returns:
            CentralObject or list[CentralObject, ...]
        """
        # match = None
        device_type = utils.listify(device_type)
        default_kwargs = {"retry": False, "completion": completion, "silent": True}
        if "dev" in qry_funcs:  # move dev query last
            qry_funcs = [*[q for q in qry_funcs if q != "dev"], *["dev"]]

        match: List[CentralObject] = []
        for _ in range(0, 2):
            for q in qry_funcs:
                kwargs = default_kwargs.copy()
                if q == "dev":
                    kwargs["dev_type"] = device_type
                    kwargs["swack"] = swack
                    kwargs["conductor_only"] = conductor_only
                elif q == "template":
                    kwargs["group"] = group
                this_match = getattr(self, f"get_{q}_identifier")(qry_str, **kwargs) or []
                match = [*match, *utils.listify(this_match)]

                if match and not completion:
                    # user selects which device if multiple matches returned
                    if len(match) > 1:
                        match = self.handle_multi_match(match, query_str=qry_str,)

                    return match[0]

            # No match found trigger refresh and try again.
            if not match and not completion:
                self.check_fresh(
                    dev_db=True if "dev" in qry_funcs else False,
                    site_db=True if "site" in qry_funcs else False,
                    template_db=True if "template" in qry_funcs else False,
                    group_db=True if "group" in qry_funcs else False,
                )

        if completion:
            if all:
                if "all".startswith(qry_str.lower()):
                    match = utils.listify(match)
                    match += CentralObject("dev", {"name": "all", "help_text": "All Devices"})
            return match

        if not match:
            emoji_console.print(f":warning:  [bright_red]Unable to find a matching identifier[/] for [cyan]{qry_str}[/], tried: [cyan]{qry_funcs}[/]")
            raise typer.Exit(1)

    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: constants.AllDevTypes | List[constants.AllDevTypes] = None,
        swack: bool = False,
        conductor_only: bool = False,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        include_inventory: bool = False,
        exit_on_fail: bool = True,
    ) -> CentralObject | List[CentralObject] | None:
        """Get Devices from local cache, starting with most exact match, and progressively getting less exact.

        If multiple matches are found user is promted to select device.

        Args:
            query_str (str | Iterable[str]): The query string or list of strings to attempt to match.
            dev_type (constants.AllDevTypes | List[constants.AllDevTypes], optional): Limit matches to specific device type. Defaults to None (all device types).
            swack (bool, optional): For switches only return the conductor switch that matches. For APs only return the VC of the swarm the match belongs to. Defaults to False.
                If swack=True devices that lack a swack_id (swarm_id | stack_id) are filtered (even if they match).
            conductor_only (bool, optional): Similar to swack, but only filters member switches of stacks, but will also return any standalone switches that match.
                Does not filter non stacks, the way swack option does. Defaults to False.
            retry (bool, optional): If failure to match should result in a cache update and retry. Defaults to True.
            completion (bool, optional): If this is being called for tab completion (Allows multiple matches, implies retry=False, silent=True, exit_on_fail=False). Defaults to False.
            silent (bool, optional): Do not display errors / output, simply returns match if match is found. Defaults to False.
            include_inventory (bool, optional): Whether match attempt should also include Inventory DB (devices in GLCP that have yet to connect to Central). Defaults to False.
            exit_on_fail (bool, optional): Whether a failure to match exits the program. Defaults to True.

        Raises:
            typer.Exit: Exit CLI / command, occurs if there is no match unless exit_on_fail is set to False.

        Returns:
            CentralObject | List[CentralObject] | None: List of matching CentralObjects (devices, sites, groups ...) that match query_str
        """

        retry = False if completion else retry
        # TODO dev_type currently not passed in or handled identifier for show switches would also
        # try to match APs ...  & (self.Q.type == dev_type)
        # TODO refactor to single test function usable by all identifier methods 1 search with a more involved test
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # Try exact match
            match = self.DevDB.search(
                (self.Q.name == query_str)
                | (self.Q.ip.test(lambda v: v and v.split("/")[0] == query_str))
                | (self.Q.mac == utils.Mac(query_str).cols)
                | (self.Q.serial == query_str)
            )
            # Inventory must be exact match expecting full serial numbers but will allow MAC if exact match
            if not match and include_inventory:
                match = self.InvDB.search(
                    (self.Q.serial == query_str)
                    | (self.Q.mac == utils.Mac(query_str).cols)
                )

            # retry with case insensitive name match if no match with original query
            if not match:
                match = self.DevDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                    | self.Q.mac.test(lambda v: v.lower() == utils.Mac(query_str).cols.lower())
                    | self.Q.serial.test(lambda v: v.lower() == query_str.lower())
                )

            # retry name match swapping - for _ and _ for -
            if not match:
                if "-" in query_str:
                    match = self.DevDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match = self.DevDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.DevDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.serial.test(lambda v: v.lower().startswith(query_str.lower()))
                )
                if not match:
                    qry_mac = utils.Mac(query_str)
                    qry_mac_fuzzy = utils.Mac(query_str, fuzzy=True)
                    if qry_mac or len(qry_mac) == len(qry_mac_fuzzy):
                        match = self.DevDB.search(
                            self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str, fuzzy=completion).cols.lower()))
                        )

            # no match found initiate cache update
            if retry and not match and self.central.get_all_devicesv2 not in self.updated:
                if FUZZ:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [d["name"] for d in self.devices], limit=1)[0]
                    confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.DevDB.search(self.Q.name == fuzz_match)
                if not match:
                    kwargs = {"dev_db": True}
                    if include_inventory:
                        _word = " & Inventory "
                        kwargs["inv_db"] = True
                    else:
                        _word = " "
                    print(f"[bright_red]No Match Found[/] for [cyan]{query_str}[/], Updating Device{_word}Cache.")
                    self.check_fresh(refresh=True, **kwargs)

            if match:
                match = [CentralObject("dev", dev) for dev in match]
                break

        all_match = None
        if dev_type:
            all_match = match.copy()
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"]))

            match = [d for d in all_match if d.type in dev_type]

        # swack is swarm/stack id.  We filter out all but the commander for a stack and all but the VC for a swarm
        # For a stack a multi-match is expected when they are using hostname as all members have the same hostname.
        # This param returns only the commander matching the name.
        if len(match) > 1 and (swack or conductor_only):
            unique_swack_ids = set([d.swack_id for d in match if d.swack_id])
            stacks = [d for d in match if d.swack_id in unique_swack_ids and d.ip or (d.switch_role and d.switch_role == 2)]
            if swack:
                match = stacks
            elif conductor_only:
                match = [*stacks, *[d for d in match if not d.swack_id]]

        if completion:
            return match or []

        if match:
            # user selects which device if multiple matches returned
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str,)

            return match[0]

        elif retry:
            log.error(f"Unable to gather device info from provided identifier {query_str}", show=not silent)
            if all_match:
                all_match_msg = f"{', '.join(m.name for m in all_match[0:5])}{', ...' if len(all_match) > 5 else ''}"
                _dev_type_str = ", ".join(dev_type)
                log.error(
                    f"The Following devices matched {all_match_msg} excluded as device type != [{_dev_type_str}]",
                    show=True,
                )
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return None

    def get_site_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject | List[CentralObject]:
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)


        if completion and query_str == "":
            return [CentralObject("site", s) for s in self.sites]

        match = None
        for _ in range(0, 2 if retry else 1):
            # try exact match by name
            match = self.SiteDB.search(
                (self.Q.name == query_str)
            )

            # try exact match by other fields
            if not match:
                match = self.SiteDB.search(
                    (self.Q.id.test(lambda v: str(v) == query_str))
                    | (self.Q.zipcode == query_str)
                    | (self.Q.address == query_str)
                    | (self.Q.city == query_str)
                    | (self.Q.state == query_str)
                    | (self.Q.state.test(lambda v: constants.state_abbrev_to_pretty.get(query_str.upper(), query_str).title() == v.title()))
                )

            # try case insensitive name
            if not match:
                match = self.SiteDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                )
            # try case insensitve address match
            if not match:
                match = self.SiteDB.search(
                    self.Q.address.test(lambda v: v.lower().replace(" ", "") == query_str.lower().replace(" ", ""))
                )

            # try case insensitive name swapping _ and -
            if not match:
                if "-" in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # try case insensitive name starts with
            if not match:
                match = self.SiteDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # Last Chance try other fields case insensitive startswith provided value
            if not match:
                match = self.SiteDB.search(
                    self.Q.zipcode.test(lambda v: v.startswith(query_str))
                    | self.Q.city.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.state.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: " ".join(v.split(" ")[1:]).lower().startswith(query_str.lower()))
                )

            # err_console.print(f'\n{match=} {query_str=} {retry=} {completion=} {silent=}')  # DEBUG
            if retry and not match and self.central.get_all_sites not in self.updated:
                if FUZZ and not completion:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [s["name"] for s in self.sites], limit=1)[0]
                    confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.SiteDB.search(self.Q.name == fuzz_match)
                if not match:
                    typer.secho(f"No Match Found for {query_str}, Updating Site Cache", fg="red")
                    self.check_fresh(refresh=True, site_db=True)
            if match:
                match = [CentralObject("site", s) for s in match]
                break

        if completion:
            return match

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="site",)

            return match[0]

        elif retry:
            log.error(f"Unable to gather site info from provided identifier {query_str}", show=not silent)
            raise typer.Exit(1)

    def get_group_identifier(
        self,
        query_str: str,
        ret_field: str = "name",
        retry: bool = True,
        multi_ok: bool = False,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject | List[CentralObject]:
        """Allows Case insensitive group match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            # TODO change all get_*_identifier functions to continue to look for matches when match is found when
            #       completion is True
            # Exact match
            if query_str == "":
                match = self.groups
            else:
                match = self.GroupDB.search((self.Q.name == query_str))

            # case insensitive
            if not match:
                match = self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match:
                match = self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match:
                if "_" in query_str or "-" in query_str:
                    match = self.GroupDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith ignore - _
            if not match:
                match = self.GroupDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().strip("-_").startswith(query_str.lower().strip("-_"))
                    )
                )

            # TODO add fuzzy match other get_*_identifier functions and add fuzz as dep
            # fuzzy match
            if not match and retry and self.central.get_all_groups not in self.updated:
                print(f"[bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [g["name"] for g in self.groups], limit=1)[0]
                    if fuzz_confidence >= 70 and typer.confirm(f"Did you mean {fuzz_match}?"):
                        match = self.GroupDB.search(self.Q.name == fuzz_match)
                if not match:
                    typer.secho(f"No Match Found for {query_str}, Updating group Cache", fg="red")
                    self.check_fresh(refresh=True, group_db=True)
                _ += 1
            if match:
                match = [CentralObject("group", g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="group",)  # multi_ok=multi_ok)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather group data from provided identifier {query_str}", show=True)
            valid_groups = "\n".join(self.group_names)
            typer.secho(f"{query_str} appears to be invalid", fg="red")
            typer.secho(f"Valid Groups:\n--\n{valid_groups}\n--\n", fg="cyan")
            raise typer.Exit(1)
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather group data from provided identifier {query_str}", show=not silent
                )

    def get_label_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject | List[CentralObject]:
        """Allows Case insensitive label match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            # TODO change all get_*_identifier functions to continue to look for matches when match is found when
            #       completion is True
            # Exact match
            if query_str == "":
                match = self.labels
            else:
                match = self.LabelDB.search((self.Q.name == query_str))

            # case insensitive
            if not match:
                match = self.LabelDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match:
                match = self.LabelDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match:
                if "_" in query_str or "-" in query_str:
                    match = self.LabelDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith ignore - _
            if not match:
                match = self.LabelDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().strip("-_").startswith(query_str.lower().strip("-_"))
                    )
                )

            # TODO add fuzzy match other get_*_identifier functions and add fuzz as dep
            # fuzzy match
            if not match and retry and self.central.get_labels not in self.updated:
                print(f"[bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ:
                    fuzz_resp = process.extract(query_str, [label["name"] for label in self.labels], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.LabelDB.search(self.Q.name == fuzz_match)
                if not match:
                    typer.secho(f"No Match Found for {query_str}, Updating label Cache", fg="red")
                    self.check_fresh(refresh=True, label_db=True)
                _ += 1
            if match:
                match = [CentralObject("label", g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="label",)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=True)
            valid_labels = "\n".join(self.label_names)
            # TODO convert all these to rich
            typer.secho(f"{query_str} appears to be invalid", fg="red")
            typer.secho(f"Valid Labels:\n--\n{valid_labels}\n--\n", fg="cyan")
            raise typer.Exit(1)
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=not silent
                )

    def get_template_identifier(
        self,
        query_str: str,
        ret_field: str = "name",
        group: str = None,
        retry: bool = True,
        multi_ok: bool = False,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject:
        """Allows case insensitive template match by template name"""
        retry = False if completion else retry
        if not query_str and completion:
            return [CentralObject("template", data=t) for t in self.templates]

        # TODO verify and remove
        if multi_ok:
            log.error("deprecated parameter multi_ok sent to get_template_identifier.")

        match = None
        for _ in range(0, 2 if retry else 1):
            # exact
            match = self.TemplateDB.search(
                (self.Q.name == query_str)
            )

            # case insensitive
            if not match:
                match = self.TemplateDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive with -/_ swap
            if not match:
                if "_" in query_str:
                    match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))
                elif "-" in query_str:
                    match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))

            # startswith
            if not match:
                match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower().startswith(query_str.lower())))

            if retry and not match and self.central.get_all_templates not in self.updated:
                if FUZZ:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [t["name"] for t in self.templates], limit=1)[0]
                    confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.TemplateDB.search(self.Q.name == fuzz_match)
                if not match:
                    typer.secho(f"No Match Found for {query_str}, Updating template Cache", fg="red")
                    self.check_fresh(refresh=True, template_db=True)
            if match:
                match = [CentralObject("template", tmplt) for tmplt in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                if group:
                    match = [d for d in match if d.group.lower() == group.lower()]

            if len(match) > 1:
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="template",
                    # multi_ok=multi_ok,
                )

            return match[0]

        elif retry:
            log.error(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Exit(1)
        else:
            if not completion and not silent:
                log.warning(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=False)

    def get_client_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        exit_on_fail: bool = False,
        silent: bool = False,
    ) -> models.Client | List[models.Client]:
        """Allows Case insensitive client match"""
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        if completion and not query_str.strip():
            return [models.Client(**c) for c in self.clients]

        match = None
        for _ in range(0, 2 if retry else 1):
            # Try exact match
            match = self.ClientDB.search(
                (self.Q.name == query_str)
                | (self.Q.mac == utils.Mac(query_str).cols)
                | (self.Q.ip == query_str)
            )

            # retry with case insensitive name match if no match with original query
            if not match:
                match = self.ClientDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                    | self.Q.mac.test(lambda v: v.lower() == utils.Mac(query_str).cols.lower())
                )

            # retry name match swapping - for _ and _ for -
            if not match:
                if "-" in query_str:
                    match = self.ClientDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match = self.ClientDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.ClientDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.ip.test(lambda v: v.lower().startswith(query_str.lower()))
                )
                if not match:
                    qry_mac = utils.Mac(query_str)
                    qry_mac_fuzzy = utils.Mac(query_str, fuzzy=True)
                    if qry_mac or len(qry_mac) == len(qry_mac_fuzzy):
                        match = self.ClientDB.search(
                            self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str, fuzzy=completion).cols.lower()))
                        )

            # no match found initiate cache update
            if retry and not match and self.central.get_clients not in self.updated:
                if FUZZ and self.clients:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [d["name"] for d in self.clients], limit=1)[0]
                    confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.ClientDB.search(self.Q.name == fuzz_match)
                if not match:
                    print(f"[bright_red]No Match Found[/] for [cyan]{query_str}[/], Updating Client Cache")
                    asyncio.run(self.update_client_db("wireless"))  # on demand update only for WLAN as kick only applies to WLAN currently

            if match:
                match = [models.Client(**c) for c in match]
                break

        if completion:
            return match or []

        if match:
            # user selects which device if multiple matches returned
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="client")

            return match[0]

        elif retry:
            log.error(f"Unable to gather client info from provided identifier {query_str}", show=not silent)
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return None

    # cencli completion can be removed..  Moved to get_event_identifier
    def get_log_identifier(self, query: str) -> str:
        if "audit_trail" in query:
            return query
        elif query == "":  # tab completion
            return ["cencli", *[x["id"] for x in self.logs]]

        try:
            if "cencli".startswith(query.lower()):
                return ["cencli"]

            match = self.LogDB.search(self.Q.id == int(query))
            if not match:
                log.warning(f"Unable to gather log id from short index query {query}", show=True)
                typer.echo("Short log_id aliases are built each time 'show logs' is ran.")
                typer.echo("  You can verify the cache by running (hidden command) 'show cache logs'")
                typer.echo("  run 'show logs [OPTIONS]' then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1]["long_id"]

        except ValueError as e:
            log.exception(f"Exception in get_log_identifier {e.__class__.__name__}\n{e}")
            typer.secho(f"Exception in get_log_identifier {e.__class__.__name__}", fg="red")
            raise typer.Exit(1)

    def get_event_identifier(self, query: str) -> str:
        if query == "":  # tab completion
            return [x["id"] for x in self.events]

        try:
            match = self.EventDB.search(self.Q.id == str(query))
            if not match:
                log.warning(f"Unable to gather event details from short index query {query}", show=True)
                print("Short event_id aliases are built each time [cyan]'show events'[/] is ran.")
                print("  You can verify the cache by running (hidden command) [cyan]'show cache events'[/]")
                print("  run [cyan]'show events [OPTIONS]'[/] then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1]["details"]

        except ValueError as e:
            log.error(f"Exception in get_event_identifier {e.__class__.__name__}", show=True)
            log.exception(e)
            # print(f"[bright_red]Exception[/] in get_event_identifier [dark_orange4]{e.__class__.__name__}[/]")
            raise typer.Exit(1)

    def get_mpsk_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject | List[CentralObject]:
        """Allows Case insensitive ssid match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            if query_str == "":
                match = self.mpsk
            else:
                match = self.MpskDB.search((self.Q.name == query_str))

            # case insensitive
            if not match:
                match = self.MpskDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match:
                match = self.MpskDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match:
                if "_" in query_str or "-" in query_str:
                    match = self.MpskDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith search for mspk id
            if not match:
                match = self.MpskDB.search(
                    self.Q.id.test(
                        lambda v: v.lower().startswith(query_str.lower())
                    )
                )

            if not match and retry and self.central.cloudauth_get_mpsk_networks not in self.updated:
                if FUZZ:
                    fuzz_resp = process.extract(query_str, [mpsk["name"] for mpsk in self.mpsk], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.MpskDB.search(self.Q.name == fuzz_match)
                if not match:
                    err_console.print(f":warning:  [bright_red]No Match found for[/] [cyan]{query_str}[/].  Updating mpsk Cache")
                    asyncio.run(self.update_mpsk_db())
                _ += 1
            if match:
                match = [CentralObject("mpsk", g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="mpsk",)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=True)
            valid_mpsk = "\n".join([f'[cyan]{m["name"]}[/]' for m in self.mpsk])
            print(f":warning:  [cyan]{query_str}[/] appears to be invalid")
            print(f"\n[bright_green]Valid MPSK Networks[/]:\n--\n{valid_mpsk}\n--\n")
            raise typer.Exit(1)
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=not silent
                )


    def get_name_id_identifier(
        self,
        cache_name: Literal["dev", "site", "template", "group", "label", "mpsk", "portal"],
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject | List[CentralObject]:
        cache_details = CacheDetails(self)
        this: CacheAttributes = getattr(cache_details, cache_name)
        db_all = this.db.all()
        db = this.db
        """Allows Case insensitive ssid match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            if query_str == "":
                match = db_all
            else:
                match = db.search((self.Q.name == query_str))

            # case insensitive
            if not match:
                match = db.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match:
                match = db.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match:
                if "_" in query_str or "-" in query_str:
                    match = db.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith search for mspk id
            if not match:
                match = db.search(
                    self.Q.id.test(
                        lambda v: v.lower().startswith(query_str.lower())
                    )
                )

            if not match and retry and this.already_updated_func not in self.updated:
                if FUZZ:
                    fuzz_resp = process.extract(query_str, [item["name"] for item in db_all], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        confirm_str = render.rich_capture(f"[bright_red]{query_str}[/] not found in cache.  Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.db.search(self.Q.name == fuzz_match)
                if not match:
                    err_console.print(f":warning:  [bright_red]No Match found for[/] [cyan]{query_str}[/].  Updating {cache_name} Cache")
                    asyncio.run(this.cache_update_func())
                _ += 1
            if match:
                match = [CentralObject(this.name, g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type=this.name,)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=True)
            valid = "\n".join([f'[cyan]{m["name"]}[/]' for m in db_all])
            print(f":warning:  [cyan]{query_str}[/] appears to be invalid")
            print(f"\n[bright_green]Valid Names[/]:\n--\n{valid}\n--\n")
            raise typer.Exit(1)
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=not silent
                )

class CacheAttributes:
    def __init__(self, name: Literal["dev", "site", "template", "group", "label", "mpsk", "portal"], db: Table, already_updated_func: Callable, cache_update_func: Callable) -> None:
        self.name = name
        self.db = db
        self.already_updated_func = already_updated_func
        self.cache_update_func = cache_update_func

class CacheDetails:
    def __init__(self, cache = Cache):
        self.dev = CacheAttributes(name="dev", db=cache.DevDB, already_updated_func=cache.central.get_all_devicesv2, cache_update_func=cache.update_dev_db)
        self.site = CacheAttributes(name="site", db=cache.SiteDB, already_updated_func=cache.central.get_all_sites, cache_update_func=cache.update_site_db)
        self.portal = CacheAttributes(name="portal", db=cache.PortalDB, already_updated_func=cache.central.get_portals, cache_update_func=cache.update_portal_db)
        self.mpsk = CacheAttributes(name="mpsk", db=cache.MpskDB, already_updated_func=cache.central.cloudauth_get_mpsk_networks, cache_update_func=cache.update_mpsk_db)