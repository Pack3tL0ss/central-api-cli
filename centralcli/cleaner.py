#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collection of functions used to clean output from Aruba Central API into a consistent structure.
"""
from pathlib import Path
import sys
import functools
import logging
from typing import Dict, List, Any, Union
import pendulum
import ipaddress


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, constants
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, constants
    else:
        print(pkg_dir.parts)
        raise e


def epoch_convert(func):
    @functools.wraps(func)
    def wrapper(epoch):
        if len(str(int(epoch))) > 10:
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
def _duration_words(secs: int) -> str:
    return pendulum.duration(seconds=secs).in_words()


@epoch_convert
def _time_diff_words(epoch: float) -> str:
    # if len(str(int(epoch))) > 10:
    #     epoch = epoch / 1000
    return pendulum.from_timestamp(epoch, tz="local").diff_for_humans()


@epoch_convert
def _log_timestamp(epoch: float) -> str:
    return pendulum.from_timestamp(epoch, tz="local").format("MMM DD h:mm:ss A")


def _short_connection(value: str) -> str:
    return value.replace("802.11", "")


_NO_FAN = ["Aruba2930F-8G-PoE+-2SFP+ Switch(JL258A)"]


_short_value = {
    "Aruba, a Hewlett Packard Enterprise Company": "HPE/Aruba",
    "No Authentication": "open",
    "last_connection_time": _time_diff_words,
    "uptime": _duration_words,
    "updated_at": _time_diff_words,
    "last_modified": _convert_epoch,
    "ts": _log_timestamp,
    "Unknown": "?",
    "HPPC": "SW",
    "vc_disconnected": "vc disc.",
    "MAC Authentication": "MAC",
    "connection": _short_connection,
    "DOT1X": ".1X"
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
    "ap_deployment_mode": "mode",
    "authentication_type": "auth",
    "last_connection_time": "last connected",
    "connection": "802.11",
    "user_role": "role",
}


def strip_outer_keys(data: dict) -> dict:
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

    if isinstance(value, (str, int, float)):
        return (
            short_key(key),
            _short_value.get(value, value) if key not in _short_value or not value else _short_value[key](value),
        )
    else:
        return short_key(key), _unlist(value)


def _get_group_names(
    data: List[
        str,
    ]
) -> list:
    groups = [g for _ in data for g in _ if g != "unprovisioned"]
    groups.insert(0, groups.pop(groups.index("default")))
    return groups


def get_all_groups(
    data: List[
        dict,
    ]
) -> list:
    _keys = {"group": "name", "template_details": "template group"}
    return [{_keys[k]: v for k, v in g.items()} for g in data]


def _client_concat_associated_dev(
    data: Dict[str, Any],
    verbose: bool = False,
    cache=None,
) -> Dict[str, Any]:
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
        dev = cache.get_dev_identifier(data["associated_device"], ret_field="name")

    if data.get("gateway_serial"):
        _gw = cache.get_dev_identifier(data["gateway_serial"], ret_field="name")
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


def get_clients(data: List[dict], verbose: bool = False, cache: callable = None, **kwargs) -> list:
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
                        d.get(k),
                    )
                    for k in _sort_keys
                )
                for d in data
            ]

    # data = [_client_concat_associated_dev(d, verbose=verbose, cache=cache, **kwargs) for d in data]
    data = strip_no_value(data)

    return data


def strip_no_value(data: List[dict]) -> List[dict]:
    """strip out any columns that have no value in any row"""
    no_val: List[List[int]] = [
        [
            idx
            for idx, v in enumerate(id.values())
            if not isinstance(v, bool)
            and not v
            or (isinstance(v, str) and v == "Unknown" or isinstance(v, str) and v == "NA" or isinstance(v, str) and v == "--")
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
            "addr_mode",
            "admin_mode",
            "oper_mode",
            "untagged_ports",
            "tagged_ports",
            "status",
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
            'firmware_backup_version'
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

    # if sort and data and sort in data[-1]:
    #     return sorted(data, key=sort)
    # else:
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

    if len(data) > 1 and cache_update_func:
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
