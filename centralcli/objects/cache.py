from collections.abc import KeysView, MutableMapping
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeAlias

import pendulum
from rich.text import Text
from sqlalchemy import select
from sqlalchemy.orm import Session
from yarl import URL

from centralcli import api_clients, config, log, render, utils
from centralcli.constants import BranchGwRoleTypes, ClientType, DeviceTypes, LibAllDevTypes
from centralcli.models.sql import Building, Device, InventoryDevice
from centralcli.response import CombinedResponse, Response
from centralcli.typedefs import CacheSiteDict

from . import DateTime

if TYPE_CHECKING:
    from ..cache import Cache
    from ..typedefs import CacheSiteDict, CertType, ClientType, PortalAuthTypes


api = api_clients.classic
CacheTable = Literal["dev", "inv", "sub", "site", "group", "template", "label", "license", "svc", "client", "log", "event", "hook_data", "mpsk_network", "mpsk", "portal", "cert"]


class CentralObject(MutableMapping):
    def __init__(
        self,
        data: dict[str, Any] | list[dict[str, Any]] = None,
        is_dev: bool = None,
        is_inv: bool = None,
        is_group: bool = None,
        is_template: bool = None,
        is_site: bool = None,
    ):
        self.data = data or {}
        self._help_text_parts = list(data.values())
        if [x for x in [is_dev, is_inv, is_group, is_template, is_site] if x is not None]:  # We want an AttributeError if these are not passed in
            self.is_dev = is_dev or False
            self.is_inv = is_inv or False
            self.is_group = is_group or False
            self.is_template = is_template or False
            self.is_site = is_site or False

    def __bool__(self):
        return bool(self.data)

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self._help_text_parts and self._help_text_parts[0] or bool(self)}) object at {hex(id(self))}>"  # pragma: no cover used for debugging

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]  # pragma: no cover

    def __len__(self):
        return len(self.data)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def keys(self) -> KeysView:
        return self.data.keys()

    @cached_property
    def text(self) -> Text:
        parts = [p for p in self._help_text_parts if p]

        def _get_color(idx: int, item: str):
            if idx == 0:
                return "dark_olive_green2"
            if str(item).lower() in ["up", "enabled", "active"]:
                return "bright_green"
            if str(item).lower() in ["down", "disabled", "inactive"]:
                return "red1"
            if idx % 2 == 0:
                return "turquoise4"
            return "cyan"

        ignore_emoji = [":cd:", ":ab:"]
        text = "|".join(
            [
                f"[{_get_color(idx, p)}]{p}[/]" for idx, p in enumerate(parts)
            ]
        )
        return Text.from_markup(text, emoji=not text.count(":") >= 5 and not any([e in text.lower() for e in ignore_emoji]))

    def __str__(self) -> str:
        return self.text.plain  # pragma: no cover

    def __rich__(self) -> str:
        return self.text.markup  # pragma: no cover

    @property
    def help_text(self) -> str:
        return render.rich_capture(self.text.markup)

    @property
    def summary_text(self) -> str:
        return self.text.markup

    @property
    def rich_help_text(self) -> str:
        return self.text.markup


class MigrateDevice(CentralObject):
    def __init__(self, data: dict[str, Any]):
        super().__init__(data, is_dev=True, is_inv=True)
        self.name = data["name"]
        self.status = data["status"]
        self.type = data["type"]
        self.model = data["model"]
        self.ip = data["ip"]
        self.serial = data["serial"]
        self.mac = data["mac"]
        self.id = data["id"]
        self.site = data["site"]
        self.group = data["group"]
        self.swack_id = data["swack_id"]
        self.subscription = data["subscription"]
        self.assigned = data["assigned"]
        self.archived = data["archived"]
        self._help_text_parts = [self.name, self.type, self.status, self.serial, self.mac, self.ip, self.model, self.group, self.site, self.subscription]
        if not self.subscription:
            if self.archived:
                self._help_text_parts += ["[red]ARCHIVED[/]"]
            elif not self.assigned:
                self._help_text_parts += ["[red]NOT ASSIGNED[/]"]

    def __hash__(self):
        return hash(self.serial)

    @property
    def generic_type(self):
        return "switch" if self.data["type"] in ["cx", "sw"] else self.data["type"]


