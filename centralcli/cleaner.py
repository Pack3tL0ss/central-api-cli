#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection of functions used to format/clean output from Aruba Central API.
"""
from __future__ import annotations

import ipaddress
import json
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Literal

import pendulum
import yaml
from rich.console import Console
from rich.markup import escape

from centralcli import log, utils

from .constants import STRIP_KEYS, LLDPCapabilityTypes, PoEDetectionStatus, RadioBandOptions, SwitchRolesShort
from .models.cache import Sites
from .models.formatter import CloudAuthUploadResponse
from .objects import DateTime, ShowInterfaceFilters
from .render import tty

if TYPE_CHECKING:
    from .cache import Cache, CacheDevice
    from .constants import DevTypes, LibAllDevTypes, StatusOptions
    from .typedefs import CertType, InsightSeverityType

TableFormat = Literal["json", "yaml", "csv", "rich", "tabulate"]


def _short_connection(value: str) -> str:
    return "" if value is None else value.replace("802.11", "")


def _serial_to_name(sernum: str | None) -> str | None:
    if sernum is None:  #  show audit logs ... have seen "target" of None
        return sernum
    # TODO circular import if placed at top review import logic
    from centralcli import cache

    if not utils.is_serial(sernum):
        return sernum

    match = cache.get_dev_identifier(sernum, retry=False, silent=True, exit_on_fail=False)
    if not match:
        return sernum

    return match.name


def _get_dev_name_from_mac(mac: str, dev_type: LibAllDevTypes | list[LibAllDevTypes] = None, summary_text: bool = False) -> str:
    if mac.count(":") != 5:
        return mac
    else:
        # TODO circular import if placed at top review import logic
        from centralcli import cache
        match = cache.get_dev_identifier(mac, dev_type=dev_type, retry=False, silent=True)
        if not match:
            return mac

        match = utils.unlistify(match)

        if isinstance(match, list) and len(match) > 1:
            return mac

        return match.name if not summary_text else f'{match.name}|{match.ip}|Site: {match.site}'


def _extract_names_from_id_name_dict(id_name: dict) -> str:
    if isinstance(id_name, dict) and "id" in id_name and "name" in id_name:
        names = [x.get("name", "Error") for x in id_name]
        return ", ".join(names)
    else:
        return id_name


def _extract_event_details(details: list[dict]) -> dict:  # pragma: no cover  TODO get_event_logs no longer includes fetching this, may be safe to remnove
    data = {
        k: v for k, v in [tuple(short_value(k, v)) for d in details for k, v in d.items()]
    }
    return "\n".join([f"{k}: {v}" for k, v in data.items()])


def _format_memory(mem: int) -> str:
    # gw and aps report memory in bytes
    gmk = [(1_073_741_824, "GB"), (1_048_576, "MB"), (1024, "KB")]
    if len(str(mem)) > 4:
        for divisor, indicator in gmk:
            if mem / divisor > 1:
                return f'{round(mem / divisor, 2)} {indicator}'

    return f'{mem}'


# TODO determine all modes possible (CX)
vlan_modes = {
    1: "Access",
    2: "LAG",
    3: "Trunk",
}

class radio_modes(Enum):
    access = 0
    mesh = 1
    mesh_point = 2
    monitor = 3
    spectrum = 4


_short_value = {
    "Aruba, a Hewlett Packard Enterprise Company": "HPE/Aruba",
    "No Authentication": "open",
    "last_connection_time": lambda x: DateTime(x, "timediff"),
    "uptime": lambda x: DateTime(x, "durwords-short", round_to_minute=True),
    "updated_at": lambda x: DateTime(x, "mdyt"),
    "last_modified": lambda x: DateTime(x, "day-datetime"),
    "next_rekey": lambda x: DateTime(x, "log"),
    "connected_uptime": lambda x: DateTime(x, "durwords"),
    "lease_start_ts": lambda x: DateTime(x, "log"),
    "lease_end_ts": lambda x: DateTime(x, "log"),
    "create_date": lambda x: DateTime(x, "date-string"),
    "created_at": lambda x: DateTime(x, "mdyt"),  # show portals
    "expire_at": lambda x: DateTime(x, "mdyt"),  # show portals
    "acknowledged_timestamp": lambda x: DateTime(x, "log"),
    "lease_time": lambda x: DateTime(x, "durwords"),
    "lease_time_left": lambda x: DateTime(x, "durwords-short"),
    "token_created": lambda x: DateTime(x, "mdyt"),
    "ts": lambda x: DateTime(x, format="log"),
    "timestamp": lambda x: DateTime(x, format="log"),
    # "subscription_expires": lambda x: DateTime(x, "timediff", format_expiration=True),
    "firmware_scheduled_at": lambda x: DateTime(x, "mdyt"),
    "Unknown": "?",
    "HPPC": "SW",
    "labels": _extract_names_from_id_name_dict,
    "sites": _extract_names_from_id_name_dict,
    "ACCESS POINT": "AP",
    "GATEWAY": "GW",
    # "events_details": _extract_event_details,
    "vc_disconnected": "vc disc.",
    "MAC Authentication": "MAC",
    "connection": _short_connection,
    "DOT1X": ".1X",
    "target": _serial_to_name,
    "0.0.0.0": "-",
    "free_ip_addr_percent": lambda x: f"{x}%",
    "cpu_utilization": lambda x: f"{x}%",
    "AOS-CX": "cx",
    "type": lambda t: t.lower(),
    "release_status": lambda v: u"\u2705" if "beta" in v.lower() else "",
    "start_date": lambda x: DateTime(x, "date-string"),
    "end_date": lambda x: DateTime(x, "date-string", format_expiration=True,),
    "auth_type": lambda v: v if v != "None" else "-",
    "vlan_mode": lambda v: vlan_modes.get(v, v),
    "allowed_vlan": lambda v: v if not isinstance(v, list) or len(v) == 1 else ",".join([str(sv) for sv in sorted(v)]),
    "mem_total": _format_memory,
    "mem_free": _format_memory,
    "firmware_version": lambda v: v if not v or len(set(v.split("-"))) == len(v.split("-")) else "-".join(v.split("-")[1:]),
    "recommended": lambda v: v if not v or len(set(v.split("-"))) == len(v.split("-")) else "-".join(v.split("-")[1:]),
    "learn_time":  lambda x: DateTime(x, "log"),
    "last_state_change":  lambda x: DateTime(x, "log"),
    "graceful_restart_timer": lambda x: DateTime(x, "durwords"),
    "disable_ssid": lambda v: '✅' if not v else '❌', # field is changed to "enabled" check: \u2705 x: \u274c
    "reserved": lambda v: '✅' if v is True else '❌', # field is changed to "enabled" check: \u2705 x: \u274c
    "poe_detection_status": lambda i: PoEDetectionStatus(i).name,
    "reserved_power_in_watts": lambda v: round(v, 2),
    "speed": lambda v: "1000BaseT FD" if v == "1000BaseTFD - Four-pair Category 5 UTP, full duplex mode" else v,
    "ec": lambda v: v if not isinstance(v, list) else ", ".join([LLDPCapabilityTypes(ec).name.replace("_", " ") for ec in v]),
    "sc": lambda v: v if not isinstance(v, list) else ", ".join([LLDPCapabilityTypes(ec).name.replace("_", " ") for ec in v]),
    "chassis_id_type": lambda v: None,
    "chassis_id_type_str": lambda v: None,
    "usage": lambda v: utils.convert_bytes_to_human(v),
    "tx_data_bytes": lambda v: utils.convert_bytes_to_human(v),
    "rx_data_bytes": lambda v: utils.convert_bytes_to_human(v),
    "model": lambda v: v.removeprefix("Aruba").replace(" switch", "").replace("Switch", "").replace(" Swch", "").replace(" Sw ", "").replace("1.3.6.1.4.1.14823.1.2.140", "AP-605H"),
    "device_claim_type": lambda v: None if v and v == "UNKNOWN" else v,
    "radio_name": lambda v: v.removeprefix("Radio "),
    "ip_address_v6": lambda v: v if v and v != "::" else None,
    "ip_v6_address": lambda v: v if v and v != "::" else None,
    # "enabled": lambda v: not v, # field is changed to "enabled"
    # "allowed_vlan": lambda v: str(sorted(v)).replace(" ", "").strip("[]")
}

_short_key = {
    "interface_port": "interface",
    "firmware_version": "version",
    "firmware_backup_version": "backup version",
    "firmware_scheduled_at": "scheduled_at",
    "group_name": "group",
    "public_ip_address": "public ip",
    "ip_address": "ip",
    "ip_addr": "ip",
    "ip_address_v6": "ipv6",
    "ip_v6_address": "ipv6",
    "macaddr": "mac",
    "mac_address": "mac",
    "switch_type": "type",
    "stack_member_id": "stck mbr #",
    "uplink_ports": "uplk ports",
    "total_clients": "clients",
    "updated_at": "updated",
    "cpu_utilization": "cpu %",
    "mem_pct": "mem %",
    "app_name": "app",
    "device_type": "type",
    "classification": "class",
    "ts": "time",
    "timestamp": "time",
    "ap_deployment_mode": "mode",
    "authentication_type": "auth",
    "last_connection_time": "last connected",
    "connection": "802.11",
    "user_role": "role",
    "lease_start_ts": "lease start",
    "lease_end_ts": "lease end",
    "lease_time_left": "lease remaining",
    "classification_method": "classification\nmethod",
    "containment_status": "status",
    "first_det_device": "first det\ndevice",
    "first_det_device_name": "first det\ndevice name",
    "last_det_device": "last det\ndevice",
    "last_det_device_name": "last det\ndevice name",
    "vlan_id": "pvid",
    "free_ip_addr_percent": "free ip %",
    "events_details": "details",
    "associated_device_count": "devices",
    "label_id": "id",
    "command_id": "id",
    "label_name": "name",
    # "acknowledged": "ack",
    "acknowledged_by": "ack by",
    "acknowledged_timestamp": "ack time",
    "aruba_part_no": "sku",
    "network": "ssid",
    "release_status": "beta",
    "license_type": "name",
    "subscription_key": "key",
    "subscription_type": "type",
    "subscription_expires": "expires in",
    "capture_url": "url",
    "register_accept_email": "reg by email",
    "register_accept_phone": "reg by phone",
    "neighbor_id": "router id",
    "dr_address": "DR IP",
    "bdr_address": "BDR IP",
    "dr_id": "DR rtr id",
    "bdr_id": "BDR rtr id",
    "auth_type": "auth",
    "neighbor_count": "nbrs",
    "area_id": "area",
    "intf_state_down_reason": "Down Reason",
    "is_uplink": "Uplink",
    "client_count": "clients",
    "is_best": "best",
    "num_routes": "routes",
    "disable_ssid": "enabled",
    "mac_authentication": "mac auth",
    "hide_ssid": "hidden",
    "essid": "ssid",
    "opmode": "security",
    "power_consumption": "poe usage",
    "poe_priority": "priority",
    "poe_detection_status": "status",
    "power_drawn_in_watts": "draw",
    "pse_allocated_power": "allocated",
    "reserved_power_in_watts": "reserved",
    "power_class": "class",
    "cluster_group_name": "group",
    "cluster_redundancy_type": "redundancy type",
    "ec": "enabled capabilities",
    "sc": "system capabilities",
    "ec_str": "enabled capabilities",
    "tx_data_bytes": "TX",
    "rx_data_bytes": "RX",
    "link_speed": "speed",
    "device_claim_type": "claim_type",
    "device_model": "model",
    "part_number": "sku",
    "serial_number": "serial",
    "radio_name": "band",
    "power_denied_count": "denied count"
}


def ensure_common_keys(data: list[dict]) -> list[dict]:
    try:
        common_keys = []  # This preserves field order vs using set/intersection
        _ = [common_keys.append(k) for inner in data for k in inner.keys() if k not in common_keys]
        res = [{k: iface.get(k) for k in common_keys} for iface in data]
    except Exception as e:  # pragma: no cover
        log.exception(f"{repr(e)} occured in cleaner.ensure_common_keys.\n{e}")
        return data

    return res

def strip_outer_keys(data: dict) -> list[dict[str, Any]] | dict[str, Any]:
    """strip unnecessary wrapping key from API response payload

    Args:
        data (dict): The response payload (aiohttp.Response.json())

    Returns:
        list[dict[str, Any]] | dict[str, Any]: typically list of dicts
    """
    # return unaltered payload if payload is not a dict, or if it has > 5 keys (wrapping typically has 2 sometimes 3)
    if not isinstance(data, dict) or len([key for key in data.keys() if key not in ["cid", "status_code"]]) > 5:
        return data

    data = data if "result" not in data else data["result"]
    _keys = [k for k in STRIP_KEYS if k in data]
    if len(_keys) == 1:
        return data[_keys[0]]
    elif _keys:  # pragma: no cover
        log.warning(f"cleaner.strip_outer_keys(): More wrapping keys than expected from return {_keys}", show=True)
    return data


def short_key(key: str) -> str:
    return _short_key.get(key, key.replace("_", " "))


def short_value(key: str, value: Any):
    # Run any inner dicts through cleaner funcs
    if isinstance(value, dict):
        value = {short_key(k): v if k not in _short_value else _short_value[k](v) for k, v in value.items()}

    if isinstance(value, (str, int, float)):
        return (
            short_key(key),
            _short_value.get(value, value) if key not in _short_value or (not isinstance(value, (bool, int)) and not value) else _short_value[key](value),
        )
    elif isinstance(value, list) and all(isinstance(x, dict) for x in value):
        if key in ["sites", "labels"]:
            value = _extract_names_from_id_name_dict(value)
        elif key in ["events_details"]:  # pragma: no cover  TODO get_event_logs no longer includes fetching this, may be safe to remnove
            value = _extract_event_details(value)
    elif key in _short_value and value is not None:
        value = _short_value[key](value)

    return short_key(key), utils.unlistify(value)

def simple_kv_formatter(data: list[dict[str, Any]], key_order: list[str] = None, strip_keys: list[str] = None, strip_null: bool = False, emoji_bools: bool = False, show_false: bool = True, filter: Callable = None) -> list[dict[str, Any]]:
    """Default simple formatter

    Args:
        data (list[dict[str, Any]]): Data to be formatted, data is returned unchanged if data is not a list.
        key_order (list[str], optional): List of keys in the order desired.
            If defined only key_order key/value pairs are returned. Defaults to None.
        strip_keys (list[str], optional): List of keys to be stripped from output.
        strip_null (bool, optional): Set True to strip keys that have no value for any items.  Defaults to False.
        emoji_bools (bool, optional): Replace boolean values with emoji ✅ for True ❌ for False. Defaults to False.
        show_false (bool, optional): When emoji_bools is True.  Set this to False to only show ✅ for True items, leave blank for False.
        filter (Callable, optional): Callable that returns a bool, if set only items in the list that return True will be included.

    Returns:
        list[dict[str, Any]]: Formatted data
    """
    if not isinstance(data, list):  # pragma: no cover
        log.warning(f"cleaner.simple_kv_formatter expected a list but rcvd {type(data)}")
        return data

    def convert_bools(value: Any) -> Any:
        if not emoji_bools or not isinstance(value, bool):
            return value

        return '\u2705' if value is True else '\u274c' if show_false else ''  # /u2705 = white_check_mark (✅) \u274c :x: (❌)

    strip_keys = strip_keys or []
    if key_order:
        data = [{k: inner_dict.get(k) for k in key_order} for inner_dict in data if not filter or filter(inner_dict)]

    data = [
        dict(
            short_value(
                k,
                convert_bools(v),
            )
            for k, v in d.items()
            if k not in strip_keys
        )
        for d in data
    ]

    return data if not strip_null else utils.strip_no_value(data)

def get_archived_devices(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_order = [
        "serial_number",
        "mac_address",
        "device_type",
        "device_model",
        "part_number",
        "resource_id",
        "device_claim_type",
        "extra_attributes",
        "indent_level",
        "tag_entities",
    ]

    # if all platform_customer_id are the same the calling func adds it to the caption.
    plat_cust_id = list(set([inner.get("platform_customer_id", "--") for inner in data]))
    if len(plat_cust_id) > 1:
        key_order.insert(6, "platform_customer_id")

    data = simple_kv_formatter(data=data, key_order=key_order)
    return sorted(utils.strip_no_value(data), key=lambda x: x["serial"])


def show_groups(data: list[dict], cleaner_format: TableFormat = "rich") -> list[dict]:
    if cleaner_format == "csv":  # Makes allowed types a space separated str, to match format of import file for batch add groups
        data = [{k: v if k != "allowed_types" or not isinstance(v, list) else " ".join(v) for k, v in inner.items()} for inner in data]
    else:
        collapse_keys = ["wlan_tg", "wired_tg", "monitor_only_sw", "monitor_only_cx"]
        data = [
            {
                **{k: v for k, v in inner.items() if k not in collapse_keys},
                "template group": "--" if not any([inner["wlan_tg"], inner["wired_tg"]]) else ", ".join([tgtype for tgtype, tgvar in zip(["Wired", "WLAN"], ["wired_tg", "wlan_tg"]) if inner.get(tgvar)]),
                "monitor only": "--" if not any([inner["monitor_only_sw"], inner["monitor_only_cx"]]) else ", ".join([tgtype for tgtype, tgvar in zip(["sw", "cx"], ["monitor_only_sw", "monitor_only_cx"]) if inner.get(tgvar)])
            } for inner in data
        ]
        if cleaner_format == "rich":
            data = simple_kv_formatter(data, emoji_bools=True)
        data = utils.strip_no_value(data, aggressive=cleaner_format not in ["table", "rich"])

    return data


def get_labels(
    data: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    data = utils.listify(data)
    field_order = ["label_name", "label_id", "associated_device_count", "tags"]
    data = simple_kv_formatter(data, key_order=field_order, strip_null=True, filter=lambda d: d["category_id"] == 1)

    return data


def _client_concat_associated_dev(
    data: dict[str, Any],
    cache: Cache,
    verbose: bool = False,
) -> dict[str, Any]:
    strip_keys = [
        "associated_device_name",
        "associated_device",
        "associated_device_mac",
        "connected_device_type",
        # "interface_port",  # Needed to collapse interface for wired
        "interface_mac",
        "gateway_serial",
        # "group_name",
        # "site",
        "group_id",
        "group id",
        "label_id",
        "swarm_id",
    ]

    dev, _gw = "", ""
    if data.get("associated_device"):
        dev = cache.get_dev_identifier(data["associated_device"], retry=False, exit_on_fail=False)

    if data.get("gateway_serial"):
        _gw = cache.get_dev_identifier(data["gateway_serial"], retry=False, exit_on_fail=True)
        _gateway = {
            "name": None if not _gw else _gw.name,
            "serial": data.get("gateway_serial", ""),
        }
        if verbose:
            data["gateway"] = utils.unlistify(utils.strip_no_value([_gateway]))
        else:
            data["gateway"] = None if not _gw else _gw.name or data["gateway_serial"]
    _connected = {
        "name": data.get("associated_device") if not hasattr(dev, "name") else dev.name,
        "type": data.get("connected_device_type"),
        "serial": data.get("associated_device"),
        "mac": data.get("associated_device_mac"),
        "interface": data.get("interface_port"),
        "interface mac": data.get("interface_mac"),
    }
    data["connected device"] = utils.unlistify(utils.strip_no_value([_connected])) if verbose else f"{_connected['name']}"

    # collapse radio details into sub dict
    _radio = {}
    if "radio_number" in data:
        _radio = {
            "radio number": data["radio_number"],
            "band": data.get("band"),
            "channel": data.get("channel"),
            "radio mac": data.get("radio_mac"),
        }
        strip_keys += ["radio_number", "band", "channel", "radio_mac"]

    _signal = {}
    if "signal_db" in data and data["signal_db"] != "NA":
        _signal = {
            "snr": data.get("snr"),
            "signal db": data["signal_db"],
            "signal strength": data.get("signal_strenth"),  # TODO need to define enum to convert int strength to human readable.  1-5?
            "health": data.get("health"),
        }
        strip_keys += ["snr", "signal_db", "signal_strength", "health"]

    _fingerprint = {}
    if "client_category" in data:
        _fingerprint = {
            "category": data["client_category"],
            "OS": data.get("os_type"),
        }
        if data.get("manufacturer"):
            _fingerprint["manufacturer"] = data["manufacturer"]

        strip_keys += ["client_category", "os_type", "manufacturer"]

    data = {k: v for k, v in data.items() if k not in strip_keys}

    if _radio:
        data["radio"] = utils.unlistify(utils.strip_no_value([_radio]))
    if _signal:
        data["signal"] = utils.unlistify(utils.strip_no_value([_signal]))
    if _fingerprint:
        data["fingerprint"] = utils.unlistify(utils.strip_no_value([_fingerprint]))


    return data


def get_clients(
    data: list[dict],
    verbosity: int = 0,
    cache: callable = None,
    format: TableFormat = None,
    **kwargs
) -> list:
    data = utils.listify(data)
    data = [_client_concat_associated_dev(d, cache=cache, verbose=verbosity) for d in data]
    format = format or "rich" if not verbosity else "yaml"

    verbosity_keys = {
        0:  [
            "name",
            "ip_address",
            "macaddr",
            "user_role",
            "vlan",
            "network",
            "connection",
            "connected device",
            "gateway",
            "failure_reason",
            "failure_stage",
            "group_name",
            "site",
            "last_connection_time",
        ],
        1: [
            "client_type",
            "name",
            "ip_address",
            "macaddr",
            "user_role",
            "vlan",
            "network",
            "authentication_type",
            "usage",
            "connection",
            "connected device",
            "gateway",
            "radio",
            "signal",
            "fingerprint",
            "failure_reason",
            "failure_stage",
            "group_name",
            "site",
            "last_connection_time"
        ]
    }
    if all([c.get("failure_reason") for c in data]):
        verbosity_keys[0].insert(2, "client_type")  # failed clients could be wired or wireless on some devices.

    _short_value["speed"] = lambda x: utils.convert_bytes_to_human(x, speed=True)
    _short_value["maxspeed"] = lambda x: utils.convert_bytes_to_human(x, speed=True)

    if data and all([isinstance(d, dict) for d in data]):
        data = [
            dict(
                short_value(
                    k,
                    f"wired ({data[idx].get('interface_port', '?')})" if d.get(k) == "NA" and k == "network" else d.get(k),
                ) if not verbosity or format == "csv" else short_value(k, d.get(k))
                for k in verbosity_keys.get(verbosity, [*verbosity_keys[max(verbosity_keys.keys())], *d.keys()])  # All keys if verbosity level exceeds what's defined
                if k != "interface_port"  # it's collapsed into the network key, so don't need it as separate key
            )
            for idx, d in enumerate(data)
        ]

    # if tablefmt is tabular we need each row to have the same columns
    if format in ["csv", "rich", "table"]:
        all_keys = list(set([key for d in data for key in d.keys()]))
        data = [
            {k: d.get(k) for k in [*list(d.keys()), *[k for k in sorted(all_keys) if k not in d.keys()]]}
            for d in data
        ]

    data = utils.strip_no_value(data, aggressive=bool(verbosity and format not in  ["csv", "rich", "table"]))

    return data


def sort_result_keys(data: list[dict], order: list[str] = None) -> list[dict]:
    # data = utils.listify(data)
    all_keys = list(set([ik for k in data for ik in k.keys()]))
    ip_word = "ipv4" if "ipv4" in all_keys else "ip_address"
    mask_word = "ipv4_mask" if "ipv4_mask" in all_keys else "subnet_mask"

    # concat ip_address & subnet_mask fields into single ip field ip/mask
    if ip_word in all_keys and mask_word in all_keys:
        for inner in data:
            if inner.get(ip_word) and inner.get(mask_word):
                mask = ipaddress.IPv4Network((inner[ip_word], inner[mask_word]), strict=False).prefixlen
                inner[ip_word] = f"{inner[ip_word]}/{mask}"
                del inner[mask_word]

    # -- calculate used memory percentage if ran with stats --
    if "mem_total" and "mem_free" in all_keys:
        all_keys += ["mem_pct"]
        for inner in data:
            if any([v in [None, "--"] for v in [inner.get("mem_total"), inner.get("mem_free")]]):  # testing for pre-cleaned data for sake of pytest (cache.responses.dev is already populated)
                mem_pct = inner["mem_total"] = inner["mem_free"] = None
            elif inner["mem_total"] and inner["mem_free"]:
                if inner["mem_total"] + inner["mem_free"] == 100:  # CX shows mem total / free as percentages
                    mem_pct = inner["mem_total"]
                else:
                    mem_pct = round(((float(inner["mem_total"]) - float(inner["mem_free"])) / float(inner["mem_total"])) * 100, 2)
            else:
                mem_pct = 0
            inner["mem_pct"] = f'{mem_pct}%'

    # concat stack_member_id and switch_role
    stack_fields = ["stack_member_id", "switch_role"]
    stack_remove_fields = ["stack_member_id"]
    if all([key in all_keys for key in stack_fields]):
        data = [{k: v if k != "name" or "switch_role" not in inner or inner["switch_role"] < 3 else f"{v} ({inner.get('stack_member_id')}:{SwitchRolesShort(inner['switch_role']).name})" for k, v in inner.items() if k not in stack_remove_fields} for inner in data]
    elif "switch_role" in all_keys:
        data = [{k: v if k != "name" or "switch_role" not in inner or inner["switch_role"] or 0 < 3 else f"{v} ({inner.get('stack_member_id')}:{SwitchRolesShort(inner['switch_role']).name})" for k, v in inner.items() if k not in stack_remove_fields} for inner in data]

    if order:
        to_front = order
    else:
        to_front = [
            "vlan_id",
            "name",
            "status",
            "type",
            "stack_member_id",
            "client_count",
            "model",
            'mode',
            "vlan_desc",
            "id",  # pvid for VLAN output
            "ip",
            "ip_address",
            "ipaddress",
            "ipv4",
            "subnet_mask",
            "ipv4_mask" "serial",
            "macaddr",
            "mac",
            "serial",
            "ap_deployment_mode",
            "group_name",
            "group",
            "site",
            "labels",
            "addr_mode",
            "admin_mode",
            "oper_mode",
            "untagged_ports",
            "tagged_ports",
            "is_management_vlan",
            "is_jumbo_enabled",
            "is_voice_enabled",
            "is_igmp_enabled",
            "uptime",
            'reboot_reason',
            'cpu_utilization',
            'mem_total',
            'mem_free',
            'mem_pct',
            'firmware_version',
            'version',
            'firmware_backup_version',
            'oper_state_reason',
            "services",
            "subscription_key",
            "subscription_expires",
        ]
    to_front = [i for i in to_front if i in all_keys]
    _ = [all_keys.insert(0, all_keys.pop(all_keys.index(tf))) for tf in to_front[::-1]]
    data = [{k: id.get(k) for k in all_keys} for id in data]

    return data

class FilterRows:
    _version: str = None

    def __init__(self, version: str = None):
        self._version = version

    @classmethod
    def set_filters(cls, version: str = None):  # TODO look for design pattern for this.  Could take tuples (key: str, filter: str, fuzzy: bool, inverse: bool)
        cls._version = version

    def __call__(self, data: dict[str, Any]) -> bool:
        if self._version is None:
            return True
        if self._version.startswith("-"):
            return True if self._version.lstrip("-") not in data["firmware_version"] else False
        else:
            return True if self._version in data["firmware_version"] else False


def get_devices(data: list[dict[str, Any]] | dict[str, Any], *, verbosity: int = 0, output_format: TableFormat = None, version: str = None) -> list[dict] | dict:
    """Clean device output from Central API (Monitoring)

    Args:
        data (list[dict[str, Any]] | dict[str, Any]): Response data from Central API
        verbose (bool, optional): Not Used yet. Defaults to True.
        version (str, optional): Filters output based on (firmware) version (fuzzy match)
            or when prefixed by '-', Show all devices other than devices matching the version provided. Defaults to None.

    Returns:
        list[dict[str, Any]] | dict[str, Any]: The cleaned data with consistent field heading, and human readable values.
    """
    data = utils.listify(data)
    all_keys = set([k for inner in data for k in inner.keys()])
    # common_keys = set.intersection(*map(set, data))
    table_formats = ["csv", "rich", "tabulate"]

    # pre cleaned key values
    verbosity_keys = {
        0:  [
                "name",
                "status",
                "type",
                "client_count",
                "model",
                "ip_address",
                "macaddr",
                "mac",  # get_devices_with_inventory has already cleaned keys
                "serial",
                "group_name",
                "site",
                "firmware_version",
                "services",
                "subscription_key",
                "subscription_expires",
        ]
    }
    if "services" not in all_keys:  # indicates inventory is part of the listing
        verbosity_keys[0].insert(10, "uptime") # more space if inventory not in listing so provide uptime.
    if "type" not in all_keys:  # indicates data is for single device type. typically allows more space
        verbosity_keys[0].insert(10, "cpu_utilization")
        verbosity_keys[0].insert(10, "mem_pct")

    if "status" in all_keys and "subscription_key" in all_keys:  # combined device/inventory.  too much for non-verbose remove the sub keyu
        _ = verbosity_keys[0].pop(verbosity_keys[0].index("subscription_key"))
        if "client_count" in all_keys:
            _ = verbosity_keys[0].pop(verbosity_keys[0].index("client_count"))

    data = sort_result_keys(data)
    filter_rows = FilterRows(version=version)

    data = [
        {k: v for k, v in inner.items() if k in verbosity_keys.get(verbosity, all_keys)}
        for inner in data
        if filter_rows(inner)
    ]

    _short_key["subscription_key"] = "subscription key"
    data = simple_kv_formatter(data)

    # strip any cols that have no value across all rows,
    # strip any keys that have no value regardless of other rows (dict lens won't match, but display is vertical)
    data = utils.strip_no_value(data, aggressive=output_format not in table_formats)

    data = sorted(data, key=lambda i: (i.get("site") or "", i.get("type") or "", i.get("name") or ""))

    return data

def get_audit_logs(data: list[dict], cache_update_func: callable = None, verbosity: int = 0) -> list[dict]:
    if verbosity > 1:
        return data  # No formatting with verbosity -vv

    field_order = [
        "id",
        "ts",
        "app_name",
        "classification",
        "device_type",
        "description",
        "target",
        "ip_addr",
        "user",
        "has_details",
    ]

    if not verbosity:
        data = [inner for inner in data if inner.get("user") != "periodic_system_default_app_task"]

    data = [dict(short_value(k, d.get(k)) for k in field_order) for d in data]
    data = utils.strip_no_value(data)

    if len(data) > 0 and cache_update_func:
        idx, cache_list = 1, []
        for d in data:
            if d.get("has details") is True:
                cache_list += [{"id": idx, "long_id": d["id"]}]
                d["id"] = idx
                idx += 1
            else:
                d["id"] = "-"
            del d["has details"]
        if cache_list:
            cache_update_func(cache_list)

    return data


def get_alerts(data: list[dict],) -> list[dict]:
    # TODO Need cleaner to strip all state: "Close" alerts, and all associated state: "Open"

    field_order = [
        "timestamp",
        "severity",
        "type",
        # "group_name",
        # "device info",
        "description",
        # "labels",
        "acknowledged",
        # "acknowledged_by",
        # "acknowledged_timestamp",
        # "state",
    ]
    for d in data:
        # d["details"] = d.get("details") or {}
        # d["device info"] = f"{d['details'].get('hostname', '')}|" \
        #     f"{d.get('device_id', '')}|Group: {d.get('group_name', '')}".lstrip("|")
        d["severity"] = d.get("severity", "INFO")
        if d.get("acknowledged"):
            d["acknowledged"] = f'{"by " if d.get("acknowledged_by") else ""}' \
                f'{d.get("acknowledged_by")}{" @ " if d.get("acknowledged_by") else ""}' \
                f'{"" if not d.get("acknowledged_timestamp") else DateTime(d["acknowledged_timestamp"], "log")}'
        else:
            d["acknowledged"] = None

    data = [dict(short_value(k, d[k]) for k in field_order if k in d) for d in data]
    data = utils.strip_no_value(data)

    return data


def get_event_logs(data: list[dict], cache_update_func: callable = None) -> list[dict]:
    # TODO accept verbose option and provide additional details with verbose. (currently just bypasses cleaner and displays yaml)

    field_order = [
        "id",
        "timestamp",
        # "level",
        # "event_type",
        "description",
        # "events_details",
        # "device_type",
        # "client_mac",
        "device info",
        # "device",
        # "hostname",
        # "device_serial",
        # "device_mac",
        # "group_name",
        # "labels",
        # "sites",
    ]
    for d in data:
        site = d.get('sites')
        if site:
            site = site[0].get("name")
        site = "" if not site else f"|S:{site}"
        d["device info"] = f"{d.get('hostname', '')}|" \
            f"{d.get('device_serial', '')}|G:{d.get('group_name', '')}{site}"

    # Stash event_details in cache indexed starting @ most recent event
    if len(data) > 1 and cache_update_func:
        idx, cache_list = 1, []
        for d in data:
            if d.get("has_rowdetail") is True:
                _details = {
                    k: v for inner in d["events_details"] for k, v in inner.items()
                }
                cache_list += [{"id": str(idx), "device": d["device info"], "details": _details}]
                d["id"] = idx
                idx += 1
            else:
                d["id"] = "-"
            # del d["has_rowdetail"]
        if cache_list:
            cache_update_func(cache_list)

    data = [dict(short_value(k, d[k]) for k in field_order if k in d) for d in data]
    data = utils.strip_no_value(data)

    return data


def sites(data: list[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]]:
    data = utils.listify(data)
    data = Sites(data)
    return data.model_dump()


def get_certificates(data: dict[str, Any], valid: bool = None, cert_types: list[CertType] = None) -> list[dict[str, Any]]:
    data = utils.listify(data)
    short_keys = {
        "cert_name": "name",
        "cert_type": "type",
        "expire_date": "expiration",
        "expire": "expired",
        "cert_md5_checksum": "md5 checksum",
        "cert_sha1_checksum": "sha1 checksum",
    }
    _unfiltered_cnt = len(data)
    if valid is not None:
        data = [cert for cert in data if "expire" not in cert or cert["expire"] is not valid]
    if cert_types:
        data = [cert for cert in data if "cert_type" not in cert or cert["cert_type"] in cert_types]
    if not data:
        econsole = Console(stderr=True)
        econsole.print(f"[dark_orange3]:warning:[/]  Provided filters have filtered out all results.  Cache was updated with {_unfiltered_cnt} certificates prior to applying filters. ")
        econsole.print("   Use [cyan]cencli show cache certs[/] [dim italic]to see results from cache [green](No additional API call)[/green][/dim italic]")
        econsole.print("   or [cyan]cencli show certs[/] again, without filters [dim italic]to see unfiltered response[/]")
        return data

    def format_expire_fields(field_name: Literal["expire_date", "expired"], value: bool | str) -> DateTime | str:
        if field_name == "expire_date":
            return DateTime(pendulum.from_format(value.rstrip("Z"), "YYYYMMDDHHmmss").timestamp(), "date-string")

        return f"[bright_red]{value}[/]" if value is True else value


    if data and len(data[0]) != len(short_keys):  # pragma: no cover
        log = logging.getLogger()
        log.error(
            f"get_certificates has returned more keys than expected, check for changes in response schema\n"
            f"    expected keys: {short_key.keys()}\n"
            f"    got keys: {data[0].keys()}"
        )
        return data
    else:
        data = [
            {short_keys[k]: d[k] if not k.startswith("expire") else format_expire_fields(k, d[k]) for k in short_keys}
            for d in data
        ]
        return data


def get_lldp_neighbor(data: list[dict[str, str]]) -> dict[str: dict[str, str]]:
    data = utils.listify(data)
    strip_keys = ["cid"]
    # grab the key details from switch lldp return, make data look closer to lldp return from AP
    if data and "dn" in data[0].keys():
        data = [{**dict(d if "dn" not in d else d["dn"]), "vlan_id": ",".join(d.get("vlan_id", [])), "lldp_poe": d.get("lldp_poe_enabled")} for d in data]
        data = sort_interfaces(data, interface_key="port")
    # simplify some of the values and strip the bond0 entry from AP
    data = [dict(short_value(k, d[k]) for k in d if d.get("localPort", "") != "bond0" and k not in strip_keys) for d in data]

    return utils.strip_no_value(data)


def get_vlans(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    short_keys = {
        # site
        "vlanName": "name",
        "vlanId": "pvid",
        # switch
        "id": "pvid",
        "ipaddress": "ip",
        "is_management_vlan": "mgmt",
        "is_igmp_enabled": "igmp",
        "is_jumbo_enabled": "jumbo",
        "is_voice_enabled": "voice",
        "tagged_ports": "tagged",
        "untagged_ports": "untagged",
        # gateways
        "admin_mode": "admin state",
        "ipv4": "ip",
        "ipv4_mask": "mask",
        "addr_mode": "type",
        "vlan_desc": "desc.",
        "vlan_id": "pvid",
    }

    data = sort_result_keys(data)
    # strip 'type' field which is 'primary vlan type' if all are "Regular"
    # ["Regular", "Private-Primary", "Private-Isolated", "Private-Community"]
    strip_keys = []
    if all([k.get("type", "") == "Regular" for k in data]):
        strip_keys += ["type"]

    data = [
        {short_keys.get(k, k.replace("_", " ")): utils.unlistify(d[k]) for k in d if k not in strip_keys} for d in utils.strip_no_value(data)
    ]

    return data


def wids(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # all_keys = set([k for d in data for k in d])
    key_order = [
        "id",
        "name",
        "mac_vendor",
        "signal",
        "ssid",
        "encryption",
        "class",
        "containment_status",
        "classification_method",
        "acknowledged",
        "first_seen",
        "first_det_device",
        "first_det_device_name",
        "last_seen",
        "last_det_device",
        "last_det_device_name",
        "labels",
        "lan_mac",
        "group",
    ]
    return simple_kv_formatter(data, key_order=key_order, strip_null=True, emoji_bools=False)


def get_dhcp(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = utils.unlistify(data)
    if "free_ip_addr_percent" in data[-1]:
        field_order = [
            "pool_name",
            "pool_size",
            "vlan_id",
            "subnet",
            "lease_time",
            "free_ip_addr_percent",
        ]
    else:
        field_order = [
            "client_name",
            "mac",
            "ip",
            "reservation",
            "reserved",
            # "mask",
            "pool_name",
            "vlan_id",
            "subnet",
            "lease_start_ts",
            "lease_end_ts",
            "lease_time",
            "lease_time_left",
            # "infra_type",
            "client_type",
        ]

    # API-FLAW Reservations for APs show nonsense values for lease_ fields, so we strip them.  Most reservations only show ip and mac for reservations.
    data = [d if not d.get("reserved") else {k: v for k, v in d.items() if not k.startswith("lease")} for d in data]
    data = [{"client name": None, **dict(short_value(k, d.get(k)) for k in field_order)} for d in data]
    data = utils.strip_no_value(data)
    return data

def get_template_details_for_device(data: str, device: CacheDevice) -> str:
    """Convert form-data response to dict

    Args:
        data (str): string data with summary and optionally running config

    Returns:
        dict: dict with summary(dict), running config(str) and
        central side config(str).
    """
    data = utils.unlistify(data)  # TODO we listify before sending to cleaner, this function expects str so unlistify here.  See if listify can be removed in _display_results
    split_line = data.split("\n")[0].rstrip()
    data_parts = [
        d.lstrip().splitlines() for d in data.split(split_line)
        if d.lstrip().startswith("Content-Disposition")
    ]

    console = Console(emoji=False)
    with console.capture() as cap:
        for part in data_parts:
            if 'name="Summary"' in part[0]:
                console.rule(f"[bright_green]Configuration Summary[/] for [magenta]{device.name}[/] ({device.serial})")
                summary = yaml.safe_dump(json.loads("\n".join(part[2:])), sort_keys=True)
                console.print(summary)
            elif 'name="Device_running_config"' in part[0].replace(" ", "_"):
                console.rule(f"[magenta]{device.name}[/] ({device.serial}) [bright_green]Running Configuration[/]")
                console.print("\n".join(part[2:]))
            elif 'name="Device_central_side_config"' in part[0].replace(" ", "_"):
                console.rule(f"[magenta]{device.name}[/] ({device.serial}) [bright_green]Central Side Configuration[/]")
                console.print("\n".join(part[2:]))
            elif 'name="Configuration_error_details"' in part[0].replace(" ", "_"):
                console.rule(f"[magenta]{device.name}[/] ({device.serial}) Configuration [red]Error Details[/]")
                console.print("\n".join(part[2:]))

        console.print(
            "\n[italic][deep_sky_blue]:information:[/]  The Order and format of lines from running config may differ from the Central side config depending on how the template is structured.[/italic]",
            emoji=True
        )

    output = cap.get()

    return output


def parse_caas_response(data: dict | list[dict[str, Any]]) -> list[str]:
    """Parses Response Object from caas API updates output attribute

    """
    console = Console(emoji=False, record=True)
    data = utils.unlistify(data)
    out = []
    lines = f"[reset]{'-' * 22}"
    _code_to_markup = {
        0: "[bright_green]OK[/bright_green]",
        1: "[red]ERROR[/red]",
        2: "[dark_orange3]WARNING[/dark_orange3]"
    }

    if data.get("_global_result", {}).get("status", '') == 0:
        global_res = "[bright_green]Success[/bright_green]"
    else:
        global_res = "[red]Failure[/red]"
    out += [lines, f"Global Result: {global_res}", lines]

    if data.get("cli_cmds_result"):
        out += ["\n -- [cyan bold]Command Results[/cyan bold] --"]
        for cmd_resp in data["cli_cmds_result"]:
            for _c, _r in cmd_resp.items():
                _r_code = _r.get("status")
                _r_pretty = _code_to_markup.get(_r_code, f"[red]ERROR ({_r_code})[/red]")
                out += [f" [{_r_pretty}] {_c}"]
                cmd_status = _r.get('status_str')
                if cmd_status:
                    _r_txt = f"[italic]{escape(cmd_status)}[/italic]"
                    out += [lines, _r_txt, lines]

        console.begin_capture()
        console.print("\n".join(out))
        out = console.end_capture()

    return out

def get_all_webhooks(data: list[dict]) -> list[dict]:
    class HookRetryPolicy(Enum):
        none = 0
        important = 1  # Up to 5 retries over 6 minutes
        critical = 2  # Up to 5 retries over 32 hours
        # none = 99  # indicates an error retrieving policy from payload

    del_keys = ["retry_policy", "secure_token", "urls"]
    # flatten dict
    data = [
        {**{k: v for k, v in d.items() if k not in del_keys},
         "urls": "\n".join(d.get("urls", [])),
         "retry_policy": HookRetryPolicy(d.get("retry_policy", {}).get("policy", 0)).name,
         "token": d.get("secure_token", {}).get("token", ""), "token_created": d.get("secure_token", {}).get("ts", 0)
         }
         for d in data
    ]

    data = [
        dict(short_value(k, d[k]) for k in d) for d in utils.strip_no_value(data)
    ]

    return data

def get_branch_health(data: list, down: bool = False, wan_down: bool = False) -> list:
    field_order = [
                "name",
                "potential_issue",
                "device_up",
                "device_down",
                "connected_count",
                "failed_count",
                "wan_tunnels_down",
                "wan_tunnels_no_issue",
                "wan_uplinks_down",
                "wan_uplinks_no_issue",
                "branch_cpu_high",
                "branch_device_status_up",
                "branch_device_status_down",
                "cape_state",
                "cape_state_dscr",
                "cape_url",
                "device_high_ch_2_4ghz",
                "device_high_ch_5ghz",
                "device_high_cpu",
                "device_high_mem",
                "device_high_noise_2_4ghz",
                "device_high_noise_5ghz",
                "insight_hi",
                "insight_lo",
                "insight_mi",
                "score",
                "silverpeak_state",
                "silverpeak_state_summary",
                "silverpeak_url",
                "user_conn_health_score",
                "wired_cpu_high",
                "wired_device_status_down",
                "wired_device_status_up",
                "wired_mem_high",
                "wlan_cpu_high",
                "wlan_device_status_down",
                "wlan_device_status_up",
                "branch_mem_high",
                "wlan_mem_high",
    ]
    data = [
        dict(short_value(k, d[k]) for k in field_order) for d in data
    ]
    data = utils.strip_no_value(data)


    return data


def get_device_inventory(data: list[dict], sub: bool = None, key: str = None) -> list[dict]:
    field_order = [
        "id",
        "serial",
        "mac",
        "type",
        "model",
        "sku",
        "services",
        "subscription_key",
        "subscription_expires",
        "archived"
    ]

    _short_key["subscription_key"] = "subscription key"  # override the default short value which is used for subscription output
    data = simple_kv_formatter(data, key_order=field_order, emoji_bools=True)
    data = sorted(utils.strip_no_value(data), key=lambda i: (i["services"] or "", i["model"]))

    if key is not None:
        data = [{k: v for k, v in d.items()} for d in data if(d["subscription key"] or "") == key]
    elif sub is not None:
        if sub:
            data = [{k: v for k, v in d.items()} for d in data if d["services"]]
        else:
            data = [{k: v for k, v in d.items()} for d in data if not d["services"]]

    return data


def get_client_roaming_history(data: list[dict]) -> list[dict]:
    # field order is b4 key conversion _short_key
    field_order = [
        "previous_ap_name",
        "ap_name",
        "ap_serial",
        "network",
        "bssid",
        "band",
        "channel",
        "roaming_type",
        "rssi",
        "ts",
    ]
    data = sorted(data, key=lambda i: i.get("ts", ""))
    data = simple_kv_formatter(data, key_order=field_order, strip_null=True)

    return data

def get_fw_version_list(data: list[dict], format: TableFormat = "rich", verbose: bool = False) -> list[dict]:
    # Override default behavior of k, v formatter (default which implies rich will use unicode check mark for beta)
    if format != "rich" and "release_status" in data[-1].keys():
        _short_value["release_status"] = lambda v: "True" if "beta" in v.lower() else "False"

    data = [
        dict(short_value(k, d[k]) for k in d) for d in data
    ]
    data = utils.strip_no_value(data)

    if format == "rich" and not verbose and tty:  # pragma: no cover condition depends on tty
        data = data[0:tty.rows - 12]

    return data

def get_subscriptions(data: list[dict], default_sort: bool = True) -> list[dict]:
    field_order = [
        "name",
        "license_type",
        "key",
        "type",
        "sku",
        "status",
        "subscription_type",
        "quantity",
        "qty",
        "available",
        "subscription_key",
        "start_date",
        "end_date",
    ]
    _short_value["status"] = lambda s: f"[red]{s}[/]" if s == "EXPIRED" else f"[bright_green]{s}[/]"
    _short_value["available"] = lambda s: s if s > 0 else f"[red]{s}[/]"
    if default_sort:
        data = sorted(data, key=lambda s: s.get("name", s.get("tier", s.get("license_type", 0))))
        ok_subs = [sub for sub in data if sub["status"] == "OK"]
        expired_subs = [sub for sub in data if sub["status"] != "OK"]
        data = [*ok_subs, *expired_subs]
    data = [
        dict(short_value(k, d[k]) for k in field_order if k in d) for d in data
    ]

    return data

def get_portals(data: list[dict],) -> list[dict]:
    field_order = [
        "name",
        "id",
        "auth_type",
        # "auth_type_num",
        "capture_url",
        # "is_aruba_cert",
        # "is_default",
        # "is_editable",
        # "is_shared",
        "register_accept_email",
        "register_accept_phone",
        # "scope"
    ]
    short_auth_types = {
        "Username/Password": "user/pass",
        "Self-Registration": "self-reg",
        "Anonymous": "anon",
    }
    for d in data:
        for k, v in short_auth_types.items():
            if k in d["auth_type"]:
                d["auth_type"] = d["auth_type"].replace(k, v)

    data = simple_kv_formatter(data, key_order=field_order, emoji_bools=True)
    data = utils.strip_no_value(data)

    return data


def get_portal_profile(data: list[dict[str, Any]]) -> dict[str, Any]:
    # _display_output will listify the dict prior to sending it in as most outputs are list[dict]
    data = utils.unlistify(data)
    return {k: v for k, v in data.items() if k != "logo"}

def get_ospf_neighbor(data: list[dict[str, Any]] | dict[str, Any],) -> list[dict[str, Any]]:
    data = utils.listify(data)

    # send all key/value pairs through formatters and return
    # swapping "address" for ip here as address is also used for site address
    data = [
        dict(short_value(k if k != "address" else "ip", v) for k, v in inner.items()) for inner in data
    ]

    return data

def get_ospf_interface(data: list[dict[str, Any]] | dict[str, Any],) -> list[dict[str, Any]]:
    data = utils.listify(data)

    # send all key/value pairs through formatters and return
    # swapping "address" for ip here as address is also used for site address
    data = [
        dict(
            short_value(
                k if k != "address" else "ip/mask", v if k != "address" else str(ipaddress.ip_network(f"{inner['address']}/{inner['mask']}", strict=False))
            ) for k, v in inner.items() if k != "mask"
        ) for inner in data
    ]

    return data


def sort_interfaces(interfaces: list[dict[str, Any]], interface_key: str= "port_number") -> list[dict[str, Any]]:
    try:
        sorted_interfaces = sorted(
            interfaces, key=lambda i: [int(i[interface_key].split("/")[y]) for y in range(i[interface_key].count("/") + 1)]
        )
        return sorted_interfaces
    except Exception as e:  # pragma: no cover
        log.error(f"Exception in cleaner.sort_interfaces {e.__class__.__name__}")
        return interfaces


def show_interfaces(data: list[dict] | dict, verbosity: int = 0, dev_type: DevTypes = "cx", filters: ShowInterfaceFilters = None, by_interface: bool = None) -> list[dict] | dict:
    """Clean Output of interface endpoints for each device type.

    Args:
        data (list[dict] | dict): The API response payload
        verbosity (int, optional): verbosity, more fields displayed. Defaults to 0.
        dev_type (DevTypes, optional): One of ap, gw, cx, sw, switch. Defaults to "cx".
        by_interface (bool, optional): By default if verbosity > 0 list[dict] will be converted to dict keyed by interface, set this to False to always return a list.
            This is useful for multi-device interface listings.  Defaults to None.

    Returns:
        list[dict] | dict: Cleaned API response payload with less interesting fields removed
    """
    if isinstance(data, list) and data and "member_port_detail" in data[0]:  # switch stack
        common = {"device": data[0]["device"], "_dev_type": data[0]["_dev_type"]}
        normal_ports = [{**common, **p} for sw in data[0]["member_port_detail"] for p in sw["ports"]]
        stack_ports = [{**common, **{k: "--" if k not in p else p[k] for k in normal_ports[0].keys()}, "type": "STACK PORT"} for sw in data[0]["member_port_detail"] for p in sw.get("stack_ports", [])]
        data = sort_interfaces([*normal_ports, *stack_ports])
    else:
        data = utils.listify(data)

    filters = filters if filters is not None else ShowInterfaceFilters()

    # TODO verbose and non-verbose
    # TODO determine if "mode" has any value, appears to always be Access on SW
    key_order = [
        "device",
        "macaddr",
        "type",
        "phy_type",
        "port",
        "oper_state",
        "operational_state",  # ap
        "admin_state",
        "status",
        "intf_state_down_reason",
        "speed",
        "link_speed",  # ap
        "duplex_mode",
        "vlan",
        "allowed_vlan",
        "vlan_mode",
        "mode",
        "has_poe",
        "poe_state",
        "power_consumption",
        "is_uplink",
        "trusted",
        "tx_usage",
        "rx_usage",
        "mux",
        "vsx_enabled",
    ]
    strip_keys = ["port_number", "alignment", "oper_state"]

    verbosity_keys = {
        0: [
            "device", # multi device. stripped in combiner
            "port_number",
            "name", # ap
            "vlan",
            "allowed_vlan",
            "vlan_mode",
            "admin_state",
            "status",
            "power_consumption",
            "intf_state_down_reason",
            "speed",
            "link_speed",  # ap
            "is_uplink",
            "phy_type",
            "type"
        ]
    }

    # API for AOS_SW always shows VLAN as 1
    if dev_type in ["sw", "switch"]:
        # _ = verbosity_keys[0].pop(verbosity_keys[0].index("vlan"))
        data = [
            d if d.get("_dev_type", "") != "sw" and dev_type != "sw" else {
                **d,
                "vlan_mode": "Trunk" if len(d.get("allowed_vlan")) > 1 else "Access",
                "vlan": "?" if len(d.get("allowed_vlan")) > 1 else d["allowed_vlan"][0],
            } for d in data
        ]
    elif dev_type == "gw":
        verbosity_keys[0].insert(4, "trusted")
    elif dev_type == "ap" and data:
        if "device" in data[0]:
            data = [{"device": d["device"], **iface} for d in data for iface in d.get("ethernets", [])]
        elif "ethernets" in data[0]:
            data = data[0]["ethernets"]
        verbosity_keys[0].insert(3, "macaddr")
        verbosity_keys[0].insert(11, "duplex_mode")
        for iface in data:
            if iface.get("status", "").lower() != "up":
                iface["duplex_mode"] = "--"
                iface["link_speed"] = "--"

    # Append any additional keys to the end
    if verbosity == 0:
        key_order = verbosity_keys[verbosity]
        # send all key/value pairs through formatters
        data = [
            dict(short_value(k, d[k],) for k in key_order if k in d) for d in data
        ]
    else:
        key_order = [*key_order, *data[-1].keys()]
        # send all key/value pairs through formatters and convert list[dict] to dict where port_number is key
        if by_interface is not False:
            key_field = "port_number" if dev_type != "ap" else "name"
            data = {
                d[key_field] if not d[key_field].isdigit() else int(d[key_field]): dict(short_value(k, d.get(k),) for k in key_order if k not in strip_keys) for d in data
            }
        else:
            strip_keys = [k for k in strip_keys if k != "port_number"]
            data = [
                dict(short_value(k, d.get(k),) for k in key_order if k not in strip_keys) for d in data
            ]

    return utils.strip_no_value(data)


def get_switch_poe_details(data: list[dict[str, Any]], verbosity: int = 0, powered: bool = False, aos_sw: bool = False) -> list[dict[str, Any]]:
    verbosity_keys = {
        0: [
            "port",
            "poe_detection_status",
            "poe_priority",
            "power_drawn_in_watts",
            # "amperage_drawn_in_milliamps",
            "pse_allocated_power",
            "reserved_power_in_watts",
            "pre_standard_detect",
            "power_class",
            "power_denied_count"
        ]
    }
    if powered:
        data = list(filter(lambda d: d.get("poe_detection_status", 99) == 3, data))

    # AOS-SW does not return usage in watts, calculate it to make it consistent with CX.  CX has these fields but always returns 0 for the 2 fields.
    if aos_sw:
        data = [{**d, "power_drawn_in_watts": round(d.get("amperage_drawn_in_milliamps", 0) / 1000 * d.get("port_voltage_in_volts", 0), 2)} for d in data]

    if verbosity == 0:
        data = [dict(short_value(k, d.get(k),) for k in verbosity_keys[verbosity]) for d in data]
        data = utils.strip_no_value(data)

    return sort_interfaces(data, interface_key="port")

def show_ts_commands(data: list[dict[str, Any]] | dict[str, Any],) -> list[dict[str, Any]]:
    key_order = [
        "command_id",
        "category",
        "command",
    ]
    strip_keys = [
        "summary"
    ]

    data = [
        dict(short_value(k, d.get(k),) for k in key_order if k not in strip_keys) for d in data if "arguments" not in d.keys()
    ]

    return data

def get_overlay_routes(data: list[dict[str, Any]] | dict[str, Any], format: TableFormat = "rich", simplify: bool = True) -> list[dict[str, Any]]:
    if "routes" in data:
        data = data["routes"]

    data = utils.listify(data)
    if "nexthop_list" in data[-1].keys():
        base_data = [{"destination": f'{r["prefix"]}/{r["length"]}', **{k: v for k, v in r.items() if k not in ["prefix", "length", "nexthop_list"]}} for r in data]
        outdata = base_data
    else:
        base_data = [{"destination": f'{r["prefix"]}/{r["length"]}', **{k: v for k, v in r.items() if k not in ["prefix", "length", "nexthop"]}} for r in data]
        if isinstance(data[-1]["nexthop"], list):
            next_hop_data = [[{"interface": "" if not hops.get("interface") else utils.unlistify(hops["interface"]), **{k if k != "address" else "nexthop": v for k, v in hops.items() if k != "interface"}} for hops in r["nexthop"]] for r in data]
        else:
            next_hop_data = [[{"nexthop": _get_dev_name_from_mac(r["nexthop"], dev_type=("gw", "ap",), summary_text=True)}] for r in data]

        field_order = [
            "destination",
            "interface",
            "nexthop",
            "protocol",
            "flags",
            "learn_time",
            "metric",
            "is_best",
        ]

        # Collapse next_hop data into base dict
        outdata = []
        for base, nh in zip(base_data, next_hop_data):
            for idx, route in enumerate(nh):
                if idx == 0 or not simplify:
                    route = {**base, **route}
                else:
                    route = {**{k: "" for k in base.keys()}, **route}
                outdata += [{k: route.get(k) for k in field_order if k in route.keys()}]  # Put fields in desired order

        if format == "rich" and data and "is_best" in outdata[-1].keys():
            outdata = [
                {k: str(v).replace("True", "\u2705").replace("False", "") if k == "is_best" else v for k, v in d.items()}
                for d in outdata
            ]

    _short_value["0.0.0.0"] = "0.0.0.0"  # OVERRIDE default referenced by simple_kv_formatter.  Otherwise will replace with "-"
    data = simple_kv_formatter(outdata)

    return data


def get_overlay_interfaces(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        data = [
            {
                k: v if k != "endpoint" else _get_dev_name_from_mac(v, dev_type="ap") for k, v in i.items()
            }
            for i in data
        ]
    except Exception as e:  # pragma: no cover
        log.error(f'get_overlay_interfaces cleaner threw {repr(e)} trying to get ap name from mac, skipping.', show=True)

    return simple_kv_formatter(data)

def get_full_wlan_list(data: list[dict] | str | dict[str, Any], verbosity: int = 0, format: TableFormat = "rich") -> list[dict]:
    # TODO PlaceHolder logic, currently only support verbosity level 0
    verbosity_keys = {
        0: [
            'group',
            'name',
            'essid',
            'type',
            'hide_ssid',
            'disable_ssid',
            'rf_band',
            'mac_authentication',
            'vlan',
            'opmode',
            'access_type',
            'cluster_name'
        ]
    }
    pretty_data = []

    # rf_band all is a legacy key so all means 2.4 and 5, this updates so that all is only the value if 6 is also enabled.
    # also grabs values for keys that are stored in dicts
    def _simplify_value(wlan: dict, k: str, v: Any) -> Any:
        if k == "rf_band":
            _band = v.replace("all", "2.4, 5").replace("5.0", "5")
            if wlan.get("rf_band_6ghz", {}).get("value"):
                _band = "6" if _band == "none" else f"{_band}, 6"
            return "all" if _band.count(",") == 2 else _band

        return v if not isinstance(v, dict) or "value" not in v else v["value"]


    for wlan in data:
        ssid_data = {
            k: _simplify_value(wlan, k, wlan[k])
            for k in verbosity_keys.get(verbosity, verbosity_keys[max(verbosity_keys.keys())]) if k in wlan
        }
        if ssid_data.get("name", "") == ssid_data.get("essid", ""):
            ssid_data["name"] = None
        pretty_data += [ssid_data]

    # override default which swaps in unicode checkmark/X (for rich output)
    if format != "rich" and "disable_ssid" in data[-1].keys():
        _short_value["disable_ssid"] = lambda v: 'True' if not v else 'False'

    pretty_data = simple_kv_formatter(pretty_data)
    pretty_data = utils.strip_no_value(pretty_data)
    return pretty_data


def get_wlans(data: list[dict]) ->  list[dict]:
    field_order = [
        "essid",
        "security",
        "type",
        "client_count"
    ]

    data = [{**{k: inner[k] for k in field_order if k in inner}, **inner} for inner in data]
    return simple_kv_formatter(data)


def get_switch_stacks(data: list[dict[str, str]], status: StatusOptions = None, stack_ids: list[str] = None, version: str = None):
    simple_types = {"ArubaCX": "cx"}
    data = [{"name": d.get("name"), **d, "switch_type": simple_types.get(d.get("switch_type", ""), d.get("switch_type"))} for d in data]
    before = len(data)
    if status:  # Filter up / down
        data = [d for d in data if d.get("status").lower() == status.value.lower()]
    if stack_ids:  # Filter Stack IDs
        data = [d for d in data if d.get("id") in stack_ids]

    # TODO single facncy filtering design pattern / callable class.  Instantiated with the filters then called...
    matches_filter = FilterRows(version=version)
    data = [d for d in data if matches_filter(d)]

    if before and not data:
        data = "\nNo stacks matched provided filters"

    data = utils.strip_no_value(data)
    return simple_kv_formatter(data)


def cloudauth_upload_status(data: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    if not data:
        return data
    else:
        data = utils.unlistify(data)  # _display_results will listify the data as most outputs are lists of dicts

    try:
        resp_model = CloudAuthUploadResponse(**data)
        data = resp_model.model_dump()
    except Exception as e:  # pragma: no cover
        log.error("Attempt to normalize cloudauth upload status response through model failed.")
        log.exception(e)

    if "durationNanos" in data:
        data["duration_secs"] = round(data["durationNanos"] / 1_000_000_000, 2)
        del data["durationNanos"]

    return data

def cloudauth_get_namedmpsk(data: list[dict[str, Any]], verbosity: int = 0,) -> list[dict[str, Any]]:
    verbosity_keys = {
        0: [
            'ssid',
            'name',
            'role',
            'status',
        ]
    }

    if verbosity == 0:  # currently no verbosity beyond 0, we just don't filter the fields
        data = [{k: d.get(k) for k in verbosity_keys.get(verbosity, verbosity_keys[max(verbosity_keys.keys())]) if k in d} for d in data]

    return data


def show_all_ap_lldp_neighbors_for_site(data, filter: Literal["up", "down"] = None):
    data = utils.unlistify(data)
    # TODO circular import if placed at top review import logic
    from centralcli import cache

    if filter is None:
        aps_in_site = {dev["serial"]: dev for dev in data["devices"] if dev["role"] == "IAP"}
    else:
        status = 0 if filter == "down" else 1
        aps_in_site = {dev["serial"]: dev for dev in data["devices"] if dev["role"] == "IAP" and dev["status"] == status}
    ap_connections = {edge["toIf"]["serial"]: edge for edge in data["edges"] if edge["toIf"]["serial"] in aps_in_site}
    data = [
        {
            "ap": aps_in_site[ap].get("name", "--"),
            "ap_ip": aps_in_site[ap].get("ipAddress", "--"),
            "ap_serial": aps_in_site[ap].get("serial", "--"),
            "ap_port": ap_connections.get(ap, {"toIf": {}})["toIf"].get("portNumber", "--"),
            # "ap_untagged_vlan": x["toIf"].get("untaggedVlan"),
            # "ap_tagged_vlans": x["toIf"].get("taggedVlans"),
            "switch": ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("deviceName", "--"),
            "switch_ip": ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("ipAddress", "--") if ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("ipAddress") not in [None, "Unknown"] else cache.devices_by_serial.get(ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("serial", "--"), {}).get("ip", "--"),
            "switch_serial": ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("serial", "--"),
            "switch_port": ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("name", "--"),
            "untagged_vlan": ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("untaggedVlan", "--"),
            "tagged_vlans": ",".join([str(v) for v in sorted(ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("taggedVlans") or []) if v != ap_connections.get(ap, {"fromIf": {}})["fromIf"].get("untaggedVlan", 9999)]),
            "healthy": "✅" if aps_in_site[ap].get("health", "") == "good" else "❌"
        } for ap in aps_in_site
    ]

    return simple_kv_formatter(data)


def get_gw_tunnels(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Also used for get_gw_uplinks_details
    _short_value["throughput"] = lambda x: utils.convert_bytes_to_human(x, throughput=True)
    return simple_kv_formatter(data)


def get_gw_uplinks_bandwidth(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_order = [
        "timestamp",
        "tx_data_bytes",
        "rx_data_bytes",
    ]
    return simple_kv_formatter(data, key_order=key_order)


def get_device_firmware_details(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_order = [
        "hostname",
        "device_status",
        "model",
        "mac_address",
        "serial",
        "is_stack",
        "recommended",
        "firmware_version",
    ]
    if data:
        key_order = [*key_order, *[k for k in data[0].keys() if k not in key_order]]
    def collapse_status(key: str, value: Any) -> Any:
        if key != "status" or not isinstance(value, dict):
            return value
        else:
            return value.get("reason", value.get("state"))

    # We use firmware/swarms/swarm_id for APs as firmware/device/serial doesn't respond to APs so need to make it consistent with device endpoint
    def swarm_to_device(data: dict) -> dict:
        if "aps" not in data:
            return data

        out = data if not data["aps"] else {**data, **{k if k != "name" else "hostname": v for k, v in data["aps"][0].items()}}  # TODO need to test with AOS8 IAP likely multiple APs not sure if they work with /firmware/device
        del out["aps"]
        del out["aps_count"]
        return out


    data = [{k: collapse_status(k, v) for k, v in swarm_to_device(inner).items()} for inner in data]
    global _short_key
    _short_key = {**_short_key, "firmware_version": "running version", "is_stack": "stack", "device_status": "status", "status": "fw status"}
    _short_value["status"] = lambda v: "up to date" if v == "Firmware version upto date" else v

    return simple_kv_formatter(data, key_order=key_order, strip_null=True)


def get_swarm_firmware_details(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_order = [
        "name",
        "device_status",
        "model",
        "mac_address",
        "serial",
        "recommended",
        "firmware_version",
    ]
    # keys are not stripped until return.  aps is available and is used to flatten the dict
    strip_keys = [
        "aps",
        "aps_count",
    ]
    if data:
        key_order = [*key_order, *[k for k in data[0].keys() if k not in [*key_order, *strip_keys]]]
    def collapse_status(key: str, value: Any) -> Any:
        if key != "status" or not isinstance(value, dict):
            return value
        else:
            return value.get("reason", value.get("state"))

    # We use firmware/swarms/swarm_id for APs as firmware/device/serial doesn't respond to APs so need to make it consistent with device endpoint
    def swarm_to_device(data: dict) -> dict:
        if "aps" not in data:
            return data

        if data["aps"]:  # Down APs don't show the AP details
            out = {**data, **data["aps"][0]}
        else:
            out = {"name": data.get("swarm_name") if data.get('firmware_version', '').startswith('10.') else None, **data}
        del out["aps"]
        del out["aps_count"]
        return out

    data = [{k: collapse_status(k, v) for k, v in swarm_to_device(inner).items()} for inner in data]

    # if ap name == swarm_name no need to include swarm_name
    if all([inner.get("name", "name") == inner.get("swarm_name", "swarm_name") for inner in data]):
        data = [{k: v for k, v in inner.items() if k != "swarm_name"} for inner in data]
        if "swarm_name" in key_order:
            _ = key_order.pop(key_order.index("swarm_name"))

    global _short_key
    _short_key = {**_short_key, "firmware_version": "running version", "is_stack": "stack", "device_status": "status", "status": "fw status"}
    _short_value["status"] = lambda v: "up to date" if v == "Firmware version upto date" else v

    return simple_kv_formatter(data, key_order=key_order)

def show_radios(data: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    key_order = ["name", "macaddr", "radio_name", "status", "channel", "radio_type", "spatial_stream", "mode", "tx_power", "utilization",]  # "band", "index"]
    def pretty_mode(mode: int) -> str | int:
        try:
            mode: Enum = radio_modes(mode)
            return mode.name
        except ValueError:
            return mode

    global _short_value
    _short_value["mode"] = lambda m: pretty_mode(m)
    data = simple_kv_formatter(data, key_order=key_order)

    return data


def get_bssids(data: list[dict[str, str | int]], output_format: TableFormat = "rich", band: RadioBandOptions | None = None) -> list[dict[str, str | int]]:
    key_order = ["name", "serial", "macaddr", "radio_bssids"]  # "swarm_id",
    pretty_band = {0: "5Ghz", 1: "2.4Ghz", 2: "6Ghz"}
    data = simple_kv_formatter(data, key_order=key_order)

    data_out = []
    for ap in data:
        ap_data = []
        for radio in ap["radio bssids"]:
            bssids = radio["bssids"] or [{"essid": None, "macaddr": radio["macaddr"]}]
            if output_format == "rich":
                ap_data += [
                    {"ap": f'{ap["name"]} [dim]({ap["serial"]})[/dim]', "band": pretty_band[radio["index"]], "ssid": r["essid"], "bssid": r["macaddr"]}
                    for r in bssids if band is None or pretty_band[radio["index"]].removesuffix("Ghz") == band
                ]
            else:
                ap_data += [
                    {**{k: v for k, v in ap.items() if "bssid" not in k}, "band": pretty_band[radio["index"]], "ssid": r["essid"], "bssid": r["macaddr"]}
                    for r in bssids if band is None or pretty_band[radio["index"]].removesuffix("Ghz") == band
                ]
        data_out += sorted(ap_data, key=lambda r: r["band"])

    return data_out


def get_guests(data: list[dict[str, Any]], output_format: TableFormat = "yaml") -> list[dict[str, Any]]:
    def calc_remaining_expiration(expire_ts: int) -> DateTime:
        if expire_ts is None:
            return "[bright_green]Will Not Expire[/]"
        now = pendulum.now(tz="UTC")
        if now.int_timestamp > expire_ts:
            return "[red]Expired[/]"

        expire = pendulum.from_timestamp(expire_ts)
        remaining = expire.int_timestamp - now.int_timestamp
        return DateTime(remaining, "durwords-short")

    # flatten user key which is a dict with email in phone
    data = [
            {
                **{k: v for k, v in inner.items() if k != "user" and not k.startswith("valid_till") and not k.startswith("notify")},
                **inner.get("user", {}),
                "remaining": calc_remaining_expiration(inner.get("expire_at", None)),
                "notify_to": None if not inner.get("notify") else inner.get("notify_to")
            }
            for inner in data
    ]
    all_keys = list(set([key for d in data for key in d.keys()]))
    key_order = [
        "portal",
        "name",
        "display_name",
        "email",
        "phone",
        "company_name",
        "created_at",
        "expire_at",
        "remaining",
        "is_enabled",
        "status",
        "notify_to",
        "auto_created",
        *all_keys
    ]

    global _short_key
    _short_key = {
        **_short_key,
        "created_at": "created",
        "expire_at": "expires",
        "is_enabled": "enabled"
    }
    strip_keys = ["auto_created"] if all([item.get("auto_created") is False for item in data]) else None

    return simple_kv_formatter(data, key_order=key_order, strip_keys=strip_keys, strip_null=output_format == "rich", emoji_bools=output_format == "rich")

def show_ai_insights(data: list[dict[str, str | bool | int]], severity: InsightSeverityType = None):
    field_order = [
        "insight_id",
        "severity",
        "category",
        "insight",
        "impact",
        "is_config_recommendation_insight"
    ]
    all_keys = list(set([key for d in data for key in d.keys()]))
    field_order = [*field_order, *[k for k in all_keys if k not in field_order]]
    global _short_key
    _short_key["is_config_recommendation_insight"] = "config insight"
    data = [{f: inner.get(f) for f in field_order if f != "description" or inner[f].casefold() != inner.get("insight", "").casefold()} for inner in data]
    if severity:
        data = [{k: v for k, v in inner.items() if inner.get("severity") is None or inner["severity"] == severity} for inner in data]

    return simple_kv_formatter(data, key_order=field_order, strip_null=True, emoji_bools=True, show_false=False)

def get_dirty_diff(data: list[dict[str, str]],) -> list[dict[str, str]]:
    if not data:
        return data

    return [{"ap": f"{item.get('name', 'err-no-name-field')} [dim]({item.get('id', 'err-no-id-field')})[/]", "dirty diff": item["dirty_diff"]} for item in data]

def get_denylist_clients(data: dict[str, str | list[str]]) -> list[dict[str, str]]:
    return [
        {"ap": f'{device["device_name"]} {device["device_id"]}', "denylisted MAC": mac} for device in data for mac in device["blacklist"]
    ]
