from enum import Enum
from typing import Union

# TODO replace references -> use arg_to_what
dev_to_url = {
    "switch": "switches",
    "ap": "aps",
    "iap": "aps"
              }


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


class RefreshWhat(str, Enum):
    cache = "cache"
    token = "token"
    tokens = "tokens"


class DoArgs(str, Enum):
    bounce_poe = "bounce-poe"              # Switches Only
    bounce_interface = "bounce-interface"  # Switches only
    reboot = "reboot"                      # IAP/Controllers/Switches
    sync = "sync"                          # Controllers
    blink_led = "blink-led"                # IAP/Switches
    factory_default = "factory-default"    # Switches only
    write_mem = "write-mem"                # IAP & Switches
    halt = "halt"                          # controllers only


class TemplateLevel1(str, Enum):
    update = "update"
    delete = "delete"
    add = "add"


# Used to determine if arg is for a device (vs group, templates, ...)
devices = ["switch", "aps", "gateway", "all", "device"]

# wrapping keys from return for some calls that have no value
STRIP_KEYS = ["data", "gateways", "switches", "aps", "devices", "mcs", "group", "clients", "sites"]


class ArgToWhat:
    def __init__(self):
        """Mapping object to map supported variations of input for 'what' argument

        Central uses different variations depending on the method (age of method)
        This CLI uses this standard set (whatever is newer of more prevelent) in
        central.  If the API method uses a different one, we'll convert from our
        std set in the method invoking the API call.
        """
        self.gateway = self.gateways = "gateway"
        self.aps = self.ap = self.iap = "aps"
        self.switch = self.switches = "switch"
        self.groups = self.group = "groups"
        self.site = self.sites = "sites"
        self.template = self.templates = "template"
        self.all = "all"
        self.device = self.devices = "device"

    def get(self, key: Union[ShowArgs, str], default: str = None) -> str:
        if isinstance(key, Enum):
            key = key._value_
        return getattr(self, key, default or key)


arg_to_what = ArgToWhat()


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


MESSAGES = {
    "SPIN_TXT_AUTH": "Initializing Arunba Central Base...",
    "SPIN_TXT_CMDS": "Sending Commands to Aruba Central API Gateway...",
    "SPIN_TXT_DATA": "Collecting Data from Aruba Central API Gateway..."
}