class _MigrateDevice(CentralObject):
    def __init__(self, row: InventoryDevice | Device):
        super().__init__({"name": row.name, "status": row.status, "type": row.type, "model": row.model, "ip": row.ip, "serial": row.serial, "mac": row.mac, "id": row.id, "site": row.site, "group": row.group, "subscription": row.subscription, "assigned": row.assigned, "archived": row.archived}, is_dev=True, is_inv=True)
        self.name = row.name
        self.status = row.status
        self.type = row.type
        self.model = row.model
        self.ip = row.ip
        self.serial = row.serial
        self.mac = row.mac
        self.id = row.id
        self.site = row.site
        self.group = row.group
        self.swack_id = row.swack_id
        self.subscription = row.subscription
        self.assigned = row.assigned
        self.archived = row.archived
        self._help_text_parts = [self.name, self.type, self.status, self.serial, self.mac, self.ip, self.model, self.group, self.site, self.subscription]
        if not self.subscription:
            if self.archived:
                self._help_text_parts += ["[red]ARCHIVED[/]"]
            elif not self.assigned:
                self._help_text_parts += ["[red]NOT ASSIGNED[/]"]

    def __hash__(self):
        return hash(self.serial)

    @property
    def generic_type(self):
        return "switch" if self.data["type"] in ["cx", "sw"] else self.data["type"]


class CacheInvDevice(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data, is_inv=True)
        self.id: str = data.get("id")  # glp only
        self.serial: str = data["serial"]
        self.mac: str = data["mac"]
        self.type: str = data["type"]
        self.model: str = data["model"]
        self.sku: str = data["sku"]
        self.services: str | None = data.get("services", data.get("subscription"))  # backward compat new field name is subscription
        self.subscription_key: str = data.get("subscription_key")
        self.subscription_expires: int | float = data.get("subscription_expires")
        self.assigned: bool = data.get("assigned")  # glp only
        self.archived: bool = data.get("archived")  # glp only
        id_str = None if not self.id else f"[dim]glp id: {self.id}[/dim]"
        self._help_text_parts = [self.serial, self.mac, self.type, self.sku, id_str]

    @property
    def generic_type(self):
        return "switch" if self.type in ["cx", "sw"] else self.type

    def __eq__(self, value: "CacheInvDevice" | str):
        if hasattr(value, "serial"):
            return value.serial == self.serial
        if utils.is_resource_id(value):
            return value == self.id
        return value == self.serial

    def __hash__(self):
        return hash(self.serial)

    def __rich__(self) -> str:
        return f'[bright_green]Inventory Device[/]:[bright_green]{self.serial}[/]|[cyan]{self.mac}[/]'


class CacheDevice(CentralObject):
    cache: Cache = None

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data, is_dev=True)
        self.name: str = data["name"]
        self.status: Literal["Up", "Down"] | None = data["status"]
        self.type: DeviceTypes = data["type"].lower()
        self.model: str = data["model"]
        self.ip: str | None = data["ip"]
        self.mac: str = data["mac"]
        self.serial: str = data["serial"]
        self.group: str = data["group"]
        self.site: str = data["site"]
        self.version: str = data["version"]
        self.swack_id: str | None = data["swack_id"]
        self.switch_role: str | None = data["switch_role"]
        self._help_text_parts = [self.name, self.type, self.status, self.serial, self.mac, self.ip, self.model]

    def __eq__(self, value: str | "CacheDevice"):
        if hasattr(value, "serial"):
            return value.serial == self.serial
        return value == self.serial  # pragma: no cover

    def __hash__(self):
        return hash(self.serial)

    @property
    def is_aos10(self) -> bool:
        if self.type != "ap":
            return False
        return True if self.version.startswith("10.") else False

    @property
    def generic_type(self):
        return "switch" if self.data["type"] in ["cx", "sw"] else self.data["type"]

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

    @property
    def glp_id(self):
        stmt = select(InventoryDevice.id).where(InventoryDevice.serial == self.serial)
        with Session(self.cache.engine) as session:
            with session.bind.connect() as connection:
                result = connection.execute(stmt)
                for row in result:
                    return row.id

    def get_completion(self, incomplete: str, args: list[str] = None) -> tuple[str, str]:  # TODO do this for other objects
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
        data = {**(self.inv and self.inv.data or {}), **mon_data}

        super().__init__(data)
        # inventory
        self.id: str = inventory and inventory.data.get("id")  # glp only
        self.serial: str = inventory and inventory.data["serial"]
        self.mac: str = inventory and inventory.data["mac"]
        self.type: str = inventory and inventory.data["type"]
        self.model: str = inventory and inventory.data["model"]
        self.sku: str = inventory and inventory.data["sku"]
        self.services: str | None = inventory and inventory.data.get("subscription", inventory.data.get("services"))
        self.subscription_key: str = inventory and inventory.data.get("subscription_key")
        self.subscription_expires: int | float = inventory and inventory.data.get("subscription_expires")
        self._assigned: bool = inventory and inventory.data.get("assigned")  # glp only
        self.archived: bool = inventory and inventory.data.get("archived")  # glp only
        # monitoring
        self.name: str = monitoring and monitoring.data["name"]
        self.status: Literal["Up", "Down"] | None = None if monitoring is None else monitoring.data["status"]
        self.type: DeviceTypes = None if monitoring is None else monitoring.data["type"]
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
        self._help_text_parts = [self.name, self.type, self.status, self.serial, self.mac, self.ip, self.model, self.sku]

    def __fields__(self) -> list[str]:
        return [k for k in self.__dir__() if not k.startswith("_") and not callable(k)]

    def __eq__(self, value: "CacheInvMonDevice" | str):
        if hasattr(value, "serial"):
            return value.serial == self.serial
        if utils.is_resource_id(value):
            return value == self.id
        return value == self.serial

    def __hash__(self):
        return hash(self.serial)

    @property
    def generic_type(self):
        return "switch" if self.type in ["cx", "sw"] else self.type

    @property
    def assigned(self) -> bool:
        return bool(self._assigned)


