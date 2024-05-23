from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union, Dict, Any

import pendulum
from pydantic import BaseModel, Field, validator, IPvAnyAddress



class DeviceStatus(str, Enum):
    Up = "Up"
    Down = "Down"

# TODO This is a dup of DevTypes from constants verify if can import w/out circular issues
class DevType(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"

class TemplateDevType(str, Enum):
    MobilityController = "MobilityController"
    IAP = "IAP"
    CX = "CX"
    ArubaSwitch = "ArubaSwitch"

# fields from Response.output after cleaner
class Inventory(BaseModel):
    type: str
    model: Optional[str]
    sku: Optional[str]
    mac: str
    serial: str
    services: Union[List[str], str] = Field(alias="license")

# Not used yet  None of the Cache models below are currently used.
# TODO have Cache return model for attribute completion support in IDE
class Device(BaseModel):
    name: str
    status: DeviceStatus
    type: DevType
    model: str
    ip: IPvAnyAddress
    mac: str
    serial: str
    group: str
    site: str
    version: str
    swack_id: Optional[str] = None  # Would need to convert swarm_id (ap) and stack_id (cx, sw) to common swack_id

class Site(BaseModel):
    name: str
    id: int
    address: str
    city: str
    state: str
    zipcode: str    # str because zip+4 with hyphen may be possible
    country: str
    longitude: str  # could do float here
    latitude: str   # could do float here
    associated_devices: int  # field in cache actually has space "associated devices"

class Template_Group(BaseModel):
    Wired: bool
    Wireless: bool

class Group(Template_Group):
    name: str
    template_group: Template_Group

class Template(BaseModel):
    device_type: TemplateDevType
    group: str
    model: str  # model as in sku here
    name: str
    template_hash: str
    version: str

class Label(BaseModel):
    name: str


class ClientType(str, Enum):
    WIRED = "WIRED"
    WIRELESS = "WIRELESS"

# Client Cache
class Client(BaseModel):
    mac: str = Field(default_factory=str)
    name: str = Field(default_factory=str)
    ip: str = Field(default_factory=str)
    type: str = Field(default_factory=str)
    connected_port: str = Field(default_factory=str)
    connected_serial: str = Field(default_factory=str)
    connected_name: str = Field(default_factory=str)
    site: str = Field(default_factory=str)
    group: str = Field(default_factory=str)
    last_connected: datetime = Field(default=None)



class Event(BaseModel):
    id: int
    device: str  # formatted str from cleaner i.e. "av-655.21af-ap|CNXXYYZZN Group: WadeLab"
    details: dict  # Not reliable source for the fields that are possible here
    connected_port: str  # The Wired interface or WLAN SSID
    connected_serial: str
    connected_name: str

class Logs(BaseModel):
    """Audit logs model

    We only store id and long_id so user can gather more details using long_id
    actual Audit log details pulled from Central on demand, but not cached.
    """
    id: int
    long_id: str

class WebHookState(str, Enum):
    Open = "Open"
    Close = "Close"

# TODO 2 enums below are repeats of what is already defined in constants.  import or move all to here?
class AllowedGroupDevs(str, Enum):
    ap = "ap"
    gw = "gw"
    cx = "cx"
    sw = "sw"

class GatewayRole(str, Enum):
    branch = "branch"
    vpnc = "vpnc"
    wlan = "wlan"

# TODO clibranch already had a model built for this, this isn't used, but consider moving models out of clibatch to here
class GroupImport(BaseModel):
    group: str = Field(..., alias="name")
    allowed_types: List[AllowedGroupDevs] = ["ap", "gw", "cx"]
    wired_tg: bool = False
    wlan_tg: bool = False
    aos10: bool = False
    microbranch: bool = False
    gw_role: GatewayRole = False
    monitor_only_sw: bool = False
    monitor_only_cx: bool = False


# This is what is in the cache for the hook-proxy
class WebHookData(BaseModel):
    id: str
    snow_incident_num: Optional[str] = None
    ok: bool
    alert_type: str
    device_id: str  # serial#
    state: WebHookState
    text: str
    timestamp: int  # could use datetime here

def pretty_dt(dt: datetime) -> str:
    return pendulum.from_timestamp(dt.timestamp(), tz="local").to_day_datetime_string()

class WIDS(BaseModel):
    acknowledged: Optional[bool] = Field(default=None)
    containment_status: Optional[str] = Field(default_factory=str)
    classification: Optional[str] = Field(default_factory=str)
    classification_method: Optional[str] = Field(default_factory=str)
    cust_id: Optional[str] = Field(default_factory=str)
    encryption: Optional[str] = Field(default_factory=str)
    first_det_device: Optional[str] = Field(default_factory=str)
    first_det_device_name: Optional[str] = Field(default_factory=str)
    first_seen: Optional[datetime] = Field(default=None)
    group: Optional[str] = Field(default_factory=str, alias="group_name")
    id: Optional[str] = Field(default_factory=str)
    _labels: Optional[str] = Field(default_factory=str, alias="labels")
    lan_mac: Optional[str] = Field(default_factory=str)
    last_det_device: Optional[str] = Field(default_factory=str)
    last_det_device_name: Optional[str] = Field(default_factory=str)
    last_seen: Optional[datetime] = Field(default=None)
    mac_vendor: Optional[str] = Field(default_factory=str)
    name: Optional[str] = Field(default_factory=str)
    signal: Optional[str] = Field(default_factory=str)
    ssid: Optional[str] = Field(default_factory=str)

    # custom input conversion for timestamp
    _normalize_datetimes = validator("first_seen", "last_seen", allow_reuse=True)(pretty_dt)

    class Config:
        json_encoders = {
            datetime: lambda v: pendulum.from_format(v.rstrip("Z"), "YYYY-MM-DDTHH:mm:s.SSS").to_day_datetime_string(),
        }
    # TODO json_encoders above removed from pydantic in v2 below was what migration tool came up with but causes last command dump
    # to file to puke [TypeError: keys must be str, int, float, bool or None, not type]
    # json.dumps @ line 370 of clicommon _display_results
            # if stash:
            #     config.last_command_file.write_text(
            # ==>        json.dumps({k: v for k, v in kwargs.items() if k != "config"})
            #     )

    # Pydantic v2 conversion result that causes the    !!! Pinning to pydantic <2 until fully migrated
    # model_config = ConfigDict(json_encoders={
    #     datetime: lambda v: pendulum.from_format(v.rstrip("Z"), "YYYY-MM-DDTHH:mm:s.SSS").to_day_datetime_string(),
    # })

class WIDS_LIST(BaseModel):
    rogue: Optional[List[WIDS]] = Field(default_factory=list)
    interfering: Optional[List[WIDS]] = Field(default_factory=list)
    neighbor: Optional[List[WIDS]] = Field(default_factory=list)
    suspectrogue: Optional[List[WIDS]] = Field(default_factory=list)

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
    client_count: Optional[int] = None # converting from str
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
    count: Optional[int] = None # convert from str
    max: Optional[int] = None # convert from str
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

_example_snow_payload = {
        "u_affected_user": "blah",
        "u_assignment_group":"TE-sn-servicenow",
        "u_business_service": "",
        "u_call_back": False,
        "u_category": "",
        "u_contact_type": "integration",
        "u_description": "",
        "u_configuration_item": "valid snow config item",
        "u_external_source": "40 chars",
        "u_external_ticket": "40 chars",
        "u_raised_severity": 2,
        "u_reported_by": "valid TE ID",
        "u_servicenow_number": "Only on Update",
        "u_service_offering": "snow valid service offering",
        "u_short_description":"Test Ticket Mandatory Create 160 char",
        "u_state": "resolved",
        "u_subcategory": "must be valid sub cat of cat",
        "u_work_notes": "4000 chars",
        "u_attachment_name":"Integration_Sample.txt",
        "u_attachment_type":"text/plain",
        "u_attachment_encoded_code":"SW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA==",
        "u_impact": 2,
        "u_urgency": 2,
        "u_watch_list":"TE308801,TE163762"
    }

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
    u_short_description: str # = Field(..., le=160)
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

# TODO not currently used.  ROUTES ospf/overlay/etc
class Summary(BaseModel):
    admin_status: bool
    oper_state: str
    channel_state: str
    site: str
    up_count: int
    down_count: int
    last_state_change: datetime
    num_interfaces: int
    advertised_routes: int
    learned_routes: int

    _normalize_datetimes = validator("last_state_change", allow_reuse=True)(lambda v: " ".join(pendulum.from_timestamp(v.timestamp(), tz="local").to_day_datetime_string().split()[1:]))

    class Config:
        json_encoders = {
            datetime: lambda v: pendulum.from_timestamp(v).to_day_datetime_string(),
        }

#learned
class NexthopItem(BaseModel):
    address: str
    protocol: str
    flags: str
    is_best: bool
    metric: int
    interface: List[str]

# advertised
class NexthopListItem(BaseModel):
    address: str
    protocol: str
    flags: str
    metric: int
    interface: str


class RouteLearned(BaseModel):
    prefix: str
    length: int
    protocol: str
    flags: str
    nexthop: str
    metric: int
    interface: str
    nexthop_list: List[NexthopItem]


class RouteAdvertised(BaseModel):
    prefix: str
    length: int
    protocol: str
    flags: str
    nexthop: str
    metric: int
    interface: str
    nexthop_list: List[NexthopListItem]


class RoutesLearned(BaseModel):
    summary: Summary
    routes: List[RouteLearned]

class RoutesAdvertised(BaseModel):
    summary: Summary
    routes: List[RouteAdvertised]


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
    details: Dict[str, Any]
    status: str
    stats: CloudAuthUploadStats
    submittedAt: datetime
    lastUpdatedAt: datetime
    durationNanos: int
    fileName: str

    _normalize_datetimes = validator("lastUpdatedAt", "submittedAt", allow_reuse=True)(lambda v: " ".join(pendulum.from_timestamp(v.timestamp(), tz="local").to_day_datetime_string().split()[1:]))

    class Config:
        json_encoders = {
            datetime: lambda v: pendulum.from_timestamp(v).to_day_datetime_string(),
        }

class MpskNetwork(BaseModel):
    id: str
    ssid: str
    accessURL: str
    passwordPolicy: str


class MpskNetworks(BaseModel):
    items: List[MpskNetwork]


class CacheMpskNetwork(BaseModel):
    id: str
    name: str = Field(alias="ssid")


class CacheMpskNetworks(BaseModel):
    items: List[CacheMpskNetwork]


class CachePortal(BaseModel):
    name: str
    id: str
    url: str = Field(alias="capture_url")
    auth_type: str
    is_aruba_cert: bool
    is_default: bool
    is_editable: bool
    is_shared: bool
    register_accept_email: bool
    register_accept_phone: bool


class CachePortals(BaseModel):
    portals: List[CachePortal]