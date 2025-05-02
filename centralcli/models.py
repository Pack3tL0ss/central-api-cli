from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from random import randint
from typing import TYPE_CHECKING, Annotated, Any, Dict, Iterable, List, Literal, Optional

import pendulum
from pydantic import AliasChoices, BaseModel, BeforeValidator, ConfigDict, Field, RootModel, field_serializer, field_validator, model_validator
from rich.console import Console
from typing_extensions import Self

from centralcli import log, utils
from centralcli.constants import DevTypes, DynamicAntMode, RadioBandOptions, SiteStates, state_abbrev_to_pretty
from centralcli.objects import DateTime

if TYPE_CHECKING:
    from collections.abc import KeysView


# This is the same as DevTypes (plural in constants) other than DevTypes includes sdwan.
# Could probably use same model for everything in here.  One or the other.
class DevType(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"


# fields from Response.output after cleaner
class InventoryDevice(BaseModel):
    serial: str
    mac: str = Field(alias=AliasChoices("mac", "macaddr"))
    type: Optional[str] = Field(None, alias=AliasChoices("type", "device_type"))
    model: Optional[str] = None
    sku: Optional[str] = Field(None, alias=AliasChoices("aruba_part_no", "sku"))
    services: Optional[List[str] | str] = Field(None, alias=AliasChoices("license", "services"))
    subscription_key: Optional[str] = None
    subscription_expires: Optional[int] = None


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
            if key in ["device_type", "type"]:
                return self._inv_type(value, model=device.get("model"))
            if key == "subscription_expires" and value:
                return value / 1000  # convert ts in ms to ts in seconds
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


class ImportSite(BaseModel):
    # model_config = ConfigDict(extra="allow", use_enum_values=True)
    model_config = ConfigDict(use_enum_values=True)
    site_name: str = Field(..., alias=AliasChoices("site_name", "site", "name"))
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None  # Field(None, min_length=3)
    zipcode: Optional[str | int] = Field(None, alias=AliasChoices("zip", "zipcode"))
    latitude: Optional[str | float] = Field(None, alias=AliasChoices("lat", "latitude"))
    longitude: Optional[str | float] = Field(None, alias=AliasChoices("lon", "longitude"))

    @field_validator("state")
    @classmethod
    def short_to_long(cls, v: str) -> str:
        if v.lower() == "district of columbia":
            return "District of Columbia"

        try:
            return SiteStates(state_abbrev_to_pretty.get(v.upper(), v.title())).value
        except ValueError:
            return SiteStates(v).value


class ImportSites(RootModel):
    root: List[ImportSite]

    def __init__(self, data: List[Dict[str, Any]]) -> None:
        formatted = self._convert_site_key(data)
        super().__init__([ImportSite(**s) for s in formatted])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    @staticmethod
    def _convert_site_key(_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def auto_usa(data: Dict[str, str | int | float]) -> str | None:
            _country = data.get("country", "")
            if _country.isdigit():  # Data from large customer had country as '1' for some sites
                _country = ""

            if not _country and data.get("state") and data["state"].upper() in [kk.upper() for k, v in state_abbrev_to_pretty.items() for kk in [k, v]]:
                return "United States"
            if _country.upper() in ["USA", "US"]:
                return "United States"

            return _country or None

        _data = [
            {
                **inner.get("site_address", {}),
                **inner.get("geolocation", {}),
                **{k: v for k, v in inner.items() if k not in ["site_address", "geolocation"]},
                "country": auto_usa(inner),
            }
            for inner in _data
        ]
        # _data = {_site_aliases.get(k, k): v for k, v in _data.items()}
        return _data


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


class WidsItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    acknowledged: Optional[bool] = Field(default=None)
    containment_status: Optional[str] = Field(default_factory=str)
    classification: Optional[str] = Field(default_factory=str)
    classification_method: Optional[str] = Field(default_factory=str)
    cust_id: Optional[str] = Field(default_factory=str)
    encryption: Optional[str] = Field(default_factory=str)
    first_det_device: Optional[str] = Field(default_factory=str)
    first_det_device_name: Optional[str] = Field(default_factory=str)
    first_seen: Optional[datetime] = Field(default=None)
    group: Optional[str] = Field(default_factory=str, alias=AliasChoices("group_name", "group"))
    id: Optional[str] = Field(default_factory=str)
    labels: Optional[str] = Field(default_factory=str)
    lan_mac: Optional[str] = Field(default_factory=str)
    last_det_device: Optional[str] = Field(default_factory=str)
    last_det_device_name: Optional[str] = Field(default_factory=str)
    last_seen: Optional[datetime] = Field(default=None)
    mac_vendor: Optional[str] = Field(default_factory=str)
    name: Optional[str] = Field(default_factory=str)
    signal: Optional[int] = Field(default_factory=int)
    ssid: Optional[str] = Field(default_factory=str)

    @field_serializer("first_seen", "last_seen")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        return DateTime(dt.timestamp(), "mdyt")


class Wids(RootModel):
    root: List[WidsItem]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([WidsItem(**w) for w in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.model_dump())


# SNOW Response
class SysTargetSysId(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class SysImportSet(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class ImportSetRun(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class SysTransformMap(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class Result(BaseModel):
    u_comments_to_customer: Optional[str] = None
    template_import_log: Optional[str] = None
    u_service_offering: Optional[str] = None
    sys_updated_on: Optional[str] = None
    u_urgency: Optional[str] = None
    sys_target_sys_id: SysTargetSysId
    u_watch_list: Optional[str] = None
    u_reported_by: Optional[str] = None
    u_business_service: Optional[str] = None
    sys_updated_by: Optional[str] = None
    u_short_description: Optional[str] = None
    sys_created_on: Optional[str] = None
    sys_import_set: SysImportSet
    u_additional_comments: Optional[str] = None
    sys_created_by: Optional[str] = None
    sys_import_row: Optional[str] = None
    sys_row_error: Optional[str] = None
    u_work_notes: Optional[str] = None
    u_subcategory: Optional[str] = None
    u_state: Optional[str] = None
    u_attachment_type: Optional[str] = None
    import_set_run: ImportSetRun
    u_contact_type: Optional[str] = None
    u_attachment_encoded_code: Optional[str] = None
    u_description: Optional[str] = None
    u_close_notes: Optional[str] = None
    u_call_back: Optional[str] = None
    sys_import_state_comment: Optional[str] = None
    sys_class_name: Optional[str] = None
    u_priority: Optional[str] = None
    sys_id: Optional[str] = None
    u_external_source: Optional[str] = None
    sys_transform_map: SysTransformMap
    u_external_ticket: Optional[str] = None
    u_servicenow_number: Optional[str] = None
    u_resolved_by_group: Optional[str] = None
    u_assigned_to: Optional[str] = None
    u_raised_severity: Optional[str] = None
    u_hold_reason: Optional[str] = None
    sys_target_table: Optional[str] = None
    sys_mod_count: Optional[str] = None
    u_assignment_group: Optional[str] = None
    u_affected_user: Optional[str] = None
    u_impact: Optional[str] = None
    sys_tags: Optional[str] = None
    sys_import_state: Optional[str] = None
    u_contact_number: Optional[str] = None
    u_category: Optional[str] = None
    u_cause_code: Optional[str] = None
    u_close_code: Optional[str] = None
    u_configuration_item: Optional[str] = None
    u_cause_sub_code: Optional[str] = None
    u_attachment_name: Optional[str] = None


class SnowResponse(Result):
    result: Result


# WebHook Models WebHookDetails no reliable source for all possible fields.
class WebHookDetails(BaseModel):  # extra="allow"):  Pydantic 2.x
    customer_id: Optional[str] = None
    rule_number: Optional[str] = Field(None, alias="_rule_number")
    name: Optional[str] = None
    ap_model: Optional[str] = None
    group: Optional[str] = None
    labels: Optional[List[str]] = []
    params: Optional[List[str]] = []
    serial: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[str] = None
    threshold: Optional[str] = None
    time: Optional[str] = None
    site: Optional[str] = Field(None, alias="site_name")
    device: Optional[str] = None
    ssid: Optional[str] = None
    sub_message: Optional[str] = None
    labels: Optional[List[str]] = []  # sometimes a comma sep str
    delay: Optional[str] = None
    ts: Optional[str] = None
    group_name: Optional[str] = None
    conn_status: Optional[str] = None
    unit: Optional[str] = None
    ds_key: Optional[str] = None
    alert_key: Optional[str] = None
    _band: Optional[str] = None
    _radio_num: Optional[str] = None
    channel: Optional[str] = None
    client_count: Optional[int] = None  # converting from str
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    alias_map_name: Optional[str] = None
    mac: Optional[str] = None
    ip: Optional[str] = Field(None, alias="ip_address")
    max_value_for_percentage: Optional[str] = None
    intf_name: Optional[str] = None
    mode: Optional[str] = None
    old_serial: Optional[str] = None
    old_mac: Optional[str] = None
    new_serial: Optional[str] = None
    new_mac: Optional[str] = None
    host: Optional[str] = Field(None, alias="hostname")
    stack_id: Optional[str] = None
    mem_id: Optional[str] = None
    role: Optional[List[str]] = None
    action: Optional[str] = None
    pr1: Optional[str] = None
    pr2: Optional[str] = None
    host1: Optional[str] = None
    host2: Optional[str] = None
    gateway1: Optional[str] = None
    gateway2: Optional[str] = None
    ip1: Optional[str] = None
    ip2: Optional[str] = None
    serial1: Optional[str] = None
    serial2: Optional[str] = None
    type: Optional[str] = None
    nbr_addr: Optional[str] = None
    nbr_as: Optional[str] = None
    nbr_id: Optional[str] = None
    count: Optional[int] = None  # convert from str
    max: Optional[int] = None  # convert from str
    default_gw_status: Optional[str] = None
    uplink_tag: Optional[str] = None
    link_tag: Optional[str] = None
    status: Optional[str] = None
    current_status: Optional[str] = None
    speed: Optional[str] = None
    new_speed: Optional[str] = None
    reason: Optional[str] = None
    vm_id: Optional[str] = None
    account_name: Optional[str] = None
    region_id: Optional[str] = None
    customer_name: Optional[str] = None
    health: Optional[str] = None
    vpc_id: Optional[str] = None
    provider_name: Optional[str] = None
    cluster_name: Optional[str] = Field(None, alias="cluster-name")


class WebHook(BaseModel):
    id: Optional[str] = None
    nid: Optional[int] = None
    alert_type: Optional[str] = None
    setting_id: Optional[str] = None
    device_id: Optional[str] = None
    description: Optional[str] = None
    state: Optional[str] = None
    severity: Optional[str] = None
    operation: Optional[str] = None
    timestamp: Optional[int] = None
    details: Optional[dict] = None  # Prob need to use dict here or allow extra fields
    webhook: Optional[str] = None
    text: Optional[str] = None


# _example_snow_payload = {
#         "u_affected_user": "blah",
#         "u_assignment_group":"TE-sn-servicenow",
#         "u_business_service": "",
#         "u_call_back": False,
#         "u_category": "",
#         "u_contact_type": "integration",
#         "u_description": "",
#         "u_configuration_item": "valid snow config item",
#         "u_external_source": "40 chars",
#         "u_external_ticket": "40 chars",
#         "u_raised_severity": 2,
#         "u_reported_by": "valid TE ID",
#         "u_servicenow_number": "Only on Update",
#         "u_service_offering": "snow valid service offering",
#         "u_short_description":"Test Ticket Mandatory Create 160 char",
#         "u_state": "resolved",
#         "u_subcategory": "must be valid sub cat of cat",
#         "u_work_notes": "4000 chars",
#         "u_attachment_name":"Integration_Sample.txt",
#         "u_attachment_type":"text/plain",
#         "u_attachment_encoded_code":"SW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA==",
#         "u_impact": 2,
#         "u_urgency": 2,
#         "u_watch_list":"TE308801,TE163762"
#     }


class HighMedLow(str, Enum):
    High = 1
    Medium = 2
    Low = 3


class SnowCreate(BaseModel):
    u_affected_user: Optional[str] = None
    u_assignment_group: str
    u_business_service: Optional[str] = None
    u_call_back: Optional[bool] = None
    u_category: Optional[str] = None
    u_contact_type: Optional[str] = None
    u_description: Optional[str] = None
    u_configuration_item: Optional[str] = None
    u_external_source: Optional[str] = None
    u_external_ticket: Optional[str] = None
    u_raised_severity: Optional[int] = None
    u_reported_by: Optional[str] = None
    u_service_offering: Optional[str] = None
    u_short_description: str  # = Field(..., le=160)
    u_state: Optional[str] = None
    u_subcategory: Optional[str] = None
    u_work_notes: Optional[str] = None
    u_attachment_name: Optional[str] = None
    u_attachment_type: Optional[str] = None
    u_attachment_encoded_code: Optional[str] = None
    u_impact: Optional[HighMedLow] = None
    u_urgency: Optional[HighMedLow] = None
    u_watch_list: Optional[str] = None


class SnowUpdate(BaseModel):
    u_affected_user: Optional[str] = None
    u_assignment_group: Optional[str] = None
    u_business_service: Optional[str] = None
    u_call_back: Optional[bool] = None
    u_category: Optional[str] = None
    u_contact_type: Optional[str] = None
    u_description: Optional[str] = None
    u_configuration_item: Optional[str] = None
    u_external_source: Optional[str] = None
    u_external_ticket: Optional[str] = None
    u_raised_severity: Optional[int] = None
    u_reported_by: Optional[str] = None
    u_servicenow_number: str
    u_service_offering: Optional[str] = None
    u_short_description: Optional[str] = None
    u_state: Optional[str] = None
    u_subcategory: Optional[str] = None
    u_work_notes: Optional[str] = None
    u_attachment_name: Optional[str] = None
    u_attachment_type: Optional[str] = None
    u_attachment_encoded_code: Optional[str] = None
    u_impact: Optional[HighMedLow] = None
    u_urgency: Optional[HighMedLow] = None
    u_watch_list: Optional[str] = None


# get_user_accounts
class Scope(BaseModel):
    groups: List[str]
    labels: List
    sites: List


class InfoItem(BaseModel):
    role: str
    scope: Scope


class Application(BaseModel):
    info: List[InfoItem]
    name: str


class Name(BaseModel):
    firstname: str
    lastname: str


class Item(BaseModel):
    applications: List[Application]
    name: Name
    system_user: bool
    username: str


class UserAccounts(BaseModel):
    items: List[Item]
    total: int


class CloudAuthUploadStats(BaseModel):
    completed: int
    failed: int
    total: int


class CloudAuthUploadResponse(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: pendulum.from_timestamp(v).to_day_datetime_string(),
        },
    )
    details: Dict[str, Any]
    status: str
    stats: CloudAuthUploadStats
    submittedAt: datetime
    lastUpdatedAt: datetime
    durationNanos: int
    fileName: str

    @field_serializer("lastUpdatedAt", "submittedAt")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        return DateTime(dt.timestamp())


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


# Not Used currently, For reference this is what auth_type_num List[int] in portal payload maps to
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


def _str_to_list(value: str | int | float | List[Enum] | List[str] | List[int, float]) -> None | List[str]:
    """Allows import file to be a space or quoted comma separated str vs. a list

    useful for csv.  A comma seperated str (wrapped in quotes in the csv) is also valid.
    i.e. '2.4 5 6' would return ["2.4", "5", "6"]

    Args:
        value (str | int | float | List[Enum] | List[str] | List[int, float]): The value of the field

    Returns:
        None | List[str]: None if the field is not in the import file or has no value otherwise
            returns a list based on the value(s) provided.
    """
    if value is None:
        return value

    if isinstance(value, list):
        if value and hasattr(value[0], "value"):
            return [v.value for v in value]

        return list(map(str, value))

    if isinstance(value, (int, float)):  # possible with yaml/json import
        return [str(value)]

    if "," in value:
        return [v.strip() for v in map(str, value.split(","))]

    if " " in value:
        return list(map(str, value.split()))

    return utils.listify(value)


class APUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    serial: str
    hostname: Optional[str] = None
    ip: Optional[str] = None
    mask: Optional[str] = None
    gateway: Optional[str] = None
    dns: Annotated[List[str], BeforeValidator(_str_to_list)] = None
    domain: Optional[str] = None
    disable_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    enable_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    access_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    monitor_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    spectrum_radios: Annotated[List[RadioBandOptions], BeforeValidator(_str_to_list)] = None
    flex_dual_exclude: Optional[RadioBandOptions] = None
    dynamic_ant_mode: Optional[DynamicAntMode] = Field(None, alias=AliasChoices("antenna_width", "dynamic_ant_mode"))
    uplink_vlan: Optional[int] = Field(None, alias=AliasChoices("uplink_vlan", "tagged_uplink_vlan"))
    gps_altitude: Optional[float] = None

    def __str__(self):
        console = Console(force_terminal=False, emoji=False)
        with console.capture() as cap:
            console.print(self.__rich__())
        return cap.get()

    def __rich__(self):
        iden = f"[bright_green]{self.serial}[/]"
        items = "|".join(
            [
                f"{field}: {getattr(self, field) if not isinstance(getattr(self, field), list) else ','.join(getattr(self, field))}"
                for field in self.model_fields_set
                if field != "serial" and getattr(self, field) is not None
            ]
        )
        reboot_msg = "\u267b  " if self.ip else ""  # \u267b :recycle: ♻
        return f"{reboot_msg}{iden}|{items}"

    @model_validator(mode="after")
    def validate_radio_modes(self) -> Self:
        radios = ["2.4", "5", "6"]
        enable_radios = self.enable_radios or []
        disable_radios = self.disable_radios or []
        access_radios = self.access_radios or []
        monitor_radios = self.monitor_radios or []
        spectrum_radios = self.spectrum_radios or []
        checks = [
            {"values": [*disable_radios, *enable_radios], "msg": "radio set to be both enabled and disabled. Which makes no sense."},
            {"values": [*access_radios, *monitor_radios, *spectrum_radios], "msg": "radio defined multiple modes (access, monitor, spectrum)."},
        ]
        for c in checks:
            for r in radios:
                if c["values"].count(r) > 1:
                    ap_iden = self.serial if not self.hostname else f"{self.hostname} ({self.serial})"
                    raise ValueError(f"Invalid import data for {ap_iden},  {r}Ghz {c['msg']}")

        return self

    @model_validator(mode="after")
    def validate_ip_fields(self) -> Self:
        ap_iden = self.serial if not self.hostname else f"{self.hostname} ({self.serial})"
        if self.ip and self.ip.lower() == "dhcp":
            if any([self.mask, self.gateway]):
                raise ValueError(f"Invalid import data for {ap_iden}, mask and gateway are not expected if ip is being set to dhcp")

            # reset static IP values to default (for DHCP)  This is the default so only necessary when changing an AP that previously had a static IP
            self.ip = self.mask = self.gateway = "0.0.0.0"
            # Unsure if static DNS/domain can be configured with dynamic IP
            self.dns = self.dns or ["0.0.0.0"]
            self.domain = self.domain or ""

        elif any([self.ip, self.mask, self.gateway]) and not all([self.ip, self.mask, self.gateway, self.dns]):  # unsure if dns by itself is valid.
            raise ValueError(f"Invalid import data for {ap_iden},  if any of ip, mask, gateway are provided all of ip, mask, gateway, and dns must be provided")

        return self

    @staticmethod
    def _parse_disable_radio_values(enable_radios: None | list, disable_radios: None | list) -> tuple:
        if not disable_radios and not enable_radios:
            return None, None, None

        radio_24_disable = None if not enable_radios or "2.4" not in enable_radios else False
        radio_5_disable = None if not enable_radios or "5" not in enable_radios else False
        radio_6_disable = None if not enable_radios or "6" not in enable_radios else False

        if disable_radios:
            if radio_24_disable is None and "2.4" in disable_radios:
                radio_24_disable = True
            if radio_5_disable is None and "5" in disable_radios:
                radio_5_disable = True
            if radio_6_disable is None and "6" in disable_radios:
                radio_6_disable = True

        return radio_24_disable, radio_5_disable, radio_6_disable

    @staticmethod
    def _parse_radio_mode_values(
        access_radios: None | list,
        monitor_radios: None | list,
        spectrum_radios: None | list,
    ) -> tuple:
        radio_24_mode, radio_5_mode, radio_6_mode = None, None, None
        modes = ["access", "monitor", "spectrum"]
        for mode, radios in zip(modes, [access_radios, monitor_radios, spectrum_radios]):
            if radios is None:
                continue
            if radio_24_mode is None:
                radio_24_mode = None if "2.4" not in radios else mode
            if radio_5_mode is None:
                radio_5_mode = None if "5" not in radios else mode
            if radio_6_mode is None:
                radio_6_mode = None if "6" not in radios else mode

        return radio_24_mode, radio_5_mode, radio_6_mode

    @property
    def api_params(self):
        radios_24_diable, radio_5_disable, radio_6_disable = self._parse_disable_radio_values(self.enable_radios, self.disable_radios)
        radio_24_mode, radio_5_mode, radio_6_mode = self._parse_radio_mode_values(self.access_radios, self.monitor_radios, self.spectrum_radios)
        kwargs = {
            **{k: v for k, v in self.model_dump().items() if k not in ["gps_altitude"] and not k.endswith("_radios")},
            **{
                "radio_24_disable": radios_24_diable,
                "radio_5_disable": radio_5_disable,
                "radio_6_disable": radio_6_disable,
                "radio_24_mode": radio_24_mode,
                "radio_5_mode": radio_5_mode,
                "radio_6_mode": radio_6_mode,
            },
        }

        return kwargs


class APUpdates(RootModel):
    root: List[APUpdate]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([APUpdate(**ap) for ap in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)
