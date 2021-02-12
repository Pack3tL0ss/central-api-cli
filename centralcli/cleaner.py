'''
Collection of functions used to clean output from Aruba Central API into a consistent structure.
'''

import functools
from centralcli import utils, constants
from typing import List, Any, Union
import pendulum
import ipaddress


def epoch_convert(func):
    @functools.wraps(func)
    def wrapper(epoch):
        if len(str(int(epoch))) > 10:
            epoch = epoch / 1000
        return func(epoch)

    return wrapper


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


_NO_FAN = [
    "Aruba2930F-8G-PoE+-2SFP+ Switch(JL258A)"
]


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
    "vc_disconnected": "vc disc."
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
    "ap_deployment_mode": "mode"
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


def _unlist(data: Any):
    if isinstance(data, list):
        if not data:
            data = ''
        elif len(data) == 1:
            data = data[0] if not isinstance(data[0], str) else data[0].replace('_', ' ')
        elif all([isinstance(d, list) and len(d) == 1 for d in data]):
            out = [i for ii in data for i in ii if not isinstance(i, list)]
            if out:
                data = out

    return data


def _check_inner_dict(data: Any) -> Any:
    if isinstance(data, list):
        if True in set([isinstance(id, dict) for id in data]):
            if list(set([dk for d in data for dk in d.keys()]))[0] == 'port':
                return _unlist([d['port'] for d in data])
            else:
                return _unlist(
                            [
                                dict(short_value(vk, vv) for vk, vv in pre_clean(inner).items()
                                     if vk != "index")
                                for inner in data
                            ]
                        )
    return data


def short_key(key: str) -> str:
    return _short_key.get(key, key.replace('_', ' '))


def short_value(key: str, value: Any):
    # _unlist(value)

    if isinstance(value, (str, int, float)):
        return (
            short_key(key), _short_value.get(value, value)
            if key not in _short_value or not value else _short_value[key](value)
        )
    else:
        return short_key(key), _unlist(value)


def _get_group_names(data: List[str, ]) -> list:
    groups = [g for _ in data for g in _ if g != "unprovisioned"]
    groups.insert(0, groups.pop(groups.index("default")))
    return groups


def get_all_groups(data: List[dict, ]) -> list:
    _keys = {
        "group": "name",
        "template_details": "template group"
    }
    return [{_keys[k]: v for k, v in g.items()} for g in data]


def get_all_clients(data: List[dict]) -> list:
    """Remove all columns that are NA for all clients in the list"""

    strip_na = [[k for k, v in d.items() if str(v) == 'NA'] for d in data]
    strip_na = set([i for o in strip_na for i in o])
    data = [dict(short_value(k, v) for k, v in d.items() if k not in strip_na) for d in data]
    return data


def strip_no_value(data: List[dict]) -> List[dict]:
    """strip out any columns that have no value in any row"""
    no_val: List[List[int]] = [
        [
            idx for idx, v in enumerate(id.values()) if not isinstance(v, bool) and not v or (
                isinstance(v, str) and v == "Unknown"
            )
        ] for id in data
    ]
    if no_val:
        common_idx: set = set.intersection(*map(set, no_val))
        data = [
            {k: v for idx, (k, v) in enumerate(id.items()) if idx not in common_idx} for id in data
        ]

    return data


def sort_device_keys(data: List[dict]) -> List[dict]:
    all_keys = list(set([ik for k in data for ik in k.keys()]))

    # concat ip_address & subnet_mask fields into single ip field ip/mask
    if 'ip_address' in all_keys:
        if 'subnet_mask' in all_keys:
            for inner in data:
                if inner['ip_address'] and inner['subnet_mask']:
                    mask = ipaddress.IPv4Network((inner['ip_address'], inner['subnet_mask']), strict=False).prefixlen
                    inner['ip_address'] = f"{inner['ip_address']}/{mask}"
                    del inner['subnet_mask']
                if inner.get('public_ip_address'):
                    inner['ip_address'] += f'\npublic: {inner["public_ip_address"]}'
                    del inner["public_ip_address"]

    to_front = [
        'name',
        'ip',
        'ip_address',
        'subnet_mask',
        'serial',
        'macaddr',
        'mac',
        'ap_deployment_mode',
        'model',
        'group_name',
        'group',
        'site'
    ]
    to_front = [i for i in to_front if i in all_keys]
    _ = [all_keys.insert(0, all_keys.pop(all_keys.index(tf))) for tf in to_front[::-1]]
    data = [{k: id.get(k) for k in all_keys} for id in data]

    return data


def get_devices(data: Union[List[dict], dict], sort: str = None) -> Union[List[dict], dict]:
    data = utils.listify(data)

    # gather all keys from all dicts in list each dict could potentially be a diff size
    # Also concats ip/mask if provided in sep fields
    data = sort_device_keys(data)

    # strip any cols that have no value across all rows
    data = strip_no_value(data)

    # send all key/value pairs through formatters and return
    data = _unlist(
        [dict(short_value(k, _check_inner_dict(v)) for k, v in pre_clean(inner).items()
              if "id" not in k[-3:] and k != "mac_range")
         for inner in data
         ]
        )

    # if sort and data and sort in data[-1]:
    #     return sorted(data, key=sort)
    # else:
    return data


def get_audit_logs(data: List[dict]) -> List[dict]:
    field_order = [
        "ts", "app_name", "classification", "device_type", "description",
        "target", "ip_addr", "user", "id", "has_details"
        ]
    data = [dict(short_value(k, d.get(k)) for k in field_order) for d in data]
    return data


def sites(data: Union[List[dict], dict]) -> Union[List[dict], dict]:
    data = utils.listify(data)

    _sorted = ["site_name", "site_id", "address", "city", "state", "zipcode", "country", "longitude",
               "latitude", "associated_device_count"]  # , "tags"]
    key_map = {
        "associated_device_count": "associated devices",
        "site_id": "id",
        "site_name": "name"
    }

    return _unlist(
        [{key_map.get(k, k): s[k] for k in _sorted} for s in data if s.get("site_name", "") != "visualrf_default"]
    )
