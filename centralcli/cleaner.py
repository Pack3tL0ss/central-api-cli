'''
Collection of functions used to clean output from Aruba Central API into a consistent structure.
'''

from centralcli import utils, constants
from typing import List, Any, Union
import pendulum


def _convert_epoch(epoch: float) -> str:
    # return time.strftime('%x %X',  time.localtime(epoch/1000))
    return pendulum.from_timestamp(epoch, tz="local").to_day_datetime_string()


def _duration_words(secs: int) -> str:
    return pendulum.duration(seconds=secs).in_words()


def _time_diff_words(epoch: float) -> str:
    return pendulum.from_timestamp(epoch, tz="local").diff_for_humans()


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
    "Unknown": "?"
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
    "uplink_ports": "uplinks",
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
        if len(data) == 1:
            data = data[0] if not isinstance(data[0], str) else data[0].replace('_', ' ')
        elif not data:
            data = ''

    return data


def _check_inner_dict(data: Any) -> Any:
    if isinstance(data, list):
        if all([isinstance(id, dict) for id in data]):
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


def get_devices(data: Union[List[dict], dict]) -> Union[List[dict], dict]:
    data = utils.listify(data)
    # gather all keys from all dicts in list each dict could potentially be a diff size
    all_keys = list(set([ik for k in data for ik in k.keys()]))
    to_front = [
        'name',
        'ip_address',
        'subnet_mask',
        'serial',
        'macaddr',
        'ap_deployment_mode',
        'model',
        'group_name',
        'site'
    ]
    to_front = [i for i in to_front if i in all_keys]
    _ = [all_keys.insert(0, all_keys.pop(all_keys.index(tf))) for tf in to_front[::-1]]
    data = [{k: id.get(k) for k in all_keys} for id in data]

    # strip out any columns that have no value in any row
    no_val: List[List[int]] = [
        [
            idx for idx, v in enumerate(id.values()) if not isinstance(v, bool) and not v or (
                isinstance(v, str) and v == "Unknown"
            )
        ] for id in data
    ]
    common_idx: set = set.intersection(*map(set, no_val))
    data = [{k: v for idx, (k, v) in enumerate(id.items()) if idx not in common_idx} for id in data]

    # send all key/value pairs through formatters and return
    return _unlist(
        [dict(short_value(k, _check_inner_dict(v)) for k, v in pre_clean(inner).items()
              if "id" not in k[-3:] and k != "mac_range")
         for inner in data
         ]
        )


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
        "site_id": "id"
    }

    return _unlist(
        [{key_map.get(k, k): s[k] for k in _sorted} for s in data if s.get("site_name", "") != "visualrf_default"]
    )
