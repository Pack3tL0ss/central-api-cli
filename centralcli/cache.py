#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Literal, Optional, Sequence, Set, Tuple, Union

import typer
from rich import print
from rich.console import Console
from tinydb import Query, TinyDB
from tinydb.table import Document
from yarl import URL

from centralcli import CentralApi, Response, config, constants, log, models, render, utils
from centralcli.response import CombinedResponse


if TYPE_CHECKING:
    from tinydb.table import Table
    from .config import Config
    from .typedefs import PortalAuthTypes, SiteData

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
econsole = Console(stderr=True)
console = Console()
TinyDB.default_table_name = "devices"

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


CacheTable = Literal["dev", "inv", "site", "group", "template", "label", "license", "client", "log", "event", "hook_config", "hook_data", "mpsk", "portal"]

class CentralObject:
    def __init__(
        self,
        db: Literal["dev", "site", "template", "group", "label", "mpsk", "portal"],
        data: Document | Dict[str, Any] | List[Document | Dict[str, Any]],
    ) -> list | Dict[str, Any]:
        self.is_dev, self.is_template, self.is_group, self.is_site, self.is_label, self.is_mpsk, self.is_portal = False, False, False, False, False, False, False
        data: Dict | List[dict] = None if not data else data
        setattr(self, f"is_{db}", True)
        self.cache = db
        self.doc_id = None if not hasattr(data, "doc_id") else data.doc_id

        if isinstance(data, list):
            if len(data) > 1:
                raise ValueError(f"CentralObject expects a single item. Got list of {len(data)}")
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
                *[a for a in [self.city, self.state, self.zipcode] if a]
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

    def __bool__(self):
        return True if self.status == "Up" else False

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
    def doc_id(self, doc_id: int | None) -> int | None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Device[/]:[cyan]{self.name}[/]|({utils.color(self.status, "green_yellow")})'


