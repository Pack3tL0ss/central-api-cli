#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# TODO keep addl attributes from return in cache with key prefixed with _ or under another internal use key
# device results include site_id which we strip out as it's not useful for display, but it is useful for
# internally.  Currently the site_id is being looked up from the site cache
from typing import Any, Literal, Dict, Sequence, Union, List
from aiohttp.client import ClientSession
from tinydb import TinyDB, Query
from rich import print
from centralcli import log, utils, config, CentralApi, cleaner, constants, Response
from pathlib import Path

import asyncio
import time
import typer

try:
    import readline  # noqa imported for backspace support during prompt.
except Exception:
    pass

# TODO remove after TESTING NEW string matching lookup
try:
    from fuzzywuzzy import process # type: ignore noqa
    FUZZ = True
except Exception:
    FUZZ = False
    pass

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
        db: Literal["dev", "site", "template", "group", "label"],
        data: Union[list, Dict[str, Any]],
    ) -> Union[list, Dict[str, Any]]:
        self.is_dev, self.is_template, self.is_group, self.is_site, self.is_label = False, False, False, False, False
        data = None if not data else data
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
                self.site,
            ]
            parts = utils.strip_none(parts, strip_empty_obj=True)
            if self.site:
                parts[-1] = f"s:{parts[-1]}"
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
        return "|".join(
            [
                f'{"[blue]" if not idx % 2 == 0 else "[cyan]"}{p}[/]' for idx, p in enumerate(parts)
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
                f"{'[cyan]' if idx > 0 else '[bright_green]'}{p}[/]" for idx, p in enumerate(parts)
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
    ) -> None:
        self._dev = dev
        self._inv = inv
        self._site = site
        self._template = template
        self._group = group
        self._label = label

    def update_rl(self, resp: Response) -> Response:
        """Returns provided Response object with the RateLimit info from the most recent API call.
        """
        _last_rl = sorted([r.rl for r in [self._dev, self._inv, self._site, self._template, self._group] if r is not None], key=lambda k: k.remain_day)
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

    @group.setter
    def label(self, resp: Response):
        self._label = resp


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
        if config.valid and config.cache_dir.exists():
            self.DevDB = TinyDB(config.cache_file)
            self.InvDB = self.DevDB.table("inventory")
            self.SiteDB = self.DevDB.table("sites")
            self.GroupDB = self.DevDB.table("groups")
            self.TemplateDB = self.DevDB.table("templates")
            self.LabelDB = self.DevDB.table("labels")
            # log db is used to provide simple index to get details for logs
            # vs the actual log id in form 'audit_trail_2021_2,...'
            # it is updated anytime show logs is ran.
            self.LogDB = self.DevDB.table("logs")
            self.EventDB = self.DevDB.table("events")
            self.HookConfigDB = self.DevDB.table("wh_config")
            self.HookDataDB = self.DevDB.table("wh_data")
            self._tables = [self.DevDB, self.InvDB, self.SiteDB, self.GroupDB, self.TemplateDB, self.LabelDB]
            self.Q = Query()
            if data:
                self.insert(data)
            if central:
                self.check_fresh(refresh)

    def __call__(self, refresh=False) -> None:
        if refresh:
            self.check_fresh(refresh)

    def __iter__(self) -> list:
        for db in self._tables:
            yield db.name(), db.all()

    @property
    def devices(self) -> list:
        return self.DevDB.all()

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
            force_refresh (bool, optional): Force a refresh of cache. Defaults to True.
                Refresh will only occur if cache was not updated during this session.
                Setting force_refresh to False means it will not occur regardless.

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
        combined = [
            {**self.inventory_by_serial[serial], **self.devices_by_serial.get(serial, {})}
            for serial in self.inventory_by_serial

        ]
        res[-1].output = combined  # TODO this may be an issue if check_fresh has a failure, don't think it returns Response object
        return res[-1]

    @staticmethod
    def account_completion(incomplete: str,):
        for a in config.defined_accounts:
            if a.lower().startswith(incomplete.lower()):
                yield a

    # TODO maybe build script to gather completion and help text and place in flat file
    def method_test_completion(self, incomplete: str, args: List[str] = []):
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
        kwds = ["group", "mac", "serial"]
        out = []

        if not args:  # HACK click 8.x work-around now pinned at click 7.2 until resolved
            args = [v for k, v in ctx.params.items() if v and k[:2] in ["kw", "va"]]

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
        incomplete: str,
        args: List[str] = None,
    ):
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
                elif m.mac.strip(":.-").lower().startswith(incomplete.strip(":.-")):
                    out += [tuple([m.mac, m.help_text])]
                elif m.ip.startswith(incomplete):
                    out += [tuple([m.ip, m.help_text])]
                else:
                    # failsafe, shouldn't hit
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_switch_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ):
        """Device completion for returning matches that are either switch or AP

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI.
        """
        match = self.get_dev_identifier(incomplete, dev_type=["switch"], completion=True)

        out = []
        if match:
            out = [
                tuple([m.name, m.help_text]) for m in sorted(match, key=lambda i: i.name)
                if m.name not in args
                ]

        for m in out:
            yield m

    def dev_kwarg_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ):
        """Completion for commands that allow a list of devices followed by group/site.

        i.e. cencli move dev1 dev2 dev3 site site_name group group_name

        Args:
            ctx (typer.Context): Provided automatically by typer
            incomplete (str): The incomplete word for autocompletion
            args (List[str], optional): The prev args passed into the command.

        Yields:
            tuple: matching completion string, help text
        """
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
        incomplete: str,
        args: List[str] = [],
    ):
        """Completion for argument where only APs are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.
        """
        dev_types = ["ap"]
        match = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_client_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ):
        """Completion for client output.

        Returns only devices that apply based on filter provided in command, defaults to clients
        on both APs and switches (wires/wireless), but returns applicable devices if "wireless" or
        "wired" filter is used.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI.
        """
        gen = self.dev_switch_ap_completion

        if args:
            if args[-1].lower() == "wireless":
                gen = self.dev_ap_completion
            elif args[-1].lower() == "wired":
                gen = self.dev_switch_completion
            elif args[-1].lower() == "all":
                return

        for m in [dev for dev in gen(incomplete, args)]:
            yield m

    def dev_switch_ap_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ):
        """Device completion for returning matches that are either switch or AP

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI.
        """
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
        incomplete: str,
        args: List[str] = None,
    ):
        """Device completion that returns only ap and gw.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.
        """
        dev_types = ["ap", "gw"]
        match = [m for m in self.dev_completion(incomplete) if m.generic_type in dev_types]

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
    ):
        """Device completion that returns only switches and gateways.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.
        """
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
    ):
        """Completion for device idens where only gateways are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            tuple: name and help_text for the device
        """
        # match = [m for m in self.dev_completion(incomplete) if m.generic_type == "gw"]
        match = self.get_identifier(incomplete, ["dev"], device_type="gw", completion=True)

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
        incomplete: str,
        args: List[str] = None,
    ):
        """Completion for argument that can be either group or device.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.
        """
        group_match = self.get_group_identifier(incomplete, completion=True)

        dev_types = ["ap", "gw"]
        match = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)

        match = group_match + match


        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        if " ".join(args).lower() == "show config" and "cencli".lower().startswith(incomplete):
            out += [("cencli", "show cencli configuration")]

        # partial completion by serial: out appears to have list with expected tuple but does
        # not appear in zsh

        for m in out:
            log.debug(f"yielding to completion {m}")  # DEBUG remove me serial completion yielding expected tuple but does not appear in zsh
            yield m

    def group_dev_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        """Completion for argument that can be either group or a gateway.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.
        """
        # dev_types = ["gw"]
        # dev_match = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)
        # match = [*self.get_group_identifier(incomplete, completion=True), *dev_match]
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
        incomplete: str,
        args: List[str] = None,
    ):
        """Completion for argument that can be either group, site, or a gateway or keyword "commands".

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.
        """
        if args[-1] == "all":
            yield "commands"
        elif args[-1] in ["commands", "file"]:
            yield None
        elif args[-1] not in ["group", "site", "device"]:
            yield "commands"
        else:
            if args[-1] == "group":
                db = "group"
            elif args[-1] == "site":
                db = "site"
            else:
                db = "dev"

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
        args: List[str] = None,
    ):
        match = self.get_group_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def label_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
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

    def event_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        for event in self.events:
            if event["id"].startswith(incomplete):
                yield event["id"], f"{event['id']}|{event['device'].split('Group:')[0].rstrip()}"

        # for match, help_txt in sorted(matches, key=lambda i: int(i[0])):
        #     yield match, help_txt
        # for event_id in self.event_ids:
        #     if event_id.startswith(incomplete):
        #         yield event_id, f"Details for Event with id {event_id}"

    # TODO add support for zip code city state etc.
    def site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
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
    ):
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
    ):
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
    ):
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

    def remove_completion(
        self,
        incomplete: str,
        args: List[str],
    ):
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
                out += [m for m in self.dev_completion(incomplete)]
            else:
                out += [m for m in self.null_completion(incomplete)]

            for m in out:
                yield m

    def completion(
        self,
        incomplete: str,
        args: List[str],
    ):
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
    async def update_dev_db(self,  data: Union[str, List[str], List[dict]] = None, remove: bool = False) -> Union[List[int], Response]:
        """Update Device Database (local cache).

        Args:
            data (Union[str, List[str]], List[dict] optional): serial number of list of serials numbers to add or remove. Defaults to None.
            remove (bool, optional): Determines if update is to add or remove from cache. Defaults to False.

        Raises:
            ValueError: if provided data is of wrong type or does not appear to be a serial number

        Returns:
            Union[Response, None]: returns Response object from inventory api call if no data was provided for add/remove.
                If adding/removing (providing serials) returns None.  Logs errors if any occur during db update.
        """
        if data:
            data = utils.listify(data)
            if not remove:
                db_res = self.DevDB.insert_multiple(data)
                if False in db_res:
                    log.error(f"TinyDB DevDB update returned an error.  db_resp: {db_res}", show=True)
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
            resp = await self.central.get_all_devicesv2()
            if resp.ok:
                if resp.output:
                    resp.output = utils.listify(resp.output)
                    resp.output = cleaner.get_devices(resp.output)

                    self.DevDB.truncate()
                    update_res = self.DevDB.insert_multiple(resp.output)
                    if False in update_res:
                        log.error("Tiny DB returned an error during dev db update")

                # TODO change updated from  list of funcs to class with bool attributes or something
                self.updated.append(self.central.get_all_devicesv2)
                self.responses.dev = resp
            return resp

    async def update_inv_db(self, data: Union[str, List[str]] = None, remove: bool = False) -> Union[List[int], Response]:
        """Update Inventory Database (local cache).

        Args:
            data (Union[str, List[str]], optional): serial number of list of serials numbers to add or remove. Defaults to None.
            remove (bool, optional): Determines if update is to add or remove from cache. Defaults to False.

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
                        doc_ids += [self.InvDB.get((self.Q.serial == qry)).doc_id]

                if len(doc_ids) != len(data):
                    log.error(
                        f"Warning update_inv_db: no match found for {len(data) - len(doc_ids)} of the {len(data)} serials provided.",
                        show=True
                    )

                db_res = self.InvDB.remove(doc_ids=doc_ids)
                if False in db_res:
                    log.error(f"Tiny DB returned an error during Inventory db update {db_res}", show=True)
        else:
            resp = await self.central.get_device_inventory()
            if resp.ok:
                if resp.output:
                    resp.output = utils.listify(resp.output)
                    resp.output = cleaner.get_device_inventory(resp.output)

                    self.InvDB.truncate()
                    db_res = self.InvDB.insert_multiple(resp.output)
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
                return self.SiteDB.insert_multiple(data)
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
                    log.error("Tiny DB returned an error during group db update")
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
                    log.error("Tiny DB returned an error during group db update")
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

    # TODO cache.groups cache.devices etc change to Response object with data in output.  So they can be leveraged in commands with all attributes
    async def _check_fresh(
        self,
        dev_db: bool = False,
        inv_db: bool = False,
        site_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
        label_db: bool = False,
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
        async with ClientSession() as self.central.aio_session:
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
                                self.update_label_db()
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
    ) -> List[Response]:
        db_res = None
        if True in [site_db, inv_db, dev_db, group_db, template_db, label_db]:
            refresh = True

        if refresh or not config.cache_file.is_file() or not config.cache_file.stat().st_size > 0:
            _word = "Refreshing" if refresh else "Populating"
            print(f"[cyan]-- {_word} Identifier mapping Cache --[/cyan]", end="")

            start = time.monotonic()
            db_res = asyncio.run(self._check_fresh(
                dev_db=dev_db, inv_db=inv_db, site_db=site_db, template_db=template_db, group_db=group_db, label_db=label_db
                )
            )

            if not all([r.ok for r in db_res]):
                res_map = ["dev_db", "inv_db", "site_db", "template_db", "group_db", "label_db"]
                res_map = ", ".join([db for idx, db in enumerate(res_map[0:len(db_res)]) if not db_res[idx]])
                self.central.spinner.fail(f"Cache Refresh Returned an error updating ({res_map})")
            else:
                self.central.spinner.succeed(f"Cache Refresh Completed in {round(time.monotonic() - start, 2)} sec")
            log.info(f"Cache Refreshed in {round(time.monotonic() - start, 2)} seconds", show=False)

        return db_res

    def handle_multi_match(
        self,
        match: List[CentralObject],
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
        else:  # device
            fields = ("name", "serial", "mac", "type")
        out = utils.output(
            [{k: d[k] for k in d.data if k in fields} for d in match],
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
        group: str = None,
        multi_ok: bool = False,
        all: bool = False,
        completion: bool = False,
    ) -> Union[CentralObject, List[CentralObject]]:
        """Get Identifier when iden type could be one of multiple types.  i.e. device or group

        Args:
            qry_str (str): The query string provided by user.
            qry_funcs (Sequence[str]): Sequence of strings "dev", "group", "site", "template"
            device_type (Union[str, List[str]], optional): Restrict matches to specific dev type(s).
                Defaults to None.
            group (str, optional): applies to get_template_identifier, Only match if template is in this group.
                Defaults to None.
            multi_ok (bool, optional): DEPRECATED, NO LONGER USED
            all (bool, optional): For use in completion, adds keyword "all" to valid completion.
            completion (bool, optional): If function is being called for AutoCompletion purposes. Defaults to False.
                When called for completion it will fail silently and will return multiple when multiple matches are found.

        Raises:
            typer.Exit: If not ran for completion, and there is no match, exit with code 1.

        Returns:
            CentralObject or list[CentralObject, ...]
        """
        match = None
        device_type = utils.listify(device_type)
        default_kwargs = {"retry": False, "completion": completion, "silent": True}
        for _ in range(0, 2):
            for q in qry_funcs:
                kwargs = default_kwargs.copy()
                if q == "dev":
                    kwargs["dev_type"] = device_type
                elif q == "template":
                    kwargs["group"] = group
                match: CentralObject = getattr(self, f"get_{q}_identifier")(qry_str, **kwargs)

                if match and not completion:
                    return match

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
            typer.secho(f"Unable to find a matching identifier for {qry_str}, tried: {qry_funcs}", fg="red")
            raise typer.Exit(1)

    def get_dev_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        dev_type: Union[constants.GenericDevTypes, List[constants.GenericDevTypes]] = None,
        # ret_field: str = "serial",       # TODO ret_field believe to be deprecated, now returns an object with all attributes
        retry: bool = True,
        # multi_ok: bool = True,          # TODO multi_ok also believe to be deprecated check
        completion: bool = False,
        silent: bool = False,
        include_inventory: bool = False,
    ) -> CentralObject:

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
                kwargs = {"dev_db": True}
                if include_inventory:
                    _word = " & Inventory "
                    kwargs["inv_db"] = True
                else:
                    _word = " "
                typer.secho(f"No Match Found for {query_str}, Updating Device{_word}Cache", fg="red")
                self.check_fresh(refresh=True, **kwargs)

            if match:
                match = [CentralObject("dev", dev) for dev in match]
                break

        all_match = None
        if dev_type:
            all_match = match.copy()
            dev_type = utils.listify(dev_type)
            match = []
            for _dev_type in dev_type:
                match += [d for d in all_match if d.generic_type.lower() in "".join(_dev_type[0:len(d.generic_type)]).lower()]

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
            raise typer.Exit(1)

    def get_site_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        ret_field: str = "id",
        retry: bool = True,
        multi_ok: bool = False,
        completion: bool = False,
        silent: bool = False,
    ) -> CentralObject:
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)


        if completion and query_str == "":
            return [CentralObject("site", s) for s in self.sites]

        match = None
        for _ in range(0, 2 if retry else 1):
            # TODO match on name first then the other stuff
            # 'm' returns Pommore          main-batch-demo  mb1-batch-demo
            #   because Pommore is in Milford
            # try exact site match
            match = self.SiteDB.search(
                (self.Q.name == query_str)
                | (self.Q.id.test(lambda v: str(v) == query_str))
                | (self.Q.zipcode == query_str)
                | (self.Q.address == query_str)
                | (self.Q.city == query_str)
                | (self.Q.state == query_str)
                | (self.Q.state.test(lambda v: constants.state_abbrev_to_pretty.get(query_str.upper(), query_str).title() == v.title()))
            )

            # raise ValueError(f'>{query_str}<, {type(query_str)}, {", ".join([m["name"] for m in match])} {bool(match)}')

            # retry with case insensitive name & address match if no match with original query
            if not match:
                match = self.SiteDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                    | self.Q.address.test(lambda v: v.lower().replace(" ", "") == query_str.lower().replace(" ", ""))
                )

            # swap _ and - and case insensitive
            if not match:
                if "-" in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.SiteDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.zipcode.test(lambda v: v.startswith(query_str))
                    | self.Q.city.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.state.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: " ".join(v.split(" ")[1:]).lower().startswith(query_str.lower()))
                )

            if retry and not match and self.central.get_all_sites not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating Site Cache", fg="red")
                self.check_fresh(refresh=True, site_db=True)
            if match:
                match = [CentralObject("site", s) for s in match]
                # raise ValueError(f'>{query_str}<, {type(query_str)}, {", ".join([m.name for m in match])}')
                break

        if completion:
            return match

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="site",)  # multi_ok=multi_ok)

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
    ) -> List[CentralObject]:
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
    ) -> CentralObject:
        """Allows Case insensitive group match"""
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
                    fuzz_resp = process.extract(query_str, [g["name"] for g in self.labels], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        if fuzz_confidence >= 70 and typer.confirm(f"Did you mean {fuzz_match}?"):
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

            match = self.EventDB.search(self.Q.id == int(query))
            if not match:
                log.warning(f"Unable to gather event details from short index query {query}", show=True)
                typer.echo("Short event_id aliases are built each time 'show events' is ran.")
                typer.echo("  You can verify the cache by running (hidden command) 'show cache events'")
                typer.echo("  run 'show events [OPTIONS]' then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1]["details"]

        except ValueError as e:
            log.exception(f"Exception in get_event_identifier {e.__class__.__name__}\n{e}")
            typer.secho(f"Exception in get_event_identifier {e.__class__.__name__}", fg="red")
            raise typer.Exit(1)
