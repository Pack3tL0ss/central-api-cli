#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from typing import Union

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
    dev = "dev"


class RefreshWhat(str, Enum):
    cache = "cache"
    token = "token"
    tokens = "tokens"


out_format_dict = {"do_json": "json", "do_yaml": "yaml", "do_csv": "csv", "do_rich": "rich"}


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
    port = "port"  # IAP/Controllers/Switches


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


# Used to determine if arg is for a device (vs group, templates, ...)
# devices = ["switch", "aps", "gateway", "all", "device"]

class ArgToWhat:
    def __init__(self):
        """Mapping object to map supported variations of input for 'what' argument

        Central uses different variations depending on the method (age of method)
        This CLI uses this standard set (whatever is newer of more prevelent) in
        central.  If the API method uses a different one, we'll convert from our
        std set in the method invoking the API call.
        """
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
        self.certs = self.certificates = self.certificate = self.cert = "certs"
        self.clients = self.client = "clients"
        self.logs = self.log = self.event = self.events = "logs"
        self.interfaces = self.interface = self.ports = self.port = "interfaces"
        self.vlans = self.vlan = "vlans"
        self.wlans = self.wlan = self.ssids = self.ssid = "wlans"
        self.run = self.running = "run"

    def __call__(self, key: Union[ShowArgs, str], default: str = None) -> str:
        if isinstance(key, Enum):
            key = key._value_
        return getattr(self, key, default or key)


arg_to_what = ArgToWhat()


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
        self.all = "All Device Types"
        self.device = self.devices = "Devices"

    def __call__(self, key: Union[ShowArgs, str], default: str = None) -> str:
        if isinstance(key, Enum):
            key = key._value_
        return getattr(self, key, default or key)


arg_to_what = ArgToWhat()
what_to_pretty = WhatToPretty()


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


class SortOptions(str, Enum):
    name_asc = "+name"
    name_des = "-name"
    mac_asc = "+mac"
    mac_des = "-mac"
    serial_asc = "+serial"
    serial_des = "-serial"


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
