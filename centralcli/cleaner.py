'''
Collection of functions used to clean output from Aruba Central API into a consistent structure.
'''

from typing import List, Any
import time


def _convert_epoch(epoch: float) -> time.strftime:
    return time.strftime('%x %X',  time.localtime(epoch/1000))


_short_value = {
    "Aruba, a Hewlett Packard Enterprise Company": "HPE/Aruba",
    "No Authentication": "open",
    "last_connection_time": _convert_epoch
}

_short_key = {
    "interface_port": "interface"
}


def short_value(key: str, value: Any):
    if isinstance(value, list) and len(value) == 1:
        value = value[0]

    if isinstance(value, (str, int, float)):
        return _short_key.get(key, key), _short_value.get(value, value) if key not in _short_value else _short_value[key](value)
    else:
        return _short_key.get(key, key), value


def get_all_groups(data: List[str, ]) -> list:
    return [g for _ in data for g in _ if g != "unprovisioned"]


def get_all_clients(data: List[dict]) -> list:
    """Remove all columns that are NA for all clients in the list"""

    strip_na = [[k for k, v in d.items() if str(v) == 'NA'] for d in data]
    strip_na = set([i for o in strip_na for i in o])
    data = [dict(short_value(k, v) for k, v in d.items() if k not in strip_na) for d in data]
    return data
