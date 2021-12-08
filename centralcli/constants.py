#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from typing import Literal, Union

# ------ // Central API Consistent Device Types \\ ------
lib_dev_idens = ["ap", "cx", "sw", "switch", "gw"]
LibDevIdens = Literal["ap", "cx", "sw", "switch", "gw"]


class GenericDevIdens(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"
    switch = "switch"


class TemplateDevIdens(str, Enum):
    ap = "ap"
    sw = "sw"
    cx = "cx"
    gw = "gw"


# wrapping keys from return for some calls that have no value
STRIP_KEYS = [
    "data",
    "gateways",
    "switches",
    "aps",
    "swarms"
    "devices",
    "mcs",
    "group",
    "clients",
    "sites",
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
]


CLIENT_STRIP_KEYS_VERBOSE = ["group_id", "label_id", "swarm_id"]
CLIENT_STRIP_KEYS = [
    *CLIENT_STRIP_KEYS_VERBOSE,
    "interface_mac",
    "labels",
    "phy_type",
    "radio_mac",
    "radio_number",
    "ht_type",
    "maxspeed",
    "speed",
    "signal_db",
    "signal_strength",
    "encryption_method",
    "usage",
    "manufacturer",
    "health",
    "signal_strength"
    "channel",
    "os_type",
    "band",
    "snr",
    "username",
    "client_type",
    ]


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


class ClientArgs(str, Enum):
    wired = "wired"
    wireless = "wireless"
    all = "all"
    mac = "mac"
    device = "device"


class RefreshWhat(str, Enum):
    cache = "cache"
    token = "token"
    tokens = "tokens"


class BlinkArgs(str, Enum):
    on = "on"
    off = "off"


class DeleteArgs(str, Enum):
    certificate = "certificate"
    cert = "cert"
    site = "site"


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
    sites = "sites"
    templates = "templates"
    groups = "groups"
    logs = "logs"


class KickArgs(str, Enum):
    all = "all"
    mac = "mac"
    wlan = "wlan"


class BatchApArgs(str, Enum):
    rename = "rename"


class RenameArgs(str, Enum):
    group = "group"
    # ap = "ap"


class DhcpArgs(str, Enum):
    clients = "clients"
    server = "server"


class ArgToWhat:
    def __init__(self):
        """Mapping object to map supported variations of input for 'what' argument

        Central uses different variations depending on the method (age of method)
        This CLI uses this standard set (whatever is newer of more prevelent) in
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
        self.logs = self.log = self.event = self.events = "logs"
        self.interfaces = self.interface = self.ports = self.port = "interfaces"
        self.vlans = self.vlan = "vlans"
        self.wlans = self.wlan = self.ssids = self.ssid = "wlans"
        self.run = self.running = "run"
        self.routes = self.route = "routes"

    def _init_update(self):
        self.template = self.templates = "template"
        self.variables = self.variable = "variables"
        self.group = self.groups = "group"

    def _init_delete(self):
        self.site = self.sites = "site"
        self.group = self.groups = "group"
        self.certificate = self.certs = self.certificates = self.cert = "certificate"
        self.wlan = self.wlans = "wlan"

    def _init_upgrade(self):
        self.device = self.devices = self.dev = "device"
        self.group = self.groups = "group"
        self.swarm = "swarm"

    def _init_add(self):
        self.group = self.groups = "group"
        self.wlan = self.wlans = "wlan"
        self.device = self.devices = self.dev = "device"

    def _init_clone(self):
        self.group = self.groups = "group"

    def _init_bounce(self):
        self.interface = self.port = self.ports = self.interfaces = "interface"

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
    "site"
]


class LibToAPI:
    """Convert device type stored in Cache to type required by the different API methods

    # TODO Working toward a consistent set of device_types, needs review, goal is to have
    all API methods in CentralApi use a consistent set of device type values.  i.e.
    'ap', 'switch', 'gw' ('controller' appears to be the same as gw).  Then use this callable
    object to convert appropriate device type to whatever random value is reqd by the API
    method.
    """
    def __init__(self):
        # default from random to CentralApi consistent value
        self.gateways = self.gateway = self.gw = "gw"
        self.controller = self.mcd = "gw"
        self.aps = self.ap = self.iap = "ap"
        self.switches = self.switch = "switch"
        self.SW = self.sw = self.HPPC = self.HP = "sw"
        self.CX = self.cx = "cx"
        self.method_iden = None

        # from CentralApi consistent value to Random API value.
        self.site_to_api = {
            "gw": "CONTROLLER",
            "ap": "IAP",
            "switch": "SWITCH",
            "cx": "SWITCH",
            "sw": "SWITCH",
            "gateway": "CONTROLLER"  # TODO remove once cache is re-factored to use ['ap', 'cx', 'sw', 'gw']
        }
        self.template_to_api = {
            "gw": "MobilityController",
            "ap": "IAP",
            "switch": "CX",
            "cx": "CX",
            "sw": "ArubaSwitch"
        }
        self.upgrade_to_api = {
            "gw": "CONTROLLER",
            "ap": "IAP",
            "switch": "HP",
            "cx": "HP",
            "sw": "HP"
        }

    def __call__(self, method: APIMethodType, key: str, default: str = None) -> str:
        if isinstance(key, Enum):
            key = key.value

        if hasattr(self, f"{method}_to_api"):
            self.method_iden = method
            return getattr(self, f"{method}_to_api").get(key.lower(), default or key)

        return getattr(self, key, default or key)

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

        The inverse of ArgToWhat, but always returns plural with apporpriate
        case for display.  Normally title case.  i.e. switch --> Switches

        """
        self.gateway = self.gateways = "Gateways"
        self.aps = self.ap = self.iap = "Acess Points"
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
        self.ap = "acess points"
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


# TODO remove once all refs removed
class SortOptions(str, Enum):
    name_asc = "+name"
    name_des = "-name"
    mac_asc = "+mac"
    mac_des = "-mac"
    serial_asc = "+serial"
    serial_des = "-serial"


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


class SortTemplateOptions(str, Enum):
    device_type = "device_type"
    group = "group"
    model = "model"
    name = "name"
    template_hash = "template_hash"
    version = "version"


class SortCertOptions(str, Enum):
    name = "name"
    type = "type"
    expiration = "expiration"
    expired = "expired"
    md5_checksum = "md5_checksum"
    sha1_checksum = "sha1_checksum"


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
    "SPIN_TXT_AUTH": "Initializing Arunba Central Base...",
    "SPIN_TXT_CMDS": "Sending Commands to Aruba Central API Gateway...",
    "SPIN_TXT_DATA": "Collecting Data from Aruba Central API Gateway...",
}


class IdenMetaVars:
    def __init__(self):
        self.dev = "[name|ip|mac-address|serial]"
        self.dev_many = "[name|ip|mac-address|serial] ... (multiple allowed)"
        self.site = "[name|site_id|address|city|state|zip]"
        self.client = "[username|ip|mac]"
        self.dev_words = f"Optional Identifying Attribute: {self.dev}"


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
    has_details = "has_details"