class CacheGroup(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data, is_group=True)
        self.name: str = data["name"]
        self.allowed_types: list[DeviceTypes] = data["allowed_types"]
        self.gw_role: BranchGwRoleTypes = data["gw_role"]
        self.aos10: bool = data.get("aos10")
        self.microbranch: bool = data.get("microbranch")
        self.wlan_tg: bool = data.get("wlan_tg")
        self.wired_tg: bool = data.get("wired_tg")
        self.monitor_only_sw: bool = data.get("monitor_only_sw")
        self.monitor_only_cx: bool = data.get("monitor_only_cx")
        self.cnx: bool = data.get("cnx")
        _allowed_types_str = f"[magenta]allowed types[/]: {utils.color(self.allowed_types)}"
        _mon_only = [f"[magenta]monitor only {_type}[/]: \u2705" for _type, _mon_only in zip(["sw", "cx"], [self.monitor_only_sw, self.monitor_only_cx]) if _mon_only]
        _template_group = [f"[magenta]{_type} TG[/]: \u2705" for _type, _tg in zip(["wired", "wlan"], [self.wired_tg, self.wlan_tg]) if _tg]
        _other = []
        if "ap" in self.allowed_types:
            _other += ["AOS10" if self.aos10 else "AOS8"]
        if "gw" in self.allowed_types or "sdwan" in self.allowed_types:
            _other += [f"[magenta]GW Role[/]: {self.gw_role}"]
        if self.cnx:
            _other += ["[magenta]New Central Managed[/]: \u2705"]
        self._help_text_parts = [self.name, _allowed_types_str, *_mon_only, *_template_group, *_other]


class CacheSite(CentralObject):
    def __init__(self, data: CacheSiteDict) -> None:
        super().__init__(data, is_site=True)
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
        parts = [a for a in [self.name, self.city, self.state, self.zip] if a]
        self._help_text_parts = parts if len(parts) > 1 else [*parts, self.lat, self.lon]


