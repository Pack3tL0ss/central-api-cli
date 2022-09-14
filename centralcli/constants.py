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


class SendConfigDevIdens(str, Enum):
    ap = "ap"
    gw = "gw"
    # sw = "sw"  # hopefully some day
    # cx = "cx"


class ShowInventoryArgs(str, Enum):
    all = "all"
    ap = "ap"
    gw = "gw"
    vgw = "vgw"
    switch = "switch"
    others = "others"


SHOWINVENTORY_LIB_TO_API = {
    "all": "all",
    "ap": "all_ap",
    "switch": "switch",
    "gw": "gateway",
    "vgw": "vgw",
    "others": "others"
}

class InventorySortOptions(str, Enum):
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
    templates = "templates"
    groups = "groups"
    labels = "labels"
    logs = "logs"
    events = "events"


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


class BatchDelArgs(str, Enum):
    sites = "sites"
    # groups = "groups"
    devices = "devices"


class BatchRenameArgs(str, Enum):
    sites = "sites"
    aps = "aps"
    groups = "groups"


class RenameArgs(str, Enum):
    group = "group"
    ap = "ap"


class DhcpArgs(str, Enum):
    clients = "clients"
    server = "server"


class LicenseTypes(str, Enum):
    advance_70xx = "advance-70xx"
    advance_72xx = "advance-72xx"
    advance_90xx_sec = "advance-90xx-sec"
    advance_base_7005 = "advance-base-7005"
    advanced_ap = "advanced-ap"
    advanced_switch_6100 = "advanced-switch-6100"
    advanced_switch_6200 = "advanced-switch-6200"
    advanced_switch_6300 = "advanced-switch-6300"
    advanced_switch_6400 = "advanced-switch-6400"
    advanced_switch_8400 = "advanced-switch-8400"
    dm = "dm"
    foundation_70xx = "foundation-70xx"
    foundation_72xx = "foundation-72xx"
    foundation_90xx_sec = "foundation-90xx-sec"
    foundation_ap = "foundation-ap"
    foundation_base_7005 = "foundation-base-7005"
    foundation_base_90xx_sec = "foundation-base-90xx-sec"
    foundation_switch_6100 = "foundation-switch-6100"
    foundation_switch_6200 = "foundation-switch-6200"
    foundation_switch_6300 = "foundation-switch-6300"
    foundation_switch_6400 = "foundation-switch-6400"
    foundation_switch_8400 = "foundation-switch-8400"
    foundation_wlan_gw = "foundation-wlan-gw"
    vgw2g = "vgw2g"
    vgw4g = "vgw4g"
    vgw500m = "vgw500m"


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

    def _init_refresh(self):
        self.token = self.tokens = "token"

    def _init_update(self):
        self.template = self.templates = "template"
        self.variables = self.variable = "variables"
        self.group = self.groups = "group"
        self.webhooks = self.webhook = "webhook"

    def _init_rename(self):
        self.group = self.groups = "group"
        self.ap = self.aps = "ap"

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

    def _init_clone(self):
        self.group = self.groups = "group"

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
    "event",
]


class LibToAPI:
    """Convert device type stored in Cache to type required by the different API methods

    TODO Working toward a consistent set of device_types, needs review, goal is to have
    all API methods in CentralApi use a consistent set of device type values.  i.e.
    'ap', 'switch', 'gw' ('controller' appears to be the same as gw).  Then use this callable
    object to convert appropriate device type to whatever random value is required by the API
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
        self.method_iden = None,

        # from CentralApi consistent value to Random API value
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
        # Valid Values: ACCESS POINT, SWITCH, GATEWAY, CLIENT
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
            "ap": "IAP",
            "cx": "CX",
            "sw": "SWITCH"
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
    "SPIN_TXT_AUTH": "Initializing Aruba Central Base...",
    "SPIN_TXT_CMDS": "Sending Commands to Aruba Central API Gateway...",
    "SPIN_TXT_DATA": "Collecting Data from Aruba Central API Gateway...",
}


class IdenMetaVars:
    def __init__(self):
        self.dev = "[name|ip|mac|serial]"
        self.dev_many = "[name|ip|mac|serial] ... (multiple allowed)"
        self.group_many = "[GROUP NAME] ... (multiple allowed)"
        self.site = "[name|site id|address|city|state|zip]"
        self.client = "[username|ip|mac]"
        self.dev_words = f"Optional Identifying Attribute: {self.dev}"
        self.generic_dev_types = "[ap|gw|switch]"
        self.dev_types = "[ap|gw|cx|sw]"
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


NO_LOAD_COMMANDS = [
    "show config cencli",
    "show last"
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
