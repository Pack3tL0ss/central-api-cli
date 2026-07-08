from __future__ import annotations

from datetime import datetime as dt
from typing import List, Literal, Optional
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


# WebHook Models WebHookDetails no reliable source for all possible fields.
class WebHookDetails(BaseModel):
    model_config = ConfigDict(extra="allow")
    customer_id: Optional[str] = None
    rule_number: Optional[str] = Field(None, alias=AliasChoices("_rule_number", "rule_number"))
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
    site: Optional[str] = Field(None, alias=AliasChoices("site_name", "site"))
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
    ip: Optional[str] = Field(None, alias=AliasChoices("ip_address", "ip"))
    max_value_for_percentage: Optional[str] = None
    intf_name: Optional[str] = None
    mode: Optional[str] = None
    old_serial: Optional[str] = None
    old_mac: Optional[str] = None
    new_serial: Optional[str] = None
    new_mac: Optional[str] = None
    host: Optional[str] = Field(None, alias=AliasChoices("hostname", "host"))
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
    cluster_name: Optional[str] = Field(None, alias=AliasChoices("cluster-name", "cluster_name"))


class WebHook(BaseModel):
    model_config = ConfigDict(extra="allow")
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


class HookResponse(BaseModel):
    result: str
    updated: bool

    class Config:
        json_schema_extra = {
            "example": {"result": "OK", "updated": True, }
        }


class HookResponseTooBig(HookResponse):
    class Config:
        json_schema_extra = {
            "example": {"result": "Content too long", "updated": False}
        }


class HookResponseTokenFail(BaseModel):
    result: str
    updated: bool

    class Config:
        json_schema_extra = {
            "example": {"result": "Unauthorized", "updated": False}
        }


class BranchResponse(BaseModel):
    id: str
    ok: bool
    alert_type: str
    device_id: str
    state: Literal["Open", "Close"]
    text: str
    timestamp: Optional[int]

    class Config:
        json_schema_extra = {
            "example": {
                    "id": "CNF1234567_init",
                    "ok": False,
                    "alert_type": "BH_POLL_UPLK_OR_TUN_DOWN",
                    "device_id": "CNF1234567",
                    "state": "Open",
                    "text": "sdbranch1:7008:uplk_g1694_v3250_inet::vpnc1:uplk_g1694_v3250_inet found to be down at hook proxy startup",
                    "timestamp": int(dt.now().timestamp())
            }
        }


wh_resp_schema = {
    401: {"model": HookResponseTokenFail},
    413: {"model": HookResponseTooBig}
}


class MonitoringWebHookDetails(BaseModel):
    model_config = ConfigDict(extra="allow")
    params: List[str]
    ts: Optional[str] = None
    serial: str
    conn_status: Optional[str] = None
    time: str
    group_name: str


class AlertType(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    OTHER = "OTHER"


class MonitoringWebHook(BaseModel):
    id: str
    cid: Optional[str] = None
    nid: int
    alert_type: str
    setting_id: str
    device_id: str
    description: str
    state: str
    severity: str
    operation: Optional[str] = None
    timestamp: int
    details: MonitoringWebHookDetails
    webhook: Optional[str] = None
    text: Optional[str] = None

    @field_validator("alert_type", mode="before")
    @classmethod
    def _normalize_alert_type(cls, v: str) -> str:
        return v.lower().replace("_", " ")

    @field_validator("cid", mode="before")
    @classmethod
    def _to_str(cls, v: int | str | None) -> str | None:
        return v and str(v)

    @property
    def dev_type(self) -> str:
        if "switch" in self.alert_type:
            return "switch"  # could be stack, that determination is made in watcher.py # TODO stacks not really accomodated currently
        if "ap" in self.alert_type:
            return "ap"
        if "gateway" in self.alert_type:
            return "gw"

    @property
    def type(self) -> AlertType:
        if "disconnected" in self.alert_type:  # this needs to go first... connected is in disconnected
            return AlertType.DISCONNECTED
        elif ("detected" in self.alert_type or "connected" in self.alert_type):
            return AlertType.CONNECTED
        else:
            return AlertType.OTHER

    @property
    def delete_method(self) -> str | None:
        if self.type == AlertType.DISCONNECTED:
            if "switch" in self.alert_type:
                return "delete_switch"  # could be stack, that determination is made in watcher.py
            if "ap" in self.alert_type:
                return "delete_ap"
            if "gateway" in self.alert_type:
                return "delete_gateway"