class CacheInvDevice(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('dev', data)
        self.serial: str = data["serial"]
        self.mac: str = data["mac"]
        self.type: str = data["type"]
        self.model: str = data["model"]
        self.sku: str = data["sku"]
        self.services: str | None = data["services"]
        self.subscription_key: str = data.get("subscription_key")
        self.subscription_expires: int | float = data.get("subscription_expires")

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
    def doc_id(self, doc_id: int | None) -> int | None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Inventory Device[/]:[bright_green]{self.serial}[/]|[cyan]{self.mac}[/]'


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
    def doc_id(self, doc_id: int | None) -> int | None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Group[/]:[cyan]{self.name}[/]|({utils.color(self.allowed_types, "green_yellow")})'


class CacheSite(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
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
    def doc_id(self, doc_id: int | None) -> int | None:
        self._doc_id = doc_id


    def __rich__(self) -> str:
        return f'[bright_green]Group[/]:[cyan]{self.name}[/]|({utils.color(self.allowed_types, "green_yellow")})'


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
    def doc_id(self, doc_id: int | None) -> None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Label[/]:[bright_green]{self.name}[/]|[cyan]{self.id}[/]'


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
        super().__init__('group', data)
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

    def get_group(self) -> CacheGroup:
        if self.cache is None:
            return None
        return self.cache.get_group_identifier(self.group)

    def get_site(self) -> CacheSite:
        if self.cache is None:
            return None
        return self.cache.get_site_identifier(self.site)

    @doc_id.setter
    def doc_id(self, doc_id: int | None) -> int | None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]Client[/]:[cyan]{self.name}[/]|({utils.color([self.type, self.ip, self.mac, self.connected_name],  "green_yellow", sep="|")}|s:[green_yellow]{self.site})[/]'

    @property
    def help_text(self) -> str:
        return render.rich_capture(
            f"[bright_green]{self.name}[/]|[cyan]{self.mac}[/]|[bright_green]{self.ip}[/]|[cyan]{f's:{self.site}' if self.site else f'g:{self.group}'}[/]|[dark_olive_green2]{self.connected_name}[/]"
        )


class CacheMpskNetwork(CentralObject):
    db: Table | None = None

    def __init__(self, data: Document | Dict[str, Any]) -> None:
        self.data = data
        super().__init__('mpsk', data)
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
    def doc_id(self, doc_id: int | None) -> int | None:
        self._doc_id = doc_id

    def __rich__(self) -> str:
        return f'[bright_green]MPSK Network[/]:[cyan]{self.id}[/]|[green_yellow]{self.name})[/]'


class CacheResponses:
    def __init__(
        self,
        dev: CombinedResponse = None,
        inv: Response = None,
        site: Response = None,
        template: Response = None,
        group: Response = None,
        label: Response = None,
        mpsk: Response = None,
        portal: Response = None,
        license: Response = None,
        client: Response = None,
        guest: Response = None,
    ) -> None:
        self._dev = dev
        self._inv = inv
        self._site = site
        self._template = template
        self._group = group
        self._label = label
        self._mpsk = mpsk
        self._portal = portal
        self._license = license
        self._client = client
        self._guest = guest

    def update_rl(self, resp: Response | CombinedResponse | None) -> Response | CombinedResponse | None:
        """Returns provided Response object with the RateLimit info from the most recent API call.
        """
        if resp is None:
            return

        _last_rl = sorted([r.rl for r in [self._dev, self._inv, self._site, self._template, self._group, self._label, self._mpsk, self._portal, self._license, self._client, self._guest] if r is not None])  # , key=lambda k: k.remain_day)
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


class Cache:
    config: Config = None

    @classmethod
    def set_config(cls, config: Config) -> None:
        cls.config = config

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
            self.GuestDB: Table = self.DevDB.table("guest")  # Only updated when show guests is ran or as needed
            self._tables: List[Table] = [self.DevDB, self.InvDB, self.SiteDB, self.GroupDB, self.TemplateDB, self.LabelDB, self.LicenseDB, self.ClientDB]
            self.Q = Query()
            if data:
                raise ValueError("This should not have happened.  Passing data directly to cache object was deprecated.  Please open issue on GitHub. I apparently missed something.")
                # TODO should be good, once soaked to be sure remove data from constructor and this conditional
            if central:
                self.check_fresh(refresh)

    def __call__(self, refresh=False) -> None:
        if refresh:
            self.check_fresh(refresh)

    # def __iter__(self) -> Iterator[Tuple[str, List[Document]]]:
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
                license.endswith("alletra"),
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

    @property
    def all_tables(self) -> Iterator[Table, None, None]:
        for table in self.DevDB.tables():
            yield self.DevDB.table(table)

    @property
    def key_tables(self) -> Iterator[Table, None, None]:
        for table in self._tables:
            yield table

    @property
    def devices(self) -> list:
        return self.DevDB.all()

    @property
    def device_types(self) -> Set[str]:
        db = self.InvDB if self.InvDB else self.DevDB
        return set([d["type"] for d in db.all()])

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
    def sites(self) -> list:
        return self.SiteDB.all()

    @property
    def sites_by_id(self) -> list:
        return {s["id"]: s for s in self.sites}

    @property
    def groups(self) -> list:
        return self.GroupDB.all()

    @property
    def groups_by_name(self) -> Dict[str: CacheGroup]:
        return {g["name"]: CacheGroup(g) for g in self.groups}

    @property
    def labels(self) -> list:
        return self.LabelDB.all()

    @property
    def labels_by_name(self) -> Dict[str: CacheLabel]:
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
    def mpsk(self) -> list:
        return self.MpskDB.all()

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
    def templates_by_name_group(self) -> list:
        return {
            f'{template["name"]}_{template["group"]}': template
            for template in self.TemplateDB.all()
        }

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
        # if remove:
        #     if len(remove) != expected:
        #         log.warning(
        #             f'{db_str}DB cache update_db provided {expected} records to remove but found only {len(remove)} matching records.  This can be normal if cache was outdated.{elapsed_msg}'
        #         )

        #     expected = len(remove)

        msg = f"remove {expected} records" if remove else f"add/update {expected} records"
        update_ok = True if expected == resp_cnt else False

        if update_ok:
            log.info(f'{db_str} cache update SUCCESS: {msg}{elapsed_msg}')
            return True
        else:
            log.error(f'{db_str} cache update ERROR:  Attempt to {msg} appears to have failed.  Expecting {expected} doc_ids TinyDB returned {resp_cnt}', show=True, caption=True, log=True)
            log.error(f'{db_str} update response: {response}{elapsed_msg}')
            return False

    def get_devices_with_inventory(self, no_refresh: bool = False, inv_db: bool = None, dev_db: bool = None, dev_type: constants.GenericDeviceTypes = None, status: constants.DeviceStatus = None,) -> List[Response] | Response:
        """Returns List of Response objects with data from Inventory and Monitoring

        Args:
            no_refresh (bool, optional): Used currently cached data, skip refresh of cache.
                Refresh will only occur if cache was not updated during this session.
                Setting no_refresh to True means it will not occur regardless.
                Defaults to False.
            inv_db (bool, optional): Update inventory cache. Defaults to None.
            dev_db (bool, optional): Update device (monitoring) cache. Defaults to None.
            dev_type (Literal['ap', 'gw', 'switch'], optional): Filter devices by type:
                Valid Types: 'ap', 'gw', 'switch'.  'cx' and 'sw' also accepted, both will result in 'switch' which includes both types.
                Defalts to None (no Filter/All device types).
            status (Literal 'up', 'down', optional): Filter results by status.
                Inventory only devices (have never checked in, so lack status) are retained.
                Defaults to None.

        Returns:
            List[Response]: Response objects where output is list of dicts with
                            data from Inventory and Monitoring.
        """
        if not no_refresh:
            res = self.check_fresh(dev_db=dev_db or self.responses.dev is None, inv_db=inv_db or self.responses.inv is None, dev_type=dev_type)
        else:
            res = [self.responses.dev or Response()]

        _inv_by_ser = self.inventory_by_serial if not self.responses.inv else {d["serial"]: d for d in self.responses.inv.output}
        if self.responses.dev:
            _dev_by_ser = {d["serial"]: d for d in self.responses.dev.output}  # Need to use the resp value not what was just stored in cache (self.devices_by_serial) as we don't store all fields
        else:
            _dev_by_ser = self.devices_by_serial  # TODO should be no case to ever hit this.

        if dev_type:
            _dev_types = [dev_type] if dev_type != "switch" else ["cx", "sw", "mas"]
            _dev_by_ser = {serial: _dev_by_ser[serial] for serial in _dev_by_ser if _dev_by_ser[serial]["type"] in _dev_types}
            _inv_by_ser = {serial: _inv_by_ser[serial] for serial in _inv_by_ser if _inv_by_ser[serial]["type"] in _dev_types}


        if status:
            _dev_by_ser = {serial: _dev_by_ser[serial] for serial in _dev_by_ser if _dev_by_ser[serial]["status"] == status.capitalize()}

        _all_serials = set([*_inv_by_ser.keys(), *_dev_by_ser.keys()])
        # dev_common_keys = list(filter(lambda k: k != "macaddr", set.intersection(*map(set, _dev_by_ser.values()))))
        combined = [
            {
                # **{k: None for k in dev_common_keys},
                **_inv_by_ser.get(serial, {}),
                **_dev_by_ser.get(serial, {})
            } for serial in _all_serials
        ]
        # TODO this may be an issue if check_fresh has a failure, don't think it returns Response object
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
    def account_completion(ctx: typer.Context, args: List[str], incomplete: str):
        for a in config.defined_accounts:
            if a.lower().startswith(incomplete.lower()):
                yield a

    def method_test_completion(self, incomplete: str, args: List[str] = []):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
            econsole.print(":warning:  Invalid config")
            return

        kwds = ["group", "mac", "serial"]
        out = []

        if not args:  # HACK click 8.x work-around now pinned at click 7.2 until resolved
            args = [v for k, v in ctx.params.items() if v and k != "account"]  # TODO ensure k is last item when v = incomplete
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
        args: List[str] = None
    ):
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

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
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are switches (AOS-SW or CX)

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
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are of specific switch type (cx by default)

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
    ) -> Iterator[Tuple[str, str]]:
        for match in self.dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="cx"):
            yield match

    def dev_sw_completion(
            self,
            incomplete: str,
            args: List[str] = [],
    ) -> Iterator[Tuple[str, str]]:
        for match in self.dev_switch_by_type_completion(incomplete=incomplete, args=args, dev_type="sw"):
            yield match

    def dev_ap_gw_sw_completion(
        self,
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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
            econsole.print(":warning:  Invalid config")
            return

        match = self.get_mpsk_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or ctx.params.values()  # HACK as args stopped working / seems to be passing args typer 0.10.0 / click 7.1.2
        if match:
            # remove items that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if m.name.startswith(incomplete):
                    out += [tuple([m.name, m.id])]
                elif m.name.lower().startswith(incomplete.lower()):
                    out += [tuple([m.name, m.id])]
                elif m.id.startswith(incomplete):
                    out += [tuple([m.id, m.name])]
                else:
                    out += [tuple([m.name, f"{m.help_text} FS match".lstrip()])]  # failsafe, shouldn't hit

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
            econsole.print(":warning:  Invalid config")
            return

        match = self.get_name_id_identifier(
            "portal",
            incomplete,
            completion=True,
        )
        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        if match:
            # remove items that are already on the command line
            match = [m for m in match if m.name not in args]
            for m in sorted(match, key=lambda i: i.name):
                if m.name.startswith(incomplete):
                    out += [tuple([m.name, m.help_text])]
                elif m.id.startswith(incomplete):
                    out += [tuple([m.id, m.help_text])]
                else:
                    out += [tuple([m.name, m.help_text])]  # failsafe, shouldn't hit

        for m in out:
            yield m

    def get_guest_identifier(
        self,
        query_str: str,
        portal_id: str | List[str] = None,
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

            # startswith - phone has all non digit characters stripped
            if not match:
                match = self.GuestDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.email.test(lambda v: v and v.lower().startswith(query_str.lower()))
                    | self.Q.id.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.phone.test(lambda v: v and "".join([d for d in v if d.isdigit()]).startswith("".join([d for d in query_str if d.isdigit()])))
                )

            # phone with only last 10 digits (strip country code)
            if not match:
                match = self.GuestDB.search(
                    self.Q.phone.test(lambda v: v and "".join([d for d in v if d.isdigit()][::-1][0:10][::-1]).startswith("".join([d for d in query_str if d.isdigit()][::-1][0:10][::-1])))
                )

            if match and portal_id:
                all_match: List[Document] = match.copy()
                match = [d for d in all_match if d.get("portal_id", "") == portal_id]

            if retry and not match and self.responses.guest is None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [g["name"] for g in self.guests if portal_id is None or g["portal_id"] == portal_id], limit=1)[0]
                    confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.GuestDB.search(self.Q.name == fuzz_match)
                if not match:
                    if not portal_id:
                        econsole.print(f"[red]:warning:[/]  Unable to gather guest from provided identifier {query_str}.  Use [cyan]cencli show guest <PORTAL>[/] to update cache.")
                        raise typer.Exit(1)
                    econsole.print(":arrows_clockwise: Updating guest Cache")
                    self.central.request(self.refresh_guest_db, portal_id=portal_id)
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

        elif retry:
            log.error(f"Unable to gather guest from provided identifier {query_str}", show=not silent, log=silent)
            if all_match:
                first_five = [f"[bright_green]{m['name']}[/]" for m in all_match[0:5]]
                all_match_msg = f"{', '.join(first_five)}{', ...' if len(all_match) > 5 else ''}"
                log.error(
                    f"The Following guests matched: {all_match_msg} [red]Excluded[/] as they are not associated with portal id [cyan]{portal_id}[/] group ",
                    show=True,
                )
            raise typer.Exit(1)
        else:
            if not completion and not silent:
                log.warning(f"Unable to gather guest from provided identifier {query_str}", show=False)

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
                if m.name.startswith(incomplete) and m.name not in args:
                    out += [tuple([m.name, m.help_text])]
                elif m.email.startswith(incomplete) and m.email not in args:
                    out += [tuple([m.email, m.help_text])]
                elif m.phone.startswith(incomplete) and m.phone not in args:
                    out += [tuple([m.phone, m.help_text])]
                elif m.id.startswith(incomplete) and m.id not in args:
                    out += [tuple([m.id, m.help_text])]
                else:
                    out += [tuple([m.name, m.help_text])]  # failsafe, shouldn't hit

        for m in out:
            yield m


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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        if not args:  # HACK resolves click 8.x issue now pinned to 7.2 until fixed upstream
            args = [k for k, v in ctx.params.items() if v and k[:2] not in ["kw", "va"]]
            args += [v for k, v in ctx.params.items() if v and k[:2] in ["kw", "va"]]

        if args and args[-1].lower() == "group":
            out = [m for m in self.group_completion(incomplete, args)]
            for m in out:
                yield m

        elif args and args[-1].lower() == "site":
            out = [m for m in self.site_completion(ctx, incomplete, args)]
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
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument where only APs are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        dev_types = ["ap"]
        match: List[CacheDevice] = self.get_dev_identifier(incomplete, dev_type=dev_types, completion=True)

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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
    ) -> Iterator[Tuple[str, str]]:
        """Device completion for returning matches that are either switch or AP

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI.

        Yields:
            Iterator[Tuple[str, str]]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match: List[CacheDevice] = self.get_dev_identifier(incomplete, dev_type=["switch", "ap"], completion=True)

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
    ) -> Iterator[Tuple[str, str]]:
        """Device completion that returns only ap and gw.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Yields Tuple with completion and help text, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
    ) -> Iterator[Tuple[str, str]]:
        """Device completion that returns only switches and gateways.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
    ) -> Iterator[Tuple[str, str]]:
        """Completion for device idens where only gateways are valid.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match = self.get_dev_identifier(incomplete, dev_type="gw", completion=True)

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m[0], m[1]

    # FIXME not completing partial serial number is zsh get_dev_completion appears to return as expected
    # works in BASH and powershell
    def _group_dev_completion(
        self,
        incomplete: str,
        ctx: typer.Context = None,
        dev_type: constants.LibAllDevTypes | List[constants.LibAllDevTypes] = None,
        conductor_only: bool = False,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument that can be either group or device.

        Args:
            ctx (typer.Context): The click/typer Context.
            incomplete (str): The last partial or full command before completion invoked.
            dev_type: (str, optional): One of "ap", "cx", "sw", "switch", or "gw"
                where "switch" is both switch types.  Defaults to None (all device types)
            conductor_only (bool, optional): If there are multiple matches (stack) return only the conductor as a match.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        # Add cencli as option to show and update config commands (update not implememnted yet)
        utils.listify(dev_type)
        out = []
        if args:
            if " ".join(args).lower() == "show config" and "cencli".lower().startswith(incomplete):
                out += [("cencli", "show cencli configuration")]
            elif " ".join(args).lower() == "update config" and "cencli".lower().startswith(incomplete):
                out += [("cencli", "update cencli configuration")]
        elif ctx is not None:
            args = [a for a in ctx.params.values() if a is not None]
            if ctx.command_path == "cencli show config" and ctx.params.get("group_dev") is None:  # typer not sending args fix
                if "cencli".lower().startswith(incomplete):
                    out += [("cencli", "show cencli configuration")]
            elif ctx.command_path == "cencli update config" and ctx.params.get("group_dev") is None:  # typer not sending args fix
                if "cencli".lower().startswith(incomplete):
                    out += [("cencli", "update cencli configuration")]
        else:
            args = []

        group_out = self.group_completion(incomplete=incomplete, args=args)
        if group_out:
            out += list(group_out)


        if not bool([t for t in out if t[0] == incomplete]):  # exact match
            _args = args if not dev_type else [*args, "dev_type", *dev_type]  # TODO not tested yet
            dev_out = self.dev_completion(incomplete, args=_args)
            if dev_out:
                out += list(dev_out)

        for m in out:
            yield m

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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        return self._group_dev_completion(incomplete, ctx=ctx, args=args)

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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        dev_types = ["ap", "gw"]
        match = self.get_identifier(incomplete, ["group", "dev"], device_type=dev_types, completion=True)

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
            yield m

    def group_dev_gw_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        """Completion for argument that can be either group or a gateway.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the device, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match: List[CacheDevice | CacheGroup] = self.get_identifier(incomplete, ["group", "dev"], device_type="gw", completion=True)

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

        match: List[CacheGroup] = self.get_group_identifier(
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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match: List[CacheLabel] = self.get_label_identifier(
            incomplete,
            completion=True,
        )

        out = []
        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]
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
    ) -> Iterator[Tuple[str, str]]:
        """Completion for clients.

        Args:
            incomplete (str): The last partial or full command before completion invoked.
            args (List[str], optional): The previous arguments/commands on CLI. Defaults to None.

        Yields:
            Iterator[Tuple[str, str]]: Name and help_text for the client, or
                Returns None if config is invalid
        """
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match: List[CacheClient] = self.get_client_identifier(
            incomplete,
            completion=True,
        )
        out = []
        args = args or []
        if match:
            # remove clients that are already on the command line
            match = [m for m in match if m.name not in args]
            for c in sorted(match, key=lambda i: i.name):
                if c.name.lower().startswith(incomplete.lower()):
                    out += [(c.name, c.help_text)]
                elif c.mac.strip(":.-").lower().startswith(incomplete.strip(":.-")):
                    out += [(c.mac, c.help_text)]
                elif c.ip.startswith(incomplete):
                    out += [(c.ip, c.help_text)]
                else:
                    # failsafe, shouldn't hit
                    out += [(c.name, f'{c.help_text} FailSafe Match')]

        for c in out:
            yield c[0].replace(":", "-"), c[1]  # TODO completion behavior has changed.  This works-around issue bash doesn't complete past 00: and zsh treats each octet as a dev name when : is used.

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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        if incomplete == "":
            out = [("cencli", "Show cencli logs"), *[(x['id'], f"{x['id']}|{x['device'].split('Group:')[0].rstrip()}") for x in self.events]]
            for m in out:
                yield m[0], m[1]

        elif "cencli".startswith(incomplete.lower()):
            yield "cencli", "Show cencli logs"
        else:
            for event in self.events:
                if str(event["id"]).startswith(incomplete):
                    yield event["id"], f"{event['id']}|{event['device'].split('Group:')[0].rstrip()}"

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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        if incomplete == "":
            for m in self.logs:
                yield m["id"]
        else:
            for log in self.logs:
                if str(log["id"]).startswith(incomplete):
                    yield log["id"]

    # TODO add support for zip code city state etc.
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
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        args = args or [item for k, v in ctx.params.items() if v for item in [k, v]]

        match: CacheSite = self.get_site_identifier(
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

    def template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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

    def dev_site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        match: List[CacheDevice] = self.get_dev_identifier(
            incomplete,
            completion=True,
        ) or []  # TODO update get_*_identifier methods to return empty list when no completion yields no matches

        site_match: List[CacheSite] = self.get_site_identifier(
            incomplete,
            completion=True,
        ) or []
        match += site_match

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                # TODO needs check to see if key fields already in args
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_gw_switch_completion(
        self,
        ctx: typer.Context,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
            return

        # typer stopped providing args pulling from ctx.params
        if not args:
            args = [arg for p in ctx.params.values() for arg in utils.listify(p)]

        match: List[CacheDevice] = self.get_dev_identifier(
            incomplete,
            dev_type=["gw", "switch"],
            completion=True,
        )
        match = match or []

        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if all([attr not in args for attr in [m.name, m.serial, m.mac, m.ip]]):  # TODO many completions won't filter items on command line already as it's eval is m not in args but m is a CentralObject
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_gw_switch_site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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
                if m.name not in args:
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def remove_completion(
        self,
        incomplete: str,
        args: List[str],
    ) -> Iterator[Tuple[str, str]]:
        # Prevents exception during completion when config missing or invalid
        if not config.valid:
            econsole.print(":warning:  Invalid config")
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

    async def format_dev_response_for_cache(self, resp: Response):
        if not resp.ok:
            return

        try:
            resp = CombinedResponse.flatten_resp([resp])
            _start_time = time.perf_counter()
            with console.status(f"Preparing {len(resp)} records from dev response data for cache update"):
                raw_data = await self.format_raw_devices_for_cache(resp)
                devices = [models.Device(**inner) for k in raw_data for inner in raw_data[k]]

                _ret = [d.model_dump() for d in devices]
                log.debug(f"{len(resp)} records from dev response prepared for cache update in {round(time.perf_counter() - _start_time, 2)}s")
        except Exception as e:
            log.error(f"Exception while formatting device data from {resp.url.path} for cache {e.__class__.__name__}")
            log.exception(e)
            _ret = None

        return _ret

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
            truncate (bool, optional): Existing DB data will be discarded, and all data in DB will be replaced with provided. Defaults to True.

        Returns:
            bool: _description_
        """
        _start_time = time.perf_counter()
        if data is not None:
            data = utils.listify(data)
            with econsole.status(f":arrows_clockwise:  Updating [dark_olive_green2]{db.name}[/] Cache: [cyan]{len(data)}[/] records."):
                if truncate:
                    db.truncate()
                db_res = db.insert_multiple([dict(d) for d in data])  # Converts any TinyDB.Documents to dict as that has unexpected results.
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

        if dev_type:
            switch_types = ["cx", "sw"] if "switch" in dev_type else []
            cache_type = [*[t for t in dev_type if t != "switch"], *switch_types]
        else:
            cache_type = []

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
        resp: List[Response] | CombinedResponse = await self.central.get_all_devices(
            cache=True,
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
                if not dev_type:
                    self.updated.append(self.central.get_all_devices)
                    self.responses.dev = resp
                _ = await self.update_db(self.DevDB, data=update_data, truncate=True)
            else:  # Response is filtered or incomplete due to partial failure merge with existing cache data (update)
                _ = await self._add_update_devices(update_data)

        return resp

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
            # return await self.update_db(self.InvDB, doc_ids=data)
            # TODO batch update_dev_inv_cache... needs to be updated to send doc_ids for removal b4 this can be simplified.
            if all([isinstance(d, int) for d in data]):
                doc_ids = data
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
                    if not utils.is_serial(qry):
                        raise ValueError("Provided str does not appear to be a serial number.")
                    else:
                        match = self.InvDB.get((self.Q.serial == qry))
                        if match:
                            doc_ids += [match.doc_id]
                        else:
                            log.warning(f'Warning update_inv_db: no match found for {qry}', show=True)

            db_res = self.InvDB.remove(doc_ids=doc_ids)

            if len(db_res) != len(doc_ids):
                log.error(f"TinyDB InvDB table update returned an error.  data included {len(doc_ids)} to remove but DB only returned {len(db_res)} doc_ids", show=True, caption=True,)


    async def refresh_inv_db(
            self,
            device_type: Literal['ap', 'gw', 'switch', 'all'] = None,
    ) -> Response:
        """Get devices from device inventory, and Update device Cache with results.

        This combines the results from 2 API calls:
            - central.get_device_inventory: /platform/device_inventory/v1/devices
            - central.get_subscriptions: /platform/licensing/v1/subscriptions

        Args:
            device_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.

        Returns:
            Response: CentralAPI Response object
        """
        br = self.central.BatchRequest
        batch_resp = await self.central._batch_request(
            [
                br(self.central.get_device_inventory, device_type=device_type),
                br(self.central.get_subscriptions, device_type=device_type)
            ]
        )
        if not any([r.ok for r in batch_resp]):
            log.error("Unable to perform Inv cache update due to API call failure", show=True)
            return batch_resp

        inv_resp, sub_resp = batch_resp  # if first call failed above if would result in return.
        _inv_by_ser = {} if not inv_resp.ok else {dev["serial"]: dev for dev in inv_resp.raw["devices"]}

        if not batch_resp[1].ok:
            log.error(f"Call to fetch subscription details failed.  {batch_resp[1].error}.  Subscription details provided from previously cached values.", caption=True)
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
        if device_type is None or device_type == "all":
            self.updated.append(self.central.get_device_inventory)
            self.responses.inv = resp

            _ = await self.update_db(self.InvDB, data=resp.output, truncate=True)
        else:
            _ = await self._add_update_devices(resp.output, "inv")

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
                doc_ids = []
                if all([isinstance(s, int) for s in data]):
                    doc_ids = data
                else:
                    for qry in data:  # TODO remove once all cache removal calls refactored to use doc_ids from cache
                        # provided list of site_ids to remove
                        if isinstance(qry, str) and qry.isdigit():
                            doc_ids += [self.SiteDB.get((self.Q.id == qry)).doc_id]
                        else:
                            # list of dicts with {search_key: value_to_search_for}
                            if len(qry.keys()) > 1:
                                raise ValueError(f"cache.update_site_db remove Should only have 1 query not {len(qry.keys())}")
                            q = list(qry.keys())[0]
                            doc_ids += [self.SiteDB.get((self.Q[q] == qry[q])).doc_id]
                return await self.update_db(self.SiteDB, doc_ids=doc_ids)

    async def refresh_site_db(self, force: bool = False) -> Response:
        if self.responses.site and not force:
            log.warning("cache.refresh_side_db called, but site cache has already been fetched this session.  Returning stored response.")
            return self.responses.site

        resp = await self.central.get_all_sites()
        if resp.ok:
            self.responses.site = resp
            self.updated.append(self.central.get_all_sites)  # TODO remove once all checks refactored to look for self.responses.site

            sites = models.Sites(resp.raw["sites"])
            resp.output = sites.model_dump()

            _ = await self.update_db(self.SiteDB, data=resp.output, truncate=True)
        return resp

    async def update_group_db(self, data: list | dict, remove: bool = False) -> bool:
        data = utils.listify(data)
        if not remove:
            return await self.update_db(self.GroupDB, data=data, truncate=False)
        else:
            if isinstance(data, list) and all([isinstance(item, int) for item in data]):  # sent list of doc_ids
                doc_ids = data
            else:
                doc_ids = []
                for qry in data:
                    if len(qry.keys()) > 1:
                        raise ValueError(f"cache.update_group_db remove Should only have 1 query not {len(qry.keys())}")
                    q = list(qry.keys())[0]
                    doc_ids += [self.GroupDB.get((self.Q[q] == qry[q])).doc_id]

            return await self.update_db(self.GroupDB, doc_ids=doc_ids)


    async def refresh_group_db(self) -> Response:
        if self.responses.group:
            log.info("Update Group DB already refreshed in this session, returning previous group response")
            return self.responses.group

        resp = await self.central.get_all_groups()
        if resp.ok:
            groups = models.Groups(resp.output)
            resp.output = groups.model_dump()

            self.responses.group = resp
            self.updated.append(self.central.get_all_groups)

            _ = await self.update_db(self.GroupDB, data=resp.output, truncate=True)
        return resp

    async def update_label_db(self, data: List[Dict[str, Any]] | Dict[str, Any] | List[int], remove: bool = False) -> Response:
        data = utils.listify(data)
        if not remove:
            return await self.update_db(self.LabelDB, data=data, truncate=False)
        else:
            return await self.update_db(self.LabelDB, doc_ids=data)

    async def refresh_label_db(self) -> bool:
        resp = await self.central.get_labels()
        if resp.ok:
            self.responses.label = resp
            self.updated.append(self.central.get_labels)
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
        resp = await self.central.get_valid_subscription_names()
        if resp.ok:
            resp.output = [{"name": k} for k in resp.output.keys() if self.is_central_license(k)]
            self.updated.append(self.central.get_valid_subscription_names)  # TODO finish removing this method of verifying an update has occured
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

        resp = await self.central.get_all_templates(groups=groups)
        if resp.ok:
            if len(resp) > 0: # handles initial cache population when none of the groups are template groups
                resp.output = utils.listify(resp.output)
                template_models = models.Templates(resp.output)
                resp.output = template_models.model_dump()
                self.updated.append(self.central.get_all_templates)
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

        except Exception as e:
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

        all args are passed to central.get_clients, Local Cache is updated with any results.
        Local Cache retains clients connected within last 90 days.

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
        resp: Response = await self.central.get_clients(
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
                self.updated.append(self.central.get_clients)
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

    # Currently not used
    def update_hook_config_db(self, data: List[Dict[str, Any]], remove: bool = False) -> bool:
        data = utils.listify(data)
        return asyncio.run(self.update_db(self.HookConfigDB, data=data, truncate=True))

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

    # Not tested or used yet, until we have commands that add/del MPSK networks
    async def update_mpsk_db(self, data: List[Dict[str, Any]], remove: bool = False) -> bool:
        if remove:
            return await self.update_db(self.MpskDB, doc_ids=data)

        data = models.MpskNetworks(data)
        data = data.model_dump()
        return await self.update_db(self.MpskDB, data=data, truncate=True)


    async def refresh_mpsk_db(self) -> Response:
        resp = await self.central.cloudauth_get_mpsk_networks()
        if resp.ok:
            self.updated.append(self.central.cloudauth_get_mpsk_networks)  # TODO remove once all check use responses.mpsk check
            self.responses.mpsk = resp
            if resp.output:
                _update_data = models.MpskNetworks(resp.raw)
                _update_data = _update_data.model_dump()

                _ = await self.update_db(self.MpskDB, data=_update_data, truncate=True)

        return resp

    async def update_portal_db(self, data: List[Dict[str, Any]] | List[int], remove: bool = True) -> bool:
        if remove:
            return await self.update_db(self.PortalDB, doc_ids=data)

        portal_models = models.Portals(data)
        data_by_id = {p.id: p.model_dump() for p in portal_models}
        update_data = {**self.portals_by_id, **data_by_id}
        return await self.update_db(self.PortalDB, data=update_data, truncate=True)

    async def refresh_portal_db(self) -> Response:
            resp = await self.central.get_portals()
            if not resp.ok:
                return resp

            self.updated.append(self.central.get_portals)
            self.responses.portal = resp

            portal_model = models.Portals(deepcopy(resp.output))
            update_data = portal_model.model_dump()
            _ = await self.update_db(self.PortalDB, data=update_data, truncate=True)

            return resp

    async def update_guest_db(self, data: List[Dict[str, Any]] | List[int], portal_id: str = None, remove: bool = True) -> bool:
        if remove:
            return await self.update_db(self.GuestDB, doc_ids=data)

        # TODO there is no simple add unless update_db is called directly
        guest_models = models.Guests(portal_id, data)
        data_by_id = {p.id: p.model_dump() for p in guest_models}
        update_data = {**self.guests_by_id, **data_by_id}
        return await self.update_db(self.GuestDB, data=list(update_data.values()), truncate=True)

    async def refresh_guest_db(self, portal_id: str) -> Response:
            resp: Response = await self.central.get_guests(portal_id)
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
        update_funcs, db_res = [], []
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
        async with self.central.aio_session:
            if update_funcs:
                kwargs = {} if update_funcs[0].__name__ not in dev_update_funcs else {"dev_type": dev_type}
                db_res += [await update_funcs[0](**kwargs)]
                if not db_res[-1]:
                    log.error(f"Cache Update aborting remaining {len(update_funcs)} cache updates due to failure in {update_funcs[0].__name__}", show=True, caption=True)
                    if len(update_funcs) > 1:
                        db_res += [Response(error=f"{f.__name__} aborted due to failure in previous cache update call ({update_funcs[0].__name__})") for f in update_funcs[1:]]
                else:
                    if len(update_funcs) > 1:
                        db_res = [*db_res, *await asyncio.gather(*[f() for f in update_funcs[1:]])]

            # If all *_db params are false refresh cache for all
            # TODO make more elegant
            else:  # TODO asyncio.sleep is a temp until build better session wide rate limit handling.
                br = self.central.BatchRequest
                db_res += await self.central._batch_request([br(self.refresh_group_db), br(asyncio.sleep, .5)])  # update groups first so template update can use the result group_update is 3 calls.
                if db_res[-1]:
                    db_res += await self.central._batch_request([br(self.refresh_dev_db), br(asyncio.sleep, .5)])   # dev_db separate as it is a multi-call 3 API calls.
                    if db_res[-1]:
                        batch_reqs = [
                            self.central.BatchRequest(req)
                            for req in [self.refresh_inv_db, self.refresh_site_db, self.refresh_template_db, self.refresh_label_db, self.refresh_license_db]
                        ]
                        db_res = [
                            *db_res,
                            *await self.central._batch_request(batch_reqs)
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
        refresh = refresh or bool(update_count)  # if any DBs are set to update they will update regardless of refresh value
        update_all = True if not update_count else False  # if all are False default is to update all DBs but only if refresh=True

        if refresh or not config.cache_file_ok:
            _word = "Refreshing" if config.cache_file_ok else "Populating"
            updating_db = "[bright_green]Full[/] Identifier mapping" if not update_count else utils.color([k for k, v in db_map.items() if v])
            print(f"[cyan]-- {_word} {updating_db} Cache --[/cyan]", end="")

            start = time.perf_counter()
            db_res = asyncio.run(self._check_fresh(**db_map, dev_type=dev_type))
            elapsed = round(time.perf_counter() - start, 2)
            passed = [r for r in db_res if r.ok]
            failed = (update_count or len(db_map)) - len(passed)
            log.info(f"Cache Refreshed {update_count if update_count != len(db_map) else 'all'} tables in {elapsed}s")

            if failed:
                res_map = ", ".join(db for idx, (db, do_update) in enumerate(db_map.items()) if do_update or update_all and not db_res[idx].ok)
                err_msg = f"Cache refresh returned an error updating ({res_map})"
                log.error(err_msg)
                self.central.spinner.fail(err_msg)
            else:
                self.central.spinner.succeed(f"Cache Refresh [bright_green]Completed[/] in [cyan]{elapsed}[/]s")

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
            data = [{k: d[k] for k in d.keys() if k in fields} for d in match]
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

        return [match[int(selection) - 1]]

    def get_identifier(
        self,
        qry_str: str,
        qry_funcs: Sequence[str],
        device_type: Union[str, List[str]] = None,
        swack: bool = False,
        conductor_only: bool = False,
        group: str | List[str] = None,
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
            group (str, List[str], optional): applies to get_template_identifier, Only match if template is in provided group(s).
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
        for idx in range(0, 2):
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
            if idx == 0 and not match and not completion:
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
            econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]Unable to find a matching identifier[/] for [cyan]{qry_str}[/], tried: [cyan]{qry_funcs}[/]")
            raise typer.Exit(1)

    def get_dev_identifier(
        self,
        query_str: str | Iterable[str],
        dev_type: constants.LibAllDevTypes | List[constants.LibAllDevTypes] = None,
        swack: bool = False,
        conductor_only: bool = False,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        include_inventory: bool = False,
        exit_on_fail: bool = True,
    ) -> CacheDevice | CacheInvDevice | List[CacheDevice | CacheInvDevice | None] | None:
        """Get Devices from local cache, starting with most exact match, and progressively getting less exact.

        If multiple matches are found user is promted to select device.

        Args:
            query_str (str | Iterable[str]): The query string or list of strings to attempt to match.
            dev_type (Literal["ap", "cx", "sw", "switch", "gw"] | List[Literal["ap", "cx", "sw", "switch", "gw"]], optional): Limit matches to specific device type. Defaults to None (all device types).
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
                | (self.Q.mac == utils.Mac(query_str).cols)
                | (self.Q.serial == query_str)
            )
            # Inventory must be exact match expecting full serial numbers but will allow MAC if exact match
            if not match and include_inventory:
                match = self.InvDB.search(
                    (self.Q.serial == query_str)
                    | (self.Q.mac == utils.Mac(query_str).cols)
                )
                if match:
                    Model = CacheInvDevice

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

            if match and dev_type:
                all_match: List[Document] = match.copy()
                match = [d for d in all_match if d.get("type", "") in dev_type]


            # no match found initiate cache update
            if retry and not match and self.responses.dev is None:
                if dev_type and cache_updated:
                    ...  # self.responses.dev is not currently updated if dev_type provided, but cache update may have already occured in this session.
                else:
                    dev_type_sfx = "" if not dev_type else f" [grey42 italic](Device Type: {utils.unlistify(dev_type)})[/]"
                    econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/]{dev_type_sfx}.")
                    if FUZZ:
                        if dev_type:
                            fuzz_match, fuzz_confidence = process.extract(query_str, [d["name"] for d in self.devices if "name" in d and d["type"] in dev_type], limit=1)[0]
                        else:
                            fuzz_match, fuzz_confidence = process.extract(query_str, [d["name"] for d in self.devices if "name" in d], limit=1)[0]
                        confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.DevDB.search(self.Q.name == fuzz_match)
                    if not match:
                        kwargs = {"dev_db": True}
                        if include_inventory:
                            _word = " & Inventory "
                            kwargs["inv_db"] = True
                        else:
                            _word = " "
                        econsole.print(f":arrows_clockwise: Updating Device{_word}Cache.")
                        self.check_fresh(refresh=True, dev_type=dev_type, **kwargs )
                        cache_updated = True  # Need this for scenario when dev_type is the only thing refreshed, as that does not update self.responses.dev

            if match:
                match = [Model(dev) for dev in match]
                break

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
                match = self.handle_multi_match(sorted(match, key=lambda m: m.get("name", "")), query_str=query_str,)

            return match[0]

        elif retry:
            log.error(f"Unable to gather device info from provided identifier {query_str}", show=not silent)
            if all_match:
                all_match_msg = f"{', '.join(m.get('name', m.get('serial')) for m in all_match[0:5])}{', ...' if len(all_match) > 5 else ''}"
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
        exit_on_fail: bool = True,
    ) -> CacheSite | List[CacheSite]:
        retry = False if completion else retry
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)
        elif not isinstance(query_str, str):
            query_str = str(query_str)


        if completion and query_str == "":
            return [CentralObject("site", s) for s in self.sites]

        match = None
        for _ in range(0, 2 if retry else 1):
            match = []
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
                    | (self.Q.zipcode == query_str)
                    | (self.Q.address == query_str)
                    | (self.Q.city == query_str)
                    | (self.Q.state == query_str)
                    | (self.Q.state.test(lambda v: constants.state_abbrev_to_pretty.get(query_str.upper(), query_str).title() == v.title()))
                )

            # try case insensitive name
            if not match or completion:
                match += self.SiteDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                )
            # try case insensitve address match
            if not match or completion:
                match += self.SiteDB.search(
                    self.Q.address.test(lambda v: v.lower().replace(" ", "") == query_str.lower().replace(" ", ""))
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
                    self.Q.zipcode.test(lambda v: v.startswith(query_str))
                    | self.Q.city.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.state.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.address.test(lambda v: " ".join(v.split(" ")[1:]).lower().startswith(query_str.lower()))
                )

            # err_console.print(f'\n{match=} {query_str=} {retry=} {completion=} {silent=}')  # DEBUG
            if retry and not match and self.central.get_all_sites not in self.updated:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and not silent:
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
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="site",)

            return match[0]

        elif retry:
            log.error(f"Unable to gather site info from provided identifier {query_str}", show=not silent)
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return None


    def get_group_identifier(
        self,
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
        exit_on_fail: bool = True,
    ) -> CacheGroup | List[CacheGroup]:
        """Allows Case insensitive group match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            # TODO change all get_*_identifier functions to continue to look for matches when match is found when
            #       completion is True
            # Exact match
            match = []
            if query_str == "":
                match = self.groups
            else:
                match += self.GroupDB.search((self.Q.name == query_str))

            # case insensitive
            if not match or completion:
                match += self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match or completion:
                match += self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match or completion:
                if "_" in query_str or "-" in query_str:
                    match += self.GroupDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith ignore - _
            if not match or completion:
                match += self.GroupDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().strip("-_").startswith(query_str.lower().strip("-_"))
                    )
                )

            if not match and retry and self.central.get_all_groups not in self.updated:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found for[/] [cyan]{query_str}[/].")
                if FUZZ and not silent:
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
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="group",)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather group data from provided identifier {query_str}", show=True)

            if exit_on_fail:
                valid_groups = utils.summarize_list(self.group_names, max=50)
                econsole.print(f":warning:  [cyan]{query_str}[/] appears to be [red]invalid[/]")
                econsole.print(f"Valid Groups:\n{valid_groups}")
                raise typer.Exit(1)
            else:
                return
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
        exit_on_fail: bool = True,
    ) -> CacheLabel | List[CacheLabel] | None:
        """Allows Case insensitive label match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            match = []
            # Exact match
            if query_str == "":
                match = self.labels
            else:
                match += self.LabelDB.search((self.Q.name == query_str))

            # case insensitive
            if not match or completion:
                match += self.LabelDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive startswith
            if not match or completion:
                match += self.LabelDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive ignore -_
            if not match or completion:
                if "_" in query_str or "-" in query_str:
                    match += self.LabelDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith ignore - _
            if not match or completion:
                match += self.LabelDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().strip("-_").startswith(query_str.lower().strip("-_"))
                    )
                )

            # TODO add fuzzy match other get_*_identifier functions and add fuzz as dep
            # fuzzy match
            if not match and retry and self.central.get_labels not in self.updated:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] [cyan]{query_str}[/].")
                if FUZZ and not silent:
                    fuzz_resp = process.extract(query_str, [label["name"] for label in self.labels], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.LabelDB.search(self.Q.name == fuzz_match)
                if not match:
                    econsole.print(":arrows_clockwise: Updating [cyan]label[/] Cache")
                    self.check_fresh(refresh=True, label_db=True)
                _ += 1
            if match:
                match = [CacheLabel(g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="label",)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=True)

            if exit_on_fail:
                valid_labels = "\n".join(self.label_names)
                # TODO convert all these to rich
                typer.secho(f"{query_str} appears to be invalid", fg="red")
                typer.secho(f"Valid Labels:\n--\n{valid_labels}\n--\n", fg="cyan")
                raise typer.Exit(1)
            else:
                return
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=not silent
                )

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
            return [CentralObject("template", data=t) for t in self.templates]

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
                if FUZZ:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [t["name"] for t in self.templates if group is None or t["group"] == group], limit=1)[0]
                    confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.TemplateDB.search(self.Q.name == fuzz_match)
                if not match:
                    econsole.print(":arrows_clockwise: Updating template Cache")
                    self.check_fresh(refresh=True, template_db=True)
            if match:
                match = [CacheTemplate(tmplt) for tmplt in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="template",
                )

            return match[0]

        elif retry:
            log.error(f"Unable to gather template from provided identifier {query_str}", show=not silent, log=silent)
            if all_match:
                first_five = [f"[bright_green]{m['name']}[/] from group [cyan]{m['group']}[/]" for m in all_match[0:5]]
                all_match_msg = f"{', '.join(first_five)}{', ...' if len(all_match) > 5 else ''}"
                log.error(
                    f"The Following templates matched: {all_match_msg}... [red]excluded[/] as they are not in [cyan]{group}[/] group ",
                    show=True,
                )
            raise typer.Exit(1)
        else:
            if not completion and not silent:
                log.warning(f"Unable to gather template from provided identifier {query_str}", show=False)

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
            if retry and not match and self.responses.client is not None:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ and self.clients:
                    fuzz_match, fuzz_confidence = process.extract(query_str, [d["name"] for d in self.clients], limit=1)[0]
                    confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                    if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                        match = self.ClientDB.search(self.Q.name == fuzz_match)
                if not match:  # on demand update only for WLAN as roaming and kick only applies to WLAN currently
                    econsole.print(":arrows_clockwise: Updating [cyan]client[/] Cache")
                    self.central.request(self.refresh_client_db, "wireless")

            if match:
                match = [CacheClient(c) for c in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:  # user selects which device if multiple matches returned
                match = self.handle_multi_match(match, query_str=query_str, query_type="client")

            return match[0]

        elif retry:
            log.error(f"Unable to gather client info from provided identifier {query_str}", show=not silent)
            if exit_on_fail:
                raise typer.Exit(1)
            else:
                return None

    def get_audit_log_identifier(self, query: str) -> str:
        if "audit_trail" in query:
            return query

        try:
            match = self.LogDB.search(self.Q.id == int(query))
            if not match:
                econsole.print(f"\nUnable to gather log id from short index query [cyan]{query}[/]")
                econsole.print("Short log_id aliases are built each time [cyan]show logs[/] / [cyan]show audit logs[/]... is ran.")
                econsole.print("  repeat the command without specifying the log_id to populate the cache.")
                econsole.print("  You can verify the cache by running (hidden command) 'show cache logs'")
                raise typer.Exit(1)
            else:
                return match[-1]["long_id"]

        except ValueError as e:
            econsole.print(f"\n[dark_orange3]:warning:[/]  [bright_red]{e.__class__.__name__}[/]:  Expecting an intiger for log_id. '{query}' does not appear to be an integer.")
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
                print("  You can verify the cache by running (hidden command) [cyan]show cache events[/]")
                print("  run [cyan]show logs [OPTIONS][/] then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1]["details"]

        except ValueError as e:
            log.error(f"Exception in get_event_identifier {e.__class__.__name__}", show=True)
            raise typer.Exit(1)


    def get_mpsk_identifier(
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

            if not match and retry and self.responses.mpsk is None:
                if FUZZ:
                    econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                    fuzz_resp = process.extract(query_str, [mpsk["name"] for mpsk in self.mpsk], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.MpskDB.search(self.Q.name == fuzz_match)
                if not match:
                    econsole.print(":arrows_clockwise: Updating [cyan]MPSK[/] Cache")
                    self.central.request(self.refresh_mpsk_db)
                _ += 1
            if match:
                match = [CacheMpskNetwork(g) for g in match]
                break

        if completion:
            return match or []

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="mpsk",)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather MPSK data from provided identifier {query_str}", show=True)
            valid_mpsk = "\n".join([f'[cyan]{m["name"]}[/]' for m in self.mpsk])
            econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{query_str}[/] appears to be invalid")
            econsole.print(f"\n[bright_green]Valid MPSK Networks[/]:\n--\n{valid_mpsk}\n--\n")
            raise typer.Exit(1)
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather label data from provided identifier {query_str}", show=not silent
                )


    # TODO make this a wrapper for other specific get_portal_identifier.... calls
    def get_name_id_identifier(
        self,
        cache_name: Literal["dev", "site", "template", "group", "label", "mpsk", "portal"],
        query_str: str,
        retry: bool = True,
        completion: bool = False,
        silent: bool = False,
    ) -> CachePortal | List[CachePortal] | CacheLabel | List[CacheLabel]:
        cache_details = CacheDetails(self)
        this: CacheAttributes = getattr(cache_details, cache_name)
        db_all = this.db.all()
        db = this.db
        """Fetch items from cache based on query

        This is a common identifier lookup function for all stored types that primarily have
        name and id as potential match fields.

        DEV NOTE appears only to be used by portal currently

        returns:
            CentralObject | List[CentralObject]: returns any matches
        """
        name_to_model = {
            "portal": CachePortal,
            "label": CacheLabel
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
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )

            # case insensitive startswith search for mspk id
            if not match:
                match = db.search(
                    self.Q.id.test(
                        lambda v: str(v).lower().startswith(query_str.lower())
                    )
                )

            if not match and retry and not cache_updated:
                econsole.print(f"[dark_orange3]:warning:[/]  [bright_red]No Match found[/] for [cyan]{query_str}[/].")
                if FUZZ:
                    fuzz_resp = process.extract(query_str, [item["name"] for item in db_all], limit=1)
                    if fuzz_resp:
                        fuzz_match, fuzz_confidence = fuzz_resp[0]
                        confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                        if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                            match = self.db.search(self.Q.name == fuzz_match)
                if not match:
                    econsole.print(f":arrows_clockwise: Updating [cyan]{cache_name}[/] Cache")
                    self.central.request(this.cache_update_func)
                    cache_updated = True
                _ += 1
            if match:
                match = [Model(m) for m in match]
                break

        if completion:
            return match or []

        if match:
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
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather {cache_name} data from provided identifier {query_str}", show=not silent
                )

class CacheAttributes:
    def __init__(self, name: Literal["dev", "site", "template", "group", "label", "mpsk", "portal"], db: Table, already_updated_func: Callable, cache_update_func: Callable) -> None:
        self.name = name
        self.db = db
        self.already_updated_func = already_updated_func
        self.cache_update_func = cache_update_func

class CacheDetails:
    def __init__(self, cache = Cache):
        self.dev = CacheAttributes(name="dev", db=cache.DevDB, already_updated_func=cache.central.get_all_devices, cache_update_func=cache.refresh_dev_db)
        self.site = CacheAttributes(name="site", db=cache.SiteDB, already_updated_func=cache.central.get_all_sites, cache_update_func=cache.refresh_site_db)
        self.group = CacheAttributes(name="group", db=cache.GroupDB, already_updated_func=cache.central.get_all_groups, cache_update_func=cache.refresh_group_db)
        self.portal = CacheAttributes(name="portal", db=cache.PortalDB, already_updated_func=cache.central.get_portals, cache_update_func=cache.refresh_portal_db)
        self.mpsk = CacheAttributes(name="mpsk", db=cache.MpskDB, already_updated_func=cache.central.cloudauth_get_mpsk_networks, cache_update_func=cache.refresh_mpsk_db)
        self.label = CacheAttributes(name="label", db=cache.LabelDB, already_updated_func=cache.central.get_labels, cache_update_func=cache.refresh_label_db)