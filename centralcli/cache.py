# -*- coding: utf-8 -*-
#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import datetime as dt
import time
from collections.abc import Generator, Iterator, KeysView, MutableMapping
from copy import deepcopy
from enum import Enum
from functools import cached_property, lru_cache, wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Literal, Optional, Sequence, Tuple, Union, overload

import pendulum
import typer
from pydantic import ValidationError
from rich import print
from rich.console import Console
from rich.markup import escape
from rich.text import Text
from tinydb import Query, TinyDB
from tinydb.table import Document
from yarl import URL

from centralcli import config, constants, log, render, utils
from centralcli.response import CombinedResponse

from .classic.api import ClassicAPI
from .client import BatchRequest, Session
from .cnx.models.cache import Inventory as GlpInventory
from .cnx.models.cache import Subscriptions, get_inventory_with_sub_data
from .environment import env
from .exceptions import CentralCliException
from .models import cache as models
from .objects import DateTime
from .response import Response

api = ClassicAPI(config.classic.base_url)

if config.glp.ok:
    from .cnx.api import GreenLakeAPI
    glp_api = GreenLakeAPI(config.glp.base_url)
else:
    glp_api = None  # pragma: no cover

if TYPE_CHECKING:
    from tinydb.table import Document, Table

    from .config import Config
    from .typedefs import CacheSiteDict, CertType, MPSKStatus, PortalAuthTypes, SiteData

try:
    import readline  # noqa imported for backspace support during prompt.
except Exception:  # pragma: no cover
    pass

try:
    from fuzzywuzzy import process  # type: ignore noqa
    FUZZ = True
except Exception:  # pragma: no cover
    FUZZ = False

# Used to debug completion
econsole = Console(stderr=True)
console = Console()
TinyDB.default_table_name = "devices"


CacheTable = Literal["dev", "inv", "sub", "site", "group", "template", "label", "license", "client", "log", "event", "hook_config", "hook_data", "mpsk_network", "mpsk", "portal", "cert"]


