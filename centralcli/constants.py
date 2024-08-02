#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from enum import Enum
from typing import Literal, Union

# ------ // Central API Consistent Device Types \\ ------
lib_dev_idens = ["ap", "cx", "sw", "switch", "gw"]
LibDevIdens = Literal["ap", "cx", "sw", "switch", "gw"]


class AllDevTypes(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"
    switch = "switch"


class GenericDevTypes(str, Enum):
    ap = "ap"
    gw = "gw"
    switch = "switch"


class DevTypes(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"


class TSDevTypes(str, Enum):
    ap = "ap"
    sw = "sw"
    switch = "switch"
    cx = "cx"
    gateway = "gateway"
    gw = "gw"
    mas = "mas"


class SendConfigDevIdens(str, Enum):
    ap = "ap"
    gw = "gw"
    # sw = "sw"  # hopefully some day
    # cx = "cx"

class PoEDetectionStatus(Enum):
    NA = 0
    Undefined = 1  # TODO figure out what this status is
    Searching = 2
    Delivering = 3

# Here are all the types for the below Enum
# 3: Bridge (Switch)
# DOCSIS Cable Device
# Other
# Repeater
# 5 but think 5: Router
# Station
# Telephone
# 4: WLAN Access Point
class LLDPCapabilityTypes(Enum):
    unknown0 = 0
    unknown1 = 1
    unknown2 = 2
    Bridge = 3  # 3 and 5 are assumption need to verify
    Wlan_Access_Point = 4
    Router = 5
    unknown6 = 6
    unknown7 = 7

# Not used currently # TODO reference in cleaner
class SwitchRoles(Enum):
    ERR = 0
    stand_alone = 1
    stack_conductor = 2
    stack_standby = 3
    stack_member = 4


class SwitchRolesShort(Enum):
    ERR = 0
    stand_alone = 1
    conductor = 2
    stby = 3
    mbr = 4


class ShowInventoryArgs(str, Enum):
    all = "all"
    ap = "ap"
    gw = "gw"
    vgw = "vgw"
    sw = "sw"
    cx = "cx"
    switch = "switch"


class SortStackOptions(str, Enum):
    group = "group"
    _id = "id"
    mac = "mac"
    name = "name"
    split_policy = "split_policy"
    status = "status"
    topology = "topology"


class SortWebHookOptions(str, Enum):
    name = "name"
    updated = "updated"
    wid = "wid"
    urls = "urls"
    retry_policy = "retry-policy"
    token = "token"
    token_created = "token-created"


class SortInventoryOptions(str, Enum):
    type = "type"
    model = "model"
    sku = "sku"
    mac = "mac"
    serial = "serial"
    services = "services"

class GatewayRole(str, Enum):
    branch = "branch"
    vpnc = "vpnc"
    wlan = "wlan"


class CertTypes(str, Enum):
    SERVER_CERT = "SERVER_CERT"
    CA_CERT = "CA_CERT"
    CRL = "CRL"
    INTERMEDIATE_CA = "INTERMEDIATE_CA"
    OCSP_RESPONDER_CERT = "OCSP_RESPONDER_CERT"
    OCSP_SIGNER_CERT = "OCSP_SIGNER_CERT"
    PUBLIC_CERT = "PUBLIC_CERT"


class CertFormat(str, Enum):
    PEM = "PEM"
    DER = "DER"
    PKCS12 = "PKCS12"


class StartArgs(str, Enum):
    hook_proxy = "hook-proxy"
    hook2snow = "hook2snow"


class ResetArgs(str, Enum):
    overlay = "overlay"


# wrapping keys from return for some calls that have no value
STRIP_KEYS = [
    "data",
    "gateways",
    "switches",
    "aps",
    "swarms",
    "devices",
    "mcs",
    "group",
    "clients",
    "sites",
    "labels",
    "neighbors",
    "audit_logs",
    "vlans",
    "result",
    "networks",
    "ports",
    "rogue_aps",
    "suspect_aps",
    "interfering_aps",
    "neighbor_aps",
    "events",
    "notifications",
    "settings",
    "items",
    "poe_details",
    "trails",
    "servers",
    "subscriptions",
    "portals",
    "visitors",
    "interfaces",
    "areas",
    "lsas",
    "commands",
    "stacks",
    "routes",
    "samples",
    "dirty_diff_list",
]


class TimeRange(str, Enum):  # = Literal["3h", "1d", "1w", "1m", "3m"]
    _3h = "3h"
    _1d = "1d"
    _1w = "1w"
    _1m = "1m"
    _3m = "3m"


class BandwidthInterval(str, Enum):  # 5m, 1h, 1d, 1w
    _5m = "5m"
    _1h = "1h"
    _1d = "1d"
    _1w = "1w"


class BandwidthRadioOptions(str, Enum):  # 5m, 1h, 1d, 1w
    _24 = "2.4"
    _5 = "5"
    _6 = "6"


class UplinkNames(str, Enum):
    uplink101 = "uplink101"
    uplink102 = "uplink102"
    uplink103 = "uplink103"
    uplink104 = "uplink104"
    uplink105 = "uplink105"

class ShowArgs(str, Enum):
    all = "all"
    device = "device"
    devices = "devices"
    ap = "ap"
    aps = "aps"
    switch = "switch"
    switches = "switches"
    gateway = "gateway"
    gateways = "gateways"
    group = "group"
    groups = "groups"
    site = "site"
    sites = "sites"
    clients = "clients"
    template = "template"
    templates = "templates"
    variables = "variables"
    certs = "certs"
    cache = "cache"
    log = "log"
    logs = "logs"


class NotifyToArgs(str, Enum):
    phone = "phone"
    email = "email"


class RefreshWhat(str, Enum):
    cache = "cache"
    token = "token"
    tokens = "tokens"


class FirmwareDeviceType(str, Enum):
    cx = "cx"
    sw = "sw"
    switch = "switch"
    gw = "gw"
    mas = "mas"


class BlinkArgs(str, Enum):
    on = "on"
    off = "off"


class DeleteArgs(str, Enum):
    certificate = "certificate"
    cert = "cert"
    site = "site"


class EventDevTypeArgs(str, Enum):
    ap = "ap"
    switch = "switch"
    gw = "gw"
    client = "client"


class BounceArgs(str, Enum):
    poe = "poe"  # Switches Only
    interface = "interface"  # Switches only
    # port = "port"  # IAP/Controllers/Switches
    # TODO handle conversion from "interface" to port for gw/iap


class TemplateLevel1(str, Enum):
    update = "update"
    delete = "delete"
    add = "add"


class CacheArgs(str, Enum):
    devices = "devices"
    inventory = "inventory"
    sites = "sites"
    clients = "clients"
    templates = "templates"
    groups = "groups"
    labels = "labels"
    licenses = "licenses"
    logs = "logs"
    events = "events"
    hook_config = "hook_config"
    hook_data = "hook_data"
    hook_active = "hook_active"
    mpsk = "mpsk"
    portals = "portals"


class KickArgs(str, Enum):
    all = "all"
    mac = "mac"
    wlan = "wlan"


class BatchApArgs(str, Enum):
    rename = "rename"


class BatchAddArgs(str, Enum):
    sites = "sites"
    groups = "groups"
    devices = "devices"
    labels = "labels"
    macs = "macs"
    mpsk = "mpsk"

# CloudAuthUploadType = Literal["mpsk", "mac"]
class CloudAuthUploadType(str, Enum):
    mpsk = "mpsk"
    mac = "mac"

class BatchDelArgs(str, Enum):
    sites = "sites"
    groups = "groups"
    devices = "devices"
    labels = "labels"


class BatchRenameArgs(str, Enum):
    # sites = "sites"
    aps = "aps"
    # groups = "groups"


class EnableDisableArgs(str, Enum):
    auto_sub = "auto-sub"



class DhcpArgs(str, Enum):
    clients = "clients"
    server = "server"


class LicenseTypes(str, Enum):
    advance_70xx = "advance-70xx"
    advance_72xx = "advance-72xx"
    advance_90xx_sec = "advance-90xx-sec"
    advanced_91xx = "advanced-91xx"
    advanced_91xx_sec = "advanced-91xx-sec"
    advanced_92xx_sec = "advanced-92xx-sec"
    advanced_ap = "advanced-ap"
    advanced_nw_third_party = "advanced-nw-third-party"
    advanced_switch_6100 = "advanced-switch-6100"
    advanced_switch_6200 = "advanced-switch-6200"
    advanced_switch_6300 = "advanced-switch-6300"
    advanced_switch_6400 = "advanced-switch-6400"
    advanced_switch_8xxx_9xxx_10xxx = "advanced-switch-8xxx-9xxx-10xxx"
    foundation_7005 = "foundation-7005"
    foundation_70xx = "foundation-70xx"
    foundation_72xx = "foundation-72xx"
    foundation_90xx_sec = "foundation-90xx-sec"
    foundation_91xx = "foundation-91xx"
    foundation_91xx_sec = "foundation-91xx-sec"
    foundation_92xx_sec = "foundation-92xx-sec"
    foundation_ap = "foundation-ap"
    foundation_base_90xx_sec = "foundation-base-90xx-sec"
    foundation_nw_third_party = "foundation-nw-third-party"
    foundation_sdflex = "foundation-sdflex"
    foundation_switch_6100 = "foundation-switch-6100"
    foundation_switch_6200 = "foundation-switch-6200"
    foundation_switch_6300 = "foundation-switch-6300"
    foundation_switch_6400 = "foundation-switch-6400"
    foundation_switch_8400 = "foundation-switch-8400"
    foundation_wlan_gw = "foundation-wlan-gw"
    vgw_2g = "vgw-2g"
    vgw_4g = "vgw-4g"
    vgw_500m = "vgw-500m"
    wlan_advanced_90xx_sec = "wlan-advanced-90xx-sec"
    wlan_advanced_91xx = "wlan-advanced-91xx"
    wlan_advanced_91xx_sec = "wlan-advanced-91xx-sec"
    wlan_advanced_92xx_sec = "wlan-advanced-92xx-sec"


class SubscriptionArgs(str, Enum):
    details = "details"
    stats = "stats"
    names = "names"
    auto = "auto"

class ArgToWhat:
    def __init__(self):
        """Mapping object to map supported variations of input for 'what' argument

        Central uses different variations depending on the method (age of method)
        This CLI uses this standard set (whatever is newer of more prevalent) in
        central.  If the API method uses a different one, we'll convert from our
        std set in the method invoking the API call.
        """
        self._init_show()

    def _init_show(self):
        self.gateways = self.gateway = "gateways"
        self.aps = self.ap = self.iap = "aps"
        self.switches = self.switch = "switches"
        self.groups = self.group = "groups"
        self.sites = self.site = "sites"
        self.templates = self.template = "templates"
        self.variables = self.variable = "variables"
        self.all = "all"
        self.devices = self.device = "devices"
        self.controllers = self.controller = "controllers"
        self.clients = self.client = "clients"
        self.event = self.events = "events"
        self.logs = self.log = "logs"
        self.interfaces = self.interface = self.ports = self.port = "interfaces"
        self.vlans = self.vlan = "vlans"
        self.wlans = self.wlan = self.ssids = self.ssid = "wlans"
        self.run = self.running = "run"
        self.routes = self.route = "routes"
        self.webhooks = self.webhook = "webhooks"
        self.token = self.tokens = "token"
        self.subscription = self.subscriptions = "subscription"
        self.portal = self.portals = "portals"
        self.certs = self.certificates = "certs"

    def _init_refresh(self):
        self.token = self.tokens = "token"

    def _init_update(self):
        self.template = self.templates = "template"
        self.variables = self.variable = "variables"
        self.group = self.groups = "group"
        self.webhooks = self.webhook = "webhook"
        self.sites = self.site = "site"
        self.wlan = self.wlans = "wlan"

    def _init_rename(self):
        self.group = self.groups = "group"
        self.ap = self.aps = "ap"
        self.site = self.sites = "site"

    def _init_delete(self):
        self.site = self.sites = "site"
        self.group = self.groups = "group"
        self.certificate = self.certs = self.certificates = self.cert = "certificate"
        self.wlan = self.wlans = "wlan"
        self.webhooks = self.webhook = "webhook"
        self.template = self.templates = "template"
        self.device = self.devices = self.dev = "device"

    def _init_upgrade(self):
        self.device = self.devices = self.dev = "device"
        self.group = self.groups = "group"
        self.swarm = "swarm"

    def _init_add(self):
        self.site = self.sites = "site"
        self.group = self.groups = "group"
        self.wlan = self.wlans = "wlan"
        self.device = self.devices = self.dev = "device"
        self.webhooks = self.webhook = "webhook"
        self.template = self.templates = "template"

    def _init_test(self):
        self.webhooks = self.webhook = "webhook"

    def _init_tshoot(self):
        self.ap = self.aps = self.iap = "ap"
        self.gateway = self.gateways = self.gw = "gateway"
        self.switch = self.switch = self.switches = "switch"
        self.cx = "cx"
        self.mas = "mas"
        self.ssid = self.ssids = "ssid"

    def _init_clone(self):
        self.group = self.groups = "group"

    def _init_kick(self):
        self.client = self.clients = "client"

    def _init_bounce(self):
        self.interface = self.port = self.ports = self.interfaces = "interface"

    def _init_caas(self):
        self.send_cmd = self.send_cmds = "send_cmds"

    def __call__(self, key: Union[ShowArgs, str], default: str = None, cmd: str = "show") -> str:
        if cmd != "show":
            if hasattr(self, f"_init_{cmd}"):
                getattr(self, f"_init_{cmd}")()

        if isinstance(key, Enum):
            key = key.value
        rv = getattr(self, key, default or key)

        # always reset instance to show defaults
        self._init_show()

        return rv


arg_to_what = ArgToWhat()

APIMethodType = Literal[
    "site",
    "monitoring",
    "template",
    "firmware",
    "event",
    "tshoot",
    "inventory"
]

ClientStatus = Literal["FAILED_TO_CONNECT", "CONNECTED"]

class LibToAPI:
    """Convert consistent device types used by this library to the various types used by Central API endpoints

    If no method str is provided converts various strings to consistent library device types.
    """
    def __init__(self):
        # default from random to CentralApi consistent value
        self.gateways = self.gateway = self.gw = "gw"
        self.controller = self.mcd = "gw"
        self.aps = self.ap = self.iap = "ap"
        self.switches = self.switch = "switch"
        self.SW = self.sw = self.HPPC = self.HP = "sw"
        self.CX = self.cx = "cx"
        self.method_iden = None,

        # from CentralApi consistent value to Random API endpoint value
        self.monitoring_to_api = {
            "gw": "gateways",
            "ap": "aps",
            "switch": "switches",
            "cx": "switches",
            "sw": "switches"
        }
        self.site_to_api = {
            "gw": "CONTROLLER",
            "ap": "IAP",
            "switch": "SWITCH",
            "cx": "SWITCH",
            "sw": "SWITCH",
        }
        self.template_to_api = {
            "gw": "MobilityController",
            "ap": "IAP",
            "switch": "CX",
            "cx": "CX",
            "sw": "ArubaSwitch"
        }
        self.firmware_to_api = {
            "gw": "CONTROLLER",
            "ap": "IAP",
            "switch": "HP",
            "cx": "CX",
            "sw": "HP",
            "mas": "MAS"
        }
        self.event_to_api = {
            "gw": "GATEWAY",
            "ap": "ACCESS POINT",
            "switch": "SWITCH",
            "cx": "SWITCH",
            "sw": "SWITCH",
            "client": "CLIENT",
            "clients": "CLIENT",
        }
        self.tshoot_to_api = {
            "gw": "CONTROLLER",
            "gateway": "CONTROLLER",
            "ap": "IAP",
            "cx": "CX",
            "sw": "SWITCH",
            "switch": "SWITCH",
            "mas": "MAS"
        }
        self.inventory_to_api = {
            "all": "all",
            "ap": "all_ap",
            "cx": "switch",
            "sw": "switch",
            "switch": "switch",
            "gw": "all_controller",
            "vgw": "vgw"
        }

    def __call__(self, dev_type: str, method: APIMethodType = None, default: str = None) -> str:
        if isinstance(dev_type, Enum):
            dev_type = dev_type.value

        # TODO lose the _to_api in the attributes
        if hasattr(self, f"{method}_to_api"):
            self.method_iden = method
            return getattr(self, f"{method}_to_api").get(dev_type.lower(), default or dev_type)

        return getattr(self, dev_type, default or dev_type)

    @property
    def valid(self) -> list:
        return lib_dev_idens

    @property
    def valid_str(self) -> list:
        return ", ".join(lib_dev_idens)


lib_to_api = LibToAPI()


class WhatToPretty:
    def __init__(self):
        """Mapping option to get plural form of common 'what' attributes

        The inverse of ArgToWhat, but always returns plural with appropriate
        case for display.  Normally title case.  i.e. switch --> Switches

        """
        self.gateway = self.gateways = "Gateways"
        self.aps = self.ap = self.iap = "Access Points"
        self.switch = self.switches = "Switches"
        self.groups = self.group = "Groups"
        self.site = self.sites = "Sites"
        self.template = self.templates = "Templates"
        self.variable = self.variables = "Variables"
        self.all = "All Devices"
        self.device = self.devices = "Devices"

    def __call__(self, key: Union[ShowArgs, str], default: str = None) -> str:
        if isinstance(key, Enum):
            key = key._value_
        return getattr(self, key, default or key)


what_to_pretty = WhatToPretty()


class LibToGenericPlural:
    def __init__(self):
        self.gw = "gateways"
        self.ap = "access points"
        self.switch = self.cx = self.sw = "switches"

    def __call__(self, key: Literal["ap", "cx", "sw", "switch", "gw"], default: str = None, format_func=str.title) -> str:
        if isinstance(key, Enum):
            key = key.value

        return format_func(getattr(self, key, default or key))


lib_to_gen_plural = LibToGenericPlural()


class ShowArg2(str, Enum):
    all = "all"
    device = "device"
    devices = "devices"
    switch = "switch"
    switches = "switches"
    group = "group"
    groups = "groups"
    sites = "sites"
    clients = "clients"
    ap = "ap"
    aps = "aps"
    gateway = "gateway"
    gateways = "gateways"
    templates = "templates"
    template = "template"
    variables = "variables"
    certs = "certs"


class ShowHookProxyArgs(str, Enum):
    logs = "logs"
    pid = "pid"
    port = "port"


# TODO remove once all refs removed
class SortOptions(str, Enum):
    name_asc = "+name"
    name_des = "-name"
    mac_asc = "+mac"
    mac_des = "-mac"
    serial_asc = "+serial"
    serial_des = "-serial"


class SortWlanOptions(str, Enum):
    ssid = "ssid"
    security = "security"
    type = "type"
    clients = "clients"
    enabled = "enabled"
    rf_band = "rf_band"
    mac_auth = "mac_auth"
    access_type = "access_type"
    group = "group"


class SortNamedMpskOptions(str, Enum):
    _id = "id"
    name = "name"
    role = "role"
    status = "status"
    mpsk = "mpsk"

class SortDevOptions(str, Enum):
    name = "name"
    model = "model"
    ip = "ip"
    mac = "mac"
    serial = "serial"
    group = "group"
    site = "site"
    status = "status"
    type = "type"
    labels = "labels"
    version = "version"
    uptime = "uptime"
    ap = "ap"
    ap_ip = "ap_ip"
    ap_serial = "ap_serial"
    ap_port = "ap_port"
    switch = "switch"
    switch_ip = "switch_ip"
    switch_serial = "switch_serial"
    switch_port = "switch_port"
    untagged_vlan = "untagged_vlan"
    tagged_vlans = "tagged_vlans"
    healthy = "healthy"


class SortTemplateOptions(str, Enum):
    device_type = "device_type"
    group = "group"
    model = "model"
    name = "name"
    template_hash = "template_hash"
    version = "version"


class AlertSeverity(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    warning = "warning"
    info = "info"  # cleaner will tag severity INFO if the alert lacks a severity


class AlertTypes(str, Enum):
    device = "device"
    client = "client"
    user = "user"
    ids = "ids"


class SortAlertOptions(str, Enum):
    time = "time"
    severity = "severity"
    type = "type"
    description = "description"
    acknowledged = "acknowledged"

class SortCertOptions(str, Enum):
    name = "name"
    type = "type"
    expiration = "expiration"
    expired = "expired"
    md5_checksum = "md5_checksum"
    sha1_checksum = "sha1_checksum"


class SortRouteOptions(str, Enum):
    destination = "destination"
    interface = "interface"
    nexthop = "nexthop"
    protocol = "protocol"
    flags = "flags"
    metric = "metric"
    best = "best"
    learn_time = "learn_time"


class SortOverlayInterfaceOptions(str, Enum):
    name = "name"
    endpoint = "endpoint"
    state = "state"
    uptime = "uptime"
    routes = "routes"


class SendCmdArgs(str, Enum):
    device = "device"
    site = "site"
    group = "group"
    all = "all"
    file = "file"


class SendCmdArg2(str, Enum):
    commands = "commands"


class SortSiteOptions(str, Enum):
    name = "name"
    id = "id"
    address = "address"
    city = "city"
    state = "state"
    zipcode = "zipcode"
    country = "country"
    associated_devices = "associated_devices"


class SortGroupOptions(str, Enum):
    name = "name"
    AOSVersion = "AOSVersion"
    AllowedDevTypes = "AllowedDevTypes"
    ApNetworkRole = "ApNetworkRole"
    Architecture = "Architecture"
    GwNetworkRole = "GwNetworkRole"
    template_group = "template_group"


class SortVlanOptions(str, Enum):
    name = "name"
    pvid = "pvid"
    untagged = "untagged"
    tagged = "tagged"
    status = "status"
    mgmt = "mgmt"
    jumbo = "jumbo"
    voice = "voice"
    igmp = "igmp"
    oper_state_reason = "oper_state_reason"


class SortClientOptions(str, Enum):
    name = "name"
    mac = "mac"
    vlan = "vlan"
    ip = "ip"
    role = "role"
    network = "network"
    dot11 = "dot11"
    connected_device = "connected_device"
    site = "site"
    group = "group"
    last_connected = "last_connected"


class SortSubscriptionOptions(str, Enum):
    name = "name"
    sku = "sku"
    status = "status"
    type = "type"
    key = "key"
    network = "network"
    start_date = "start_date"
    end_date = "end_date"


class SortOspfAreaOptions(str, Enum):
    area = "area"
    area_type = "area_type"
    interface_count = "interface_count"
    spf_run_count = "spf_run_count"
    default_cost = "default_cost"
    summary_enable = "summary_enable"


class SortOspfInterfaceOptions(str, Enum):
    name = "name"
    area = "area"
    ip = "ip"
    state = "state"
    oper_state = "oper_state"
    type = "type"
    cost = "cost"
    nbrs = "nbrs"
    DR_rtr_id = "DR_rtr_id"
    DR_IP = "DR_IP"
    BDR_rtr_id = "BDR_rtr_id"
    BDR_IP = "BDR_IP"
    auth = "auth"
    priority = "priority"
    hello_interval = "hello_interval"
    dead_interval = "dead_interval"
    rexmt_interval = "rexmt_interval"


class SortOspfNeighborOptions(str, Enum):
    router_id = "router_id"
    ip = "ip"
    priority = "priority"
    interface_name = "interface_name"
    interface_state = "interface_state"
    neighbor_state = "neighbor_state"
    area = "area"
    options = "options"
    dead_timer = "dead_timer"
    rexmt_timer = "rexmt_timer"


class SortOspfDatabaseOptions(str, Enum):
    area = "area"
    lsa_type = "lsa_type"
    ls_id = "ls_id"
    router_id = "router_id"
    age = "age"
    seq_no = "seq_no"
    checksum = "checksum"
    link_count = "link_count"
    route_tag = "route_tag"


class SortTsCmdOptions(str, Enum):
    command_id = "id"
    category = "category"


class StatusOptions(str, Enum):
    up = "up"
    down = "down"
    Up = "Up"
    Down = "Down"
    UP = "UP"
    DOWN = "DOWN"


class UpgradeArgs(str, Enum):
    ap = "ap"
    switch = "switch"
    gateway = "gateway"


class RemoveArgs(str, Enum):
    site = "site"


class LogAppArgs(str, Enum):
    account_setting = "account_setting"
    nms = "nms"


MESSAGES = {
    "SPIN_TXT_AUTH": "Initializing Aruba Central Base...",
    "SPIN_TXT_CMDS": "Sending Commands to Aruba Central API Gateway...",
    "SPIN_TXT_DATA": "Collecting Data from Aruba Central API Gateway...",
}


class IdenMetaVars:
    def __init__(self):
        self.dev = "[name|ip|mac|serial]"
        self.dev_many = "[name|ip|mac|serial] ... (multiple allowed)"
        self.group = "[GROUP NAME]"
        self.template = "[TEMPLATE NAME]"
        self.group_many = "[GROUP NAME] ... (multiple allowed)"
        self.site = "[name|site id|address|city|state|zip]"
        self.label = "[LABEL]"
        self.client = "[username|ip|mac]"
        self.dev_words = f"Optional Identifying Attribute: {self.dev}"
        self.generic_dev_types = "[ap|gw|switch]"
        self.dev_types = "[ap|gw|cx|sw]"
        self.dev_types_w_mas = "[ap|gw|cx|sw|mas]"
        self.group_or_dev = f"device {self.dev.upper()} | group [GROUP]"
        self.group_dev_cencli = f"{self.dev.upper().replace(']', '|GROUPNAME|cencli]')}"
        self.group_or_dev_or_site = "[DEVICE|\"all\"|GROUP|SITE]"


class LogSortBy(str, Enum):
    time = "time"
    app = "app"
    _class = "class"
    _type = "type"
    description = "description"
    target = "target"
    ip = "ip"
    user = "user"
    id = "id"


class CloudAuthMacSortBy(str, Enum):
    name = "name"
    mac = "mac"


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


state_abbrev_to_pretty = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
    "AS": "American Samoa",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico",
    "UM": "United States Minor Outlying Islands",
    "VI": "U.S. Virgin Islands"
}

# invert
state_pretty_to_abbrev = dict(map(reversed, state_abbrev_to_pretty.items()))

class SiteStates(str, Enum):
    AL = Alabama = "Alabama",
    AK = Alaska = "Alaska",
    AZ = Arizona = "Arizona",
    AR = Arkansas = "Arkansas",
    CA = California = "California",
    CO = Colorado = "Colorado",
    CT = Connecticut = "Connecticut",
    DE = Delaware = "Delaware",
    FL = Florida = "Florida",
    GA = Georgia = "Georgia",
    HI = Hawaii = "Hawaii",
    ID = Idaho = "Idaho",
    IL = Illinois = "Illinois",
    IN = Indiana = "Indiana",
    IA = Iowa = "Iowa",
    KS = Kansas = "Kansas",
    KY = Kentucky = "Kentucky",
    LA = Louisiana = "Louisiana",
    ME = Maine = "Maine",
    MD = Maryland = "Maryland",
    MA = Massachusetts = "Massachusetts",
    MI = Michigan = "Michigan",
    MN = Minnesota = "Minnesota",
    MS = Mississippi = "Mississippi",
    MO = Missouri = "Missouri",
    MT = Montana = "Montana",
    NE = Nebraska = "Nebraska",
    NV = Nevada = "Nevada",
    NH = New_Hampshire = "New Hampshire",
    NJ = New_Jersey = "New Jersey",
    NM = New_Mexico = "New Mexico",
    NY = New_York = "New York",
    NC = North_Carolina = "North Carolina",
    ND = North_Dakota = "North Dakota",
    OH = Ohio = "Ohio",
    OK = Oklahoma = "Oklahoma",
    OR = Oregon = "Oregon",
    PA = Pennsylvania = "Pennsylvania",
    RI = Rhode_Island = "Rhode Island",
    SC = South_Carolina = "South Carolina",
    SD = South_Dakota = "South Dakota",
    TN = Tennessee = "Tennessee",
    TX = Texas = "Texas",
    UT = Utah = "Utah",
    VT = Vermont = "Vermont",
    VA = Virginia = "Virginia",
    WA = Washington = "Washington",
    WV = West_Virginia = "West Virginia",
    WI = Wisconsin = "Wisconsin",
    WY = Wyoming = "Wyoming",
    DC = District_of_Columbia = "District of Columbia",
    AS = American_Samoa = "American Samoa",
    GU = Guam = "Guam",
    MP = Northern_Mariana_Islands = "Northern Mariana Islands",
    PR = Puerto_Rico = "Puerto Rico",
    UM = United_States_Minor_Outlying_Islands = "United States Minor Outlying Islands",
    VI = US_Virgin_Islands = "U.S. Virgin Islands"

TZDB = Literal[
    "Africa/Abidjan",
    "Africa/Accra",
    "Africa/Addis_Ababa",
    "Africa/Algiers",
    "Africa/Asmara",
    "Africa/Asmera",
    "Africa/Bamako",
    "Africa/Bangui",
    "Africa/Banjul",
    "Africa/Bissau",
    "Africa/Blantyre",
    "Africa/Brazzaville",
    "Africa/Bujumbura",
    "Africa/Cairo",
    "Africa/Casablanca",
    "Africa/Ceuta",
    "Africa/Conakry",
    "Africa/Dakar",
    "Africa/Dar_es_Salaam",
    "Africa/Djibouti",
    "Africa/Douala",
    "Africa/El_Aaiun",
    "Africa/Freetown",
    "Africa/Gaborone",
    "Africa/Harare",
    "Africa/Johannesburg",
    "Africa/Juba",
    "Africa/Kampala",
    "Africa/Khartoum",
    "Africa/Kigali",
    "Africa/Kinshasa",
    "Africa/Lagos",
    "Africa/Libreville",
    "Africa/Lome",
    "Africa/Luanda",
    "Africa/Lubumbashi",
    "Africa/Lusaka",
    "Africa/Malabo",
    "Africa/Maputo",
    "Africa/Maseru",
    "Africa/Mbabane",
    "Africa/Mogadishu",
    "Africa/Monrovia",
    "Africa/Nairobi",
    "Africa/Ndjamena",
    "Africa/Niamey",
    "Africa/Nouakchott",
    "Africa/Ouagadougou",
    "Africa/Porto-Novo",
    "Africa/Sao_Tome",
    "Africa/Timbuktu",
    "Africa/Tripoli",
    "Africa/Tunis",
    "Africa/Windhoek",
    "America/Adak",
    "America/Anchorage",
    "America/Anguilla",
    "America/Antigua",
    "America/Araguaina",
    "America/Argentina/Buenos_Aires",
    "America/Argentina/Catamarca",
    "America/Argentina/ComodRivadavia",
    "America/Argentina/Cordoba",
    "America/Argentina/Jujuy",
    "America/Argentina/La_Rioja",
    "America/Argentina/Mendoza",
    "America/Argentina/Rio_Gallegos",
    "America/Argentina/Salta",
    "America/Argentina/San_Juan",
    "America/Argentina/San_Luis",
    "America/Argentina/Tucuman",
    "America/Argentina/Ushuaia",
    "America/Aruba",
    "America/Asuncion",
    "America/Atikokan",
    "America/Atka",
    "America/Bahia",
    "America/Bahia_Banderas",
    "America/Barbados",
    "America/Belem",
    "America/Belize",
    "America/Blanc-Sablon",
    "America/Boa_Vista",
    "America/Bogota",
    "America/Boise",
    "America/Buenos_Aires",
    "America/Cambridge_Bay",
    "America/Campo_Grande",
    "America/Cancun",
    "America/Caracas",
    "America/Catamarca",
    "America/Cayenne",
    "America/Cayman",
    "America/Chicago",
    "America/Chihuahua",
    "America/Coral_Harbour",
    "America/Cordoba",
    "America/Costa_Rica",
    "America/Creston",
    "America/Cuiaba",
    "America/Curacao",
    "America/Danmarkshavn",
    "America/Dawson",
    "America/Dawson_Creek",
    "America/Denver",
    "America/Detroit",
    "America/Dominica",
    "America/Edmonton",
    "America/Eirunepe",
    "America/El_Salvador",
    "America/Ensenada",
    "America/Fort_Nelson",
    "America/Fort_Wayne",
    "America/Fortaleza",
    "America/Glace_Bay",
    "America/Godthab",
    "America/Goose_Bay",
    "America/Grand_Turk",
    "America/Grenada",
    "America/Guadeloupe",
    "America/Guatemala",
    "America/Guayaquil",
    "America/Guyana",
    "America/Halifax",
    "America/Havana",
    "America/Hermosillo",
    "America/Indiana/Indianapolis",
    "America/Indiana/Knox",
    "America/Indiana/Marengo",
    "America/Indiana/Petersburg",
    "America/Indiana/Tell_City",
    "America/Indiana/Vevay",
    "America/Indiana/Vincennes",
    "America/Indiana/Winamac",
    "America/Indianapolis",
    "America/Inuvik",
    "America/Iqaluit",
    "America/Jamaica",
    "America/Jujuy",
    "America/Juneau",
    "America/Kentucky/Louisville",
    "America/Kentucky/Monticello",
    "America/Knox_IN",
    "America/Kralendijk",
    "America/La_Paz",
    "America/Lima",
    "America/Los_Angeles",
    "America/Louisville",
    "America/Lower_Princes",
    "America/Maceio",
    "America/Managua",
    "America/Manaus",
    "America/Marigot",
    "America/Martinique",
    "America/Matamoros",
    "America/Mazatlan",
    "America/Mendoza",
    "America/Menominee",
    "America/Merida",
    "America/Metlakatla",
    "America/Mexico_City",
    "America/Miquelon",
    "America/Moncton",
    "America/Monterrey",
    "America/Montevideo",
    "America/Montreal",
    "America/Montserrat",
    "America/Nassau",
    "America/New_York",
    "America/Nipigon",
    "America/Nome",
    "America/Noronha",
    "America/North_Dakota/Beulah",
    "America/North_Dakota/Center",
    "America/North_Dakota/New_Salem",
    "America/Ojinaga",
    "America/Panama",
    "America/Pangnirtung",
    "America/Paramaribo",
    "America/Phoenix",
    "America/Port-au-Prince",
    "America/Port_of_Spain",
    "America/Porto_Acre",
    "America/Porto_Velho",
    "America/Puerto_Rico",
    "America/Punta_Arenas",
    "America/Rainy_River",
    "America/Rankin_Inlet",
    "America/Recife",
    "America/Regina",
    "America/Resolute",
    "America/Rio_Branco",
    "America/Rosario",
    "America/Santa_Isabel",
    "America/Santarem",
    "America/Santiago",
    "America/Santo_Domingo",
    "America/Sao_Paulo",
    "America/Scoresbysund",
    "America/Shiprock",
    "America/Sitka",
    "America/St_Barthelemy",
    "America/St_Johns",
    "America/St_Kitts",
    "America/St_Lucia",
    "America/St_Thomas",
    "America/St_Vincent",
    "America/Swift_Current",
    "America/Tegucigalpa",
    "America/Thule",
    "America/Thunder_Bay",
    "America/Tijuana",
    "America/Toronto",
    "America/Tortola",
    "America/Vancouver",
    "America/Virgin",
    "America/Whitehorse",
    "America/Winnipeg",
    "America/Yakutat",
    "America/Yellowknife",
    "Antarctica/Casey",
    "Antarctica/Davis",
    "Antarctica/DumontDUrville",
    "Antarctica/Macquarie",
    "Antarctica/Mawson",
    "Antarctica/McMurdo",
    "Antarctica/Palmer",
    "Antarctica/Rothera",
    "Antarctica/South_Pole",
    "Antarctica/Syowa",
    "Antarctica/Troll",
    "Antarctica/Vostok",
    "Arctic/Longyearbyen",
    "Asia/Aden",
    "Asia/Almaty",
    "Asia/Amman",
    "Asia/Anadyr",
    "Asia/Aqtau",
    "Asia/Aqtobe",
    "Asia/Ashgabat",
    "Asia/Ashkhabad",
    "Asia/Atyrau",
    "Asia/Baghdad",
    "Asia/Bahrain",
    "Asia/Baku",
    "Asia/Bangkok",
    "Asia/Barnaul",
    "Asia/Beirut",
    "Asia/Bishkek",
    "Asia/Brunei",
    "Asia/Calcutta",
    "Asia/Chita",
    "Asia/Choibalsan",
    "Asia/Chongqing",
    "Asia/Chungking",
    "Asia/Colombo",
    "Asia/Dacca",
    "Asia/Damascus",
    "Asia/Dhaka",
    "Asia/Dili",
    "Asia/Dubai",
    "Asia/Dushanbe",
    "Asia/Famagusta",
    "Asia/Gaza",
    "Asia/Harbin",
    "Asia/Hebron",
    "Asia/Ho_Chi_Minh",
    "Asia/Hong_Kong",
    "Asia/Hovd",
    "Asia/Irkutsk",
    "Asia/Istanbul",
    "Asia/Jakarta",
    "Asia/Jayapura",
    "Asia/Jerusalem",
    "Asia/Kabul",
    "Asia/Kamchatka",
    "Asia/Karachi",
    "Asia/Kashgar",
    "Asia/Kathmandu",
    "Asia/Katmandu",
    "Asia/Khandyga",
    "Asia/Kolkata",
    "Asia/Krasnoyarsk",
    "Asia/Kuala_Lumpur",
    "Asia/Kuching",
    "Asia/Kuwait",
    "Asia/Macao",
    "Asia/Macau",
    "Asia/Magadan",
    "Asia/Makassar",
    "Asia/Manila",
    "Asia/Muscat",
    "Asia/Nicosia",
    "Asia/Novokuznetsk",
    "Asia/Novosibirsk",
    "Asia/Omsk",
    "Asia/Oral",
    "Asia/Phnom_Penh",
    "Asia/Pontianak",
    "Asia/Pyongyang",
    "Asia/Qatar",
    "Asia/Qostanay",
    "Asia/Qyzylorda",
    "Asia/Rangoon",
    "Asia/Riyadh",
    "Asia/Saigon",
    "Asia/Sakhalin",
    "Asia/Samarkand",
    "Asia/Seoul",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Srednekolymsk",
    "Asia/Taipei",
    "Asia/Tashkent",
    "Asia/Tbilisi",
    "Asia/Tehran",
    "Asia/Tel_Aviv",
    "Asia/Thimbu",
    "Asia/Thimphu",
    "Asia/Tokyo",
    "Asia/Tomsk",
    "Asia/Ujung_Pandang",
    "Asia/Ulaanbaatar",
    "Asia/Ulan_Bator",
    "Asia/Urumqi",
    "Asia/Ust-Nera",
    "Asia/Vientiane",
    "Asia/Vladivostok",
    "Asia/Yakutsk",
    "Asia/Yangon",
    "Asia/Yekaterinburg",
    "Asia/Yerevan",
    "Atlantic/Azores",
    "Atlantic/Bermuda",
    "Atlantic/Canary",
    "Atlantic/Cape_Verde",
    "Atlantic/Faeroe",
    "Atlantic/Faroe",
    "Atlantic/Jan_Mayen",
    "Atlantic/Madeira",
    "Atlantic/Reykjavik",
    "Atlantic/South_Georgia",
    "Atlantic/St_Helena",
    "Atlantic/Stanley",
    "Australia/ACT",
    "Australia/Adelaide",
    "Australia/Brisbane",
    "Australia/Broken_Hill",
    "Australia/Canberra",
    "Australia/Currie",
    "Australia/Darwin",
    "Australia/Eucla",
    "Australia/Hobart",
    "Australia/LHI",
    "Australia/Lindeman",
    "Australia/Lord_Howe",
    "Australia/Melbourne",
    "Australia/North",
    "Australia/NSW",
    "Australia/Perth",
    "Australia/Queensland",
    "Australia/South",
    "Australia/Sydney",
    "Australia/Tasmania",
    "Australia/Victoria",
    "Australia/West",
    "Australia/Yancowinna",
    "Brazil/Acre",
    "Brazil/DeNoronha",
    "Brazil/East",
    "Brazil/West",
    "Canada/Atlantic",
    "Canada/Central",
    "Canada/Eastern",
    "Canada/Mountain",
    "Canada/Newfoundland",
    "Canada/Pacific",
    "Canada/Saskatchewan",
    "Canada/Yukon",
    "CET",
    "Chile/Continental",
    "Chile/EasterIsland",
    "CST6CDT",
    "Cuba",
    "EET",
    "Egypt",
    "Eire",
    "EST",
    "EST5EDT",
    "Etc/GMT",
    "Etc/GMT+0",
    "Etc/GMT+1",
    "Etc/GMT+10",
    "Etc/GMT+11",
    "Etc/GMT+12",
    "Etc/GMT+2",
    "Etc/GMT+3",
    "Etc/GMT+4",
    "Etc/GMT+5",
    "Etc/GMT+6",
    "Etc/GMT+7",
    "Etc/GMT+8",
    "Etc/GMT+9",
    "Etc/GMT-0",
    "Etc/GMT-1",
    "Etc/GMT-10",
    "Etc/GMT-11",
    "Etc/GMT-12",
    "Etc/GMT-13",
    "Etc/GMT-14",
    "Etc/GMT-2",
    "Etc/GMT-3",
    "Etc/GMT-4",
    "Etc/GMT-5",
    "Etc/GMT-6",
    "Etc/GMT-7",
    "Etc/GMT-8",
    "Etc/GMT-9",
    "Etc/GMT0",
    "Etc/Greenwich",
    "Etc/UCT",
    "Etc/Universal",
    "Etc/UTC",
    "Etc/Zulu",
    "Europe/Amsterdam",
    "Europe/Andorra",
    "Europe/Astrakhan",
    "Europe/Athens",
    "Europe/Belfast",
    "Europe/Belgrade",
    "Europe/Berlin",
    "Europe/Bratislava",
    "Europe/Brussels",
    "Europe/Bucharest",
    "Europe/Budapest",
    "Europe/Busingen",
    "Europe/Chisinau",
    "Europe/Copenhagen",
    "Europe/Dublin",
    "Europe/Gibraltar",
    "Europe/Guernsey",
    "Europe/Helsinki",
    "Europe/Isle_of_Man",
    "Europe/Istanbul",
    "Europe/Jersey",
    "Europe/Kaliningrad",
    "Europe/Kiev",
    "Europe/Kirov",
    "Europe/Lisbon",
    "Europe/Ljubljana",
    "Europe/London",
    "Europe/Luxembourg",
    "Europe/Madrid",
    "Europe/Malta",
    "Europe/Mariehamn",
    "Europe/Minsk",
    "Europe/Monaco",
    "Europe/Moscow",
    "Europe/Nicosia",
    "Europe/Oslo",
    "Europe/Paris",
    "Europe/Podgorica",
    "Europe/Prague",
    "Europe/Riga",
    "Europe/Rome",
    "Europe/Samara",
    "Europe/San_Marino",
    "Europe/Sarajevo",
    "Europe/Saratov",
    "Europe/Simferopol",
    "Europe/Skopje",
    "Europe/Sofia",
    "Europe/Stockholm",
    "Europe/Tallinn",
    "Europe/Tirane",
    "Europe/Tiraspol",
    "Europe/Ulyanovsk",
    "Europe/Uzhgorod",
    "Europe/Vaduz",
    "Europe/Vatican",
    "Europe/Vienna",
    "Europe/Vilnius",
    "Europe/Volgograd",
    "Europe/Warsaw",
    "Europe/Zagreb",
    "Europe/Zaporozhye",
    "Europe/Zurich",
    "Factory",
    "GB",
    "GB-Eire",
    "GMT",
    "GMT+0",
    "GMT-0",
    "GMT0",
    "Greenwich",
    "Hongkong",
    "HST",
    "Iceland",
    "Indian/Antananarivo",
    "Indian/Chagos",
    "Indian/Christmas",
    "Indian/Cocos",
    "Indian/Comoro",
    "Indian/Kerguelen",
    "Indian/Mahe",
    "Indian/Maldives",
    "Indian/Mauritius",
    "Indian/Mayotte",
    "Indian/Reunion",
    "Iran",
    "Israel",
    "Jamaica",
    "Japan",
    "Kwajalein",
    "Libya",
    "MET",
    "Mexico/BajaNorte",
    "Mexico/BajaSur",
    "Mexico/General",
    "MST",
    "MST7MDT",
    "Navajo",
    "NZ",
    "NZ-CHAT",
    "Pacific/Apia",
    "Pacific/Auckland",
    "Pacific/Bougainville",
    "Pacific/Chatham",
    "Pacific/Chuuk",
    "Pacific/Easter",
    "Pacific/Efate",
    "Pacific/Enderbury",
    "Pacific/Fakaofo",
    "Pacific/Fiji",
    "Pacific/Funafuti",
    "Pacific/Galapagos",
    "Pacific/Gambier",
    "Pacific/Guadalcanal",
    "Pacific/Guam",
    "Pacific/Honolulu",
    "Pacific/Johnston",
    "Pacific/Kiritimati",
    "Pacific/Kosrae",
    "Pacific/Kwajalein",
    "Pacific/Majuro",
    "Pacific/Marquesas",
    "Pacific/Midway",
    "Pacific/Nauru",
    "Pacific/Niue",
    "Pacific/Norfolk",
    "Pacific/Noumea",
    "Pacific/Pago_Pago",
    "Pacific/Palau",
    "Pacific/Pitcairn",
    "Pacific/Pohnpei",
    "Pacific/Ponape",
    "Pacific/Port_Moresby",
    "Pacific/Rarotonga",
    "Pacific/Saipan",
    "Pacific/Samoa",
    "Pacific/Tahiti",
    "Pacific/Tarawa",
    "Pacific/Tongatapu",
    "Pacific/Truk",
    "Pacific/Wake",
    "Pacific/Wallis",
    "Pacific/Yap",
    "Poland",
    "Portugal",
    "PRC",
    "PST8PDT",
    "ROC",
    "ROK",
    "Singapore",
    "Turkey",
    "UCT",
    "Universal",
    "US/Alaska",
    "US/Aleutian",
    "US/Arizona",
    "US/Central",
    "US/East-Indiana",
    "US/Eastern",
    "US/Hawaii",
    "US/Indiana-Starke",
    "US/Michigan",
    "US/Mountain",
    "US/Pacific",
    "US/Samoa",
    "UTC",
    "W-SU",
    "WET",
    "Zulu",
]


NO_LOAD_COMMANDS = [
    "show config cencli",
    "show last",
    "convert"
]


NO_LOAD_FLAGS = [
    "--help",
    "--cencli",
    "--show-completion",
    "--install-completion",
]


def do_load_pycentral() -> bool:
    """Determine if provided command requires pycentral load

    Allows command to complete even if config has yet to be configured.
    Useful for first run commands and auto docs.

    Returns:
        bool: True or False indicating if pycentral needs to be instantiated
        for command to complete.
    """
    args = [arg for arg in sys.argv[1:] if "--debug" not in arg]
    for x in NO_LOAD_FLAGS:
        if x in args:
            return False

    if " ".join([a for a in args if not a.startswith("-")]).lower() in NO_LOAD_COMMANDS:
        return False
    else:
        return True
