from __future__ import annotations
from ... import log, utils

from typing import List, Dict, Any, Callable


COMMON_SHORT_KEY = {}
COMMON_SHORT_VALUE = {}
NO_VAL_STRINGS = ["Unknown", "NA", "None", "NONE", "--", ""]


class CLIFormatter:
    def __init__(self, data: Any, short_key: Dict[str, str] = None, short_value: Dict[str, Callable] = None, *, key_order: List[str] = None, strip_keys: List[str] = None, strip_null: bool = False, emoji_bools: bool = False, show_false: bool = True, allow_extra: bool = True):
        """CLIFormatter Initializer

        Args:
            data (Any): data to be formatted (response data from API).
            short_key (Dict[str, str], optional): Dictionary used to convert the field name from the response to the friendly field name desired by the CLI. Defaults to None.
            short_value (Dict[str, Callable], optional): Dictionary used to transform/format the value returned from the API.  Defaults to None.
            key_order (List[str], optional): List of keys in the order desired.
                If defined only key_order key/value pairs are returned. Defaults to None.
            strip_keys (List[str], optional): List of keys to be stripped from output.
            strip_null (bool, optional): Set True to strip keys that have no value for any items.  Defaults to False.
            emoji_bools (bool, optional): Replace boolean values with emoji ✅ for True ❌ for False. Defaults to False.
            show_false (bool, optional): When emoji_bools is True.  Set this to False to only show ✅ for True items, leave blank for False.  Defaults to True
            allow_extra: (bool, optional): Allow extra fields, set to False to only accept fields from short_key dict.  Defaults to True
        """
        self.original_data = data
        short_key = short_key or {}
        short_value = short_value or {}
        self.short_key = short_key if not allow_extra else {**COMMON_SHORT_KEY, **short_key}
        self.short_value = {**COMMON_SHORT_VALUE, **short_value}
        self.key_order = key_order
        if allow_extra:
            if isinstance(data, list):
                data_keys = list(set([key for d in data for key in d.keys()]))
            elif isinstance(data, dict):
                data_keys = list(set([key for d in inner for key in d.keys()] for inner in data.values()))
            self.key_order = [*self.key_order, *[k for k in data_keys if k not in self.key_order]]
        self.strip_keys = strip_keys
        self.strip_null = strip_null
        self.emoji_bools = emoji_bools
        self.show_false = show_false

    @property
    def simple(self):
        return self.simple_kv_formatter(self.original_data)

    @staticmethod
    def _extract_names_from_id_name_dict(id_name: dict) -> str:
        if isinstance(id_name, dict) and "id" in id_name and "name" in id_name:
            names = [x.get("name", "Error") for x in id_name]
            return ", ".join(names)
        else:
            return id_name

    def format_kv(self, key: str, value: Any):
        def _short_key(key: str) -> str:
            return self.short_key.get(key, key.replace("_", " "))

        # Run any inner dicts through cleaner funcs
        if isinstance(value, dict):
            value = {_short_key(k): v if k not in self.short_value else self.short_value[k](v) for k, v in value.items()}

        if isinstance(value, (str, int, float)):
            return (
                _short_key(key),
                self.short_value.get(value, value) if key not in self.short_value or (not isinstance(value, (bool, int)) and not value) else self.short_value[key](value),
            )
        elif isinstance(value, list) and all(isinstance(x, dict) for x in value):
            if key in ["sites", "labels"]:
                value = self._extract_names_from_id_name_dict(value)
            # elif key in ["events_details"]:
            #     value = _extract_event_details(value)
        elif key in self.short_value and value is not None:
            value = self.short_value[key](value)

        return _short_key(key), utils.unlistify(value)


    @staticmethod
    def strip_no_value(data: List[dict] | Dict[dict], no_val_strings: List[str] = NO_VAL_STRINGS, aggressive: bool = False,) -> List[dict] | Dict[dict]:
        """strip out any columns that have no value in any row

        Accepts either List of dicts, or a Dict where the value for each key is a dict

        Args:
            data (List[dict] | Dict[dict]): data to process
            aggressive (bool, optional): If True will strip any key with no value, Default is to only strip if all instances of a given key have no value.


        Returns:
            List[dict] | Dict[dict]: processed data
        """
        if isinstance(data, list):
            if aggressive:
                return [
                    {
                        k: v for k, v in inner.items() if k not in [k for k in inner.keys() if (isinstance(v, str) and v in no_val_strings) or (not isinstance(v, bool) and not v)]
                    } for inner in data
                ]

            no_val: List[List[str]] = [
                [k for k, v in inner.items() if (not isinstance(v, bool) and not v) or (isinstance(v, str) and v and v in no_val_strings)]
                for inner in data
            ]
            if no_val:
                common_keys: set = set.intersection(*map(set, no_val))  # common keys that have no value
                data = [{k: v for k, v in inner.items() if k not in common_keys} for inner in data]

        elif isinstance(data, dict) and all(isinstance(d, dict) for d in data.values()):
            if aggressive:
                return {k:
                    {
                        sub_k: sub_v for sub_k, sub_v in v.items() if k not in [k for k in v.keys() if (isinstance(sub_v, str) and sub_v in no_val_strings) or (not isinstance(sub_v, bool) and not sub_v)]
                    }
                    for k, v in data.items()
                }
            # TODO REFACTOR like above using idx can be problematic with unsorted data where keys may be in different order
            no_val: List[List[int]] = [
                [
                    idx
                    for idx, v in enumerate(data[id].values())
                    if (not isinstance(v, bool) and not v) or (isinstance(v, str) and v and v in no_val_strings)
                ]
                for id in data
            ]
            if no_val:
                common_keys: set = set.intersection(*map(set, no_val))
                data = {id: {k: v for idx, (k, v) in enumerate(data[id].items()) if idx not in common_keys} for id in data}
        else:
            log.error(
                f"cleaner.strip_no_value recieved unexpected type {type(data)}. Expects List[dict], or Dict[dict]. Data was returned as is."
            )

        return data


    def simple_kv_formatter(
            self,
            data: List[Dict[str, Any]] = None,
            # key_order: List[str] = None,
            # strip_keys: List[str] = None,
            # strip_null: bool = False,
            # emoji_bools: bool = False,
            # show_false: bool = True,
        ) -> List[Dict[str, Any]]:
        """Default simple formatter

        Args:
            data (List[Dict[str, Any]]): Data to be formatted, data is returned unchanged if data is not a list.
            key_order (List[str], optional): List of keys in the order desired.
                If defined only key_order key/value pairs are returned. Defaults to None.
            strip_keys (List[str], optional): List of keys to be stripped from output.
            strip_null (bool, optional): Set True to strip keys that have no value for any items.  Defaults to False.
            emoji_bools (bool, optional): Replace boolean values with emoji ✅ for True ❌ for False. Defaults to False.
            show_false (bool, optional): When emoji_bools is True.  Set this to False to only show ✅ for True items, leave blank for False.  Defaults to True

        Returns:
            List[Dict[str, Any]]: Formatted data
        """
        data = data or self.data
        if not isinstance(data, list):
            log.warning(f"cleaner.simple_kv_formatter expected a list but rcvd {type(data)}")
            return data

        def convert_bools(value: Any) -> Any:
            if not self.emoji_bools or not isinstance(value, bool):
                return value

            return '\u2705' if value is True else '\u274c' if self.show_false else ''  # /u2705 = white_check_mark (✅) \u274c :x: (❌)

        strip_keys = self.strip_keys or []
        if self.key_order:
            data = [{k: inner_dict.get(k) for k in self.key_order} for inner_dict in data]

        data = [
            dict(
                self.format_kv(
                    k,
                    convert_bools(v),
                )
                for k, v in d.items()
                if k not in strip_keys
            )
            for d in data
        ]

        return data if not self.strip_null else self.strip_no_value(data)