class CacheLabel(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.devices: int = data.get("devices", data.get("associated_device_count", 0))
        self._help_text_parts = [self.name, f"[magenta]id[/]: {self.id}"]

    def get_completion(self, pfx: str = "'") -> tuple[str, str]:
        quoted = f"'{self.name}'" if pfx == "'" else f'"{self.name}"'
        return (self.name if " " not in self.name else quoted, self.help_text)


class CachePortal(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
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
        self._help_text_parts = [self.name, self.auth_type, f"[magenta]id[/]: {self.id}"]

    @staticmethod
    def get_auth_types(auth_types: str) -> PortalAuthTypes:
        short_auth_types = {
            "Username/Password": "user/pass",
            "Self-Registration": "self-reg",
            "Anonymous": "anon",
        }
        return [short_auth_types.get(auth_type, auth_type) for auth_type in auth_types.split()]


# TODO may not need cache item to lookup portal name, sql relationship with portal_id can prob provide portal info
class CacheGuest(CentralObject):
    def __init__(self, data: dict[str, Any], cache: "Cache" = None) -> None:
        self.cache = cache
        super().__init__(data)
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
        email_str = None if not self.email or self.email == self.name else f"|[dark_olive_green2]{self.email}[/]"
        self._help_text_parts = [self.name, f"[magenta]portal[/]: [cyan]{self.portal}[/]", self.status, email_str, f"[dim][magenta]id[/]: [cyan]{self.id}[/][/dim]"]

    @cached_property
    def portal(self):
        return self.cache.portals_by_id[self.portal_id]["name"]


class CacheTemplate(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data, is_template=True)
        self.name: str = data["name"]
        self.device_type: DeviceTypes = data["device_type"]
        self.group: str = data["group"]
        self.model: str = data["model"]  # model as in sku here =
        self.template_hash: str = data["template_hash"]
        self.version: str = data["version"]
        self._help_text_parts = [self.name, self.group, self.device_type, self.model, f"[magenta]version[/]: {self.version}"]


class CacheClient(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
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
        self._help_text_parts = [self.name, self.ip, self.mac, f'[magenta]s[/]:{self.site}' if self.site else f'[magenta]g[/]:{self.group}', self.type, self.connected_name]

    # def get_group(self) -> CacheGroup:
    #     return None if self.cache is None else self.cache.get_group_identifier(self.group)

    # def get_site(self) -> CacheSite:
    #     return None if self.cache is None else self.cache.get_site_identifier(self.site)


class CacheMpskNetwork(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self._help_text_parts = [self.name, f"[magenta]id[/]: {self.id}"]


class CacheMpsk(CentralObject):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.role: str = data["role"]
        self.ssid: str = data["ssid"]
        self.status: Literal["enabled", "disabled"] = data["status"]
        self._help_text_parts = [self.name, self.ssid, self.role, self.status, f"[magenta]id[/]: {self.id}"]


class CacheCert(CentralObject):  # , Text):
    def __init__(self, name: str, type: CertType, expired: bool, expiration: int | float | DateTime | str, md5_checksum: str, **kwargs):
        self.name = name
        self.type = type.upper()
        self.expired = expired
        self._expiration = expiration
        self.md5_checksum = md5_checksum
        expired_str = f'[magenta]expired[/]: {"[bright_red]" if self.expired is True else "[bright_green]"}{self.expired}[/]'
        self._help_text_parts = [self.name, expired_str, f'[magenta]expiration[/]: [cyan]{"" if self.expiration is None else DateTime(self.expiration, "date-string")}[/]', f'[magenta]md5[/]: [cyan]{self.md5_checksum}[/]']

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} (Certificate|{self.name}|{'OK' if not self.expired else 'EXPIRED'}) object at {hex(id(self))}>"

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

    @property
    def data(self) -> dict[str, str | bool | DateTime]:
        return {"name": self.name, "type": self.type, "expired": self.expired, "expiration": self.expiration, "md5_checksum": self.md5_checksum}


class SubscriptionTier(str, Enum):
    ADVANCED = "advanced"
    FOUNDATION = "foundation"
    OTHER = "other"


class CacheSub(CentralObject, Text):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
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
        _expired_str = f"[red1]EXPIRED[/] as of [cyan]{self.expire_string}[/]" if self.expired else f"expires {self.expire_string.expiration}"
        _glp_str = "" if not config.debug else f"[dim][magenta]glp id[/]: {self.id}[/dim]"
        _key_str = "" if not self.key else f"[dim turquoise2]{self.key}[/]"
        self._help_text_parts = [self.name, _glp_str, _key_str, _expired_str, f'[magenta]Qty Available[/][dim]:[/dim] [cyan]{self.available}[/cyan]']

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.cache}|{self.name}|{self.available}|{render.unstyle(self.status)}) object at {hex(id(self))}>"

    def __eq__(self, value: "CacheSub" | str):
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


class CacheService(CentralObject, Text):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.region: str = data["region"]
        self._help_text_parts = [self.name, self.region, self.id]

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.name}|{self.id}|{self.region} object at {hex(id(self))}>"


class CacheEvent(CentralObject, Text):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.id: str = data["id"]
        self.details: str = data["details"]
        self.device: str = data["device"]
        self._help_text_parts = [self.id, self.device]

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.id}|{self.device} object at {hex(id(self))}>"


class CacheAuditLog(CentralObject, Text):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.id: str = data["id"]
        self.long_id: str = data["long_id"]
        self._help_text_parts = [self.id, self.long_id]

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.id}|{self.long_id} object at {hex(id(self))}>"


