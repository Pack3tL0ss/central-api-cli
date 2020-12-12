from enum import Enum
from typing import Union

dev_to_url = {"switch": "switches", "ap": "aps", "iap": "aps"}


class ShowArgs(str, Enum):
    all = "all"
    # device = "device"
    # devices = "devices"
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


devices = ["switch", "aps", "gateway", "mcd"]

# wrapping keys from return for some calls that have no value
STRIP_KEYS = ["data", "devices", "mcs", "group", "clients", "sites", "switches", "aps"]


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
