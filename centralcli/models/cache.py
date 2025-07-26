from __future__ import annotations

from pydantic import BaseModel, RootModel, Field, AliasChoices, ConfigDict, field_validator, field_serializer
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Literal, Iterable
from enum import Enum
from random import randint
from datetime import datetime
import json
import pendulum
from functools import cached_property

from .. import utils, log
from ..constants import DevTypes, CertTypes
from ..objects import DateTime
from .common import MpskStatus

if TYPE_CHECKING:
    from collections.abc import KeysView


# This is the same as DevTypes (plural in constants) other than DevTypes includes sdwan.
# Could probably use same model for everything in here.  One or the other.
class DevType(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"
    sdwan = "sdwan"
    bridge = "bridge"


class InventoryDevice(BaseModel):
    id: Optional[str] = None
    serial: str = Field(alias=AliasChoices("serial", "serialNumber"))
    mac: str = Field(alias=AliasChoices("mac", "macaddr", "macAddress"))
    type: Optional[str] = Field(None, alias=AliasChoices("type", "device_type", "deviceType"))
    model: Optional[str] = None
    sku: Optional[str] = Field(None, alias=AliasChoices("aruba_part_no", "sku", "PartNumber"))
    services: Optional[List[str] | str] = Field(None, alias=AliasChoices("license", "services", "tier"))
    subscription_key: Optional[str] = Field(None, alias=AliasChoices("subscription_key", "key"))
    subscription_expires: Optional[int] = Field(None, alias=AliasChoices("subscription_expires", "end_time"))
    assigned: Optional[bool] = None
    archived: Optional[bool] = None


class Inventory(RootModel):
    root: List[InventoryDevice]

    def __init__(self, data: List[dict]) -> None:
        formatted = self.prep_for_cache(data)
        super().__init__([InventoryDevice(**d) for d in formatted])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    def prep_for_cache(self, data: List[Dict[str, str | int | float]]):
        def format_value(key: str, value: str, device: Dict[str, str | int | float]) -> str:
            if key.startswith("mac"):
                return self._normalize_mac(value)
            if key in ["device_type", "type", "deviceType"]:
                return self._inv_type(value, model=device.get("model"))
            if key == "subscription_expires" and value:
                return value if len(str(value)) == 10 else value / 1000  # convert ts in ms to ts in seconds
            return value

        return [{k: format_value(k, v, device=dev) for k, v in dev.items()} for dev in data]

    @staticmethod
    def _inv_type(dev_type: str | None, model: str | None) -> DevType | None:
        if dev_type is None:  # Only occurs when import data is passed into this model, inventory data from API should have the type
            return None

        if dev_type == "SWITCH":  # SWITCH, AP, GATEWAY
            aos_sw_models = ["2530", "2540", "2920", "2930", "3810", "5400"]  # current as of 2.5.8 not expected to change.  MAS not supported.
            return "sw" if model[0:4] in aos_sw_models else "cx"

        return "gw" if dev_type == "GATEWAY" else dev_type.lower()

    @staticmethod
    def _normalize_mac(mac: str) -> str:
        mac_out = utils.Mac(mac)
        if not mac_out.ok:
            log.warning(f"MAC Address {mac} passed into Inventory via import does not appear to be valid.", show=True, caption=True, log=True)
        return mac_out.cols.upper()

    @property
    def by_serial(self) -> Dict[int, Dict[str, str | int | float]]:
        return {s.serial: s.model_dump() for s in self.root}

    @cached_property
    def counts(self) -> str:
        _expired_cnt = len([s for s in self.root if s.subscription_expires and pendulum.now(tz="UTC") >= pendulum.from_timestamp(s.subscription_expires)])
        _ok_cnt = len(self) - _expired_cnt
        _exp_in_3_mos_cnt = len([s for s in self.root if s.subscription_expires and pendulum.now(tz="UTC") + pendulum.duration(months=3) >= pendulum.from_timestamp(s.subscription_expires)])
        _exp_in_3_mos_cnt -= _expired_cnt
        _exp_in_6_mos_cnt = len([s for s in self.root if s.subscription_expires and pendulum.now(tz="UTC") + pendulum.duration(months=6) >= pendulum.from_timestamp(s.subscription_expires)])
        _exp_in_6_mos_cnt -= _exp_in_3_mos_cnt
        count_str = f"[magenta]Subscription counts[/] Total: [cyan]{len(self)}[/], [green]Valid[/]: [cyan]{_ok_cnt}[/], [red]Expired[/]: [cyan]{_expired_cnt}[/]"
        if _exp_in_6_mos_cnt:
            count_str += f", [dark_orange3]Expiring within 6 months[/]: [cyan]{_exp_in_6_mos_cnt}[/]"
        if _exp_in_3_mos_cnt:
            count_str += f", [red]Expiring within 3 months[/]: [cyan]{_exp_in_3_mos_cnt}[/]"

        return count_str


    def cache_dump(self) -> list[dict[str, str | int | bool]]:
        return utils.strip_no_value(self.model_dump())

class DeviceStatus(str, Enum):
    Up = "Up"
    Down = "Down"


class Device(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    name: str
    status: DeviceStatus
    type: DevType = Field(alias=AliasChoices("type", "switch_type", "device_type"))
    model: str
    ip: str = Field(None, alias="ip_address")  # can't use IPvAnyAddress here as stack members do not have IP addresses
    mac: str = Field(alias="macaddr")
    serial: str
    group: str = Field(alias="group_name")
    site: Optional[str] = Field(None, alias=AliasChoices("site", "site_name"))
    version: str = Field(alias="firmware_version")
    swack_id: Optional[str] = Field(None, alias=AliasChoices("swack_id", "stack_id", "swarm_id"))
    switch_role: Optional[int] = Field(None)

    @field_validator("type", mode="before")
    @classmethod
    def transform_dev_type(cls, dev_type: str) -> DevType:
        if dev_type == "ArubaCX":
            return DevType.cx

        if dev_type == "ArubaSwitch":
            return DevType.sw

        if dev_type == "MC":
            return DevType.gw

        return DevType(dev_type)


class Devices(BaseModel):
    aps: Optional[List[Device]] = Field([])
    switches: Optional[List[Device]] = Field([])
    gateways: Optional[List[Device]] = Field([])


class Site(BaseModel):
    name: str = Field()
    id: int = Field()
    address: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    state: Optional[str] = Field(None)
    zip: Optional[str] = Field(None, alias=AliasChoices("zipcode", "zip"))  # str because zip+4 with hyphen may be possible
    country: Optional[str] = Field(None)
    lon: Optional[float] = Field(None, alias=AliasChoices("longitude", "lon"))
    lat: Optional[float] = Field(None, alias=AliasChoices("latitude", "lat"))
    devices: Optional[int] = Field(0, alias=AliasChoices("associated_device_count", "devices", "associated devices"))  # field in prev cache had space "associated devices"


class Sites(RootModel):
    root: List[Site]

    def __init__(self, data: List[dict]) -> None:
        formatted = self.prep_for_cache(data)
        super().__init__([Site(**g) for g in formatted])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    def prep_for_cache(self, data: List[Dict[str, str | int | float]]):
        def cache_keys(key: str) -> str:
            short_keys = {"longitude": "lon", "latitude": "lat", "zipcode": "zip"}

            return short_keys.get(key, key).removeprefix("site_")

        strip_keys = ["site_details", "associated devices", "associated_device_count"]
        return [
            {
                **{cache_keys(k): v for k, v in s.items() if k not in strip_keys},
                **s.get("site_details", {}),
                "devices": s.get("associated_device_count", s.get("associated devices", s.get("devices", 0))),
            }
            for s in data
        ]

    @property
    def by_id(self) -> Dict[int, Dict[str, str | int | float]]:
        return {s.id: s.model_dump() for s in self.root}


class GatewayRole(str, Enum):
    branch = "branch"
    vpnc = "vpnc"
    wlan = "wlan"
    sdwan = "sdwan"
    NA = "NA"


class Group(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    name: str = Field(alias=AliasChoices("name", "group"))
    allowed_types: List[DevTypes] = Field(["ap", "gw", "cx", "sw"], alias=AliasChoices("allowed_types", "types", "AllowedDevTypes"))
    gw_role: Optional[GatewayRole] = Field(None, alias=AliasChoices("gw_role", "GwNetworkRole"))
    aos10: Optional[bool | Literal["NA"]] = None
    microbranch: Optional[bool | Literal["NA"]] = None
    wlan_tg: Optional[bool] = Field(
        False,
    )
    wired_tg: Optional[bool] = Field(
        False,
    )
    monitor_only_sw: Optional[bool] = Field(
        False,
    )
    monitor_only_cx: Optional[bool] = Field(
        False,
    )
    cnx: Optional[bool] = False
    gw_config: Optional[Path] = Field(None, exclude=True)
    ap_config: Optional[Path] = Field(None, exclude=True)
    gw_vars: Optional[Path] = Field(None, exclude=True)
    ap_vars: Optional[Path] = Field(None, exclude=True)


class Groups(RootModel):
    root: List[Group]

    def __init__(self, data: List[dict]) -> None:
        formatted = self.format_data(data)
        super().__init__([Group(**g) for g in formatted])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.model_dump())

    @staticmethod
    def format_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def str_to_list(v: DevTypes | List[DevTypes]) -> List[DevTypes]:
            if isinstance(v, str) and " " in v:  # csv import we allow space separted for types on csv
                return v.split()
            return v if isinstance(v, list) else [v]

        if not data or "properties" not in data[0]:
            return [{k.replace("-", "_"): v if k not in ["types", "allowed_types"] else str_to_list(v) for k, v in inner.items()} for inner in data]  # from batch import file

        # from central.get_all_groups response
        aos_version_map = {"AOS_10X": "AOS10", "AOS_8X": "AOS8", "NA": "NA"}
        allowed_dev_types = {"Gateways": "gw", "AccessPoints": "ap", "AOS_CX": "cx", "AOS_S": "sw", "SD_WAN_Gateway": "sdwan"}
        # Architecture can be AOS10, Instant, or SD_WAN_Gateway.  Provides no value, as that can be derived from AOSVersion / AllowedDevTypes
        # GwNetworkRole can be WLANGateway, VPNConcentrator, BranchGateway
        # WE combine the 2 and extend GwNetworkRole to also include sdwan (Based on AllowedDevTypes, as sdwan can only be in a group by itself.)
        gw_role_map = {"WLANGateway": "wlan", "VPNConcentrator": "vpnc", "BranchGateway": "branch", "sdwan": "sdwan", "NA": "NA"}
        captured_keys = ["AllowedDevTypes", "GwNetworkRole", "AOSVersion", "ApNetworkRole", "MonitorOnly", "NewCentral"]

        clean = []
        for g in data:
            properties = {
                "AllowedDevTypes": [
                    allowed_dev_types.get(dt) for dt in [*g["properties"].get("AllowedDevTypes", []), *g["properties"].get("AllowedSwitchTypes", [])] if dt != "Switches"
                ],
                "GwNetworkRole": gw_role_map[g["properties"].get("GwNetworkRole", "NA")],
                "aos10": "NA"
                if aos_version_map.get(g["properties"].get("AOSVersion", "NA"), "err") == "NA"
                else aos_version_map.get(g["properties"].get("AOSVersion", "NA"), "err") == "AOS10",
                "microbranch": "NA" if g["properties"].get("ApNetworkRole") is None else g["properties"]["ApNetworkRole"].lower() == "microbranch",
                "monitor_only_sw": "AOS_S" in g["properties"].get("MonitorOnly", []),
                "monitor_only_cx": "AOS_CX" in g["properties"].get("MonitorOnly", []),
                "cnx": g["properties"].get("NewCentral"),
            }
            # MonitorOnly is all we need MonitorOnlySwitch is a bool and is set True if AOS_S is in MonitorOnly, it's a legacy field.  The Create Group endpoint accepts the MonitorOnly List.
            extra = {k: g["properties"][k] for k in sorted(g["properties"].keys()) if k not in ["MonitorOnlySwitch", "AllowedSwitchTypes", *captured_keys]}

            template_info = {"wired_tg": g["template_details"].get("Wired", False), "wlan_tg": g["template_details"].get("Wireless", False)}

            clean += [{"name": g["group"], **extra, **properties, **template_info}]
            clean = [
                {k.replace("-", "_"): v for k, v in inner.items()} for inner in clean
            ]  # We allow hyphen in most inputs/import keys to be consistent with the CLI Options, but we always use _ to store the data.

        return clean


class Template(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    name: str
    device_type: DevType
    group: str
    model: str  # model as in sku here
    version: str
    template_hash: str


class Templates(RootModel):
    root: List[Template]

    def __init__(self, data: List[dict]) -> None:
        formatted = self.format_data(data)
        super().__init__([Template(**t) for t in formatted])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.model_dump())

    def format_data(self, data: List[Dict[str, str]]):
        if not isinstance(data, Iterable) or not all([isinstance(d, dict) for d in data]):
            return data
        lib_dev_types = {"MobilityController": "gw", "IAP": "ap", "CX": "cx", "ArubaSwitch": "sw"}
        return [{k: v if k != "device_type" else lib_dev_types.get(v, v) for k, v in inner.items()} for inner in data]


class Label(BaseModel):
    id: int = Field(alias="label_id")
    name: str = Field(alias="label_name")
    devices: Optional[int] = Field(0, alias=AliasChoices("devices", "associated_device_count"))


class Labels(RootModel):
    root: List[Label]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([Label(**g) for g in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.model_dump())


class ClientType(str, Enum):
    wired = "wired"
    wireless = "wireless"


# Client Cache  # TODO need to include attribute for TinyDB.Table doc_id
class Client(BaseModel):
    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True, json_encoders={DateTime: lambda dt: dt.ts})
    mac: str = Field(default_factory=str, alias=AliasChoices("macaddr", "mac"))
    name: str = Field(default_factory=str, alias=AliasChoices("name", "username"))
    ip: str = Field(default_factory=str, alias=AliasChoices("ip_address", "ip"))
    type: ClientType = Field(None, alias=AliasChoices("client_type", "type"))
    network_port: str = Field(None, alias=AliasChoices("network", "interface_port", "network_port"))
    connected_serial: str = Field(None, alias=AliasChoices("associated_device", "connected_serial"))
    connected_name: str = Field(None, alias=AliasChoices("associated_device_name", "connected_name"))
    site: Optional[str] = Field(
        None,
    )
    group: str = Field(None, alias=AliasChoices("group_name", "group"))
    last_connected: datetime | None = Field(None, alias=AliasChoices("last_connection_time", "last_connection"))

    @field_serializer("last_connected")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        if dt is None:  # TODO all with potential for there not to be a value need this
            return DateTime(None, "timediff")  # resolves PydanticSerializationError when model_dump_json is called on client with None for last_connected (Failed)

        return DateTime(dt.timestamp(), "timediff")

    @property
    def summary_text(self):
        parts = [self.name, self.mac, self.ip, self.connected_name]
        parts = utils.unique([p for p in parts if p is not None])
        return "[reset]" + "|".join([f"{'[cyan]' if idx in list(range(0, len(parts), 2)) else '[bright_green]'}{p}[/]" for idx, p in enumerate(parts)])

    def __contains__(self, item: str) -> bool:
        return item in self.model_dump()

    def __getitem__(self, item) -> str | datetime | None:
        return self.model_dump()[item]

    def get(self, item: str, default: Any = None) -> Any:
        return self.model_dump().get(item, default)

    def keys(self) -> KeysView:
        return self.model_dump().keys()

    @property
    def help_text(self):
        return [tuple([self.name, f"{self.ip}|{self.mac} type: {self.type} connected to: {self.connected_name} ~ {self.network_port}"])]


class Clients(RootModel):
    root: List[Client]

    def __init__(self, data: List[dict]) -> None:
        formatted = self.prep_for_cache(data)
        super().__init__([Client(**c) for c in formatted])

    @staticmethod
    def prep_for_cache(data: List[Dict[str, str | int]]) -> List[Dict[str, str | int]]:
        return [{k: v if k not in ["client_type", "type"] else v.lower() for k, v in inner.items()} for inner in data]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    @property
    def by_mac(self) -> Dict[str, Any]:  # Nedd to use model_dump_json to use models JsonEncoder
        return {c.mac or f"NOMAC_{randint(100_000, 999_999)}": json.loads(c.model_dump_json()) for c in self.root}


class MpskNetwork(BaseModel):
    id: str
    name: str = Field(alias=AliasChoices("ssid", "name"))


class MpskNetworks(RootModel):
    root: List[MpskNetwork]

    def __init__(self, data: List[dict]) -> None:
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        super().__init__([MpskNetwork(**m) for m in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)


class Mpsk(BaseModel):
    id: str
    name: str
    role: str
    status: MpskStatus
    ssid: Optional[str] = None  # We add the SSID / MPSK network associated when fetching all Named MPSKs across all SSIDs
    # mpsk: str  #  We don't store the psk in the cache

class Mpsks(RootModel):
    root: List[Mpsk]

    def __init__(self, data: List[dict]) -> None:
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        super().__init__([Mpsk(**m) for m in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)


# Not Used currently, PortalsAuthType. For reference this is what auth_type_num List[int] in portal payload maps to
# auth_type field is ', ' seperated field showing text description of auth types: 'Username/Password, Self-Registration'
class PortalAuthType(Enum):
    anon = 0
    user_pass = 1
    self_reg = 2


class Portal(BaseModel):
    name: str
    id: str
    url: str = Field(alias=AliasChoices("url", "capture_url"))
    auth_type: str
    # auth_types: Optional[List[PortalAuthType]] = Field(None, alias=AliasChoices("auth_type_num", "auth_types"))
    is_aruba_cert: bool
    is_default: bool
    is_editable: bool
    is_shared: bool
    reg_by_email: bool = Field(alias=AliasChoices("register_accept_email", "reg_by_email"))
    reg_by_phone: bool = Field(alias=AliasChoices("register_accept_phone", "reg_by_phone"))


class Portals(RootModel):
    root: List[Portal]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([Portal(**p) for p in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)


class Cert(BaseModel):
    model_config = ConfigDict(use_enum_values=True,)
    name: str = Field(alias=AliasChoices("name", "cert_name"))
    type: CertTypes = Field(alias=AliasChoices("type", "cert_type"))
    md5_checksum: str = Field(alias=AliasChoices("md5_checksum", "cert_md5_checksum"))
    # sha1_checksum: str = Field(alias=AliasChoices("sha1_checksum", "cert_sha1_checksum"))  # We don't need this in cache as we don't use it for anything
    expired: bool = Field(alias=AliasChoices("expired", "expire"))
    expiration: int = Field(alias=AliasChoices("expiration", "expire_date"))

    @field_validator("expiration", mode="before")
    @classmethod
    def convert_expiration(cls, expiration: str) -> int:
        return pendulum.from_format(expiration.rstrip("Z"), "YYYYMMDDHHmmss").int_timestamp


class Certs(RootModel):
    root: List[Cert]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([Cert(**p) for p in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)


class Guest(BaseModel):
    portal_id: str
    name: str
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = Field(None, alias=AliasChoices("company", "company_name"))
    enabled: bool = Field(None, alias=AliasChoices("is_enabled", "enabled"))
    status: Optional[str] = None
    created: int = Field(alias=AliasChoices("created", "created_at"))
    expires: Optional[int] = Field(None, alias=AliasChoices("expires", "expire_at"))


class Guests(RootModel):
    root: List[Guest]

    def __init__(self, portal_id: str, data: List[dict]) -> None:
        data = self._flatten_guest_data(data)
        super().__init__([Guest(**{"portal_id": portal_id, **p}) for p in data])

    @staticmethod
    def _flatten_guest_data(data: List[Dict[str, str | int]]) -> List[Dict[str, str | int]]:
        return [{**{k: v for k, v in inner.items() if k != ["user"]}, **inner.get("user", {})} for inner in data]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)