class CacheBuilding(CentralObject, Text):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.campus_id: str = data["campus_id"]
        self.lat: int = data["lat"]
        self.lon: int = data["lon"]
        self._help_text_parts = [self.name, self.lat, self.lon]

    def __repr__(self):  # pragma: no cover
        return f"<{self.__module__}.{type(self).__name__} (Building|{self.name}) object at {hex(id(self))}>"

    def __eq__(self, value: "CacheBuilding" | str):
        if hasattr(value, "id"):
            return value.id == self.id
        return value == self.id

    def __hash__(self):
        return hash(self.id)


class CacheFloorPlanAP(CentralObject, Text):
    def __init__(self, data: dict[str, Any], cache: "Cache") -> None:
        super().__init__(data)
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.serial: str = data["serial"]
        self.mac: int = data["mac"]
        self.floor_id: int = data["floor_id"]
        self.building_id: str = data["building_id"]
        self.level: int | float = data["level"]
        self._cache = cache
        self._help_text_parts = [self.name, self.serial, self.mac, f"[magenta]building[/]: {self.building}|{self.building_id}", f"[magenta]floor[/]: {self.level}"]

    @cached_property
    def building(self) -> CacheBuilding:
        stmt = select(Building).where(Building.id == self.building_id)
        with Session(self._cache.engine) as session:
            this_match = session.scalars(stmt).one()
            return CacheBuilding(this_match.to_dict())

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} (floor plan AP|{self.name}|{self.serial}) object at {hex(id(self))}>"

    def __eq__(self, value: "CacheFloorPlanAP" | str):
        if hasattr(value, "id"):
            return value.id == self.id
        return value == self.id or value == self.serial

    def __hash__(self):
        return hash(self.id)

    @property
    def location(self) -> dict[str, str]:
        return {
            "id": self.id,
            "serial": self.serial,
            "building": self.building.name,
            "floor": self.level
        }


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
        service: Response = None,
        client: Response = None,
        guest: Response = None,
        cert: Response = None,
        device_type: list[LibAllDevTypes] | LibAllDevTypes = None,
        device_kwargs: dict[str, Any] = None,
        serial_numbers: str | list[str] = None,
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
        self._service = service
        self._client = client
        self._guest = guest
        self._cert = cert
        self._device_type = utils.listify(device_type)
        self._device_kwargs = device_kwargs
        self._serial_numbers = utils.listify(serial_numbers)
        self._res_list = [self._dev, self._inv, self._site, self._template, self._group, self._label, self._mpsk_network, self._mpsk, self._portal, self._license, self._service, self._client, self._guest, self._cert]

    def update_rl(self, resp: Response | CombinedResponse | None) -> Response | CombinedResponse | None:
        """Returns provided Response object with the RateLimit info from the most recent API call."""
        if resp is None:
            return

        _last_rl = sorted([r.rl for r in self._res_list if r is not None])
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
    def service(self) -> Response | None:
        return self.update_rl(self._service)

    @service.setter
    def service(self, resp: Response):
        self._service = resp

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
    def device_type(self) -> list[LibAllDevTypes] | None:
        return self._device_type

    @device_type.setter
    def device_type(self, device_type: LibAllDevTypes | list[LibAllDevTypes]):
        self._device_type = utils.listify(device_type)

    @property
    def device_kwargs(self) -> dict[str, Any]:
        return self._device_kwargs or {}

    @device_kwargs.setter
    def device_kwargs(self, device_kwargs: dict[str, Any]):
        self._device_kwargs = device_kwargs

    @property
    def serial_numbers(self) -> list[str] | None:
        return self._serial_numbers

    @serial_numbers.setter
    def serial_numbers(self, serial_numbers: str | list[str]):
        self._serial_numbers = utils.listify(serial_numbers)

    def clear(self) -> None:
        """Clears response cache.  Used for pytest runs."""
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
        self._service = None
        self._client = None
        self._guest = None
        self._cert = None
        self._device_type = None
        self._serial_numbers = None


CacheObject: TypeAlias = CacheDevice | CacheInvDevice | CacheInvMonDevice | CacheSite | CacheGroup | CacheTemplate | CacheLabel | CacheClient | CacheMpskNetwork | CacheMpsk | CacheSub | CacheBuilding | CacheFloorPlanAP | CacheService | CacheCert | CacheGuest | CachePortal