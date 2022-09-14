#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collection of functions used to clean output from Aruba Central API into a consistent structure.
"""
import functools
import ipaddress
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

import pendulum
from rich.console import Console
from rich.markup import escape

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import constants, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import constants, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import DevTypes

def epoch_convert(func):
    @functools.wraps(func)
    def wrapper(epoch):
        # FIXME don't know why started getting ValueError: invalid literal for int() with base 10: '24 minutes 20 seconds'
        # appears show all was hitting the cleaner 2x
        if str(epoch).isdigit() and len(str(int(epoch))) > 10:
            epoch = epoch / 1000
        return func(epoch)

    return wrapper


# show certificates
def _convert_datestring(date_str: str) -> str:
    return pendulum.from_format(date_str.rstrip("Z"), "YYYYMMDDHHmmss").to_formatted_date_string()


@epoch_convert
def _convert_epoch(epoch: float) -> str:
    # return time.strftime('%x %X',  time.localtime(epoch/1000))
    return pendulum.from_timestamp(epoch, tz="local").to_day_datetime_string()


@epoch_convert
def _duration_words(secs: Union[int, str]) -> str:
    return pendulum.duration(seconds=int(secs)).in_words()


@epoch_convert
def _time_diff_words(epoch: float) -> str:
    # if len(str(int(epoch))) > 10:
    #     epoch = epoch / 1000
    return pendulum.from_timestamp(epoch, tz="local").diff_for_humans()


@epoch_convert
def _log_timestamp(epoch: float) -> str:
    return pendulum.from_timestamp(epoch, tz="local").format("MMM DD h:mm:ss A")
    # DEBUG return f'{epoch} | {pendulum.from_timestamp(epoch, tz="local").format("MMM DD h:mm:ss A")}'


def _short_connection(value: str) -> str:
    return value.replace("802.11", "")


def _serial_to_name(sernum: str) -> str:
    # TODO circular import if placed at top review import logic
    from centralcli import cache
    if not (
        len(sernum) in (9, 10) and all([s.isalpha() for s in sernum[0:2]]) and all([s.isupper() for s in sernum.split()])
    ):
        return sernum

    match = cache.get_dev_identifier(sernum, retry=False, silent=True)
    if not match:
        return sernum

    return match.name


def _extract_names_from_id_name_dict(id_name: dict) -> str:
    if isinstance(id_name, dict) and "id" in id_name and "name" in id_name:
        names = [x.get("name", "Error") for x in id_name]
        return ", ".join(names)
    else:
        return id_name


def _extract_event_details(details: List[dict]) -> dict:
    data = {
        k: v for k, v in [tuple(short_value(k, v)) for d in details for k, v in d.items()]
    }
    return "\n".join([f"{k}: {v}" for k, v in data.items()])


_NO_FAN = ["Aruba2930F-8G-PoE+-2SFP+ Switch(JL258A)"]


_short_value = {
    "Aruba, a Hewlett Packard Enterprise Company": "HPE/Aruba",
    "No Authentication": "open",
    "last_connection_time": _time_diff_words,
    "uptime": _duration_words,
    "updated_at": _time_diff_words,
    "last_modified": _convert_epoch,
    "lease_start_ts": _log_timestamp,
    "lease_end_ts": _log_timestamp,
    "acknowledged_timestamp": _log_timestamp,
    "lease_time": _duration_words,
    "lease_time_left": _duration_words,
    "ts": _log_timestamp,
    "timestamp": _log_timestamp,
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
}

_short_key = {
    "interface_port": "interface",
    "firmware_version": "version",
    "firmware_backup_version": "backup version",
    "group_name": "group",
    "public_ip_address": "public ip",
    "ip_address": "ip",
    "ip_addr": "ip",
    "ip_address_v6": "ip (v6)",
    "macaddr": "mac",
    "switch_type": "type",
    "uplink_ports": "uplk ports",
    "total_clients": "clients",
    "updated_at": "updated",
    "cpu_utilization": "cpu %",
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
    "vlan_id": "pvid",
    "free_ip_addr_percent": "free ip %",
    "events_details": "details",
    "associated_device_count": "devices",
    "label_id": "id",
    "label_name": "name",
    # "acknowledged": "ack",
    "acknowledged_by": "ack by",
    "acknowledged_timestamp": "ack time",
    "aruba_part_no": "sku",
    "network": "ssid",
}


def strip_outer_keys(data: dict) -> dict:
    if not isinstance(data, dict):
        return data

    data = data if "result" not in data else data["result"]
    _keys = [k for k in constants.STRIP_KEYS if k in data]
    if len(_keys) == 1:
        return data[_keys[0]]
    elif _keys:
        print(f"More wrapping keys than expected from return {_keys}")
    return data


def pre_clean(data: dict) -> dict:
    if isinstance(data, dict):
        if data.get("fan_speed", "") == "Fail":
            if data.get("model", "") in _NO_FAN:
                data["fan_speed"] = "N/A"
    return data


# TODO moved to utils
def _unlist(data: Any):
    """Remove unnecessary outer lists.

    Returns:
        [] = ''
        ['single_item'] = 'single item'
        [[item1], [item2], ...] = [item1, item2, ...]
    """
    if isinstance(data, list):
        if not data:
            data = ""
        elif len(data) == 1:
            data = data[0] if not isinstance(data[0], str) else data[0].replace("_", " ")
        elif all([isinstance(d, list) and len(d) == 1 for d in data]):
            out = [i for ii in data for i in ii if not isinstance(i, list)]
            if out:
                data = out

    return data


def _check_inner_dict(data: Any) -> Any:
    if isinstance(data, list):
        if True in set([isinstance(id, dict) for id in data]):
            if list(set([dk for d in data for dk in d.keys()]))[0] == "port":
                return _unlist([d["port"] for d in data])
            else:
                return _unlist(
                    [dict(short_value(vk, vv) for vk, vv in pre_clean(inner).items() if vk != "index") for inner in data]
                )
    return data


def short_key(key: str) -> str:
    return _short_key.get(key, key.replace("_", " "))


def short_value(key: str, value: Any):
    # _unlist(value)
    # Run any inner dicts through cleaner funcs
    if isinstance(value, dict):
        value = {short_key(k): v if k not in _short_value else _short_value[k](v) for k, v in value.items()}

    if isinstance(value, (str, int, float)):
        return (
            short_key(key),
            _short_value.get(value, value) if key not in _short_value or not value else _short_value[key](value),
        )
    elif isinstance(value, list) and all(isinstance(x, dict) for x in value):
        if key in ["sites", "labels"]:
            value = _extract_names_from_id_name_dict(value)
        elif key in ["events_details"]:
            value = _extract_event_details(value)

    return short_key(key), _unlist(value)


def _get_group_names(data: List[List[str],]) -> list:
    """Convert list of single item lists to a list of strs

    Also removes "unprovisioned" group as it has no value for our
    purposes, and moves default group to beginning of list.

    Args:
        data (List[List[str],]): Central response payload

    Returns:
        list: List of strings with "unprovisioned" group removed
        and default moved to front.
    """
    groups = [g for _ in data for g in _ if g != "unprovisioned"]
    if "default" in groups:
        groups.insert(0, groups.pop(groups.index("default")))
    return groups


def get_all_groups(
    data: List[
        dict,
    ]
) -> list:
    _keys = {"group": "name", "template_details": "template group"}
    return [{_keys[k]: v for k, v in g.items()} for g in data]


def get_labels(
    data: Union[List[dict,], Dict]
) -> list:
    data = utils.listify(data)
    data = [
        dict(
            short_value(
                k,
                d.get(k),
            )
            for k in d.keys()
            if not k.startswith("category_")
        )
        for d in data
        if d["category_id"] == 1
    ]
    data = strip_no_value(data)

    return data


def _client_concat_associated_dev(
    data: Dict[str, Any],
    verbose: bool = False,
    cache=None,
) -> Dict[str, Any]:
    if cache is None:
        from centralcli import cache
    strip_keys = [
        "associated device",
        "associated device mac",
        "connected device type",
        "interface",
        "interface mac",
        "gateway serial",
    ]
    dev, _gw, data["gateway"] = "", "", {}
    if data.get("associated_device"):
        dev = cache.get_dev_identifier(data["associated_device"],)

    if data.get("gateway_serial"):
        _gw = cache.get_dev_identifier(data["gateway_serial"],)
        _gateway = {
            "name": _gw.name,
            "serial": data.get("gateway_serial", ""),
        }
        if verbose:
            data["gateway"] = _unlist(strip_no_value([_gateway]))
        else:
            data["gateway"] = _gw.name or data["gateway_serial"]
    _connected = {
        "name": None if not hasattr(dev, "name") else dev.name,
        "type": data.get("connected_device_type"),
        "serial": data.get("associated_device"),
        "mac": data.get("associated_device_mac"),
        "interface": data.get("interface_port"),
        "interface mac": data.get("interface_mac"),
    }
    for key in strip_keys:
        if key in data:
            del data[key]
    if verbose:
        data["connected device"] = _unlist(strip_no_value([_connected]))
    else:
        data["connected device"] = f"{_connected['name']} ({_connected['type']})"

    return data


def get_clients(
    data: List[dict],
    verbose: bool = False,
    cache: callable = None,
    filters: List[str] = None,
    **kwargs
) -> list:
    """Remove all columns that are NA for all clients in the list"""
    data = utils.listify(data)

    data = [_client_concat_associated_dev(d, verbose=verbose, cache=cache, **kwargs) for d in data]
    if verbose:
        strip_keys = constants.CLIENT_STRIP_KEYS_VERBOSE
        if data and all([isinstance(d, dict) for d in data]):
            all_keys = set([k for d in data for k in d])
            data = [
                dict(
                    short_value(
                        k,
                        d.get(k),
                    )
                    for k in all_keys
                    if k not in strip_keys
                )
                for d in data
            ]
    else:
        _sort_keys = [
            "name",
            "macaddr",
            "vlan",
            "ip_address",
            "user_role",
            "network",
            "connection",
            "connected device",
            "gateway",
            "site",
            "group_name",
            "last_connection_time",
        ]
        if data and all([isinstance(d, dict) for d in data]):
            # all_keys = set([k for d in data for k in d])
            data = [
                dict(
                    short_value(
                        k,
                        f"wired ({data[idx].get('interface_port', '?')})" if d.get(k) == "NA" and k == "network" else d.get(k),
                    )
                    for k in _sort_keys
                )
                for idx, d in enumerate(data)
            ]

    if filters:
        _filter = "~|~".join(filters)
        data = [d for d in data if d["connected device"].lower() in _filter.lower()]
    # data = [_client_concat_associated_dev(d, verbose=verbose, cache=cache, **kwargs) for d in data]
    data = strip_no_value(data)

    return data


def strip_no_value(data: List[dict]) -> List[dict]:
    """strip out any columns that have no value in any row"""
    no_val_strings = ["Unknown", "NA", "None", "--", ""]
    no_val: List[List[int]] = [
        [
            idx
            for idx, v in enumerate(id.values())
            if (not isinstance(v, bool) and not v) or (isinstance(v, str) and v and v in no_val_strings)
        ]
        for id in data
    ]
    if no_val:
        common_idx: set = set.intersection(*map(set, no_val))
        data = [{k: v for idx, (k, v) in enumerate(id.items()) if idx not in common_idx} for id in data]

    return data


def sort_result_keys(data: List[dict], order: List[str] = None) -> List[dict]:
    data = utils.listify(data)
    all_keys = list(set([ik for k in data for ik in k.keys()]))
    ip_word = "ipv4" if "ipv4" in all_keys else "ip_address"
    mask_word = "ipv4_mask" if "ipv4_mask" in all_keys else "subnet_mask"

    # concat ip_address & subnet_mask fields into single ip field ip/mask
    if ip_word in all_keys and mask_word in all_keys:
        for inner in data:
            if inner[ip_word] and inner[mask_word]:
                mask = ipaddress.IPv4Network((inner[ip_word], inner[mask_word]), strict=False).prefixlen
                inner[ip_word] = f"{inner[ip_word]}/{mask}"
                del inner[mask_word]
    if order:
        to_front = order
    else:
        to_front = [
            "vlan_id",
            "name",
            "status",
            "type",
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
            'firmware_version',
            'version',
            'firmware_backup_version',
            'oper_state_reason',
        ]
    to_front = [i for i in to_front if i in all_keys]
    _ = [all_keys.insert(0, all_keys.pop(all_keys.index(tf))) for tf in to_front[::-1]]
    data = [{k: id.get(k) for k in all_keys} for id in data]

    return data


def get_devices(data: Union[List[dict], dict], sort: str = None) -> Union[List[dict], dict]:
    data = utils.listify(data)

    # gather all keys from all dicts in list each dict could potentially be a diff size
    # Also concats ip/mask if provided in sep fields
    data = sort_result_keys(data)

    # strip any cols that have no value across all rows
    data = strip_no_value(data)

    # send all key/value pairs through formatters and return
    data = _unlist(
        [
            dict(
                short_value(k, _check_inner_dict(v))
                for k, v in pre_clean(inner).items()
                if "id" not in k[-3:] and k != "mac_range"
            )
            for inner in data
        ]
    )

    data = utils.listify(data)
    data = sorted(data, key=lambda i: (i.get("site") or "", i.get("type") or "", i.get("name") or ""))

    return data


def get_audit_logs(data: List[dict], cache_update_func: callable = None) -> List[dict]:
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
    data = [dict(short_value(k, d.get(k)) for k in field_order) for d in data]
    data = strip_no_value(data)

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


def get_alerts(data: List[dict],) -> List[dict]:
    if isinstance(data, list) and "No Alerts" in data:
        return data

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
        d["acknowledged"] = f'{"by " if d.get("acknowledged_by") else ""}' \
            f'{d.get("acknowledged_by")}{" @ " if d.get("acknowledged_by") else ""}' \
            f'{"" if not d.get("acknowledged_timestamp") else _log_timestamp(d["acknowledged_timestamp"])}' \

    data = [dict(short_value(k, d[k]) for k in field_order if k in d) for d in data]
    data = strip_no_value(data)

    return data


def get_event_logs(data: List[dict], cache_update_func: callable = None) -> List[dict]:
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
        _dev_type = short_value('device_type', d.get('device_type', ''))
        if _dev_type:
            _dev_str = f"[{_dev_type[-1]}]" if _dev_type[-1] != "CLIENT" else ""
        d["device info"] = f"{_dev_str}{d.get('hostname', '')}|" \
            f"{d.get('device_serial', '')} Group: {d.get('group_name', '')}"
        # for key in ["device_type", "hostname", "device_serial", "device_mac"]:
        #     del d[key]

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
    data = strip_no_value(data)

    return data


def sites(data: Union[List[dict], dict]) -> Union[List[dict], dict]:
    data = utils.listify(data)

    _sorted = [
        "site_name",
        "site_id",
        "address",
        "city",
        "state",
        "zipcode",
        "country",
        "longitude",
        "latitude",
        "associated_device_count",
    ]  # , "tags"]
    key_map = {"associated_device_count": "associated devices", "site_id": "id", "site_name": "name"}

    return _unlist([{key_map.get(k, k): s[k] for k in _sorted} for s in data if s.get("site_name", "") != "visualrf_default"])


def get_certificates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = utils.listify(data)
    short_keys = {
        "cert_name": "name",
        "cert_type": "type",
        "expire_date": "expiration",
        "expire": "expired",
        "cert_md5_checksum": "md5 checksum",
        "cert_sha1_checksum": "sha1 checksum",
    }

    if data and len(data[0]) != len(short_keys):
        log = logging.getLogger()
        log.error(
            f"get_certificates has returned more keys than expected, check for changes in response schema\n"
            f"    expected keys: {short_key.keys()}\n"
            f"    got keys: {data[0].keys()}"
        )
        return data
    else:
        data = [{short_keys[k]: d[k] if k != "expire_date" else _convert_datestring(d[k]) for k in short_keys} for d in data]
        return data


def get_lldp_neighbor(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    strip_keys = ["cid"]
    _short_val = {
        "1000BaseTFD - Four-pair Category 5 UTP, full duplex mode": "1000BaseT FD"
    }
    if len(data) > 1:
        data = {k: _short_val.get(d[k], d[k]) for d in data for k in d if d["localPort"] != "bond0" and k not in strip_keys}

    return strip_no_value(utils.listify(data))


def get_vlans(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
        {short_keys.get(k, k.replace("_", " ")): _unlist(d[k]) for k in d if k not in strip_keys} for d in strip_no_value(data)
    ]

    return data


def routes(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data = utils.unlistify(data)
    if isinstance(data, list) or "routes" not in data:
        return data
    else:
        rv: list = data["routes"]

    return [
        {"destination": f'{r["prefix"]}/{r["length"]}', "next hop": r["nexthop"]} for r in rv
    ]


def wids(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    all_keys = set([k for d in data for k in d])
    strip_keys = ["cust_id"]
    data = [
        dict(
            short_value(
                k,
                d.get(k),
            )
            for k in all_keys
            if k not in strip_keys
        )
        for d in data
    ]
    return data


def get_dhcp(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data = _unlist(data)
    if "servers" in data:
        data = data["servers"]
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

    data = [dict(short_value(k, d.get(k)) for k in field_order) for d in data]
    data = strip_no_value(data)
    # all_keys = set([k for d in data for k in d])
    # data = [
    #     dict(
    #         short_value(
    #             k,
    #             d.get(k),
    #         )
    #         for k in all_keys
    #     )
    #     for d in data
    # ]
    return data

def get_template_details_for_device(data: str) -> dict:
    """Convert form-data response to dict

    Args:
        data (str): string data with summary and optionally running config

    Returns:
        dict: dict with summary(dict), running config(str) and
        central side config(str).
    """
    import json

    summary, running_config, central_config = None, None, None
    split_line = data.split("\n")[0].rstrip()
    data_parts = [
        d.lstrip().splitlines() for d in data.split(split_line)
        if d.lstrip().startswith("Content-Disposition")
    ]
    for part in data_parts:
        if 'name="Summary"' in part[0]:
            summary = json.loads("\n".join(part[2:]))
            summary = {k.lower(): v for k, v in summary.items()}
        elif 'name="Device_running_config"' in part[0]:
            running_config = "\n".join(part[2:]).rstrip()
        elif 'name="Device_central_side_config"' in part[0]:
            central_config = "\n".join(part[2:]).rstrip()

    return {
        "summary": summary,
        "running_config": running_config,
        "central_config": central_config
    }

def parse_caas_response(data: Union[dict, List[dict]]) -> List[str]:
    """Parses Response Object from caas API updates output attribute

    """
    console = Console(emoji=False, record=True)
    data = utils.unlistify(data)
    out = []
    lines = f"[reset]{'-' * 22}"

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
                if _r_code == 0:
                    _r_pretty = "[bright_green]OK[/bright_green]"
                elif _r_code == 2:
                    _r_pretty = "[dark_orange3]WARNING[/dark_orange3]"
                else:
                    _r_pretty = f"[red]ERROR[/red]" if _r_code == 1 else f"[red]ERROR ({_r_code})[/red]"

                out += [f" [{_r_pretty}] {_c}"]
                cmd_status = _r.get('status_str')
                if cmd_status:
                    _r_txt = f"[italic]{escape(cmd_status)}[/italic]"
                    out += [lines, _r_txt, lines]

        console.begin_capture()
        console.print("\n".join(out))
        out = console.end_capture()

    return out

def get_all_webhooks(data: list) -> list:
    # TODO this is the default handling syntax
    data = [
        dict(short_value(k, d[k]) for k in d) for d in strip_no_value(data)
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
    # if wan_down:
    #     test = lambda d: d["wan_uplinks_down"] > 0 or d["wan_tunnels_down"] > 0
    # elif down:
    #     test = lambda d: d["device_down"] > 0
    # else:
    #     test = lambda d: True

    # data = [
    #     dict(short_value(k, d[k]) for k in field_order) for d in data if test(d)
    # ]
    data = [
        dict(short_value(k, d[k]) for k in field_order) for d in data
    ]
    data = strip_no_value(data)


    return data

def _inv_type(model: str, dev_type: str) -> DevTypes:
    if dev_type == "SWITCH":
        aos_sw_models = ["2530", "2540", "2920", "2930", "3810", "5400"]
        return "sw" if model[0:4] in aos_sw_models else "cx"

    return "gw" if dev_type == "GATEWAY" else dev_type.lower()


def get_device_inventory(data: List[dict], sub: bool = None) -> List[dict]:
    field_order = [
        "name",
        "status",
        # "device_type",
        "type",
        "model",
        "aruba_part_no",
        # "imei",
        "ip",
        "macaddr",
        "serial",
        "group",
        "site",
        "version",
        "services",
    ]
    # common_keys = set.intersection(*map(set, data))
    # combine type / device_type for verbose output, preferring type from cache

    data = [
        {"type": _inv_type(d["model"], d.get("type", d["device_type"])), **{key: val for key, val in d.items() if key != "device_type"}}
        for d in data
    ]
    data = [
        dict(short_value(k, d.get(k, "")) for k in field_order) for d in data
    ]
    data = sorted(strip_no_value(data), key=lambda i: (i["type"], i["model"]))

    if sub is not None:
        if sub:
            data = [{k: v for k, v in d.items()} for d in data if d["services"]]
        else:
            data = [{k: v for k, v in d.items()} for d in data if not d["services"]]

    return data


def get_client_roaming_history(data: List[dict]) -> List[dict]:
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
    data = [
        dict(short_value(k, d.get(k, "")) for k in field_order) for d in data
    ]
    data = strip_no_value(data)

    return data