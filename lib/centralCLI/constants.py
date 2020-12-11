from enum import Enum
from typing import Union

dev_to_url = {"switch": "switches", "ap": "aps", "iap": "aps"}


class ShowArgs(str, Enum):
    all = "all"
    # device = "device"
    # devices = "devices"
    switch = "switch"
    switches = "switches"
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


class ArgToWhat:
    def __init__(self):
        self.gateway = self.gateways = "gateway"
        self.ap = self.aps = self.iap = "aps"
        self.switch = self.switches = "switch"
        self.group = self.groups = "group"
        self.sites = self.site = "site"

    # def __call__(func, *args, **kwargs):
    #     return func(*args, **kwargs)

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
