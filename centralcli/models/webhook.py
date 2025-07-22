from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import Optional, List



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