from __future__ import annotations

from typing import List, Dict, Any, TYPE_CHECKING
from .common import CLIFormatter
from ...objects import DateTime
from ... import log

if TYPE_CHECKING:
    from ...objects import TimeFormat

import pendulum

# TODO add a method to update the caption from the cleaner either a callback or a function call

def get_subscriptions(data: List[Dict[str, Any]], verbosity: int = 0) -> List[Dict[str, Any]]:
    if not data:
        return data
    def _to_datetime(date: str, format: TimeFormat = "date-string", format_expiration: bool = None) -> DateTime:
        return DateTime(pendulum.from_format(date.rstrip("Z"), "YYYY-MM-DDTHH:mm:ss.SSS").timestamp(), format=format, format_expiration=format_expiration)

    _short_key = {
        'subscriptionType': 'subscription type',
        'createdAt': 'created at',  # 2022-03-06T06:08:46.603Z
        'updatedAt': 'updated at',  # 2022-03-06T06:08:46.603Z',
        'availableQuantity': 'available',  # str to int
        'isEval': 'eval',
        'skuDescription': 'description',
        'contract': 'contract',  # None,
        'startTime': 'start time',  # '2018-12-10T09:15:15.000Z',
        'endTime': 'end time',  # 2028-12-10T09:15:15.000Z',
        'subscriptionStatus': 'subscription status',   # lambda x: return x if not isinstance x,  # str to NoneType
        'tags': 'tags',
        'productType': 'product type',  # DEVICE',
        'tier': 'tier'  # 'ADVANCE_72XX'
    }
    _short_value = {
        'createdAt': lambda date: _to_datetime(date),
        'updatedAt': lambda date: _to_datetime(date),
        'quantity': lambda q: q if not q.isdigit() else int(q),
        'availableQuantity': lambda q: q if not q.isdigit() else int(q),  # str to int
        'startTime': lambda date: _to_datetime(date, "date-string" if verbosity == 0 else "mdyt"),
        'endTime': lambda date: _to_datetime(date, "date-string" if verbosity == 0 else "mdyt", format_expiration=True),
        'productType': lambda t: t.lower(),
        'tier': lambda name: name.lower().replace("_", " "),
        'subscriptionType': lambda t: t.removeprefix("CENTRAL_").replace("_", " ")
    }
    verbosity_keys = {
        0: [
            'tier',
            'subscriptionType',
            # 'createdAt',
            # 'updatedAt',
            'key',
            'quantity',
            'used',
            'availableQuantity',
            'isEval',
            # 'id',
            # 'type',
            # 'sku',
            # 'skuDescription',
            'contract',
            'startTime',
            'endTime',
            # 'subscriptionStatus',
            'status',
            'tags',
            'productType',
        ]
    }
    key_order = verbosity_keys.get(verbosity) or verbosity_keys[max(verbosity_keys.keys())]
    allow_extra = False if verbosity in verbosity_keys else True
    try:
        for dev in data:
            if "endTime" in dev:
                dev["status"] = "[red]EXPIRED[/]" if pendulum.now().int_timestamp > pendulum.from_format(dev["endTime"].rstrip("Z"), "YYYY-MM-DDTHH:mm:ss.SSS").timestamp() else "[bright_green]OK[/]"
            else:
                dev["status"] = None
            dev["used"] = int(dev["quantity"]) - int(dev["availableQuantity"])
    except Exception as e:
        log.error(f"{e.__class__.__name__} occured while adding status/qty used to data", show=True)
        log.exception(e)

    formatter = CLIFormatter(data, _short_key, _short_value, key_order=key_order, strip_null=True, emoji_bools=True, show_false=False, allow_extra=allow_extra)
    clean_data = formatter.simple
    clean_data = sorted(clean_data, key=lambda d: (d.get("subscription type"), d.get("tier")))
    ok_subs = [sub for sub in clean_data if "EXPIRED" not in sub["status"]]
    expired_subs = [sub for sub in clean_data if "EXPIRED" in sub["status"]]
    clean_data = [*ok_subs, *expired_subs]
    return clean_data