def ensure_config(func):
    """Prevents exception during completion when config missing or invalid."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not config.valid:
            econsole.print(":warning:  Invalid or missing config", end="")
            return []
        return func(*args, **kwargs)

    return wrapper


class CentralObject(MutableMapping):
    _doc_id = None

    def __init__(
        self,
        db: Literal["dev", "inv", "site", "template", "group", "label", "mpsk_network", "mpsk", "portal", "cert", "sub"],
        data: Document | dict[str, Any] | list[Document | dict[str, Any]],
    ):
        self.is_dev, self.is_template, self.is_group, self.is_site, self.is_label, self.is_mpsk, self.is_mpsk_network, self.is_portal, self.is_cert, self.is_sub = False, False, False, False, False, False, False, False, False, False
        data: dict | list[dict] = None if not data else data
        setattr(self, f"is_{db}", True)
        self.cache = db
        self.doc_id = None if not hasattr(data, "doc_id") else data.doc_id

        if isinstance(data, list):
            if len(data) > 1:
                raise CentralCliException(f"CentralObject expects a single item. Got list of {len(data)}")
            elif data:
                data = data[0]

        self.data = data

        # When building Central Object from Inventory this is necessary
        # TODO maybe pydantic model
        if data:
            if self.is_dev:
                self.name = self.data["name"] = self.data.get("name", self.data["serial"])
                self.status = self.data["status"] = self.data.get("status")
                self.ip = self.data["ip"] = self.data.get("ip")
                self.site = self.data["site"] = self.data.get("site")
                self.group = self.data["group"] = self.data.get("group")
                self.swack_id = self.data["swack_id"] = self.data.get("swack_id")
                self.serial: str = self.data.get("serial")

    def __rich__(self):
        return self.summary_text

    def __bool__(self):
        return bool(self.data)

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.cache}|{self.get('name', bool(self))}) object at {hex(id(self))}>"

    def __str__(self):
        if isinstance(self.data, dict):
            return "\n".join([f"  {k}: {v}" for k, v in self.data.items()])

        return str(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def keys(self) -> KeysView:
        return self.data.keys()

    def get(self, item: str, default = None):
        return self.data.get(item, default)

    # def __getattr__(self, name: str) -> Any:
    #     # import sys
    #     # print("CentralObject __getattr__", name, file=sys.stderr)
    #     if name == "data":
    #         return self.data

    #     if hasattr(self, "data") and self.data:
    #         if name in self.data:
    #             return self.data[name]

    #     if hasattr(self, "data") and hasattr(self.data, name):
    #         return getattr(self.data, name)

    #     raise AttributeError(f"'{self.__module__}.{type(self).__name__}' object has no attribute '{name}'")

    def __fields__(self) -> List[str]:
        return [k for k in self.__dir__() if not k.startswith("_") and not callable(k)]

    @property
    def generic_type(self):
        if "type" in self.data:
            return "switch" if self.data["type"].lower() in ["cx", "sw"] else self.data["type"].lower()

    @property
    def is_aos10(self) -> bool:
        if self.data.get("type", "") == "ap" and self.data.get("version", "").startswith("10"):
            return True
        else:
            return False

    def _get_help_text_parts(self):
        parts = []
        if self.cache == "site":
            parts = [
                "Site",
                *[a for a in [self.city, self.state, self.zip] if a]
            ]
        elif self.cache == "template":
            parts = [
                self.device_type,
                self.model,
                f"g:{self.group}",
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


    @property  # TODO # DEPRECATED Each object the inherits from CentralObject should have it's own summary_text property
    def summary_text(self):
        return str(self)



class CacheInvDevice(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('inv', data)
        self.id: str = data.get("id")  # glp only
        self.serial: str = data["serial"]
        self.mac: str = data["mac"]
        self.type: str = data["type"]
        self.model: str = data["model"]
        self.sku: str = data["sku"]
        self.services: str | None = data["services"]
        self.subscription_key: str = data.get("subscription_key")
        self.subscription_expires: int | float = data.get("subscription_expires")
        self.assigned: bool = data.get("assigned")  # glp only
        self.archived: bool = data.get("archived")  # glp only

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.serial is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.serial == self.serial)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __eq__(self, value: CacheInvDevice | str):
        if hasattr(value, "serial"):
            return value.serial == self.serial
        if utils.is_resource_id(value):
            return value == self.id
        return value == self.serial

    def __hash__(self):
        return hash(self.serial)

    def __rich__(self) -> str:
        return f'[bright_green]Inventory Device[/]:[bright_green]{self.serial}[/]|[cyan]{self.mac}[/]'

    @property
    def rich_help_text(self) -> str:
        return self.summary_text

    @property
    def summary_text(self) -> str:
        id_str = None if not self.id else f"[dim]glp id: {self.id}[/dim]"
        parts = [p for p in [self.serial, self.mac, self.type, self.sku, id_str] if p]
        return "[reset]" + "|".join(
            [
                f"{'[cyan]' if idx in list(range(0, len(parts), 2)) else '[turquoise4]'}{p}[/]" for idx, p in enumerate(parts)
            ]
        )


class CacheDevice(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('dev', data)
        self.name: str = data["name"]
        self.status: Literal["Up", "Down"] | None = data["status"]
        self.type: constants.DeviceTypes = data["type"]
        self.model: str = data["model"]
        self.ip: str | None = data["ip"]
        self.mac: str = data["mac"]
        self.serial: str = data["serial"]
        self.group: str = data["group"]
        self.site: str = data["site"]
        self.version: str = data["version"]
        self.swack_id: str | None = data["swack_id"]
        self.switch_role: str | None = data["switch_role"]

    def __eq__(self, value):
        if hasattr(value, "serial"):
            return value.serial == self.serial
        return value == self.serial

    def __hash__(self):
        return hash(self.serial)

    @property
    def is_aos10(self) -> bool:
        if self.type != "ap":
            return False
        return True if self.version.startswith("10.") else False

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.serial is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.serial == self.serial)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Device[/]:[cyan]{self.name}[/]|({utils.color(self.status, "green_yellow")})'

    @property
    def summary_text(self) -> str:
        def _get_color(idx: int, item: str):
            if item.lower() == "up":
                return "bright_green"
            if item.lower() == "down":
                return "red1"
            if idx % 2 == 0:
                return "bright_cyan"
            return "cyan"

        parts = [p for p in [self.name, self.status, self.serial, self.mac, self.type, self.model] if p]
        return "[reset]" + "|".join(
            [
                f"[{_get_color(idx, p)}]{p}[/]" for idx, p in enumerate(parts)
            ]
        )

    def get_ts_session_id(self, exit_on_fail: bool = True) -> int | Response:
        resp = api.session.request(api.tshooting.get_ts_session_id, self.serial)
        if resp.ok and "session_id" in resp.output:
            return resp.output["session_id"]

        if resp.status == 404:
            log.warning(f"No session id found for {self.summary_text}", caption=True)
            _ret = 0
        else:
            log.error(f"Attempt to determine session_id for {self.summary_text} failed.", caption=True)
            _ret = resp

        if not exit_on_fail:
            return _ret

        render.display_results(resp, exit_on_fail=True)

    def get_completion(self, incomplete: str, args: list[str] = None) -> tuple[str, str]:
        args = args or []
        idens = [self.name, self.serial, self.mac, self.ip]
        if any([i in args for i in idens]):
            return
        if self.name.replace("_", "-").lower().startswith(incomplete.replace("_", "-").lower()):
            return self.name, self.help_text
        if self.serial.lower().startswith(incomplete.lower()):
            return self.serial, self.help_text
        if self.mac.strip(":.-").lower().startswith(incomplete.strip(":.-").lower()):
            return self.mac, self.help_text
        if self.ip.startswith(incomplete):
            return self.ip, self.help_text
        return self.name, self.help_text  # pragma: no cover  Fall through / catch all


class CacheInvMonDevice(CentralObject):
    def __init__(self, inventory: CacheInvDevice, monitoring: CacheDevice = None):
        if inventory and monitoring and inventory.serial != monitoring.serial:
            raise ValueError(f"Device serial from inventory data ({inventory.serial}) does not match device serial ({monitoring.serial}) from monitoring data.  Data for 2 diffferent devices seems to have been provided")  # pragma: no cover

        self.inv = inventory
        self.mon = monitoring
        mon_data = {} if not monitoring else monitoring.data  # device can be in inventory but not monitoring db
        data = {**self.inv.data, **mon_data}

        super().__init__('dev', data=data)
        #inventory
        self.id: str = inventory.data.get("id")  # glp only
        self.serial: str = inventory.data["serial"]
        self.mac: str = inventory.data["mac"]
        self.type: str = inventory.data["type"]
        self.model: str = inventory.data["model"]
        self.sku: str = inventory.data["sku"]
        self.services: str | None = inventory.data["services"]
        self.subscription_key: str = inventory.data.get("subscription_key")
        self.subscription_expires: int | float = inventory.data.get("subscription_expires")
        self._assigned: bool = inventory.data.get("assigned")  # glp only
        self.archived: bool = inventory.data.get("archived")  # glp only
        # monitoring
        self.name: str = None if monitoring is None else monitoring.data["name"]
        self.status: Literal["Up", "Down"] | None = None if monitoring is None else monitoring.data["status"]
        self.type: constants.DeviceTypes = None if monitoring is None else monitoring.data["type"]
        if monitoring is not None:  # prefer the more simplified model provided by monitoring API so allow it to overwrite model provided by inventory API (679 vs AP-679-US)
            self.model: str = monitoring.data["model"]
        self.ip: str | None = None if monitoring is None else monitoring.data["ip"]
        self.mac: str = self.mac or None if monitoring is None else monitoring.data["mac"]
        self.serial: str = self.serial or None if monitoring is None else monitoring.data["serial"]
        self.group: str = None if monitoring is None else monitoring.data["group"]
        self.site: str = None if monitoring is None else monitoring.data["site"]
        self.version: str = None if monitoring is None else monitoring.data["version"]
        self.swack_id: str | None = None if monitoring is None else monitoring.data["swack_id"]
        self.switch_role: str | None = None if monitoring is None else monitoring.data["switch_role"]

    def __fields__(self) -> List[str]:
        return [k for k in self.__dir__() if not k.startswith("_") and not callable(k)]

    def __eq__(self, value: CacheInvMonDevice | str):
        if hasattr(value, "serial"):
            return value.serial == self.serial
        if utils.is_resource_id(value):
            return value == self.id
        return value == self.serial

    def __hash__(self):
        return hash(self.serial)

    def __rich__(self) -> str:
        return f'[bright_green]{self.type}[/]:[bright_green]{self.serial}[/]|[cyan]{self.mac}[/]'

    @property
    def assigned(self) -> bool:
        return bool(self._assigned)

    def get_help_text_parts(self) -> Generator[str, None, None]:
        _status = render.get_pretty_status(self.status)
        mon_parts = [p for p in [self.name, self.type, _status, self.serial, self.mac, self.ip, self.model] if p]
        inv_parts = [] if not self.sku else [self.sku]
        parts = [*mon_parts, *inv_parts]

        for idx, part in enumerate(parts):
            if "[/" in part:
                yield part
            elif idx % 2 == 0:
                yield f"[cyan]{part}[/]"
            else:
                yield f"[turquoise4]{part}[/]"

    @property
    def rich_help_text(self) -> str:
        return "|".join(self.get_help_text_parts())

    @property
    def summary_text(self) -> str:
        id_str = None if not self.id else f"[dim]glp id: {self.id}[/dim]"
        return f"{self.rich_help_text}{'' if not id_str else f'|{id_str}'}"

# TODO there is some inconsistency as this takes a dict, CacheCert and likely others need the dict unpacked
class CacheGroup(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('group', data)
        self.name: str = data["name"]
        self.allowed_types: List[constants.DeviceTypes] = data["allowed_types"]
        self.gw_role: constants.BranchGwRoleTypes = data["gw_role"]
        self.aos10: bool = data["aos10"]
        self.microbranch: bool = data["microbranch"]
        self.wlan_tg: bool = data["wlan_tg"]
        self.wired_tg: bool = data["wired_tg"]
        self.monitor_only_sw: bool = data["monitor_only_sw"]
        self.monitor_only_cx: bool = data["monitor_only_cx"]
        self.cnx: bool = data.get("cnx")

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.name is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.name == self.name)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Group[/]:[cyan]{self.name}[/]|({utils.color(self.allowed_types, "green_yellow")})'

    def get_help_text_parts(self) -> Generator[str, None, None]:
        _allowed_types_str = f"[magenta]allowed types[/]: {utils.color(self.allowed_types)}"
        _mon_only = [f"[magenta]{_type}[/]: \u2705" for _type, _mon_only in zip(["sw", "cx"], [self.monitor_only_sw, self.monitor_only_cx]) if _mon_only]
        _template_group = [f"[magenta]{_type}[/]: \u2705" for _type, _tg in zip(["wired", "wlan"], [self.wired_tg, self.wlan_tg]) if _tg]
        _other = []
        if "ap" in self.allowed_types:
            _other += ["AOS10" if self.aos10 else "AOS8"]
        if "gw" in self.allowed_types or "sdwan" in self.allowed_types:
            _other += [f"[magenta]GW Role[/]: {self.gw_role}"]
        if self.cnx:
            _other += ["[magenta]New Central Managed[/]: \u2705"]


        parts = [p for p in [self.name, _allowed_types_str, *_mon_only, *_template_group, *_other] if p]

        for idx, part in enumerate(parts):
            if "[/" in part:
                yield part
            elif idx % 2 == 0:
                yield f"[cyan]{part}[/]"
            else:
                yield f"[turquoise4]{part}[/]"

    @cached_property
    def rich_help_text(self) -> str:
        return "|".join(self.get_help_text_parts())

    @property
    def summary_text(self) -> str:
        return self.rich_help_text

class CacheSite(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | CacheSiteDict) -> None:
        self.data = data
        super().__init__('site', data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.address: Optional[str] = data.get("address")
        self.city: Optional[str] = data.get("city")
        self.state: Optional[str] = data.get("state")
        self.zip: Optional[str] = data.get("zip", data.get("zipcode"))
        self.country: Optional[str] = data.get("country")
        self.lon: Optional[str] = data.get("lon", data.get("longitude"))
        self.lat: Optional[str] = data.get("lat", data.get("latitude"))
        self.devices: int = data.get("devices")

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.name is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.name == self.name)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id


    def __rich__(self) -> str:
        return self.summary_text

    @property
    def summary_text(self):
        parts = [a for a in [self.name, self.city, self.state, self.zip] if a]
        parts = parts if len(parts) > 1 else [*parts, self.lat, self.lon]
        return "[reset]" + "|".join(
            [
                f"{'[cyan]' if idx % 2 == 0 else '[bright_green]'}{p}[/]" for idx, p in enumerate(parts)
            ]
        )


class CacheLabel(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('label', data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.devices: int = data.get("devices", data.get("associated_device_count", 0))

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int | None:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.name is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.name == self.name)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Label[/]:[bright_green]{self.name}[/]|[cyan]{self.id}[/]'

    def get_completion(self, pfx: str = "'") -> tuple[str, str]:
        quoted = f"'{self.name}'" if pfx == "'" else f'"{self.name}"'
        return (self.name if " " not in self.name else quoted, self.help_text)


class CachePortal(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('portal', data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.url: URL = URL(data["url"])
        self.auth_type: str = data["auth_type"]
        self.auth_types: PortalAuthTypes = self.get_auth_types(data["auth_type"])
        self.is_aruba_cert: bool = data["is_aruba_cert"]
        self.is_default: bool = data["is_default"]
        self.is_shared: bool = data["is_shared"]
        self.reg_by_email: bool = data["reg_by_email"]
        self.reg_by_phone: bool = data["reg_by_phone"]


    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @staticmethod
    def get_auth_types(auth_types: str) -> PortalAuthTypes:
        short_auth_types = {
            "Username/Password": "user/pass",
            "Self-Registration": "self-reg",
            "Anonymous": "anon",
        }
        return [short_auth_types.get(auth_type, auth_type) for auth_type in auth_types.split()]

    @property
    def doc_id(self) -> int | None:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.id is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.id == self.id)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Portal Profile[/]:[bright_green]{self.name}[/]|[cyan]{self.id}[/]'

    @property
    def help_text(self):
        return render.rich_capture(self.__rich__())


class CacheGuest(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('guest', data)
        self.portal_id: str = data["portal_id"]
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.email: str = data["email"]
        self.phone: str = data["phone"]
        self.company: str = data["company"]
        self.enabled: bool = data["enabled"]
        self.status: str = data["status"]
        self.created: int = data["created"]
        self.expires: int = data["expires"]


    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int | None:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.id is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.id == self.id)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Guest[/]:[bright_green]{self.name}[/]|[cyan]{self.id}[/]| portal id:[cyan]{self.portal_id}[/]'

    @property
    def help_text(self):
        return render.rich_capture(self.__rich__())


class CacheTemplate(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('template', data)
        self.name: str = data["name"]
        self.device_type: constants.DeviceTypes = data["device_type"]
        self.group: str = data["group"]
        self.model: str = data["model"]  # model as in sku here =
        self.name: str = data["name"]
        self.template_hash: str = data["template_hash"]
        self.version: str = data["version"]

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int | None:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.name is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.name == self.name)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Label[/]:[bright_green]{self.name}[/]|[cyan]{self.id}[/]'


ClientType = Literal["wired", "wireless"]

class CacheClient(CentralObject):
    db: Table | None = None
    cache: Cache | None = None

    # mac, name, ip, type, network_port, connected_serial, connected_name, site, group, last_connected
    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('client', data)
        self.name: str = data["name"]
        self.ip: str = data["ip"]
        self.mac: str = data["mac"]
        self.type: ClientType = data["type"]
        self.network_port: str = data["network_port"]
        self.connected_serial: str = data["connected_serial"]
        self.connected_name: str = data["connected_name"]
        self.site: str = data["site"]
        self.group: str = data["group"]
        self.last_connected: int | float = data.get("last_connected")

    @classmethod
    def set_db(cls, db: Table, cache: Cache = None):
        cls.db: Table = db
        cls.cache: Cache = cache

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.name is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.name == self.name)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def get_group(self) -> CacheGroup:
        return None if self.cache is None else self.cache.get_group_identifier(self.group)

    def get_site(self) -> CacheSite:
        return None if self.cache is None else self.cache.get_site_identifier(self.site)

    def __rich__(self) -> str:
        return f'[bright_green]Client[/]:[cyan]{self.name}[/]|({utils.color([self.type, self.ip, self.mac, self.connected_name],  "green_yellow", sep="|")}|s:[green_yellow]{self.site})[/]'

    @property
    def help_text(self) -> str:
        return render.rich_capture(
            f"[bright_green]{self.name}[/]|[cyan]{self.mac}[/]|[bright_green]{self.ip}[/]|[cyan]{f's:{self.site}' if self.site else f'g:{self.group}'}[/]|[dark_olive_green2]{self.connected_name}[/]"
        )

    @property
    def summary_text(self) -> str:
        return self.__rich__()


class CacheMpskNetwork(CentralObject):
    db: Table | None = None
    cache: Cache | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('mpsk_network', data)
        self.name: str = data["name"]
        self.id: int = data["id"]

    @classmethod
    def set_db(cls, db: Table, cache: Cache = None):
        cls.db: Table = db
        cls.cache: Cache = cache

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.id is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.id == self.id)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]MPSK Network[/]: [cyan]{self.name}[/]|[green_yellow]{self.id}[/]'

    @property
    def rich_help_text(self) -> str:
        return self.__rich__()

    @property
    def help_text(self) -> str:
        return "|".join(
            [
                typer.style(self.name, fg="green"),
                typer.style(self.id, fg="cyan"),
            ]
        )



class CacheMpsk(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('mpsk', data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.role: str = data["role"]

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        if self.db is not None and self.id is not None:
            Q = Query()
            match: List[Document] = self.db.search(Q.id == self.id)
            if match and len(match) == 1:
                self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]MPSK[/]:[cyan]{self.name}[/]|[green_yellow]{self.id})[/]'


class CacheCert(CentralObject):  #, Text):
    db: Table | None = None

    def __init__(self, name: str, type: CertType, expired: bool, expiration: int | float | DateTime | str, md5_checksum: str, **kwargs):
        self.name = name
        self.type = type.upper()
        self.expired = expired
        self._expiration = expiration
        self.md5_checksum = md5_checksum

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} (Certificate|{self.name}|{'OK' if not self.expired else 'EXPIRED'}) object at {hex(id(self))}>"

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        Q = Query()
        match: List[Document] = self.db.search(Q.md5_checksum == self.md5_checksum)
        if match and len(match) == 1:
            self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    @property
    def text(self) -> Text:
        return Text.from_markup(
            f'Certificate: [bright_green]{self.name}[/]|[magenta]expired[/]: {"[bright_red]" if self.expired is True else "[bright_green]"}{self.expired}[/]|'
            f'[magenta]expiration[/]: [cyan]{"" if self.expiration is None else DateTime(self.expiration, "date-string")}[/]|[magenta]md5[/]: [cyan]{self.md5_checksum}[/]'
        )

    def ok(self) -> bool:
        return not self.expired

    @property
    def expiration(self) -> DateTime:
        return self._expiration

    @expiration.setter
    def expiration(self, expiration: int | float | DateTime | str):
        if isinstance(expiration, DateTime):
            self._expiration = expiration
        if isinstance(expiration, str):
            self._expiration = DateTime(pendulum.from_format(expiration.rstrip("Z"), "YYYYMMDDHHmmss").timestamp(), "date-string")

        self._expiration = DateTime(expiration, "date-string")

    def __str__(self) -> str:
        return self.text.plain

    def __rich__(self) -> str:
        return self.text.markup

    @property
    def summary_text(self) -> str:
        return self.text.markup

    @property
    def help_text(self):
        return render.rich_capture(self.text.markup)


class SubscriptionTier(str, Enum):
    ADVANCED = "advanced"
    FOUNDATION = "foundation"
    OTHER = "other"


class CacheSub(CentralObject, Text):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        super().__init__("sub", data)
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.type: str = data["type"].lower()
        self.key: str = data["key"]
        self.qty: int = data["qty"]
        self.available: int = data["available"]
        self.sku: str = data["sku"]
        self.start_date: int = data["start_date"]
        self.end_date: int = data["end_date"]
        self.started: bool = data["started"]
        self.expired: bool = data["expired"]
        self.valid: bool = data["valid"]
        self.expire_string: DateTime = DateTime(self.end_date, format="date-string")

    @classmethod
    def set_db(cls, db: Table):
        cls.db: Table = db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        Q = Query()
        match: List[Document] = self.db.search(Q.id == self.id)
        if match and len(match) == 1:
            self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.cache}|{self.name}|{self.available}|{render.unstyle(self.status)}) object at {hex(id(self))}>"

    def __eq__(self, value: CacheSub | str):
        if hasattr(value, "id"):
            return value.id == self.id
        return value == self.id

    def __hash__(self):
        return hash(self.id)

    @property
    def api_name(self) -> str:
        return self.name.replace("-", "_")

    @property
    def tier(self) -> SubscriptionTier:
        if self.name.startswith("foudation"):
            return SubscriptionTier.FOUNDATION
        if self.name.startswith("advance"):
            return SubscriptionTier.ADVANCED
        return SubscriptionTier.OTHER

    @property
    def text(self) -> Text:
        _expired_str = f"[red1]EXPIRED[/] as of [cyan]{self.expire_string}[/]" if self.expired else f"expires {self.expire_string.expiration}"
        glp_str = "" if not config.debug else f"|[dim]glp id: {self.id}[/dim]"
        key_str = "" if not self.key else f"|[dim cadet_blue]{self.key}[/dim cadet_blue]"
        return Text.from_markup(
            f'[bright_green]{self.name}[/]{glp_str}{key_str}|{_expired_str}|[magenta]Qty Available[/][dim]:[/dim] [cyan]{self.available}[/cyan]'
        )

    @property
    def status(self) -> str:
        if self.valid:
            return "[bright_green]OK[/]"
        if self.expired:
            return "[red1]EXPIRED[/]"
        if not self.available:
            return f"[red1]Subscriptions exausted[/]: [bright_red]{self.available}[/] remaining of [cyan]{self.qty}[/] available subs."
        if not self.started:
            return f"[dark_orange3]Subscription term starts in the future[/] {DateTime(self.start_date, format='date-string')}[/]"
        return f"ERROR CATCH ALL {self.valid = }"

    @property
    def ok(self) -> bool:
        return self.valid

    def __str__(self) -> str:
        return self.text.plain

    def __rich__(self) -> str:
        return self.text.markup

    @property
    def summary_text(self) -> str:
        return self.text.markup

    @property
    def help_text(self):
        return render.rich_capture(self.text.markup)


class CacheBuilding(CentralObject, Text):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.campus_id: str = data["campus_id"]
        self.lat: int = data["lat"]
        self.lon: int = data["lon"]

    @classmethod
    def set_db(cls, db: Table, building_db: Table = None):
        cls.db: Table = db
        if building_db:
            cls.building_db = building_db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        Q = Query()
        match: List[Document] = self.db.search(Q.id == self.id)
        if match and len(match) == 1:
            self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} (Building|{self.name}) object at {hex(id(self))}>"

    def __eq__(self, value: CacheBuilding | str):
        if hasattr(value, "id"):
            return value.id == self.id
        return value == self.id

    def __hash__(self):
        return hash(self.id)

    @property
    def text(self) -> Text:
        return Text.from_markup(
            f'Building [bright_green]{self.name}[/]'
        )

    def __str__(self) -> str:
        return self.text.plain

    def __rich__(self) -> str:
        return self.text.markup

    @property
    def summary_text(self) -> str:
        return self.text.markup

    @property
    def help_text(self):
        return render.rich_capture(self.text.markup)


class CacheFloorPlanAP(Text):
    db: Table | None = None
    building_db: Table | None = None
    _building_object: CacheBuilding = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.serial: str = data["serial"]
        self.mac: int = data["mac"]
        self.floor_id: int = data["floor_id"]
        self.building_id: str = data["building_id"]
        self.level: int | float = data["level"]

    @classmethod
    def set_db(cls, db: Table, building_db: Table = None):
        cls.db: Table = db
        if building_db:
            cls.building_db = building_db

    @property
    def doc_id(self) -> int:
        if self._doc_id:
            return self._doc_id

        Q = Query()
        match: List[Document] = self.db.search(Q.id == self.id)
        if match and len(match) == 1:
            self._doc_id = match[0].doc_id

        return self._doc_id

    @doc_id.setter
    def doc_id(self, doc_id: int | None):
        self._doc_id = doc_id

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} (floor plan AP|{self.name}|{self.serial}) object at {hex(id(self))}>"

    def __eq__(self, value: CacheFloorPlanAP | str):
        if hasattr(value, "id"):
            return value.id == self.id
        return value == self.id or value == self.serial

    def __hash__(self):
        return hash(self.id)

    @property
    def text(self) -> Text:
        return Text.from_markup(
            f'[bright_green]{self.name}[/]|[cyan]{self.serial}[/]|[bright_green]{self.mac}[/]'
        )

    def __str__(self) -> str:
        return self.text.plain

    def __rich__(self) -> str:
        return self.text.markup

    @property
    def summary_text(self) -> str:
        return self.text.markup

    @property
    def help_text(self):
        return render.rich_capture(self.text.markup)

    @property
    def building(self) -> CacheBuilding | None:
        return self.get_building()

    @property
    def location(self) -> dict[str, str]:
        return {
            "id": self.id,
            "serial": self.serial,
            "building": self.building.name,
            "floor": self.level
        }

    def get_building(self) -> CacheBuilding | None:
        if self._building_object is None:
            query = Query()
            match = self.building_db.search(query.id == self.building_id)
            if not match:
                return
            self._building_object = CacheBuilding(match[0])
        return self._building_object


class CacheResponses:
    def __init__(
        self,
        dev: CombinedResponse = None,
        inv: Response = None,
        sub: Response = None,
        site: Response = None,
        template: Response = None,
        group: Response = None,
        label: Response = None,
        mpsk_network: Response = None,
        mpsk: Response = None,
        portal: Response = None,
        license: Response = None,
        client: Response = None,
        guest: Response = None,
        cert: Response = None,
        device_type: List[constants.LibAllDevTypes] | constants.LibAllDevTypes = None,
    ) -> None:
        self._dev = dev
        self._inv = inv
        self._sub = sub
        self._site = site
        self._template = template
        self._group = group
        self._label = label
        self._mpsk_network = mpsk_network
        self._mpsk = mpsk
        self._portal = portal
        self._license = license
        self._client = client
        self._guest = guest
        self._cert = cert
        self._device_type = utils.listify(device_type)

    def update_rl(self, resp: Response | CombinedResponse | None) -> Response | CombinedResponse | None:
        """Returns provided Response object with the RateLimit info from the most recent API call.
        """
        if resp is None:
            return

        _last_rl = sorted([r.rl for r in [self._dev, self._inv, self._site, self._template, self._group, self._label, self._mpsk_network, self._mpsk, self._portal, self._license, self._client, self._guest, self._cert] if r is not None])  # , key=lambda k: k.remain_day)
        if _last_rl:
            resp.rl = _last_rl[0]
        return resp

    @property
    def dev(self) -> CombinedResponse | None:
        return self.update_rl(self._dev)

    @dev.setter
    def dev(self, resp: CombinedResponse):
        self._dev = resp

    @property
    def inv(self) -> Response | None:
        return self.update_rl(self._inv)

    @inv.setter
    def inv(self, resp: Response):
        self._inv = resp

    @property
    def sub(self) -> Response | None:
        return self.update_rl(self._sub)

    @sub.setter
    def sub(self, resp: Response):
        self._sub = resp

    @property
    def site(self) -> Response | None:
        return self.update_rl(self._site)

    @site.setter
    def site(self, resp: Response):
        self._site = resp

    @property
    def template(self) -> Response | None:
        return self.update_rl(self._template)

    @template.setter
    def template(self, resp: Response):
        self._template = resp

    @property
    def group(self) -> Response | None:
        return self.update_rl(self._group)

    @group.setter
    def group(self, resp: Response):
        self._group = resp

    @property
    def label(self) -> Response | None:
        return self.update_rl(self._label)

    @label.setter
    def label(self, resp: Response):
        self._label = resp

    @property
    def mpsk_network(self) -> Response | None:
        return self.update_rl(self._mpsk_network)

    @mpsk_network.setter
    def mpsk_network(self, resp: Response):
        self._mpsk_network = resp

    @property
    def mpsk(self) -> Response | None:
        return self.update_rl(self._mpsk)

    @mpsk.setter
    def mpsk(self, resp: Response):
        self._mpsk = resp

    @property
    def portal(self) -> Response | None:
        return self.update_rl(self._portal)

    @portal.setter
    def portal(self, resp: Response):
        self._portal = resp

    @property
    def license(self) -> Response | None:
        return self.update_rl(self._license)

    @license.setter
    def license(self, resp: Response):
        self._license = resp

    @property
    def client(self) -> Response | None:
        return self.update_rl(self._client)

    @client.setter
    def client(self, resp: Response):
        self._client = resp

    @property
    def guest(self) -> Response | None:
        return self.update_rl(self._guest)

    @guest.setter
    def guest(self, resp: Response):
        self._guest = resp

    @property
    def cert(self) -> Response | None:
        return self.update_rl(self._cert)

    @cert.setter
    def cert(self, resp: Response):
        self._cert = resp

    @property
    def device_type(self) -> List[constants.LibAllDevTypes] | None:
        return self._device_type

    @device_type.setter
    def device_type(self, device_type: constants.LibAllDevTypes | List[constants.LibAllDevTypes]):
        self._device_type = utils.listify(device_type)

    def clear(self) -> None:
        """Clears response cache.  Primarily used for pytest runs."""
        self._dev = None
        self._inv = None
        self._sub = None
        self._site = None
        self._template = None
        self._group = None
        self._label = None
        self._mpsk_network = None
        self._mpsk = None
        self._portal = None
        self._license = None
        self._client = None
        self._guest = None
        self._cert = None
        self._device_type = None

def _handle_multi_word_incomplete(incomplete: str) -> tuple[str, str]:
    if incomplete.startswith("'"):
        pfx = "'"
    elif incomplete.startswith('"'):
        pfx = '"'
    else:
        pfx = ""
    if pfx:
        incomplete = incomplete.lstrip(pfx)

    return incomplete, pfx


# TODO Verify, but the set_config class method should be able to be removed as ordering
# changed in __init__
class Cache:
    config: Config = None

    @classmethod
    def set_config(cls, config: Config) -> None:
        cls.config = config

    def __init__(
        self,
        config: Config = None,
    ) -> None:
        """Central-API-CLI Cache object
        """
        self.updated: list = []  # TODO # DEPRECATED change from list of methods to something easier
        self.config = config
        self.responses = CacheResponses()
        # self.get_label_identifier: CacheLabel | list[CacheLabel] = partial(self.get_name_id_identifier, "label")
        # self.get_sub_identifier: CacheSub | list[CacheSub] = partial(self.get_name_id_identifier, "sub")
        # self.get_portal_identifier: CachePortal | list[CachePortal] = partial(self.get_name_id_identifier, "portal")
        if config.valid and config.cache_dir.exists():
            self.DevDB: TinyDB = TinyDB(config.cache_file)
            self.InvDB: Table = self.DevDB.table("inventory")
            self.SubDB: Table = self.DevDB.table("subscriptions")
            self.SiteDB: Table = self.DevDB.table("sites")
            self.GroupDB: Table = self.DevDB.table("groups")
            self.TemplateDB: Table = self.DevDB.table("templates")
            self.LabelDB: Table = self.DevDB.table("labels")
            self.LicenseDB: Table = self.DevDB.table("licenses")
            self.ClientDB: Table = self.DevDB.table("clients")  # Updated only when show clients is ran
            self.LogDB: Table = self.DevDB.table("logs")  # Only updated when show audit logs is ran.  provide simple index to get details for logs vs the actual log id in form 'audit_trail_2021_2,...'
            self.EventDB: Table = self.DevDB.table("events") # Only updated when show logs is ran
            self.HookConfigDB: Table = self.DevDB.table("wh_config")
            self.HookDataDB: Table = self.DevDB.table("wh_data")
            self.MpskNetDB: Table = self.DevDB.table("mpsk_networks")  # Only updated when show mpsk networks is ran or as needed when show named-mpsk <SSID> is ran
            self.MpskDB: Table = self.DevDB.table("mpsk")
            self.PortalDB: Table = self.DevDB.table("portal")  # Only updated when show portals is ran or as needed
            self.GuestDB: Table = self.DevDB.table("guest")  # Only updated when show guests is ran or as needed
            self.CertDB: Table = self.DevDB.table("certs")  # Only updated when show certs is ran or as needed
            self.FloorPlanAPDB: Table = self.DevDB.table("floor_plan_aps")
            self.BuildingDB: Table = self.DevDB.table("floor_plan_buildings")
            if config.glp.ok:
                self.SubDB: Table = self.DevDB.table("subscriptions")
            self._tables: List[Table] = [self.DevDB, self.InvDB, self.SiteDB, self.GroupDB, self.TemplateDB, self.LabelDB, self.LicenseDB, self.ClientDB]
            self.Q: Query = Query()


    def __call__(self, refresh=False) -> None:
        if refresh:
            self.check_fresh(refresh)

    def __iter__(self) -> Iterator[Tuple[str, List[Document]]]:
        yield from self.all_tables

    def __len__(self) -> int:
        return len(list(self.DevDB.tables()))

    def is_central_license(self, license: str) -> bool:
        if not any(
            [
                license.startswith("enhanced_"),
                license.startswith("standard_"),
                license.endswith("hciaas"),
                license.endswith("baas"),
                "_vm_" in license,
                license.endswith("zerto"),
                license in {"sta", "stb", "stc", "bridge", "st", "pr", "es", "et", "special"},
                license.startswith("private_cloud"),
                "k8s" in license,
                "proliant" in license,
                license.endswith("_storage"),
                license.endswith("edgeline"),
                license.endswith("hci_manager"),
                license.endswith("_sfm"),
                "alletra" in license,
                "_sensor_" in license
            ]
        ):
            return True
        else:
            return False

    @property
    def size(self) -> str:
        def human_size(size_in_bytes: int | float, suffix: str = "B") -> str:
            for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
                if abs(size_in_bytes) < 1024.0:
                    return f"{size_in_bytes:3.1f}{unit}{suffix}"
                size_in_bytes /= 1024.0
            return f"{size_in_bytes:.1f}Y{suffix}"

        if self.config is not None:
            db_stats = self.config.cache_file.stat()
            return human_size(db_stats.st_size)

        return "0"

    @property
    def all_tables(self) -> Iterator[Table]:
        for table in self.DevDB.tables():
            yield self.DevDB.table(table)

    @property
    def key_tables(self) -> Iterator[Table]:
        for table in self._tables:
            yield table

    @property
    def devices(self) -> list[Document]:
        return self.DevDB.all()

    @property
    def inv_device_types(self) -> set[str]:
        return set() if not self.InvDB else set([d["type"] for d in self.InvDB.all()])

    @property
    def mon_device_types(self) -> set[str]:
        return set([d["type"] for d in self.DevDB.all()])

    @property
    def devices_by_serial(self) -> Dict[str, Document]:
        return {d["serial"]: d for d in self.devices}

    @property
    def inventory(self) -> list:
        return self.InvDB.all()

    # TODO return dict of Cache Objects need to check impact, but likely easier to work with
    @property
    def inventory_by_serial(self) -> Dict[str, Document]:
        return {d["serial"]: d for d in self.inventory}

    @property
    def invdev_by_id(self) -> Dict[str, CacheInvMonDevice]:
        return {
            d["id"]: CacheInvMonDevice(
                inventory=CacheInvDevice(d),
                monitoring=None if d["serial"] not in self.devices_by_serial else CacheDevice(self.devices_by_serial[d["serial"]])
            ) for d in self.inventory
        }

    @property
    def subscriptions(self) -> list[CacheSub]:
        return [CacheSub(sub) for sub in sorted(self.SubDB.all(), key=lambda s: (s["expired"], s["name"]))]

    @property
    def subscriptions_by_id(self) -> Dict[str, Document]:
        return {s["id"]: s for s in self.subscriptions}

    @property
    def sites(self) -> list:
        return self.SiteDB.all()

    @property
    def sites_by_id(self) -> list:
        return {s["id"]: s for s in self.sites}

    @property
    def sites_by_name(self) -> dict[str, CacheSite]:
        return {s["name"]: CacheSite(s) for s in self.sites}

    @property
    def groups(self) -> list:
        return self.GroupDB.all()

    @property
    def groups_by_name(self) -> dict[str, CacheGroup]:
        return {g["name"]: CacheGroup(g) for g in self.groups}

    @property
    def group_names(self) -> list:
        return [g["name"] for g in self.GroupDB.all()]

    @property
    def ap_groups(self) -> list:
        return [CacheGroup(g) for g in self.groups if "ap" in g["allowed_types"] and g["name"] != "default"]

    @property
    def labels(self) -> list:
        return self.LabelDB.all()

    @property
    def labels_by_name(self) -> dict[str: CacheLabel]:
        return {label["name"]: CacheLabel(label) for label in self.labels}

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
    def cache_clients_by_mac(self) -> Dict[str: Document]:
        """All Clients by MAC connected within the last 90 days

        This property is used by the cache to filter clients older than 90 days

        Returns:
            Dict[str,Document]: Client Dict keyed by MAC
            with any clients last connected > 90 days ago filtered out.
        """
        days = 90 if not self.config else self.config.cache_client_days
        return {
            c["mac"]: c
            for c in self.clients
            if c["last_connected"] is not None and not utils.older_than(c["last_connected"], days)
        }

    @property
    def clients_by_mac(self) -> Dict[str: Document]:
        return {c["mac"]: c for c in self.clients}

    @property
    def mpsk_networks(self) -> list:
        return self.MpskNetDB.all()

    @property
    def mpsk(self) -> list:
        return self.MpskDB.all()

    @property
    def mpsk_by_id(self) -> dict[str, CacheMpsk]:
        return {m["id"]: CacheMpsk(m) for m in self.mpsk}

    @property
    def portals(self) -> list:
        return self.PortalDB.all()

    @property
    def portals_by_id(self) -> Dict[str, Dict[str, str | bool]]:
        return {p["id"]: p for p in self.portals}

    @property
    def guests(self) -> list:
        return self.GuestDB.all()

    @property
    def guests_by_id(self) -> Dict[str, Dict[str, str | bool]]:
        return {p["id"]: p for p in self.guests}

    @property
    def certs(self) -> List[Document]:
        return self.CertDB.all()

    @property
    def certs_by_name(self) -> Dict[str, CacheCert]:
        return {c["name"]: CacheCert(**c) for c in self.certs}

    @property
    def certs_by_md5(self) -> Dict[str, Dict[str, str | bool | int]]:
        return {cert["md5_checksum"]: cert for cert in self.certs}

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
    def label_names(self) -> list:
        return [g["name"] for g in self.LabelDB.all()]

    @property
    def license_names(self) -> list:
        return sorted([lic["name"] for lic in self.LicenseDB.all()])

    @property
    def templates(self) -> list:
        return self.TemplateDB.all()

    @property
    def templates_by_name_group(self) -> list:
        return {
            f'{template["name"]}_{template["group"]}': template
            for template in self.TemplateDB.all()
        }

    @property
    def floor_plan_aps(self) -> list[Document]:
        return self.FloorPlanAPDB.all()

    @property
    def floor_plan_buildings(self) -> list[Document]:
        return self.BuildingDB.all()

    @property
    def floor_plan_aps_by_serial(self) -> dict[str, CacheFloorPlanAP]:
        return {ap["serial"]: CacheFloorPlanAP(ap) for ap in self.FloorPlanAPDB.all()}

    @property
    def hook_config(self) -> list:
        return self.HookConfigDB.all()

    @property
    def hook_data(self) -> list:
        return self.HookDataDB.all()

    @property
    def hook_active(self) -> list:
        return [h for h in self.HookDataDB.all() if h["state"].lower() == "open"]

    async def get_hooks_by_serial(self, serial):
        return self.HookDataDB.get(self.Q.device_id == serial)

    def fuzz_lookup(self, query_str: str, db: Table, field: str = "name", group: str = None, portal_id: str = None, dev_type: list[constants.LibAllDevTypes] = None) -> list[Document] | None:  # pragma: no cover  Requires tty
        if not render.console.is_terminal or not db.all():
            return

        def _conditions(item: Document, group: str = None, portal_id: str = None) -> bool:
            if not any([group, portal_id, dev_type]):
                return True
            if group:
                return item["group"] == group
            if portal_id:
                return item["portal_id"] == portal_id
            if dev_type:
                return item["type"] in dev_type

        fuzz_resp = process.extract(
            query_str, [item[field] for item in db.all() if _conditions(item, group=group, portal_id=portal_id)], limit=1
        )
        if fuzz_resp:
            fuzz_match, fuzz_confidence = fuzz_resp[0]
            if fuzz_confidence >= 70 and render.confirm(prompt=f"Did you mean [green3]{fuzz_match}[/]?", abort=False):
                return db.search(getattr(Query(), field) == fuzz_match)

    @staticmethod
    def verify_db_action(db: Table, *, expected: int, response: List[int | List[int]], remove: bool = False, elapsed: int | float = None) -> bool:
        """Evaluate TinyDB Cache results (search/add/update/delete).

        Verifies response from TinyDB lookup/update, logs and returns a bool indicating success/failure.

        Args:
            db (CacheTable): The TinyDB Table/Cache the update/lookup was peformed on.
            expected (int): The number of records that were expected.
            response (List[int  |  List[int]]): The update/lookup response from TinyDB
            remove (bool, optional): If the operation was a delete/remove
            elapsed (int | float, optional): Amount of time it took to update the cache.

        Returns:
            bool: Bool indicating if update was succesful.
        """
        resp_cnt = len(response)
        db_str = db.name.title()
        elapsed_msg = "" if not elapsed else f" Elapsed: {elapsed}"

        msg = f"remove {expected} records" if remove else f"add/update {expected} records"
        update_ok = True if expected == resp_cnt else False

        if update_ok:
            log.info(f'{db_str} cache update SUCCESS: {msg}{elapsed_msg}')
            return True
        else:  # pragma: no cover
            log.error(f'{db_str} cache update ERROR:  Attempt to {msg} appears to have failed.  Expecting {expected} doc_ids TinyDB returned {resp_cnt}', show=True, caption=True, log=True)
            log.error(f'{db_str} update response: {response}{elapsed_msg}')
            return False

    def get_devices_with_inventory(self, no_refresh: bool = False, inv_db: bool = None, dev_db: bool = None, device_type: constants.GenericDeviceTypes = None, status: constants.DeviceStatus = None,) -> List[Response] | Response:
        """Returns List of Response objects with data from Inventory and Monitoring

        Args:
            no_refresh (bool, optional): Used currently cached data, skip refresh of cache.
                Refresh will only occur if cache was not updated during this session.
                Setting no_refresh to True means it will not occur regardless.
                Defaults to False.
            inv_db (bool, optional): Update inventory cache. Defaults to None.
            dev_db (bool, optional): Update device (monitoring) cache. Defaults to None.
            device_type (Literal['ap', 'gw', 'switch'], optional): Filter devices by type:
                Valid Types: 'ap', 'gw', 'switch'.  'cx' and 'sw' also accepted, both will result in 'switch' which includes both types.
                Defalts to None (no Filter/All device types).
            status (Literal 'up', 'down', optional): Filter results by status.
                Inventory only devices (have never checked in, so lack status) are retained.
                Defaults to None.

        Returns:
            List[Response]: Response objects where output is list of dicts with
                            data from Inventory and Monitoring combined.
        """
        if not no_refresh:
            res = self.check_fresh(dev_db=dev_db or self.responses.dev is None, inv_db=inv_db or self.responses.inv is None, dev_type=device_type)
        else:
            res = [self.responses.dev or Response()]

        _inv_by_ser = self.inventory_by_serial if not self.responses.inv else {d["serial"]: d for d in self.responses.inv.output}
        if self.responses.dev:
            _dev_by_ser = {d["serial"]: d for d in self.responses.dev.output}  # Need to use the resp value not what was just stored in cache (self.devices_by_serial) as we don't store all fields
        else:
            _dev_by_ser = self.devices_by_serial  # TODO should be no case to ever hit this.

        if device_type:
            _dev_types = [device_type] if device_type != "switch" else ["cx", "sw", "mas"]
            _dev_by_ser = {serial: _dev_by_ser[serial] for serial in _dev_by_ser if _dev_by_ser[serial]["type"] in _dev_types}
            _inv_by_ser = {serial: _inv_by_ser[serial] for serial in _inv_by_ser if _inv_by_ser[serial]["type"] in _dev_types}


        if status:
            _dev_by_ser = {serial: _dev_by_ser[serial] for serial in _dev_by_ser if _dev_by_ser[serial]["status"] == status.capitalize()}

        _all_serials = set([*_inv_by_ser.keys(), *_dev_by_ser.keys()])
        combined = [
            {
                **_inv_by_ser.get(serial, {}),
                **_dev_by_ser.get(serial, {})
            } for serial in _all_serials
        ]

        # TODO this may be an issue if check_fresh has a failure, don't think it returns Response object
        # resp: Response = min([r for r in res if r is not None and r.rl.has_value], key=lambda x: x.rl)
        resp: Response = min([r for r in res if r is not None], key=lambda x: x.rl)
        resp.output = combined
        # Both are None if a partial error occured in show all.  To test change url in-flight so one of the 3 calls fails
        try:
            resp.raw = {**self.responses.dev.raw, self.responses.inv.url.path: self.responses.inv.raw}
        except AttributeError:
            if isinstance(resp, CombinedResponse):
                resp.raw = {**resp.raw, **{f.url.path: f.raw for f in resp.failed}}
            else:
                resp.raw = {"Error": "raw output not available due to partial failure."}
        return resp

    @staticmethod
    def workspace_completion(incomplete: str):
        for ws in config.defined_workspaces:
            if ws.lower().startswith(incomplete.lower()):
                yield ws, config.data["workspaces"][ws].get("cluster") or ""  # TODO help text to include friendly name for cluster i.e. ("WadeLab", "us-west4")

    @ensure_config
    def method_test_completion(self, incomplete: str, args: List[str] = []):
        methods = list(set(
            [d for svc in api.__dir__() if not svc.startswith("_") for d in getattr(api, svc).__dir__() if not d.startswith("_")]
        ))

        import importlib
        bpdir = Path(__file__).parent / "boilerplate"
        all_calls = [
            importlib.import_module(f"centralcli.{bpdir.name}.{f.stem}") for f in bpdir.iterdir()
            if not f.name.startswith("_") and f.suffix == ".py"
        ]
        client = Session(config.classic.base_url)
        for m in all_calls:
            methods += [
                d for d in m.AllCalls(client).__dir__()
                if not d.startswith("__")
            ]

        for m in sorted(methods):
            if m.startswith(incomplete):
                yield m

    @ensure_config
    def smg_kw_completion(self, ctx: typer.Context, incomplete: str, args: List[str] = []):
        kwds = ["group", "mac", "serial"]
        out = []

        if not args:  # HACK click 8.x work-around now pinned at click 7.2 until resolved
            args = [v for k, v in ctx.params.items() if v and k != "workspace"]  # TODO ensure k is last item when v = incomplete
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

    def null_completion(self, incomplete: str):
        incomplete = "NULL_COMPLETION"
        _ = incomplete
        for m in ["|", "<cr>"]:
            yield m

    @ensure_config
    def dev_completion(
        self,
        incomplete: str,
        args: List[str] = None
    ):
        dev_type = None
        if args:
            if "dev_type" in args and len(args) > 1:
                dev_type = args[args.index("dev_type") + 1]  # HACK we can't add parameters typer doesn't expect this allows us to call this from other funcs
            elif args[-1].lower() in ["gateways", "clients", "server"]:
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
            for m in sorted(match, key=lambda i: i.name):
                out += [m.get_completion(incomplete, args=args)]

        for m in out:
            yield m

    @ensure_config
    def dev_switch_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are switches (AOS-SW or CX)

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type="switch", completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    def _dev_switch_by_type_completion(
        self,
        incomplete: str,
        args: List[str] = [],
        dev_type: Literal["cx", "sw"] = "cx",
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are of specific switch type (cx by default)

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type=[dev_type], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_cx_completion(
            self,
            incomplete: str,
            args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        yield from self._dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="cx")

    @ensure_config
    def dev_sw_completion(
            self,
            incomplete: str,
            args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        yield from self._dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="sw")

    @ensure_config
    def dev_ap_gw_sw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are ap, gw, or AOS-SW

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        yield from self.dev_ap_gw_completion(ctx, incomplete, args=args)
        yield from self.dev_sw_completion(incomplete, args=args)

    @ensure_config
    def mpsk_network_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ):
        match = self.get_mpsk_network_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or ctx.params.values()  # HACK as args stopped working / seems to be passing args typer 0.10.0 / click 7.1.2
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if str(m.id).startswith(incomplete):
                    out += [tuple([m.id, m.name])]
                elif m.name not in args:
                    out += [tuple([m.name, m.id])]

        for m in out:
            yield m

    @ensure_config
    def portal_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ):
        match: list[CachePortal] = self.get_portal_identifier(
            incomplete,
            completion=True,
        )
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        out = []
        if match:
            # remove items that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if str(m.id).startswith(incomplete):
                    out += [tuple([m.id, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @overload
    def get_guest_identifier(
        self,
        query_str: str,
        completion: bool = True,
    ) -> list[CacheGuest]: ...

    @overload
    def get_guest_identifier(
        self,
        query_str: str,
        portal_id: str = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheGuest: ...

    def get_guest_identifier(
        self,
        query_str: str,
        portal_id: str = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheGuest | List[CacheGuest]:
        """Get guest info from Guest Cache"""
        retry = False if completion else retry
        if not query_str and completion:
            return [CacheGuest(g) for g in self.guests]

        match, all_match = None, None
        for _ in range(0, 2 if retry else 1):
            # exact
            match = self.GuestDB.search(
                (self.Q.name == query_str)
                | (self.Q.email == query_str)
                | (self.Q.phone == query_str)
                | (self.Q.id == query_str)
            )

            # case insensitive
            if not match:
                match = self.GuestDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                    | self.Q.email.test(lambda v: v and v.lower() == query_str.lower())
                    | self.Q.id.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive with -/_ swap
            if not match:
                if "_" in query_str:
                    match = self.GuestDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))
                elif "-" in query_str:
                    match = self.GuestDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))

            # startswith
            if not match:
                match = self.GuestDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.email.test(lambda v: v and v.lower().startswith(query_str.lower()))
                    | self.Q.id.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # test phone match if digits in query_str (all non digit characters stripped)
            if not match:
                _phone = "".join([d for d in query_str if d.isdigit()])
                if _phone:
                    self.Q.phone.test(lambda v: v and "".join([d for d in v if d.isdigit()]).startswith(_phone))

                    # phone with only last 10 digits (strip country code)
                    if not match:
                        match = self.GuestDB.search(
                            self.Q.phone.test(lambda v: v and "".join([d for d in v if d.isdigit()][::-1][0:10][::-1]).startswith("".join(_phone[::-1][0:10][::-1])))
                        )

            if match and portal_id:
                all_match: List[Document] = match.copy()
                match = [d for d in all_match if d.get("portal_id", "") == portal_id]

            if retry and not match and self.responses.guest is None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ and self.guests and not silent:
                    match = self.fuzz_lookup(query_str, db=self.GuestDB, portal_id=portal_id)
                if not match:
                    if not portal_id:
                        econsole.print(f"[red]:warning:[/]  Unable to gather guest from provided identifier {query_str}.  Use [cyan]cencli show guest <PORTAL>[/] to update cache.")
                        raise typer.Exit(1)
                    econsole.print(":arrows_clockwise: Updating guest Cache")
                    api.session.request(self.refresh_guest_db, portal_id=portal_id)
            if match:
                match = [CacheGuest(g) for g in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="guest",
                )

            return match[0]

        log.error(f"Unable to gather guest from provided identifier {query_str}", show=not silent, log=silent)
        if retry:
            if all_match:
                first_five = [f"[bright_green]{m['name']}[/]" for m in all_match[0:5]]
                all_match_msg = f"{', '.join(first_five)}{', ...' if len(all_match) > 5 else ''}"
                log.error(
                    f"The Following guests matched: {all_match_msg} [red]Excluded[/] as they are not associated with portal id [cyan]{portal_id}[/] group ",
                    show=True,
                )
            raise typer.Exit(1)

    def guest_completion(
        self,
        ctx: typer.Context,
        incomplete: str = "",
        args: List[str] = None,
    ):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match = self.get_guest_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        if match:
            # remove items that are already on the command line
            # match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if m.email and m.email.startswith(incomplete) and m.email not in args:
                    out += [tuple([m.email, m.help_text])]
                elif m.phone and m.phone.startswith(incomplete.lstrip("+")) and m.phone.lstrip("+") not in args:
                    out += [tuple([m.phone, m.help_text])]
                elif m.id.startswith(incomplete) and m.id not in args:
                    out += [tuple([m.id, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @overload
    def get_cert_identifier(
        self,
        query_str: str,
        completion: bool,
    ) -> list[CacheCert]: ...

    def get_cert_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheCert:
        """Get certificate info from Certificate Cache"""
        retry = False if completion else retry
        if not query_str and completion:
            return list(self.certs_by_name.values())

        match = None
        for _ in range(0, 2 if retry else 1):
            # exact
            match = self.CertDB.search(
                (self.Q.name == query_str)
                | (self.Q.md5_checksum == query_str)
            )

            # case insensitive
            if not match:
                match = self.CertDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                    | self.Q.md5.checksum.test(lambda v: v and v.lower() == query_str.lower())
                )

            # case insensitive with -/_ swap
            if not match:
                if "_" in query_str:
                    match = self.CertDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))
                elif "-" in query_str:
                    match = self.CertDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))

            # startswith - phone has all non digit characters stripped
            if not match:
                match = self.CertDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.md5_checksum.test(lambda v: v and v.lower().startswith(query_str.lower()))
                )

            if retry and not match and self.responses.cert is None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ and self.certs and not silent:  # pragma: no cover  requires tty
                    match = self.fuzz_lookup(query_str, self.CertDB)
                if not match:
                    econsole.print(":arrows_clockwise: Updating certificate Cache")
                    api.session.request(self.refresh_cert_db)
            if match:
                match = [CacheCert(**c) for c in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="certificate",
                )

            return match[0]

        log.error(f"[red]Unable to gather certificate[/] from provided identifier [cyan]{query_str}[/]", show=not silent, log=silent)
        if retry:
            raise typer.Exit(1)


    def cert_completion(
        self,
        ctx: typer.Context,
        incomplete: str = "",
        args: List[str] = None,
    ):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match = self.get_cert_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.md5_checksum.startswith(incomplete) and m.md5_checksum not in args:
                    out += [tuple([m.md5_checksum, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def sub_completion(
        self,
        ctx: typer.Context,
        incomplete: str = None,
        args: List[str] = None,
    ):
        incomplete = incomplete or ""
        match: list[CacheSub] = self.get_sub_identifier(
            incomplete,
            completion=True,
        )
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.key.startswith(incomplete) and m.key not in args:
                    out += [tuple([m.key, m.help_text])]
                elif m.id.startswith(incomplete) and m.id not in args:
                    out += [tuple([m.id, m.help_text])]
                elif m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def dev_kwarg_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for commands that allow a list of devices followed by group/site.

        i.e. cencli move dev1 dev2 dev3 site site_name group group_name

        Args:
            ctx (typer.Context): Provided automatically by typer
            incomplete (str): The incomplete word for autocompletion
            args (List[str], optional): The prev args passed into the command.

        Yields:
            Iterator[Tuple[str, str]]: Matching completion string, help text, or
                Returns None if config is invalid
        """
        if not args:  # pragma: no cover # HACK resolves click 8.x issue now pinned to 7.2 until fixed upstream
            args = [k for k, v in ctx.params.items() if v and k[:2] not in ["kw", "va"]]
            args += [v for k, v in ctx.params.items() if v and k[:2] in ["kw", "va"]]

        if args and args[-1].lower() == "group":
            yield from self.group_completion(incomplete, args)

        elif args and args[-1].lower() == "site":
            yield from self.site_completion(ctx, incomplete, args)

        elif args and args[-1].lower() == "ap":
            yield from self.dev_completion(incomplete, args)

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

            for m in out:
                yield m if isinstance(m, tuple) else (m, f"{ctx.info_name} ... {m}")

    @ensure_config
    def dev_ap_completion(
        self,
        # ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument where only APs are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match: List[CacheDevice] = self.get_dev_identifier(incomplete, dev_type=["ap"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    # TODO put client names with spaces in quotes
    # TODO does not appear to be used by any command
    @ensure_config
    def dev_client_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Completion for client output.

        Returns only devices that apply based on filter provided in command, defaults to clients
        on both APs and switches (wires/wireless), but returns applicable devices if "wireless" or
        "wired" filter is used.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Tuple with completion and help text, or
                Returns None if config is invalid
        """
        if ctx.params.get("wireless"):
            gen = self.dev_ap_completion
        elif ctx.params.get("wired"):
            gen = self.dev_switch_completion
        else:
            gen = self.dev_switch_ap_completion

        yield from gen(incomplete, args)

    @ensure_config
    def dev_switch_ap_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are either switch or AP

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI.

        Yields:
            Iterator[Tuple[str, str]]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        match: list[CacheDevice] = self.get_dev_identifier(incomplete, dev_type=["switch", "ap"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_ap_gw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Device completion that returns only ap and gw.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents device completion for cencli show config self/cencli
        if ctx.command_path == "cencli show config" and ctx.params.get("group_dev", "") in ["cencli", "self"]:
            return

        yield from self.dev_ap_completion(incomplete, args=args)
        yield from self.dev_gw_completion(incomplete, args=args)

    @ensure_config
    def dev_switch_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Device completion that returns only switches and gateways.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type=["switch", "gw"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def dev_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for device idens where only gateways are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match = self.get_dev_identifier(incomplete, dev_type="gw", completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @staticmethod
    def _cencli_self(ctx: typer.Context, incomplete: str, args: tuple[str]) -> tuple[list[tuple[str, str]], list[str]]:
        word = "self" if "self".startswith(incomplete) else "cencli"
        if args:
            if " ".join(args).lower() in ["show config", "update config"] and word.startswith(incomplete):
                return [(word, "show cencli configuration")], args
        elif ctx is not None:
            args = [a for a in ctx.params.values() if a is not None]
            if ctx.command_path in ["cencli show config", "cencli update config"] and ctx.params.get("group_dev") is None:  # typer not sending args fix
                if word.startswith(incomplete):
                    return [(word, "show cencli configuration")], args
        return [[], args]

    # FIXME not completing partial serial number is zsh get_dev_completion appears to return as expected
    # works in BASH and powershell
    def _group_dev_completion(
        self,
        incomplete: str,
        ctx: typer.Context = None,
        dev_type: constants.LibAllDevTypes | List[constants.LibAllDevTypes] = None,
        swack: bool = False,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            ctx (typer.Context): The click/typer Context.
            incomplete (str): The last partial or full command before completion invoked.
            dev_type: (str, optional): One of "ap", "cx", "sw", "switch", or "gw"
                where "switch" is both switch types.  Defaults to None (all device types)
            swack (bool, optional): If there are multiple matches (stack) return only the conductor as a match.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Add cencli as option to show and update config commands (update not implememnted yet)
        utils.listify(dev_type)
        out, args = self._cencli_self(ctx, incomplete, args)

        group_out = self.group_completion(incomplete=incomplete, args=args)
        group_out = group_out if not group_out else list(group_out)
        if group_out and dev_type:
            cache_groups = [self.get_group_identifier(g[0]) for g in group_out]
            group_out = [complete_group for complete_group, cache_group in zip(group_out, cache_groups) if any([t in cache_group.allowed_types for t in dev_type])]
        if group_out:
            out += group_out

        if not bool([t for t in out if t[0] == incomplete]):  # group had exact match no need for dev
            match = self.get_dev_identifier(incomplete, dev_type=dev_type, swack=swack, completion=True)
            if match:
                out += [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m

    @ensure_config
    def group_dev_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            ctx (typer.Context): The click/typer Context.
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        yield from self._group_dev_completion(incomplete, ctx=ctx, args=args)

    @ensure_config
    def group_dev_ap_gw_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        yield from self._group_dev_completion(incomplete, ctx=ctx, dev_type=["ap", "gw"], args=args)

    # TODO NOT USED???
    @ensure_config
    def group_dev_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:  # pragma: no cover  This isn't used ... check if it was created with the intent to use it but never referenced
        """Completion for argument that can be either group or a gateway.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        match: list[CacheDevice | CacheGroup] = self.get_identifier(incomplete, ["group", "dev"], device_type="gw", completion=True)

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
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument that can be either group, site, or a gateway or keyword "commands".

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        if ctx.params.get("nodes") or ctx.params.get("kw1") == "all":
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

            match: list[CacheDevice] | list[CacheGroup] | list[CacheSite] = self.get_identifier(incomplete, [db], device_type="gw", completion=True)

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
    ) -> Iterator[Tuple[str, str]]:
        """Completion for groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
                    # FIXME zsh is displaying "name name name --help-text"  (name x 3 the help text on each line)

        for m in out:
            yield m

    def template_group_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Completion for template groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        all_match = self.get_group_identifier(
            incomplete,
            completion=True,
        )
        match = [m for m in all_match if m.wired_tg or m.wlan_tg]
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def ap_group_completion(
        self,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Completion for AP groups (by name).

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the group, or
                Returns None if config is invalid
        """
        match = self.get_group_identifier(
            incomplete,
            completion=True,
            dev_type=["ap"],
        )

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m


    @ensure_config
    def label_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        """Completion for labels.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]:  Name and help_text for the label, or
                Returns None if config is invalid
        """
        incomplete, pfx = _handle_multi_word_incomplete(incomplete)
        match: List[CacheLabel] = self.get_label_identifier(
            incomplete,
            completion=True,
        )

        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]
        if match:
            match = [m for m in match if m.name not in args and str(m.id) not in args]
            for m in sorted(match, key=lambda i: i.name):
                if str(m.id).startswith(incomplete):
                    out += [(str(m.id), m.help_text)]
                else:
                    out += [m.get_completion(pfx=pfx)]  # TODO do this for others

        for m in out:
            yield m

    @ensure_config
    def client_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for clients.

        Args:
            ctx (typer.Context): Provided automatically by typer
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the client, or
                Returns None if config is invalid
        """
        incomplete, pfx = _handle_multi_word_incomplete(incomplete)
        match = self.get_client_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or []
        if match:
            # filter by type if we can gather type from context
            if ctx.params.get("wireless") or ctx.params.get("wired"):
                match = [m for m in match if m.type == f"{'wireless' if ctx.params.get('wireless') else 'wired'}"]
            # remove clients that are already on the command line
            match = [m for m in match if m.name not in args]
            for c in sorted(match, key=lambda i: i.name):
                if c.name.lower().startswith(incomplete.lower()):
                    if pfx == '"':
                        out += [(f'"{c.name}"', c.help_text)]
                    elif pfx == "'":
                        out += [(f"'{c.name}'", c.help_text)]
                    else:
                        out += [(c.name if " " not in c.name else f"'{c.name}'", c.help_text)]
                elif utils.Mac(c.mac).clean.startswith(utils.Mac(incomplete).clean):
                    out += [(c.mac, c.help_text)]
                elif c.ip.startswith(incomplete):
                    out += [(c.ip, c.help_text)]
                else:  # pragma: no cover
                    log.warning(f"DEV WARNING FailSafe Match hit in cache.client_completion {incomplete = }")
                    out += [(c.name, f'{c.help_text} FailSafe Match')]  # failsafe, shouldn't hit

        for c in out:
            yield c[0].replace(":", "-"), c[1]  # TODO completion behavior has changed.  This works-around issue bash doesn't complete past 00: and zsh treats each octet as a dev name when : is used.

    @ensure_config
    def event_log_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for events.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Value and help_text for the event, or
                Returns None if config is invalid
        """
        _completion: list[tuple[str, str]] = [
            ("cencli", "Show cencli logs (alias for self)"),
            ("self", "Show cencli logs"),
            ("pytest", "Show cencli test run logs"),
            *[(x['id'], f"{x['id']}|{x['device'].split('Group:')[0].rstrip()}") for x in self.events]
        ]

        if incomplete == "":
            for m in _completion:
                yield m[0], m[1]

        else:
            args = args or []
            for m in _completion:
                if m[0].startswith(incomplete) and m[0] not in args:
                    yield m

    @ensure_config
    def audit_log_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for audit event logs.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to [].

        Yields:
            Iterator[Tuple[str, str]]: Value and help_text for the event, or
                Returns None if config is invalid
        """
        if incomplete == "":
            for m in self.logs:
                yield m["id"]
        else:
            for log in self.logs:
                if str(log["id"]).startswith(incomplete):
                    yield log["id"]

    @ensure_config
    def site_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for sites.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the site, or
                Returns None if config is invalid
        """
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        match = self.get_site_identifier(
            incomplete.replace('"', "").replace("'", ""),
            completion=True,
        )

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                match_attrs = [a for a in [m.name, m.id, m.address, m.city, m.state, m.zip] if a]
                if all([attr not in args for attr in match_attrs]):
                    matched_attribute = [attr for attr in match_attrs if str(attr).startswith(incomplete)]
                    # err_console.print(f"\n{match_attrs=}, {matched_attribute=}, {incomplete=}")  # DEBUG completion
                    matched_attribute = m.name if len(matched_attribute) != 1 else matched_attribute[0]
                    out += [tuple([matched_attribute if " " not in matched_attribute else f"'{matched_attribute}'", m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
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

    @ensure_config
    def dev_template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        match = match or []
        dev_match = self.get_dev_identifier(
            incomplete,
            completion=True,
        )

        # filter device matches by those that are in template groups
        group_type = [(m.group, m.type) for m in dev_match]
        template_dev_match = []
        for (group, dev_type), dev in zip(group_type, dev_match):
            if dev_type == "ap":
                if self.groups_by_name.get(group, {"wlan_tg": True})["wlan_tg"] is True:
                    template_dev_match += [dev]
            elif dev_type in ["cx", "sw"]:
                if self.groups_by_name.get(group, {"wired_tg": True})["wired_tg"] is True:
                    template_dev_match += [dev]

        match += template_dev_match or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    @ensure_config
    def dev_gw_switch_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        # typer stopped providing args pulling from ctx.params
        if not args:  # pragma: no cover
            args = [arg for p in ctx.params.values() for arg in utils.listify(p)]

        match = self.get_dev_identifier(incomplete, dev_type=["gw", "switch"], completion=True)

        out = [] if not match else [c for c in [m.get_completion(incomplete, args=args) for m in sorted(match, key=lambda i: i.name)] if c is not None]

        for m in out:
            yield m


    @ensure_config
    def dev_gw_switch_site_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if config.valid:
            yield from self.dev_gw_switch_completion(ctx, incomplete, args=args)
            yield from self.site_completion(ctx, incomplete, args=args)


    @ensure_config
    def remove_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str],
    ) -> Iterator[Tuple[str, str]]:
        if args[-1].lower() == "site":
            yield from self.site_completion(ctx, incomplete)
        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    out += ("site", )

            if "site" not in args:
                out += [m for m in self.dev_completion(incomplete=incomplete, args=args)]

            for m in out:
                yield m

    async def format_raw_devices_for_cache(self, resp: Response):
        dev_types = {
            "aps": "ap",
            "gateways": "gw",
        }
        switch_types = {
            "AOS-S": "sw",
            "AOS-CX": "cx"
        }
        raw_data = {
            url.split("/")[-1]: [
                {
                    "type": dev_types.get(url.split("/")[-1], switch_types.get(inner.get("switch_type", "err"))),
                    "swack_id": inner.get("stack_id", inner.get("swarm_id")) or (inner.get("serial", "err") if "swarm_id" in inner and inner.get("firmware_version", "").startswith("10.") else None),
                    **inner
                } for inner in resp.raw[url].get(url.split("/")[-1], {})  # Failed responses will lack the inner key with the devices
            ] for url in resp.raw
        }

        return raw_data


    async def _add_update_devices(self, new_data: List[dict], db: Literal["dev", "inv"] = "dev") -> bool:
        # We avoid using upsert as that is a read then write for every entry, and takes a significant amount of time
        new_by_serial = {dev["serial"]: dev for dev in new_data}
        if db == "dev":
            DB = self.DevDB
            cache_by_serial = self.devices_by_serial
            updated_devs_by_serial = {**cache_by_serial, **new_by_serial}
        else:
            DB = self.InvDB
            cache_by_serial = self.inventory_by_serial
            updated_devs_by_serial = {**cache_by_serial, **{serial: dict(models.InventoryDevice(**{**cache_by_serial.get(serial, {}), **new_by_serial[serial]}).model_dump()) for serial in new_by_serial}}

        # updated_devs_by_serial = {**cache_by_serial, **{serial: {**cache_by_serial.get(serial, {}), **new_by_serial[serial]} for serial in new_by_serial}}
        return await self.update_db(DB, data=list(updated_devs_by_serial.values()), truncate=True)


    async def update_db(self, db: Table, data: List[Dict[str, Any]] | Dict[str, Any] = None, *, doc_ids: List[int] | int = None, dev_types: constants.GenericDeviceTypes | List[constants.GenericDeviceTypes] = None, truncate: bool = True,) -> bool:
        """Update Local Cache DB

        Args:
            db (Table): TinyDB Table object to be updated.
            data (List[Dict[str, Any]] | Dict[str, Any], optional): Data to be added to database. Defaults to None.
            doc_ids (List[int] | int, optional): doc_ids to be deleted from the DB. Defaults to None.
            dev_types (Literal["ap", "gw", "cx", "sw", "switch"] | List["ap", "gw" ...], optional): List of dev_types the data represents as current for those types.
                This will result in any devices of the specified types that do not exist in the provided data being removed from cache. Defaults to None.
                Deprecated: dev_types is deprecated, ignored.
            truncate (bool, optional): Existing DB data will be discarded, and all data in DB will be replaced with provided. Defaults to True.

        Returns:
            bool: Bool indicating if cache update was successful.
        """
        _start_time = time.perf_counter()
        if data is not None:
            data = utils.listify(data)
            with econsole.status(f":arrows_clockwise:  Updating [dark_olive_green2]{db.name}[/] Cache: [cyan]{len(data)}[/] records."):
                if truncate:
                    db.truncate()
                db_res = db.insert_multiple([dict(d) for d in data])  # Converts any TinyDB.Documents and pydantic models to dict as that has unexpected results.
                return self.verify_db_action(db, expected=len(data), response=db_res, elapsed=round(time.perf_counter() - _start_time, 2))

        doc_ids = utils.listify(doc_ids) or []
        with econsole.status(f":wastebasket:  [red]Removing[/]] [cyan]{len(doc_ids)}[/] records from [dark_olive_green2]{db.name}[/] cache."):
            db_res = db.remove(doc_ids=doc_ids)
            return self.verify_db_action(db, expected=len(doc_ids), response=db_res, remove=True, elapsed=round(time.perf_counter() - _start_time, 2))


    # FIXME handle no devices in Central yet exception 837 --> cleaner.py 498
    async def update_dev_db(
            self,
            data: List[Dict[str, Any]] | Dict[str, Any] | List[int] | int,
            *,
            remove: bool = False,
        ) -> bool:
        """Update Device Database (local cache).

        If data is provided it's asumed to be a partial update.  No devices will be removed from the cache unless remove=True.

        Args:
            data (List[Dict[str, Any]] | Dict[str, Any] | List[int] | int): Device data to update cache with.
                Existing devices are retained and updated with any changes from the new data provided.
            remove (bool, optional): Set True to remove devices from cache, data should be a list of doc_ids (int).

        Returns:
            bool: Returns bool indicating cache update success.
        """
        data = utils.listify(data)
        if not remove:
            return await self._add_update_devices(data)
        else:
            return await self.update_db(self.DevDB, doc_ids=data)

    async def prep_filtered_devs_for_cache(self, raw_models: List[models.Device], dev_type: constants.GenericDeviceTypes | List[constants.GenericDeviceTypes] = None, site: str = None, group: str = None) -> List[dict]:
        new_by_serial = {d.serial: d.model_dump() for d in raw_models}
        filters = {
            "dev_type": dev_type,
            "site": site,
            "group": group
        }
        filter_msg = ", ".join([f"{k}: {v if k != 'dev_type' else utils.unlistify(v)}" for k, v in filters.items() if v])

        cache_type = []
        if dev_type:
            switch_types = ["cx", "sw"] if "switch" in dev_type else []
            cache_type = [*[t for t in dev_type if t != "switch"], *switch_types]

        def include_device(dev: dict) -> bool:
            criteria = []
            if cache_type:
                criteria += [dev["type"] in cache_type]
            if site:
                criteria += [dev["site"] == site]
            if group:
                criteria += [dev["group"] == group]

            if all(criteria):
                if dev["serial"] not in new_by_serial:
                    return False

            return True

        cache_devices = {cd["serial"]: cd for cd in self.devices if include_device(cd)}

        update_data = {**cache_devices, **new_by_serial}
        log.info(f"Data prepared for device cache update.  Filters: {filter_msg}. Add/update {len(new_by_serial)} devices.  Devices in cache: Now: {len(self.devices)}, After Update: {len(update_data)}.")

        return list(update_data.values())

    async def refresh_dev_db(
            self,
            dev_type: constants.GenericDeviceTypes | List[constants.GenericDeviceTypes] = None,  # TODO make consistent throughout using device_type in many places
            group: str = None,
            site: str = None,
            label: str = None,
            serial: str = None,
            mac: str = None,
            model: str = None,
            stack_id: str = None,
            swarm_id: str = None,
            cluster_id: str = None,
            public_ip_address: str = None,
            status: constants.DeviceStatus = None,
            show_resource_details: bool = True,
            calculate_client_count: bool = True,
            calculate_ssid_count: bool = False,
            fields: list = None,
            offset: int = 0,
            limit: int = 1000,  # max allowed 1000
        ) -> CombinedResponse:
        """Get all devices from Aruba Central, and refresh local cache.

        Args:
            dev_type (Literal['ap', 'gw', 'cx', 'sw', 'sdwan', 'switch'], optional): Device Types to Update. Defaults to None.
            group (str, optional): Filter by devices in a Group. Defaults to None.
            site (str, optional): Filter by devices in a Site. Defaults to None.
            label (str, optional): Filter by devices with a label assigned. Defaults to None.
            serial (str, optional): Filter by Serial. Defaults to None.
            mac (str, optional): Filter by mac. Defaults to None.
            model (str, optional): Filter by model. Defaults to None.
            stack_id (str, optional): Filter by stack id (switches). Defaults to None.
            swarm_id (str, optional): Filter by swarm id (APs). Defaults to None.
            cluster_id (str, optional): Filter by cluster id. Defaults to None.
            public_ip_address (str, optional): Filter by public ip. Defaults to None.
            status (constants.DeviceStatus, optional): Filter by status. Defaults to None.
            show_resource_details (bool, optional): Show device resource utilization details. Defaults to True.
            calculate_client_count (bool, optional): Calculate client count. Defaults to True.
            calculate_ssid_count (bool, optional): Calculate SSID count. Defaults to False.
            fields (list, optional): fields to return. Defaults to None.
            offset (int, optional): pagination offset. Defaults to 0.
            limit (int, optional): pagination limit max 1000. Defaults to 1000.

        Returns:
            CombinedResponse: CombinedResponse object.
        """
        dev_type = None if not dev_type or dev_type == "all" else utils.listify(dev_type)
        resp: List[Response] | CombinedResponse = await api.monitoring.get_all_devices(
            dev_types=dev_type,
            group=group,
            site=site,
            label=label,
            serial=serial,
            mac=mac,
            model=model,
            stack_id=stack_id,
            swarm_id=swarm_id,
            cluster_id=cluster_id,
            public_ip_address=public_ip_address,
            status=status,
            show_resource_details=show_resource_details,
            calculate_client_count=calculate_client_count,
            calculate_ssid_count=calculate_ssid_count,
            fields=fields,
            offset=offset,
            limit=limit,
            cache=True,
        )
        if isinstance(resp, CombinedResponse) and resp.ok:  # Can be Response | List[Response] if get_all_devices aborted due to failures
            # Any filters not in list below do not result in a cache update
            filtered_resonse = True if any([label, serial, mac, model, stack_id, swarm_id, cluster_id, public_ip_address, status]) else False
            raw_data = await self.format_raw_devices_for_cache(resp)
            with console.status(f"preparing {len(resp)} records for cache update"):
                _start_time = time.perf_counter()
                raw_models_by_type = models.Devices(**raw_data)
                raw_models = [*raw_models_by_type.aps, *raw_models_by_type.switches, *raw_models_by_type.gateways]
                log.debug(f"prepared {len(resp)} records for dev cache update in {round(time.perf_counter() - _start_time, 2)}")

            if dev_type:
                update_data = await self.prep_filtered_devs_for_cache(raw_models=raw_models, dev_type=dev_type, site=site, group=group)
            else:
                update_data = [dev.model_dump() for dev in raw_models]

            if resp.all_ok and not filtered_resonse:
                self.responses.dev = resp
                # we update the response cache even if by dev_type now.
                if dev_type:
                    self.responses.device_type = dev_type

                _ = await self.update_db(self.DevDB, data=update_data, truncate=True)
            else:  # Response is filtered or incomplete due to partial failure merge with existing cache data (update)
                _ = await self._add_update_devices(update_data)

        return resp

    async def refresh_sub_db(self, sub_type: str = None, dev_type: str = None) -> Response:
        """Refresh Subscriptions Database (local cache).

        Returns:
            Response: CentralAPI Response object
        """
        if not glp_api:  # We only started caching subscription data with glp addition, classic does not cache subscriptions
            return await api.platform.get_subscriptions(sub_type=sub_type, device_type=dev_type)  # pragma: no cover

        resp: Response = await glp_api.subscriptions.get_subscriptions(sub_type=sub_type, dev_type=dev_type)
        if resp.ok:
            self.responses.sub = resp
            sub_data = Subscriptions(**resp.raw)
            resp.output = sub_data.output()
            resp.caption = sub_data.counts
            if not any([sub_type, dev_type]):
                cache_data = sub_data.cache_dump()
            else:
                cache_data = list({**self.subscriptions_by_id, **{sub["id"]: sub for sub in sub_data.cache_dump()}}.values())

            _ = asyncio.create_task(self.update_db(self.SubDB, data=cache_data, truncate=True))

        return resp

    async def update_floor_plan_cache(self, data, cache: Literal["buildings", "floors"] = "buildings") -> bool:
        if cache == "floors":
            model = models.Floors
            db = self.FloorPlanAPDB
        elif cache == "buildings":
            model = models.BuildingResponses
            db = self.BuildingDB

        try:
            data = model(data)
        except ValidationError as e:
            log.error(utils.clean_validation_errors(e), show=True, caption=True, log=True)
            return False

        cache_data = data.cache_dump()
        _ = asyncio.create_task(self.update_db(db, data=cache_data, truncate=True))
        return True

    # TODO need add bool or something to prevent combining and added device with current when a device is added as insert is all that is needed
    async def update_inv_db(
            self,
            data: List[Dict[str, Any]] | Dict[str, Any] | List[int] | int,
            *,
            remove: bool = False,
        ) -> bool:
        """Update Inventory Database (local cache).

        Args:
            data (List[Dict[str, Any]] | Dict[str, Any] | List[int] | int,): Data to be updated in Inventory, Existing inventory
                data is retained, new data is added, any changes in existing device is updated.
            remove (bool, optional): Determines if update is to remove from cache. Defaults to False.
                data should be a list of doc_ids when removing from cache.

        Returns:
            bool: Returns bool indicating cache update success.
        """
        # provide serial or list of serials to remove
        data = utils.listify(data)
        if not remove:
            return await self._add_update_devices(data, "inv")
        else:
            db_res = self.InvDB.remove(doc_ids=data)
            if len(db_res) != len(data):  # pragma: no cover
                log.error(f"TinyDB InvDB table update returned an error.  data included {len(data)} to remove but DB only returned {len(db_res)} doc_ids", show=True, caption=True,)
                return False
            return True

    async def refresh_inv_db(
            self,
            dev_type: Literal['ap', 'gw', 'switch', 'bridge', 'all'] = None,
    ) -> Response:
        """Get devices from device inventory, and Update device Cache with results.

        Uses GLP API if configed, classic Central API if not.

        Args:
            dev_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.

        Returns:
            Response: CentralAPI Response object
        """
        if glp_api:
            return await self.refresh_inv_db_glp(dev_type=dev_type)
        return await self.refresh_inv_db_classic(dev_type=dev_type)  # pragma: no cover

    async def refresh_inv_db_glp(
            self,
            dev_type: Literal['ap', 'gw', 'switch', 'bridge', 'all'] = None,  # dev_type is effectively ignored for glp/cnx
    ) -> Response:
        """Get devices from device inventory, and Update device Cache with results.

        This combines the results from 2 API calls:
            - classic.api.monitoring.get_device_inventory: /devices/<api version>/devices
            - classic.api.monitoring.get_subscriptions: /devices/<api version>/subscriptions

        Args:
            dev_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.

        Returns:
            Response: CentralAPI Response object
        """
        br = BatchRequest
        batch_resp = await glp_api.session._batch_request(
            [
                br(glp_api.devices.get_glp_devices),
                br(glp_api.subscriptions.get_subscriptions),
                # br(self.refresh_sub_db)  # sub_db is updated here
            ]
        )
        if not any([r.ok for r in batch_resp]):
            log.error("Unable to perform Inv cache update due to API call failure", show=True)
            return batch_resp

        inv_resp, sub_resp = batch_resp  # if first call failed above it doesn't get this far.

        inv_data, sub_data = None, None
        if not sub_resp.ok:
            log.error(f"Call to fetch subscription details failed.  {sub_resp.error}.  Subscription details provided from previously cached values.", caption=True)
            inv_data = GlpInventory(**inv_resp.raw)
            _inv_by_ser = {} if not inv_resp.ok else {dev["serialNumber"]: dev for dev in inv_resp.raw["items"]}
            combined = {serial: {**_inv_by_ser[serial], **self.inventory_by_serial.get(serial, {})} for serial in _inv_by_ser.keys()}
            inv_model = models.Inventory(list(combined.values()))
        else:
            sub_data = Subscriptions(**sub_resp.raw)
            inv_data = GlpInventory(**inv_resp.raw)
            combined = await get_inventory_with_sub_data(inv_data, sub_data)
            inv_model = models.Inventory(combined)

        if dev_type and dev_type != "all":
            dev_type: list[str] = [dev_type] if dev_type != "switch" else ["cx", "sw"]
            inv_model = models.Inventory([i for i in inv_model.model_dump() if i["type"] in dev_type])

        resp = [r for r in batch_resp if r.ok][-1]
        resp.rl = sorted([r.rl for r in batch_resp])[0]
        resp.raw = {r.url.path: r.raw for r in batch_resp}

        resp.output = inv_model.model_dump()
        if inv_data is not None:
            resp.caption = inv_data.counts

        # -- CACHE UPDATES --
        self.responses.inv = resp
        if dev_type is None or dev_type == "all":
            _ = await self.update_db(self.InvDB, data=resp.output, truncate=True)
        else:
            self.responses.device_type = dev_type
            _ = await self._add_update_devices(resp.output, "inv")

        if sub_data:
            self.responses.sub = sub_resp
            _ = asyncio.create_task(self.update_db(self.SubDB, data=sub_data.cache_dump(), truncate=True))

        return resp

    # TODO need to make device_type consistent refresh_dev_db uses dev_type.  All CentralAPI methods use device_type
    async def refresh_inv_db_classic(
            self,
            dev_type: Literal['ap', 'gw', 'switch', 'all'] = None,
    ) -> Response:  # pragma: no cover
        """Get devices from device inventory, and Update device Cache with results.

        This combines the results from 2 API calls:
            - classic.api.monitoring.get_device_inventory: /platform/device_inventory/v1/devices
            - classic.api.monitoring.get_subscriptions: /platform/licensing/v1/subscriptions

        Args:
            device_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.

        Returns:
            Response: CentralAPI Response object
        """
        br = BatchRequest
        batch_resp = await api.session._batch_request(
            [
                br(api.platform.get_device_inventory, device_type=dev_type),
                br(api.platform.get_subscriptions, device_type=dev_type)
            ]
        )
        if not any([r.ok for r in batch_resp]):
            log.error("Unable to perform Inv cache update due to API call failure", show=True)
            return batch_resp

        inv_resp, sub_resp = batch_resp  # if first call failed above if would result in return.
        _inv_by_ser = {} if not inv_resp.ok else {dev["serial"]: dev for dev in inv_resp.raw["devices"]}

        if not sub_resp.ok:
            log.error(f"Call to fetch subscription details failed.  {sub_resp.error}.  Subscription details provided from previously cached values.", caption=True)
            combined = [{**_inv_by_ser[serial], **self.inventory_by_serial.get(serial, {})} for serial in _inv_by_ser.keys()]
        else:
            raw_devs_by_serial = {serial: dev_data["subscription_key"] for serial, dev_data in _inv_by_ser.items()}
            dev_subs = list(set(raw_devs_by_serial.values()))
            subs_by_key = {sub["subscription_key"]: {"expires_in": sub["end_date"], "expired": sub["status"] == "EXPIRED"} for sub in sub_resp.output if sub["subscription_key"] in dev_subs}
            combined = {
                serial: {
                    **dev_data,
                    "subscription_expires": None if raw_devs_by_serial[serial] is None else subs_by_key[raw_devs_by_serial[serial]]["expires_in"]
                } for serial, dev_data in _inv_by_ser.items()
            }
        resp = [r for r in batch_resp if r.ok][-1]
        resp.rl = sorted([r.rl for r in batch_resp])[0]
        resp.raw = {r.url.path: r.raw for r in batch_resp}
        inv_model = models.Inventory(list(combined.values()))
        resp.output = inv_model.model_dump()
        resp.caption = inv_model.counts

        self.responses.inv = resp
        if dev_type is None or dev_type == "all":
            _ = await self.update_db(self.InvDB, data=inv_model.cache_dump(), truncate=True)
        else:
            self.responses.device_type = dev_type
            _ = await self._add_update_devices(inv_model.cache_dump(), "inv")

        return resp

    # TODO break all update_*_db into update_*_db and refresh_*_db.  So return is consistent
    async def update_site_db(self, data: SiteData = None, remove: bool = False) -> bool | None:
        if data:
            data = utils.listify(data)
            if not remove:
                data = models.Sites(data).by_id
                combined_data = {**self.sites_by_id, **data}
                return await self.update_db(self.SiteDB, data=list(combined_data.values()), truncate=True)
            else:
                return await self.update_db(self.SiteDB, doc_ids=data)

    async def refresh_site_db(self, force: bool = False) -> Response:
        if self.responses.site and not force:
            log.warning("cache.refresh_site_db called, but site cache has already been fetched this session.  Returning stored response.")
            return self.responses.site

        resp = await api.central.get_all_sites()
        if resp.ok:
            self.responses.site = resp
            self.updated.append(api.central.get_all_sites)  # TODO remove once all checks refactored to look for self.responses.site

            sites = models.Sites(resp.raw["sites"])
            resp.output = sites.model_dump()

            _ = await self.update_db(self.SiteDB, data=resp.output, truncate=True)
        return resp

    # TODO make consistent this adds to existing cache update_site_db combines and truncates
    async def update_group_db(self, data: list | dict, remove: bool = False) -> bool:
        data = utils.listify(data)
        if not remove:
            return await self.update_db(self.GroupDB, data=data, truncate=False)
        else:
            return await self.update_db(self.GroupDB, doc_ids=data)


    async def refresh_group_db(self) -> Response:
        if self.responses.group:
            log.info("Update Group DB already refreshed in this session, returning previous group response")
            return self.responses.group

        resp = await api.configuration.get_all_groups()
        if hasattr(resp, "ok") and resp.ok:  # resp can be a list of responses if failures occured
            groups = models.Groups(resp.output)
            resp.output = groups.model_dump()

            self.responses.group = resp

            _ = await self.update_db(self.GroupDB, data=resp.output, truncate=True)
        return resp

    async def update_label_db(self, data: List[Dict[str, Any]] | Dict[str, Any] | List[int], remove: bool = False) -> Response:
        data = utils.listify(data)
        if not remove:
            return await self.update_db(self.LabelDB, data=data, truncate=False)
        else:
            return await self.update_db(self.LabelDB, doc_ids=data)

    async def refresh_label_db(self) -> Response:
        resp: Response = await api.central.get_labels()
        if resp.ok:
            self.responses.label = resp
            label_models = models.Labels(resp.output)
            cache_data = label_models.model_dump()
            _ = await self.update_db(self.LabelDB, data=cache_data, truncate=True)
        return resp

    async def refresh_license_db(self) -> Response:
        """Update License DB

        License DB stores the valid license names accepted by GreenLake/Central

        Returns:
            Response: CentralAPI Response Object
        """
        resp = await api.platform.get_valid_subscription_names()
        if resp.ok:
            resp.output = [{"name": k} for k in resp.output.keys() if self.is_central_license(k)]
            self.responses.license = resp
            _ = await self.update_db(self.LicenseDB, data=resp.output, truncate=True)
        return resp

    async def refresh_template_db(self) -> Response:
        if self.responses.template is not None:
            log.warning("cache.refresh_template_db called, but template cache has already been fetched this session.  Returning stored response.")
            return self.responses.template

        if self.responses.group is None:
            gr_resp = await self.refresh_group_db()
            if not gr_resp.ok:
                return gr_resp

        groups = self.groups

        resp = await api.configuration.get_all_templates(groups=groups)
        if resp.ok:
            if len(resp) > 0: # handles initial cache population when none of the groups are template groups
                resp.output = utils.listify(resp.output)
                template_models = models.Templates(resp.output)
                resp.output = template_models.model_dump()
                self.responses.template = resp
                _ = await self.update_db(self.TemplateDB, data=resp.output, truncate=True)
        return resp

    async def update_template_db(
            self,
            data: Dict[str, str] | List[Dict[str, str]] = None,
            doc_ids: int | List[int] = None,
            add: bool = False,
        ):
        data = utils.listify(data)

        try:
            if doc_ids:
                doc_ids = utils.listify(doc_ids)
                resp = await self.update_db(self.TemplateDB, doc_ids=doc_ids)

            elif not add:
                cache_data = self.templates_by_name_group
                data = {f'{t["name"]}_{t["group"]}': t for t in data}
                update_data = list({**cache_data, **data}.values())
                resp = await self.update_db(self.TemplateDB, data=update_data, truncate=True)
            else:
                update_data = data
                resp = await self.update_db(self.TemplateDB, data=update_data, truncate=False)

        except Exception as e:  # pragma: no cover
            log.exception(f"Exception during update of TemplateDB\n{e}")
            return

        return resp

    async def refresh_client_db(
        self,
        client_type: constants.ClientType = None,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        site: str = None,
        serial: str = None,
        os_type: str = None,
        stack_id: str = None,
        cluster_id: str = None,
        band: str = None,
        mac: str = None,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
    ) -> Response:
        """refresh client DB

        all args are passed to api.monitoring.get_clients, Local Cache is updated with any results.
        Local Cache retains clients connected within last 90 days by default.  Configuratble via cache_client_days
        in the config.

        It returns the raw data from the API with whatever filters were provided by the user
        then updates the db with the data returned

        Args:
            client_type (Literal['wired', 'wireless', 'all'], optional): Client type to retrieve.  Defaults to None.
                if not provided all client types will be returned, unless a filter specific to a client type is
                specified.  i.e. providing band will result in WLAN clients.
            group (str, optional): Filter by Group. Defaults to None.
            swarm_id (str, optional): Filter by swarm. Defaults to None.
            label (str, optional): Filter by label. Defaults to None.
            network (str, optional): Filter by WLAN SSID. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            serial (str, optional): Filter by connected device serial. Defaults to None.
            os_type (str, optional): Filter by client OS type. Defaults to None.
            stack_id (str, optional): Filter by Stack ID. Defaults to None.
            cluster_id (str, optional): Filter by Cluster ID. Defaults to None.
            band (str, optional): Filter by band. Defaults to None.
            mac (str, optional): Filter by client MAC. Defaults to None.
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for.  Format:
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H

        Past users are always retained, unless truncate=True
        """
        resp: Response = await api.monitoring.get_clients(
            client_type=client_type,
            group=group,
            swarm_id=swarm_id,
            label=label,
            network=network,
            site=site,
            serial=serial,
            os_type=os_type,
            stack_id=stack_id,
            cluster_id=cluster_id,
            band=band,
            mac=mac,
            client_status=client_status,
            past=past,
        )
        if not resp.ok:
            return resp
        else:
            if len(resp) > 0:
                resp.output = utils.listify(resp.output)
                with econsole.status(f"Preparing [cyan]{len(resp.output)}[/] clients for cache update"):
                    new_clients = models.Clients(resp.output)
                    if "wireless" in [new_clients[0].type, new_clients[-1].type]:
                        self.responses.client = resp
                    data = {**self.cache_clients_by_mac, **new_clients.by_mac}
                _ = await self.update_db(self.ClientDB, data=list(data.values()), truncate=True)
        return resp


    def update_log_db(self, log_data: List[Dict[str, Any]]) -> bool:
        return asyncio.run(self.update_db(self.LogDB, data=log_data, truncate=True))

    def update_event_db(self, log_data: List[Dict[str, Any]]) -> bool:
        return asyncio.run(self.update_db(self.EventDB, data=log_data, truncate=True))

    async def update_hook_data_db(self, data: List[Dict[str, Any]]) -> bool:  # pragma: no cover  ... used by hook proxy
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

    # Not tested or used yet, until we have commands that add/del MPSK networks
    async def update_mpsk_net_db(self, data: List[Dict[str, Any]], remove: bool = False) -> bool:  # pragma: no cover
        if remove:
            return await self.update_db(self.MpskNetDB, doc_ids=data)

        data = models.MpskNetworks(data)
        data = data.model_dump()
        return await self.update_db(self.MpskNetDB, data=data, truncate=True)


    async def refresh_mpsk_networks_db(self) -> Response:
        resp = await api.cloudauth.get_mpsk_networks()
        if resp.ok:
            self.responses.mpsk = resp
            if resp.output:
                _update_data = models.MpskNetworks(resp.raw)
                _update_data = _update_data.model_dump()

                _ = await self.update_db(self.MpskNetDB, data=_update_data, truncate=True)

        return resp

    async def refresh_mpsk_db(self, mpsk_id: str = None, name: str = None, role: str = None, status: MPSKStatus = None) -> Response:
        if not mpsk_id:
            net_resp = await self.refresh_mpsk_networks_db()
            if not net_resp.ok:
                log.error(f"Unable to refresh named mpsks as call to fetch mpsk networks failed {net_resp.error}", show=True)
                return net_resp
            mpsk_networks = {net["id"]: net["ssid"] for net in net_resp.output}
            named_reqs = [
                BatchRequest(api.cloudauth.get_named_mpsk, mpsk_id, name=name, role=role, status=status)
                for mpsk_id in mpsk_networks
            ]
            batch_resp = await api.session._batch_request(named_reqs)

            for resp, network in zip(batch_resp, mpsk_networks.values()):
                if not resp.ok:
                    log.error(f"skipping cache update for MPSKs associated with {network} due to failure {resp.error}", show=True)
                    continue
                resp.output = [
                    {"ssid": network, **inner}
                    for inner in resp.output
                ]
            combined_output = [inner for r in batch_resp for inner in r.output if r.ok]
            last_resp = sorted([r for r in batch_resp if r.ok], key=lambda r: r.rl)[0] or batch_resp[-1]  # the or comes into play if all have failed.
            resp.rl = last_resp.rl
            if resp.ok:
                resp.output = combined_output
        else:
            resp = await api.cloudauth.get_named_mpsk(mpsk_id, name=name, role=role, status=status)
            if resp.ok:
                ssid: CacheMpskNetwork = self.get_mpsk_network_identifier(mpsk_id, silent=True)
                if ssid:
                    resp.output = [{"ssid": ssid.name, **inner} for inner in resp.output]

        truncate = True if not mpsk_id and not any([name, role, status]) else False

        if resp.ok:
            self.responses.mpsk = resp
            if resp.output:
                _update_data = models.Mpsks(resp.output)
                _update_data = _update_data.model_dump()

                _ = await self.update_db(self.MpskDB, data=_update_data, truncate=truncate)

        return resp

    async def update_portal_db(self, data: List[Dict[str, Any]] | List[int], remove: bool = False) -> bool:
        if remove:
            return await self.update_db(self.PortalDB, doc_ids=data)

        portal_models = models.Portals(data)
        data_by_id = {p.id: p.model_dump() for p in portal_models}
        update_data = {**self.portals_by_id, **data_by_id}
        return await self.update_db(self.PortalDB, data=list(update_data.values()), truncate=True)

    async def refresh_portal_db(self) -> Response:
            resp = await api.guest.get_portals()
            if not resp.ok:
                return resp

            self.responses.portal = resp

            portal_model = models.Portals(deepcopy(resp.output))
            update_data = portal_model.model_dump()
            _ = await self.update_db(self.PortalDB, data=update_data, truncate=True)

            return resp

    async def update_cert_db(self, data: List[Dict[str, Any]] | List[int], remove: bool = False) -> bool:
        if remove:
            return await self.update_db(self.CertDB, doc_ids=data)

        cert_models = models.Certs(data)
        data_by_md5 = {p["md5_checksum"]: p for p in cert_models.model_dump()}
        update_data = {**self.certs_by_md5, **data_by_md5}
        return await self.update_db(self.CertDB, data=list(update_data.values()), truncate=True)

    async def refresh_cert_db(self, *, query: str = None) -> Response:
            resp: Response = await api.configuration.get_certificates(query)
            if not resp.ok:
                return resp

            self.responses.cert = resp

            if not query:
                cert_models = models.Certs(deepcopy(resp.output))
                update_data = cert_models.model_dump()
                _ = await self.update_db(self.CertDB, data=update_data, truncate=True)
            else:
                _ = await self.update_cert_db(resp.output)

            return resp

    async def update_guest_db(self, data: List[Dict[str, Any]] | List[int], portal_id: str = None, remove: bool = False) -> bool:
        if remove:
            return await self.update_db(self.GuestDB, doc_ids=data)

        # TODO there is no simple add unless update_db is called directly
        guest_models = models.Guests(portal_id, data)
        data_by_id = {p.id: p.model_dump() for p in guest_models}
        update_data = {**self.guests_by_id, **data_by_id}
        return await self.update_db(self.GuestDB, data=list(update_data.values()), truncate=True)

    async def refresh_guest_db(self, portal_id: str) -> Response:
            resp: Response = await api.guest.get_guests(portal_id)
            if not resp.ok:
                return resp

            self.responses.guest = resp

            guest_models = models.Guests(portal_id, deepcopy(resp.output))
            data_by_id = {p.id: p.model_dump() for p in guest_models}
            update_data = {**{k: v for k, v in self.guests_by_id.items() if v["portal_id"] != portal_id}, **data_by_id}
            # update_data = guest_models.model_dump()
            _ = await self.update_db(self.GuestDB, data=list(update_data.values()), truncate=True)

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
        dev_type: constants.AllDevTypes = None
        ):
        update_funcs = []
        db_res: CombinedResponse | List[Response] = []
        dev_update_funcs = ["refresh_inv_db", "refresh_dev_db"]
        if group_db:
            update_funcs += [self.refresh_group_db]
        if dev_db:
            update_funcs += [self.refresh_dev_db]
        if inv_db:
            update_funcs += [self.refresh_inv_db]
        if site_db:
            update_funcs += [self.refresh_site_db]
        if template_db:
            update_funcs += [self.refresh_template_db]
        if label_db:
            update_funcs += [self.refresh_label_db]
        if license_db:
            update_funcs += [self.refresh_license_db]
        if update_funcs:
            kwarg_list = [{} if f.__name__ not in dev_update_funcs else {"dev_type": dev_type} for f in update_funcs]
            # kwargs = {} if update_funcs[0].__name__ not in dev_update_funcs else {"dev_type": dev_type}
            db_res += [await update_funcs[0](**kwarg_list[0])]
            if isinstance(db_res[0], list):  # needed as refresh_dev_db (if no dev_types provided) may return a CombinedResponse, but can also return a list of Responses if all failed meaning the above creates a List[list]
                db_res = utils.unlistify(db_res)

            if not db_res[-1]:
                _remaining = 0 if len(update_funcs) == 1 else len(update_funcs[1:])
                if _remaining:
                    log.error(f"Cache Update aborting remaining {len(update_funcs)} cache updates due to failure in {update_funcs[0].__name__}", show=True, caption=True)
                    db_res += [Response(error=f"{f.__name__} aborted due to failure in previous cache update call ({update_funcs[0].__name__})") for f in update_funcs[1:]]
                else:
                    log.error(f"Cache Update failure in {update_funcs[0].__name__}: {db_res[0].error}", show=True, caption=True)

            else:
                if len(update_funcs) > 1:
                    db_res = [*db_res, *await asyncio.gather(*[f(**k) for f, k in zip(update_funcs[1:], kwarg_list[1:])])]

        # If all *_db params are false refresh cache for all
        # TODO make more elegant
        else:  # TODO asyncio.sleep is a temp until build better session wide rate limit handling.
            br = BatchRequest
            db_res += await api.session._batch_request([br(self.refresh_group_db), br(asyncio.sleep, .5)])  # update groups first so template update can use the result group_update is 3 calls.
            if db_res[-1]:
                dev_res = await api.session._batch_request([br(self.refresh_dev_db), br(asyncio.sleep, .5)])   # dev_db separate as it is a multi-call 3 API calls.
                dev_res = utils.unlistify(dev_res)  # should only be an issue when debugging (re-writing responses) in refresh_dev_db
                if isinstance(dev_res, list):
                    db_res = [*db_res, *dev_res]
                else:
                    db_res += [dev_res]
                if db_res[-1]:
                    batch_reqs = [
                        BatchRequest(req)
                        for req in [self.refresh_inv_db, self.refresh_site_db, self.refresh_template_db, self.refresh_label_db, self.refresh_license_db]
                    ]
                    db_res = [
                        *db_res,
                        *await api.session._batch_request(batch_reqs)
                    ]
        return db_res

    def check_fresh(
        self,
        refresh: bool = False,
        *,
        site_db: bool = False,
        dev_db: bool = False,
        inv_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
        label_db: bool = False,
        license_db: bool = False,
        dev_type: constants.GenericDeviceTypes = None
    ) -> List[Response]:
        db_res = None
        db_map = {
            "group_db": group_db,
            "dev_db": dev_db,
            "inv_db": inv_db,
            "site_db": site_db,
            "template_db": template_db,
            "label_db": label_db,
            "license_db": license_db
        }
        update_count = list(db_map.values()).count(True)
        update_count += 0 if not inv_db else 1  # inv_db includes update for sub_db
        refresh = refresh or bool(update_count)  # if any DBs are set to update they will update regardless of refresh value
        update_all = True if not update_count else False  # if all are False default is to update all DBs but only if refresh=True

        if refresh or not config.cache_file_ok:
            _word = "Refreshing" if config.cache_file_ok else "Populating"
            updating_db = "[bright_green]Full[/] Identifier mapping" if not update_count else utils.color([k for k, v in db_map.items() if v])
            print(f"[cyan]-- {_word} {updating_db} Cache --[/cyan]", end="")

            start = time.perf_counter()
            db_res = asyncio.run(self._check_fresh(**db_map, dev_type=dev_type))
            elapsed = round(time.perf_counter() - start, 2)
            failed = [r for r in db_res if not r.ok]
            log.info(f"Cache Refreshed {update_count if update_count != len(db_map) else 'all'} table{'s' if update_count > 1 else ''} in {elapsed}s")

            if failed:
                try:
                    res_map = ", ".join(db for idx, (db, do_update) in enumerate(db_map.items()) if do_update or update_all and not db_res[idx].ok)
                    err_msg = f"Cache refresh returned an error updating {res_map}"  # TODO this logic gets screwy because if dev_db all calls fail the return is List[Response] with len 3 rather than  CombinedResponse
                except IndexError:
                    err_msg = f"Cache refresh returned an error. {len(failed)} requests failed."
                log.error(err_msg)
                api.session.spinner.fail(err_msg)
            else:
                api.session.spinner.succeed(f"Cache Refresh [bright_green]Completed[/] in [cyan]{elapsed}[/]s")

        return db_res

    def handle_multi_match(
        self,
        match: List[CentralObject] | List[models.Client],
        query_str: str = None,
        query_type: str = "device",
    ) -> List[Dict[str, Any]]:  # pragma: no cover  required tty, not part of automated testing
        if env.is_pytest:
            log.error(f"handle_multi_match called from pytest run during test: {env.current_test}.  Check fixtures/cache. {match =}", show=True)
            raise typer.Exit(1)

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
        elif query_type == "certificate":
            fields = {"name", "type", "expired", "expiration", "md5_checksum",}
        elif query_type == "sub":
            fields = {"name", "end_date", "expired", "available", "id"}
        else:  # device
            fields = ("name", "serial", "mac", "type")


        if isinstance(match[0], models.Client):
            data = [{k: d[k] for k in d.keys() if k in fields} for d in match]
        elif query_type == "sub":
            data = list(sorted([{k: v if k != "end_date" else DateTime(v, 'date-string') for k, v in d.items() if k in fields} for d in match], key=lambda x: (x["end_date"], x["available"]), reverse=True))
        else:
            data = [{k: d[k] for k in d.data if k in fields} for d in match]

        out = render.output(
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

        return [match[int(selection) - 1]]

    def get_identifier(
        self,
        qry_str: str,
        qry_funcs: Sequence[str],
        device_type: Union[str, List[str]] = None,
        swack: bool = False,
        swack_only: bool = False,
        group: str | List[str] = None,
        completion: bool = False,
    ) -> CentralObject | list[CentralObject]:
        """Get Identifier when iden type could be one of multiple types.  i.e. device or group

        Args:
            qry_str (str): The query string provided by user.
            qry_funcs (Sequence[str]): Sequence of strings "dev", "group", "site", "template"
            device_type (Union[str, List[str]], optional): Restrict matches to specific dev type(s).
                Defaults to None.
            swack (bool, optional): Similar to swack, but only filters member switches of stacks, but will also return any standalone switches that match.
                Does not filter non stacks, the way swack option does. Defaults to False.
            swack_only (bool, optional): Restrict matches to only the stack commanders matching query (filter member switches).
                Defaults to False.
            group (str, List[str], optional): applies to get_template_identifier, Only match if template is in provided group(s).
                Defaults to None.
            completion (bool, optional): If function is being called for AutoCompletion purposes. Defaults to False.
                When called for completion it will fail silently and will return multiple when multiple matches are found.

        Raises:
            typer.Exit: If not ran for completion, and there is no match, exit with code 1.

        Returns:
            CentralObject or list[CentralObject, ...]
        """
        device_type = utils.listify(device_type)
        default_kwargs = {"retry": False, "completion": completion, "silent": True}
        if "dev" in qry_funcs:  # move dev query last
            qry_funcs = [*[q for q in qry_funcs if q != "dev"], *["dev"]]

        match: List[CentralObject] = []
        for idx in range(0, 2):
            for q in qry_funcs:
                kwargs = default_kwargs.copy()
                if q == "dev":
                    kwargs["dev_type"] = device_type
                    kwargs["swack_only"] = swack_only
                    kwargs["swack"] = swack
                elif q == "template":
                    kwargs["group"] = group
                this_match = getattr(self, f"get_{q}_identifier")(qry_str, **kwargs) or []
                match = [*match, *[m for m in utils.listify(this_match) if m not in match]]

                if match and not completion:
                    # user selects which device if multiple matches returned
                    if len(match) > 1:
                        match = self.handle_multi_match(match, query_str=qry_str,)

                    return match[0]

            # No match found trigger refresh and try again.
            if idx == 0 and not match and not completion:
                self.check_fresh(
                    dev_db=True if "dev" in qry_funcs else False,
                    site_db=True if "site" in qry_funcs else False,
                    template_db=True if "template" in qry_funcs else False,
                    group_db=True if "group" in qry_funcs else False,
                )

        if completion:
            return match

        if not match:
            econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]Unable to find a matching identifier[/] for [cyan]{qry_str}[/], tried: [cyan]{qry_funcs}[/]")
            raise typer.Exit(1)

    @overload
    def get_dev_identifier(
        query_str: str,
        dev_type: constants.LibAllDevTypes | list[constants.LibAllDevTypes],
        swack: Literal[True],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: list[constants.LibAllDevTypes],
        completion: Literal[True],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        completion: Literal[True],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes] | None],
        swack: Optional[bool],
        completion: Literal[True],
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes] | None],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
        exit_on_fail: Literal[False]
    ) -> list[CacheDevice | None]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        query_str: str,
        completion: Literal[True]
    ) -> list[CacheDevice]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        query_str: str,
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes] | None],
        retry: bool,
        completion: bool,
        silent: bool,
        exit_on_fail: Literal[False]
    ) -> list[CacheDevice | None]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
        include_inventory: bool,
        exit_on_fail: bool
    ) -> list[CacheDevice | CacheInvDevice | None]: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | List[constants.LibAllDevTypes],
        swack: bool,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        dev_type: constants.LibAllDevTypes | List[constants.LibAllDevTypes],
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        swack: bool,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        include_inventory: bool,
        swack: bool,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
    ) -> CacheDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str,
        silent: Literal[True],
        exit_on_fail: Literal[False]
    ) -> CacheDevice | None: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        silent: Optional[bool],
    ) -> CacheDevice: ...  # pragma: no cover


    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        silent: Optional[bool],
        include_inventory: Literal[True],
    ) -> CacheDevice | CacheInvDevice: ...  # pragma: no cover

    @overload
    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes]],
        swack: Optional[bool],
        swack_only: Optional[bool],
        retry: Optional[bool],
        silent: Optional[bool],
        include_inventory: Optional[bool] = False,
        exit_on_fail: bool = False,
    ) -> CacheDevice | CacheInvDevice | None: ...  # pragma: no cover

    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: Optional[constants.LibAllDevTypes | List[constants.LibAllDevTypes]] = None,
        swack: Optional[bool] = False,
        swack_only: Optional[bool] = False,
        retry: Optional[bool] = True,
        completion: Optional[bool] = False,
        silent: Optional[bool] = False,
        include_inventory: Optional[bool] = False,
        exit_on_fail: Optional[bool] = True,
    ) -> CacheDevice | CacheInvDevice | list[CacheDevice] | list[CacheDevice | CacheInvDevice] | list[CacheDevice | CacheInvDevice |  None] | None:
        """Get Devices from local cache, starting with most exact match, and progressively getting less exact.

        If multiple matches are found user is promted to select device.

        Args:
            query_str (str | Iterable[str]): The query string or list of strings to attempt to match.
            dev_type (Literal["ap", "cx", "sw", "switch", "gw"] | List[Literal["ap", "cx", "sw", "switch", "gw"]], optional): Limit matches to specific device type. Defaults to None (all device types).
            swack (bool, optional): For switches only return the conductor switch that matches. For APs only return the VC of the swarm the match belongs to. Defaults to False.
                Does not filter non stacks.
            swack_only (bool, optional): For switches only return the conductor switch that matches. For APs only return the VC of the swarm the match belongs to. Defaults to False.
                If swack=True devices that lack a swack_id (swarm_id | stack_id) are filtered (even if they match).
            retry (bool, optional): If failure to match should result in a cache update and retry. Defaults to True.
            completion (bool, optional): If this is being called for tab completion (Allows multiple matches, implies retry=False, silent=True, exit_on_fail=False). Defaults to False.
            silent (bool, optional): Do not display errors / output, simply returns match if match is found. Defaults to False.
            include_inventory (bool, optional): Whether match attempt should also include Inventory DB (devices in GLCP that have yet to connect to Central). Defaults to False.
            exit_on_fail (bool, optional): Whether a failure to match exits the program. Defaults to True.

        Raises:
            typer.Exit: Exit CLI / command, occurs if there is no match unless exit_on_fail is set to False.

        Returns:
            CacheDevice | List[CacheDevice] | None: if completion = True returns list[CacheDevice] containing all matches or None if there was no match.
                Otherwise return will be the CacheDevice that matched.  (If completion=False and multiple matches are found, user is prompted to select)
        """
        retry = False if completion else retry
        all_match = None
        cache_updated = False
        if dev_type:
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = list(set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"])))

        Model = CacheDevice
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # Try exact match
            match = self.DevDB.search(
                (self.Q.name == query_str)
                | (self.Q.ip.test(lambda v: v and v.split("/")[0] == query_str))
                | (self.Q.serial == query_str)
            )

            # Try Mac address match
            if not match:
                match = self.DevDB.search(
                    (self.Q.mac == utils.Mac(query_str))
                )

            # Inventory must be exact match expecting full serial numbers MAC just needs to be the same effective MAC regardless of format
            if not match and include_inventory:
                match = self.InvDB.search(
                    (self.Q.serial == query_str)
                    | (self.Q.mac == utils.Mac(query_str))
                )
                if match:
                    Model = CacheInvDevice

            # retry with case insensitive name match if no match with original query
            if not match:
                match = self.DevDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
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

            if match and dev_type:
                all_match: List[Document] = match.copy()
                match = [d for d in all_match if d.get("type", "") in dev_type]


            # no match found initiate cache update
            if retry and (not match or Model == CacheInvDevice) and self.responses.dev is None:
                if dev_type and (cache_updated or self.responses.device_type == dev_type):
                    ...  # pragma: no cover self.responses.dev is not currently updated if dev_type provided [ update it does now, but keeping this in until tested ], but cache update may have already occured in this session.
                else:
                    if not match:
                        _msg = f"[bright_red]No Match found[/] in {'Inventory or Device (monitoring)' if include_inventory else 'Device (monitoring)'} Cache"
                    else:
                        _msg = "[bright_red]No Match found[/]" if Model != CacheInvDevice else "[bright_green]Match found in Inventory Cache[/], [bright_red]No Match found in Device (monitoring) Cache[/]"
                    dev_type_sfx = "" if not dev_type else f" [dim italic](Device Type: {utils.unlistify(dev_type)})[/]"
                    econsole.print(f"[dark_orange3]:warning:[/]  {_msg} for [cyan]{query_str}[/]{dev_type_sfx}.")
                    # fuzz_match = None
                    if FUZZ and self.devices and not silent:
                        match = self.fuzz_lookup(query_str, db=self.DevDB, dev_type=dev_type)

                    # If there is an inventory only match we still update monitoring cache (to see if device came online since it was added. Otherwise commands like move will reject due to only being in Inventory)
                    if not match or Model == CacheInvDevice:
                        kwargs = {"dev_db": True}
                        if include_inventory and Model != CacheInvDevice:
                            _word = " & Inventory "
                            kwargs["inv_db"] = True
                        else:
                            _word = " "
                        econsole.print(f":arrows_clockwise: Updating Device{_word}Cache.")
                        self.check_fresh(refresh=True, dev_type=dev_type, **kwargs )
                        cache_updated = True  # Need this for scenario when dev_type is the only thing refreshed, as that does not update self.responses.dev
                        if Model == CacheInvDevice:
                            continue

            if match:
                match = [Model(dev) for dev in match]
                break

        if len(match) > 1 and (swack or swack_only):
            unique_swack_ids = set([d.swack_id for d in match if d.swack_id])
            stacks = [d for d in match if d.swack_id in unique_swack_ids and (d.ip or (d.switch_role and d.switch_role == 2))]
            if swack:
                match = [*stacks, *[d for d in match if not d.swack_id]]
            elif swack_only:
                match = stacks

        if completion:
            return match or []

        # user selects which device if multiple matches returned
        if match:
            if len(match) > 1:  # pragma: no cover  requires tty
                match = self.handle_multi_match(sorted(match, key=lambda m: m.get("name", "")), query_str=query_str,)

            return match[0]

        elif retry:
            log.error(f"Unable to gather device info from provided identifier {query_str}", show=not silent)
            if all_match:
                _all_match_summary = [m.get('name', m.get('serial')) for m in all_match[0:5]]
                all_match_msg = f"{utils.color(_all_match_summary)}{', ...' if len(all_match) > 5 else ''}"
                _dev_type_str = escape(str(utils.unlistify(dev_type)))
                log.error(
                    f"The Following devices matched {all_match_msg} excluded as device type != {_dev_type_str}",
                    show=True,
                )
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return None

    @lru_cache
    def get_inv_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: constants.LibAllDevTypes | Iterable[constants.LibAllDevTypes] = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        exit_on_fail: bool = True,
    ) -> CacheInvDevice | list[CacheInvDevice]:
        """Get Devices from local cache, starting with most exact match, and progressively getting less exact.

        This method will serach for a match in the Inventory DB (GreenLake Inventory), then if no match is found,
        it will search DeviceDB (Central Monitoring/UI), which would provide the serial # to then search the Inventory DB



        Args:
            query_str (str | Iterable[str]): The query string or Iterable of strings to attempt to match.  Iterable will be joined with ' ' to form a single string with spaces.
            dev_type (Literal["ap", "cx", "sw", "switch", "gw"] | List[Iterable["ap", "cx", "sw", "switch", "gw"]], optional): Limit matches to specific device type. Defaults to None (all device types).
            retry (bool, optional): If failure to match should result in a cache update and retry. Defaults to True.
            completion (bool, optional): If this is being called for tab completion (Allows multiple matches, implies retry=False, silent=True, exit_on_fail=False). Defaults to False.
            silent (bool, optional): Do not display errors / output, simply returns match if match is found. Defaults to False.
            include_inventory (bool, optional): Whether match attempt should also include Inventory DB (devices in GLCP that have yet to connect to Central). Defaults to False.
            exit_on_fail (bool, optional): Whether a failure to match exits the program. Defaults to True.

        Raises:
            typer.Exit: Will display error message and exit if no match is found (unless completion=True or exit_on_fail=False)

        Returns:
            CacheInvDevice | List[CacheInvDevice] | None: if completion = True returns list[CacheInvDevice] containing all matches or None if there was no match.
                Otherwise return will be the CacheInvDevice that matched.  (If completion=False and multiple matches are found, user is prompted to select)
        """
        retry = False if completion else retry
        all_match = None
        if dev_type:
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = list(set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"])))

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # Try exact match
            match = self.InvDB.search(
                (self.Q.id == query_str)
                | (self.Q.mac == utils.Mac(query_str))
                | (self.Q.serial == query_str)
            )

            # retry with case insensitive name match if no match with original query
            if not match:
                match = self.InvDB.search(
                    (self.Q.id.test(lambda v: v and v.lower() == query_str.lower()))
                    | self.Q.serial.test(lambda v: v.lower() == query_str.lower())
                )  # We don't need MAC as utils.Mac will match regardless of case or delimeter

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.InvDB.search(
                    self.Q.id.test(lambda v: v and v.lower().startswith(query_str.lower()))
                    | self.Q.serial.test(lambda v: v.lower().startswith(query_str.lower()))
                )
                if not match:
                    qry_mac = utils.Mac(query_str)
                    qry_mac_fuzzy = utils.Mac(query_str, fuzzy=True)
                    if qry_mac or len(qry_mac) == len(qry_mac_fuzzy):
                        match = self.InvDB.search(
                            self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str, fuzzy=completion).cols.lower()))
                        )

            # Try Monitoring DB may be using non inventory field
            if not match and _ == 0:
                dev: CacheDevice | None = self.get_dev_identifier(query_str, dev_type=dev_type, silent=True, retry=False, exit_on_fail=False)
                if dev:
                    query_str = dev.serial
                    continue

            if match and dev_type:
                all_match: list[Document] = match.copy()
                match = [d for d in all_match if d.get("type", "") in dev_type]



            # no match found initiate cache update
            if retry and not match and not (self.responses.inv and set(self.responses.device_type or []) == set(dev_type or [])):
                if not silent:
                    _msg = "[bright_red]No Match found[/] in Inventory Cache"
                    dev_type_sfx = "" if not dev_type else f" [dim italic](Device Type: {utils.unlistify(dev_type)})[/]"
                    econsole.print(f"[dark_orange3]:warning:[/]  {_msg} for [cyan]{query_str}[/]{dev_type_sfx}.")
                if FUZZ and self.inventory and not silent:  # pragma: no cover  requires tty
                    if dev_type:
                        inv_generator = {"id": (d["id"] for d in self.inventory if "id" in d and d["type"] in dev_type), "serial": (d["serial"] for d in self.inventory if "serial" in d and d["type"] in dev_type)}
                    else:
                        inv_generator = {"id": (d["id"] for d in self.inventory if "id" in d), "serial": (d["serial"] for d in self.inventory if "serial" in d)}

                    fuzz_match, fuzz_confidence = None, 0
                    for _field, inv_devices in inv_generator.items():
                        _match, _confidence = process.extractOne(query_str, inv_devices)
                        if _confidence > fuzz_confidence:
                            field, fuzz_match, fuzz_confidence = _field, _match, _confidence

                    if fuzz_confidence >= 70:
                        confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                        if typer.confirm(confirm_str):
                            query = getattr(self.Q, field)
                            _match = self.InvDB.search(query == fuzz_match)

                econsole.print(":arrows_clockwise: Updating Inventory Cache.")
                self.check_fresh(refresh=True, inv_db=True, dev_type=dev_type )

            if match:
                match = [CacheInvDevice(dev) for dev in match]
                break

        if completion:
            return match or []

        # user selects which device if multiple matches returned
        if match:
            if len(match) > 1:
                match = self.handle_multi_match(sorted(match, key=lambda m: m.get("serial", "")), query_str=query_str,)

            return match[0]

        log.error(f"Unable to gather inventory info from provided identifier {query_str}", show=not silent)
        if retry:
            if all_match:
                _all_match_summary = [m.get('type', m.get('serial')) for m in all_match[0:5]]
                all_match_msg = f"{utils.color(_all_match_summary)}{', ...' if len(all_match) > 5 else ''}"
                _dev_type_str = escape(str(utils.unlistify(dev_type)))
                log.error(
                    f"The Following devices matched {all_match_msg} excluded as device type != {_dev_type_str}",
                    show=True,
                )
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return None

    @lru_cache
    def get_combined_inv_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: constants.LibAllDevTypes | Iterable[constants.LibAllDevTypes] = None,
        retry_inv: bool = True,
        retry_dev: bool = True,
        completion: bool = False,
        silent: bool = False,
        exit_on_fail: bool = None,
        exit_on_inv_fail: bool = None,
        exit_on_dev_fail: bool = None,
    ) -> CacheInvMonDevice | list[CacheInvMonDevice]:
        """Searches both Inv Cache and Dev (Monitoring Cache) and returns a CacheInvMonDevice with attributes from both."""
        exit_vars = [exit_on_inv_fail, exit_on_dev_fail]
        if exit_on_fail is not None:
            if any([item is not exit_on_fail for item in exit_vars if item is not None]):
                raise ValueError("exit_on_fail is for both inv and dev. exit_on_inv_fail and exit_on_dev_fail should not conflict")
            exit_on_inv_fail = exit_on_dev_fail = exit_on_fail
        elif exit_vars.count(None) == 2:
            exit_on_inv_fail = exit_on_dev_fail = True

        for idx in range(0, 2):
            inv_dev = self.get_inv_identifier(query_str, dev_type=dev_type, retry=retry_inv, completion=completion, silent=True if idx == 0 else silent, exit_on_fail=False if idx == 0 else exit_on_inv_fail)
            if not inv_dev:
                mon_dev: CacheDevice | None = self.get_dev_identifier(query_str, dev_type=dev_type, retry=retry_dev, completion=completion, silent=True, exit_on_fail=exit_on_dev_fail)
                if mon_dev:
                    query_str = mon_dev.serial  # If they provide an identifier only available in DevDB we use it to get the serial for the InvDB lookup
            else:
                mon_dev = self.get_dev_identifier(inv_dev.serial, dev_type=dev_type, retry=retry_dev, completion=completion, silent=True, exit_on_fail=exit_on_dev_fail)
                return CacheInvMonDevice(inv_dev, mon_dev)

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        retry: Optional[bool],
        completion: bool,
        silent: Optional[bool],
        exit_on_fail: Optional[bool],
    ) -> list[CacheSite]:
        ...  # pragma: no cover

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        completion: Literal[True]
    ) -> list[CacheSite]: ...  # pragma: no cover

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
    ) -> CacheSite: ...  # pragma: no cover

    @overload
    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        retry: Optional[bool],
        completion: Optional[bool],
        silent: Optional[bool],
        exit_on_fail: bool,
    ) -> CacheSite | None: ...  # pragma: no cover

    def get_site_identifier(
        self,
        query_str: str | Sequence[str],
        retry: Optional[bool] = True,
        completion: Optional[bool] = False,
        silent: Optional[bool] = False,
        exit_on_fail: Optional[bool] = True,
    ) -> CacheSite | List[CacheSite] | None:
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)


        if completion and query_str == "":
            return [CacheSite(s) for s in self.sites]

        match = []
        for _ in range(0, 2 if retry else 1):
            # Exact match
            if query_str == "":
                match = self.sites
            else:
                match += self.SiteDB.search(
                    (self.Q.name == query_str)
                )

            # try exact match by other fields
            if not match or completion:
                match += self.SiteDB.search(
                    (self.Q.id.test(lambda v: str(v) == query_str))
                    | (self.Q.zip == query_str)
                    | (self.Q.address == query_str)
                    | (self.Q.city == query_str)
                    | (self.Q.state == query_str)
                    | (self.Q.state.test(lambda v: v is not None and constants.state_abbrev_to_pretty.get(query_str.upper(), query_str).title() == v.title()))
                )

            # try case insensitive name
            if not match or completion:
                match += self.SiteDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                )
            # try case insensitve address match
            if not match or completion:
                match += self.SiteDB.search(
                    self.Q.address.test(lambda v: v is not None and v.lower().replace(" ", "") == query_str.lower().replace(" ", ""))
                )

            # try case insensitive name swapping _ and -
            if not match or completion:
                if "-" in query_str:
                    match += self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match += self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # try case insensitive name starts with
            if not match or completion:
                match += self.SiteDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # Last Chance try other fields case insensitive startswith provided value
            if not match or completion:
                match += self.SiteDB.search(
                    self.Q.zip.test(lambda v: v is not None and v.startswith(query_str))
                    | self.Q.city.test(lambda v: v is not None and v.lower().startswith(query_str.lower()))
                    | self.Q.state.test(lambda v: v is not None and v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: v is not None and v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: v is not None and " ".join(v.split(" ")[1:]).lower().startswith(query_str.lower()))
                )

            # err_console.print(f'\n{match=} {query_str=} {retry=} {completion=} {silent=}')  # DEBUG
            if retry and not match and not self.responses.site:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and self.sites and not silent:  # pragma: no cover requires tty
                    fuzz_match, fuzz_confidence = process.extract(query_str, [s["name"] for s in self.sites], limit=1)[0]
                    confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.SiteDB.search(self.Q.name == fuzz_match)
                if not match:
                    econsole.print(":arrows_clockwise: Updating [cyan]site[/] Cache")
                    self.check_fresh(refresh=True, site_db=True)
            if match:
                match = [CacheSite(s) for s in match]
                break

        if completion:
            return match

        if match:
            if len(match) > 1:  # pragma: no cover  Requires tty
                match = self.handle_multi_match(match, query_str=query_str, query_type="site",)

            return match[0]

        log.error(f"Unable to gather site info from provided identifier {query_str}", show=not silent)
        if retry:
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[List[constants.DeviceTypes] | constants.DeviceTypes],
        completion: bool,
    ) -> list[CacheGroup]: ...  # pragma: no cover

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[List[constants.DeviceTypes] | constants.DeviceTypes] = None,
        retry: Optional[bool] = True,
        silent: Optional[bool] = False,
    ) -> CacheGroup: ...  # pragma: no cover

    @overload
    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[List[constants.DeviceTypes] | constants.DeviceTypes],
        retry: Optional[bool],
        silent: Optional[bool],
        exit_on_fail: bool,
    ) -> CacheGroup | None: ...  # pragma: no cover

    def get_group_identifier(
        self,
        query_str: str,
        dev_type: Optional[list[constants.DeviceTypes] | constants.DeviceTypes] = None,
        retry: Optional[bool] = True,
        completion: Optional[bool] = False,
        silent: Optional[bool] = False,
        exit_on_fail: Optional[bool] = True,
    ) -> CacheGroup | list[CacheGroup] | None:
        """Allows Case insensitive group match"""
        retry = False if completion else retry

        if dev_type is not None:
            dev_type = utils.listify(dev_type)
            if "switch" in dev_type:
                dev_type = list(set(filter(lambda t: t != "switch", [*dev_type, "cx", "sw"])))

        for _ in range(0, 2):
            # TODO change all get_*_identifier functions to continue to look for matches when match is found when
            #       completion is True
            # Exact match
            match, all_match = [], []
            if query_str == "":
                match = self.groups
            else:
                match += self.GroupDB.search((self.Q.name == query_str))

            # case insensitive
            if not match or completion:
                this_match = self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())  # type: ignore
                )
                match = [*match, *[m for m in this_match if m not in match]]

            # case insensitive startswith
            if not match or completion:
                this_match = self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))  # type: ignore
                )
                match = [*match, *[m for m in this_match if m not in match]]

            # case insensitive ignore -_
            if not match or completion:
                if "_" in query_str or "-" in query_str:
                    this_match = self.GroupDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")  # type: ignore
                        )
                    )
                    match = [*match, *[m for m in this_match if m not in match]]

            # case insensitive startswith ignore - _
            if not match or completion:
                this_match = self.GroupDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().strip("-_").startswith(query_str.lower().strip("-_"))  # type: ignore
                    )
                )
                match = [*match, *[m for m in this_match if m not in match]]

            if match and dev_type:
                all_match: List[Document] = match.copy()
                match = [d for d in all_match if bool([t for t in d.get("allowed_types", []) if t in dev_type])]

            if not match and retry and self.responses.group is None:
                dev_type_sfx = "" if not dev_type else f" [grey42 italic](Device Type: {utils.unlistify(dev_type)})[/]"
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found for[/] [cyan]{query_str}[/]{dev_type_sfx}.")
                if FUZZ and self.groups and not silent:    # pragma: no cover  Requires tty
                    if dev_type:
                        fuzz_match, fuzz_confidence = process.extract(query_str, [g["name"] for g in self.groups if "name" in g and bool([t for t in g["allowed_types"] if t in dev_type])], limit=1)[0]
                    else:
                        fuzz_match, fuzz_confidence = process.extract(query_str, [g["name"] for g in self.groups], limit=1)[0]
                    confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.GroupDB.search(self.Q.name == fuzz_match)
                if not match:
                    econsole.print(":arrows_clockwise: Updating [cyan]group[/] Cache")
                    self.check_fresh(refresh=True, group_db=True)
                _ += 1
            if match:
                match = [CacheGroup(g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:  # pragma: no cover  Requires tty
                match = self.handle_multi_match(match, query_str=query_str, query_type="group",)

            return match[0]

        log.error(f"Unable to gather group data from provided identifier {query_str}", show=not silent)
        if retry:
            if all_match:
                _dev_type_str = escape(str(utils.unlistify(dev_type)))
                all_match_msg = utils.summarize_list([f"{m['name']}|allowed types: {m['allowed_types']}" for m in all_match], pad=0)
                log.error(
                    f"The Following groups matched {all_match_msg} excluded as group not configured for any of {_dev_type_str}",
                    show=True,
                )

            if exit_on_fail:
                valid_groups = utils.summarize_list(self.group_names, max=50)
                econsole.print(f":warning:  [cyan]{query_str}[/] appears to be [red]invalid[/]")
                econsole.print(f"Valid Groups:\n{valid_groups}")
                raise typer.Exit(1)
            else:
                return


    @overload
    def get_template_identifier(self, query_str: str, completion: Literal[True]) -> list[CacheTemplate]: ...  # pragma: no cover

    def get_template_identifier(
        self,
        query_str: str,
        group: str | List[str] = None,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheTemplate | List[CacheTemplate]:
        """Allows case insensitive template match by template name"""
        retry = False if completion else retry
        if not query_str and completion:
            return [CacheTemplate(t) for t in self.templates]

        match, all_match = None, None
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

            if match and group:
                all_match: List[Document] = match.copy()
                match = [d for d in all_match if d.get("group", "") == group]

            if retry and not match and self.responses.template is None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ and not silent:  # pragma: no cover  Requires tty
                    match = self.fuzz_lookup(query_str, self.TemplateDB, group=group)
                if not match:
                    econsole.print(":arrows_clockwise: Updating template Cache")
                    self.check_fresh(refresh=True, template_db=True)
            if match:
                match = [CacheTemplate(tmplt) for tmplt in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:  # pragma: no cover  Requires tty
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="template",
                )

            return match[0]

        log.error(f"Unable to gather template from provided identifier {query_str}", show=not silent, log=silent)
        if retry:
            if all_match:
                first_five = [f"[bright_green]{m['name']}[/] from group [cyan]{m['group']}[/]" for m in all_match[0:5]]
                all_match_msg = f"{', '.join(first_five)}{', ...' if len(all_match) > 5 else ''}"
                log.error(
                    f"The Following templates matched: {all_match_msg}... [red]excluded[/] as they are not in [cyan]{group}[/] group ",
                    show=True,
                )
            raise typer.Exit(1)

    @overload
    def get_client_identifier(self, query_str: str, completion: Literal[False]) -> CacheClient: ...  # pragma: no cover

    @overload
    def get_client_identifier(self, query_str: str, exit_on_fail: bool = Literal[True]) -> CacheClient: ...  # pragma: no cover

    def get_client_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        exit_on_fail: bool = False,
        silent: bool = False,
    ) -> CacheClient | List[CacheClient]:
        """Search for Client in DB matching on name, ip or mac

        Allows partial and case insensitive match
        """
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        if completion and not query_str.strip():
            return [CacheClient(c) for c in self.clients]

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
                    | self.Q.ip.test(lambda v: v and v.lower().startswith(query_str.lower()))
                )
                if not match:
                    qry_mac = utils.Mac(query_str)
                    qry_mac_fuzzy = utils.Mac(query_str, fuzzy=True)
                    if qry_mac or len(qry_mac) == len(qry_mac_fuzzy):
                        match = self.ClientDB.search(
                            self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str, fuzzy=completion).cols.lower()))
                        )

            # no match found try fuzzy match (typos) and initiate cache update
            if retry and not match and self.responses.client is None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and not silent:
                    match = self.fuzz_lookup(query_str, self.ClientDB)
                if not match:  # on demand update only for WLAN as roaming and kick only applies to WLAN currently
                    econsole.print(":arrows_clockwise: Updating [cyan]client[/] Cache")
                    api.session.request(self.refresh_client_db, "wireless")

            if match:
                match = [CacheClient(c) for c in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:  # pragma: no cover  Requires tty # user selects which device if multiple matches returned
                match = self.handle_multi_match(match, query_str=query_str, query_type="client")

            return match[0]

        if retry:
            log.error(f"Unable to gather client info from provided identifier {query_str}", show=not silent)
            if exit_on_fail:
                raise typer.Exit(1)


    def get_audit_log_identifier(self, query: str) -> str:
        if "audit_trail" in query:
            return query

        try:
            match = self.LogDB.search(self.Q.id == int(query))
            if not match:
                log.warning(f"\nUnable to gather log id from short index query [cyan]{query}[/]", show=True)
                econsole.print("Short log_id aliases are built each time [cyan]show logs[/] / [cyan]show audit logs[/]... is ran.")
                econsole.print("  repeat the command without specifying the log_id to populate the cache.")
                econsole.print("  You can verify the cache by running [dim italic](hidden command)[/] [cyan]show cache logs[/]")
                raise typer.Exit(1)
            else:
                return match[-1]["long_id"]

        except ValueError as e:
            econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]{e.__class__.__name__}[/]:  Expecting an intiger for log_id. '{query}' does not appear to be an integer.")
            raise typer.Exit(1)

    def get_event_log_identifier(self, query: str) -> dict:
        """Get event log details based on identifier.

        Args:
            query (str): The short event log id, generated anytime show logs is ran for any events
                that have details.

        Raises:
            typer.Exit: If unable to find id, or the id is not a valid type

        Returns:
            dict: Dictionary containing event log details.
        """
        try:
            match = self.EventDB.search(self.Q.id == str(query))
            if not match:
                log.warning(f"Unable to gather event details from short index query {query}", show=True)
                print("Short event_id aliases are built each time [cyan]show logs[/] is ran.")
                print("  You can verify the cache by running [dim italic](hidden command)[/] [cyan]show cache events[/]")
                print("  run [cyan]show logs [OPTIONS][/] then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1]["details"]

        except ValueError as e:
            log.error(f"Exception in get_event_identifier {e.__class__.__name__}", show=True)
            raise typer.Exit(1)

    @overload
    def get_mpsk_network_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = True,
        silent: bool = False,
    ) -> list[CacheMpskNetwork]: ...  # pragma: no cover

    @overload
    def get_mpsk_network_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheMpskNetwork: ...  # pragma: no cover

    def get_mpsk_network_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheMpskNetwork | List[CacheMpskNetwork]:
        """Allows Case insensitive ssid match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            if query_str == "":
                match = self.mpsk_networks
            else:
                match = self.MpskNetDB.search((self.Q.name == query_str))

            # case insensitive
            if not match:
                match = self.MpskNetDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match:
                match = self.MpskNetDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match:
                match = self.MpskNetDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().replace("_", "-") == query_str.lower().replace("_", "-")
                    )
                )

            # case insensitive startswith search for mspk id
            if not match:
                match = self.MpskNetDB.search(
                    self.Q.id.test(
                        lambda v: v.lower().startswith(query_str.lower())
                    )
                )

            if not match and retry and self.responses.mpsk_network is None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and self.mpsk_networks and not silent:  # pragma: no cover requires tty
                    match = self.fuzz_lookup(query_str, self.MpskNetDB)
                if not match:
                    econsole.print(":arrows_clockwise: Updating [cyan]MPSK[/] Cache")
                    api.session.request(self.refresh_mpsk_networks_db)
                _ += 1
            if match:
                match = [CacheMpskNetwork(g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:  # pragma: no cover requires tty
                match = self.handle_multi_match(match, query_str=query_str, query_type="mpsk",)

            return match[0]

        log.error(f"Central API CLI Cache unable to gather MPSK Network data from provided identifier {query_str}", show=not silent or _ == 1)
        if retry:
            valid_mpsk = "\n".join([f'[cyan]{m["name"]}[/]' for m in self.mpsk_networks])
            econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Valid MPSK Networks[/]:\n--\n{valid_mpsk}\n--\n")
            raise typer.Exit(1)


    @staticmethod
    def _handle_sub_multi_match(match: list[CacheSub], *, end_date: dt.datetime, best_match: bool = False, all_match: bool = False) -> list[CacheSub]:
        if len(match) > 1 and end_date:
            end_date_day = end_date.combine(end_date, dt.time.min)  # subscription expires on the day provided
            match = [m for m in match if dt.datetime.combine(pendulum.from_timestamp(m.end_date), dt.time.min) == end_date_day]
            if len(match) > 1 and end_date_day != end_date:  # if still too many matches check for exact match if they provided time info.
                match = [m for m in match if pendulum.from_timestamp(m.end_date) == end_date]

        if len(match) > 1:
            valid_match = [m for m in match if m.valid]  # valid means it is not expired and has subscriptions available
            match = valid_match or match

        if best_match or all_match:
            sorted_match = sorted(match, key=lambda m: (m.end_date, m.available), reverse=True)
            match = sorted_match if all_match else [sorted_match[0]]

        return match

    # TODO make this a wrapper for other specific get_portal_identifier.... calls
    @lru_cache
    def get_name_id_identifier(
        self,
        cache_name: Literal["dev", "site", "sub", "template", "group", "label", "mpsk_network", "mpsk", "portal"],
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        end_date: dt.datetime = None,
        best_match: bool = False,
        all_match: bool = False,
    ) -> CachePortal | List[CachePortal] | CacheLabel | List[CacheLabel] | CacheSub | List[CacheSub]:
        """Fetch items from cache based on query

        This is a common identifier lookup function for all stored types that use name and id as potential match fields.

        DEV NOTE appears only to be used by portal and subscription currently

        Args:
            cache_name (Literal['dev', 'site', 'sub', 'template', 'group', 'label', 'mpsk_network', 'mpsk', 'portal']): The cache to search
            query_str (str): The query string used to search the cache for a match
            retry (bool, optional): Refresh the cache via API and retry if no match is found. Defaults to True.
            completion (bool, optional): Indicates function is being called for CLI completion... effectively the equiv of retry=False, Silent=True. Defaults to False.
            silent (bool, optional): Set to True to squelch out all messaging normmaly displayed when no match is found, and retry is initiated. Defaults to False.
            end_date (dt.datetime, optional): Specific to 'sub' cache.  Provide End Date to further narrow search in the event of multiple subscription matches. Defaults to None.
            best_match (bool, optional): Specific to 'sub' cache.  Set True to return the best match in the event of multiple matches.
                Best match is the valid match with the most time remaining on the subscription. Defaults to False (user is prompted to select one of the matches).
            all_match (bool, optional): Sepcific to 'sub' cache.  Return all matches in the event of multiple matches. Defaults to False.

        Raises:
            typer.Exit: Terminates program if no match is found.

        Returns:
            CachePortal | List[CachePortal] | CacheLabel | List[CacheLabel] | CacheSub | List[CacheSub]: The Cache object associated with the provided cache_name.
        """
        cache_details = CacheDetails(self)
        this: CacheAttributes = getattr(cache_details, cache_name)
        db_all = this.db.all()
        db = this.db
        name_to_model = {
            "portal": CachePortal,
            "label": CacheLabel,
            "mpsk_network": CacheMpskNetwork,
            "sub": CacheSub
        }
        cache_updated = False
        Model = name_to_model.get(cache_name, CentralObject)
        retry = False if completion else retry

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)

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
                            lambda v: v.lower().replace("_", "-") == query_str.lower().replace("_", "-")
                        )
                    )

            # case insensitive startswith search for id
            if not match:
                match = db.search(
                    self.Q.id.test(
                        lambda v: str(v).lower().startswith(query_str.lower())
                    )
                )

            if not match and retry and not cache_updated:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and db_all and not silent:  # pragma: no cover requires tty
                    match = self.fuzz_lookup(query_str, db=db)
                if not match:
                    econsole.print(f":arrows_clockwise: Updating [cyan]{cache_name}[/] Cache")
                    api.session.request(this.cache_update_func)
                    cache_updated = True
                _ += 1
            if match:
                match = [Model(m) for m in match]
                break

        if completion:
            return match or []

        if match:
            if cache_name == "sub" and len(match) > 1:
                match = self._handle_sub_multi_match(match, end_date=end_date, best_match=best_match, all_match=all_match)  # pragma: no cover
                if all_match:
                    return match

            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type=this.name,)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather {cache_name} data from provided identifier {query_str}", show=True)
            valid = "\n".join([f'[cyan]{m["name"]}[/]' for m in db_all])
            econsole.print(f":warning:  [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Valid Names[/]:\n--\n{valid}\n--\n")
            raise typer.Exit(1)
        else:
            log.error(
                f"Central API CLI Cache unable to gather {cache_name} data from provided identifier {query_str}", show=not silent
            )


    @lru_cache
    def get_sub_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        end_date: dt.datetime = None,
        best_match: bool = False,
        all_match: bool = False,
    ) -> CacheSub | list[CacheSub] | None:
        """Fetch items from subscription cache based on query

        Args:
            query_str (str): The query string used to search the cache for a match
            retry (bool, optional): Refresh the cache via API and retry if no match is found. Defaults to True.
            completion (bool, optional): Indicates function is being called for CLI completion... effectively the equiv of retry=False, Silent=True. Defaults to False.
            silent (bool, optional): Set to True to squelch out all messaging normmaly displayed when no match is found, and retry is initiated. Defaults to False.
            end_date (dt.datetime, optional): Specific to 'sub' cache.  Provide End Date to further narrow search in the event of multiple subscription matches. Defaults to None.
            best_match (bool, optional): Specific to 'sub' cache.  Set True to return the best match in the event of multiple matches.
                Best match is the valid match with the most time remaining on the subscription. Defaults to False (user is prompted to select one of the matches).
            all_match (bool, optional): Sepcific to 'sub' cache.  Return all matches in the event of multiple matches. Defaults to False.

        Raises:
            typer.Exit: Terminates program if no match is found.

        Returns:
            CachePortal | List[CachePortal] | CacheLabel | List[CacheLabel] | CacheSub | List[CacheSub]: The Cache object associated with the provided cache_name.
        """
        cache_updated = False
        retry = False if completion else retry
        db: Table = self.SubDB

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)

        for _ in range(0, 2):
            if query_str == "":
                match = [CacheSub(s) for s in db.all()]
            else:
                match = db.search(
                    (self.Q.name == query_str)
                    | (self.Q.key == query_str)
                    | (self.Q.id == query_str)
                )

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
                            lambda v: v.lower().replace("_", "-") == query_str.lower().replace("_", "-")
                        )
                    )

            # case insensitive startswith search for id
            if not match:
                match = db.search(
                    self.Q.id.test(
                        lambda v: str(v).lower().startswith(query_str.lower())
                    )
                    | self.Q.key.test(
                        lambda v: str(v).lower().startswith(query_str.lower())
                    )
                )

            if not match and retry and not cache_updated:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and db.all() and not silent:  # pragma: no cover requires tty
                    match = self.fuzz_lookup(query_str, db=db)
                if not match:
                    econsole.print(":arrows_clockwise: Updating [cyan]Subscription[/] Cache")
                    api.session.request(self.refresh_sub_db)
                    cache_updated = True
                _ += 1
            if match:
                match = [CacheSub(m) for m in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self._handle_sub_multi_match(match, end_date=end_date, best_match=best_match, all_match=all_match)
                if all_match:
                    return match

            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="sub",)  # pragma: no cover

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather Subscription data from provided identifier {query_str}", show=True)
            valid = "\n".join([sub.summary_text for sub in self.subscriptions])
            econsole.print(f":warning:  [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Available Subscriptions[/]:\n--\n{valid}\n--\n")
            raise typer.Exit(1)
        else:
            log.error(
                f"Central API CLI Cache unable to gather Subscription data from provided identifier {query_str}", show=not silent
            )

    @overload
    def get_label_identifier(
        self,
        query_str: str,
    ) -> CacheLabel: ...  # pragma: no cover

    @overload
    def get_label_identifier(
        self,
        query_str: str,
        retry: Optional[bool],
        completion: Optional[Literal[False]],
        silent: Optional[bool],
    ) -> CacheLabel: ...  # pragma: no cover

    @overload
    def get_label_identifier(
        self,
        query_str: str,
        retry: Optional[bool],
        completion: Literal[True],
        silent: Optional[bool],
    ) -> list[CacheLabel]: ...  # pragma: no cover

    def get_label_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CacheLabel | list[CacheLabel]:
        return self.get_name_id_identifier("label", query_str, retry=retry, completion=completion, silent=silent)

    def get_portal_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CachePortal | list[CachePortal]:
        return self.get_name_id_identifier("portal", query_str, retry=retry, completion=completion, silent=silent)

class CacheAttributes:
    def __init__(self, name: Literal["dev", "site", "template", "group", "label", "portal", "mpsk", "mpsk_network"], db: Table, cache_update_func: Callable) -> None:
        self.name = name
        self.db = db
        self.cache_update_func = cache_update_func

class CacheDetails:
    def __init__(self, cache = Cache):
        self.dev = CacheAttributes(name="dev", db=cache.DevDB, cache_update_func=cache.refresh_dev_db)
        self.site = CacheAttributes(name="site", db=cache.SiteDB, cache_update_func=cache.refresh_site_db)
        self.group = CacheAttributes(name="group", db=cache.GroupDB, cache_update_func=cache.refresh_group_db)
        self.label = CacheAttributes(name="label", db=cache.LabelDB, cache_update_func=cache.refresh_label_db)
        self.portal = CacheAttributes(name="portal", db=cache.PortalDB, cache_update_func=cache.refresh_portal_db)
        self.mpsk = CacheAttributes(name="mpsk", db=cache.MpskDB, cache_update_func=cache.refresh_mpsk_db)
        self.mpsk_network = CacheAttributes(name="mpsk_network", db=cache.MpskNetDB, cache_update_func=cache.refresh_mpsk_db)
        self.sub = CacheAttributes(name="sub", db=cache.SubDB, cache_update_func=cache.refresh_sub_db)
