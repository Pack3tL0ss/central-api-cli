# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from __future__ import annotations

import binascii
import json
import logging
import os
import string
import sys
import urllib.parse
from datetime import datetime
from enum import Enum
from pathlib import Path
from random import choice
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Literal, Optional, Sequence, Tuple, Union, overload

import pendulum
import typer
import yaml
from jinja2 import Environment, FileSystemLoader
from rich import print_json
from rich.color import ANSI_COLOR_NAMES
from rich.console import Console
from rich.pretty import pprint

from centralcli.typedefs import StrOrURL

if TYPE_CHECKING:
    from .typedefs import PrimaryDeviceTypes

# removed from output and placed at top (provided with each item returned)
CUST_KEYS = ["customer_id", "customer_name"]
log = logging.getLogger()


class ToBool:
    def __init__(self, value: Any,):
        self._original = value
        self.value = self.str_to_bool(value)

    def str_to_bool(self, value: str | None) -> bool | None:
        if not isinstance(value, str):
            return value
        if value.lower() in ["false", "no", "0"]:
            return False
        elif value.lower() in ["true", "yes", "1"]:
            return True

    def __bool__(self) -> bool:
        return self.value

    @property
    def ok(self) -> bool:
        if isinstance(self._original, bool):
            return True
        if not isinstance(self._original, str):
            return False

        if self._original.lower() not in ["false", "no", "0", "true", "yes", "1"]:
            return False
        else:
            return True

class MacFormat(str, Enum):
    COLS = "COLS"
    DASHES = "DASHES"
    DOTS = "DOTS"
    CLEAN = "CLEAN"
    OBJECT = "OBJECT"
    cols = "cols"
    dashes = "dashes"
    dots = "dots"
    clean = "clean"


class Convert:
    def __init__(self, mac: str, fuzzy: bool = False):
        self.orig = mac
        if not mac:
            mac = '0'
        if not fuzzy:
            self.clean = ''.join([c for c in list(mac) if c in string.hexdigits])
            self.ok = True if len(self.clean) == 12 else False
        else:
            for delim in list('.-:'):
                mac = mac.replace(delim, '')

            self.clean = mac
            if len([c for c in list(self.clean) if c in string.hexdigits]) == len(self):
                self.ok = True
            else:
                self.ok = False

    @property
    def cols(self) -> str:
        cols = ':'.join(self.clean[i:i+2] for i in range(0, len(self), 2))
        if cols.strip().endswith(':'):  # handle macs starting with 00 for oobm
            cols = f"00:{cols.strip().rstrip(':')}"
        return cols

    @property
    def dashes(self) -> str:
        return '-'.join(self.clean[i:i+2] for i in range(0, len(self), 2))

    @property
    def dots(self) -> str:
        return '.'.join(self.clean[i:i+4] for i in range(0, len(self), 4))

    @property
    def dec(self) -> int:
        try:
            return 0 if not self.ok else int(self.clean, 16)
        except ValueError:
            return 0

    @property
    def url(self) -> str:
        return urllib.parse.quote_plus(self.cols)

    def __len__(self):
        return len(self.clean)


class Mac(Convert):
    def __init__(self, mac: str | bytes, fuzzy: bool = False):
        if isinstance(mac, bytes):
            mac: str = binascii.hexlify(mac).decode('utf-8')
        super().__init__(mac, fuzzy=fuzzy)
        oobm = hex(self.dec + 1).lstrip('0x')
        self.oobm = Convert(oobm)

    def __str__(self):
        return self.orig

    def __bool__(self):
        return self.ok

    def __eq__(self, value: str | Mac):
        other = value if isinstance(value, Mac) else Convert(value)
        return other.dec == self.dec

    def __hash__(self):
        return self.dec

    def get_range(self, items: int = 10, mac_format: MacFormat = MacFormat.cols):
        mac_objects = [Convert(hex(mac_dec).lstrip("0x")) for mac_dec in range(self.dec, self.dec + items)]
        if mac_format.upper() == MacFormat.OBJECT:
            return mac_objects

        mac_format = mac_format if isinstance(mac_format, MacFormat) else MacFormat(mac_format)
        case_func = str.lower if mac_format.value.islower() else str.upper
        return list(map(case_func, [getattr(mac, mac_format.value.lower()) for mac in mac_objects]))


class Utils:
    def __init__(self):
        self.Mac = Mac

    def json_print(self, obj):  # pragma: no cover  used for debugging
        try:
            print_json(data=obj)
        except Exception:
            pprint(obj)

    @staticmethod
    def unique(_list: list, sort: bool = False) -> list:
        out = [item for item in set(_list) if item is not None]
        return out if not sort else sorted(out)


    @staticmethod
    def is_serial(serial: Union[str, List[str]]) -> bool:
        """Validate the provided str or list of strings appears to be a serial number.

        Serial validation checks that the first 2 characters of the serial are letters,
        all charachters are alpha-numeric, and that there are 9 or more characters.

        Args:
            serial (Union[str, List[str]]): single serial number of list of serial numbers

        Returns:
            bool: True if all provided strings appear to be serial numbers False if not.
        """
        serial = serial if isinstance(serial, list) else [serial]
        ret = True
        for s in serial:
            if not all([char.isalpha() for char in s[0:2]]) or not all([char.isalnum() for char in s[2:]]) or len(s) < 8:
                ret = False
                break

        return ret

    @staticmethod
    def is_resource_id(res_id: str) -> bool:
        return True if res_id and len(res_id) == 36 and res_id.count("-") == 4 else False

    @overload
    def listify(self, var: str | Sequence[str]) -> Sequence[str]: ...

    @overload
    def listify(self, var: PrimaryDeviceTypes | Sequence[PrimaryDeviceTypes]) -> Sequence[str]: ...

    @overload
    def listify(self, var: int | Sequence[int]) -> Sequence[int]: ...

    @overload
    def listify(self, var: dict | Sequence[dict]) -> Sequence[dict]: ...

    @overload
    def listify(self, var: tuple) -> Sequence: ...

    @overload
    def listify(self, var: list) -> Sequence: ...

    @overload
    def listify(self, var: None) -> None: ...

    def listify(self, var: str | Sequence[str] | int | Sequence[int] | tuple | list | dict | Sequence[dict] | PrimaryDeviceTypes | Sequence[PrimaryDeviceTypes] | None, flatten: bool = False) -> Sequence | None:
        if var is None:
            return var

        _var = var if not isinstance(var, tuple | set) else list(var)
        _var = _var if isinstance(_var, list) else [_var]
        if flatten:
            flat = []
            for inner in _var:
                flat += inner if isinstance(inner, list) else [inner]
            return flat

        return _var


    @staticmethod
    def unlistify(data: Any, replace_underscores: bool = True):
        """Remove unnecessary outer lists.

        Returns:
            [] = ''
            ['single_item'] = 'single item' by default 'single_item' if replace_underscores=False
            [[item1], [item2], ...] = [item1, item2, ...]
        """
        if isinstance(data, list):
            if not data:
                data = ""
            elif len(data) == 1:
                data = data[0] if not replace_underscores or not isinstance(data[0], str) else data[0].replace("_", " ")
            elif all([isinstance(d, list) and len(d) == 1 for d in data]):
                out = [i for ii in data for i in ii if not isinstance(i, list)]
                if out:
                    data = out

        return data

    @staticmethod
    def get_multiline_input(
        prompt: str = None,
        return_type: Literal["str", "dict", "list"] = "str",
        abort_str: str = "EXIT",
        **kwargs
    ) -> List[str] | dict | str:  # pragma: no cover
        console = Console(emoji=True)
        exit_prompt_text = "[cyan]Ctrl-Z -> Enter[/]" if os.name == "nt" else "[cyan]Ctrl-D[/] [grey42](on an empty line after content)[/]"
        exit_prompt_text = f"Use {exit_prompt_text} to submit.\nType [cyan]{abort_str}[/] or use [cyan]CTRL-C[/] to abort.\n[cyan blink]Waiting for Input...[/]\n"
        def _get_multiline_sub(prompt: str = prompt, **kwargs):
            prompt = f"{prompt}\n\n{exit_prompt_text}" if prompt else f"[cyan]Enter/Paste content[/]. {exit_prompt_text}"
            console.print(prompt, **kwargs)
            contents, line = [], ''
            while line != abort_str:
                try:
                    line = input()
                    contents.append(line)
                except EOFError:
                    break

            if line == abort_str:
                console.print("[bright_red]Aborted[/]")
                sys.exit()

            return contents

        contents = _get_multiline_sub(prompt=prompt, **kwargs)
        if return_type:
            if return_type == "dict":
                for _ in range(1, 3):
                    try:
                        contents = json.loads("\n".join(contents))
                        break
                    except Exception as e:
                        log.exception(f"get_multiline_input: Exception caught {e.__class__.__name__}\n{e}")
                        console.print("\n :warning:  Input appears to be [bright_red]invalid[/].  Please re-input or type [cyan]exit[/] to exit\n")
                        contents = _get_multiline_sub(prompt=prompt, **kwargs)
            elif return_type == "str":
                contents = "\n".join(contents)

        return contents

    @overload
    def strip_none(data: dict, strip_empty_obj: Optional[bool]) -> dict: ...

    @overload
    def strip_none(data: list, strip_empty_obj: Optional[bool]) -> list: ...

    @overload
    def strip_none(data: None, strip_empty_obj: Optional[bool]) -> None: ...

    @staticmethod
    def strip_none(data: Union[dict, list, None], strip_empty_obj: bool = False) -> dict | list | None:
        """strip all keys from a list or dict where value is NoneType

        args:
            data (Union[dict, list, None]): The iterable object to have all items/keys where value is None
            strip_empty_obj (bool): If True will strip keys that have empty objects as
                well as NoneType for value.

        returns:
            (Any) Return same type that is provided to method as first argument.
            If dict is provided it returns modified dict.
        """
        if isinstance(data, dict):
            if not strip_empty_obj:
                return {k: v if not callable(v) else v.__name__ for k, v in data.items() if v is not None}
            else:
                return {k: v for k, v in data.items() if isinstance(v, (bool, int)) or v}
        elif isinstance(data, (list, tuple)):
            if strip_empty_obj:
                return type(data)(d for d in data if d)
            return type(data)(d for d in data if d is not None)
        else:
            return data

    @staticmethod
    def strip_no_value(data: list[dict] | dict[dict], aggressive: bool = False) -> list[dict] | dict[dict]:
        """strip out any columns that have no value in any row

        Accepts either List of dicts, or a Dict where the value for each key is a dict

        Args:
            data (List[dict] | Dict[dict]): data to process
            aggressive (bool, optional): If True will strip any key with no value, Default is to only strip if all instances of a given key have no value.


        Returns:
            List[dict] | Dict[dict]: processed data
        """
        no_val_strings = ["Unknown", "NA", "None", "--", ""]
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

    @staticmethod
    def color(
        text: str | bool | List[str],
        color_str: str = "bright_green",
        pad_len: int = 0,
        italic: bool = None,
        bold: bool = None,
        blink: bool = None,
        sep: str = ", ",
    ) -> str:
        """Helper method to wrap text in rich formatting tags

        Applies standard default formatting.

        args:
            text (str|bool|list): The text to be formmated.  If a bool is provided
                it is converted to string and italics applied.  If list of strings
                is provided it is converted to str and formatted.
            color_str (str, optional): Text is formatted with this color.
                'random' will pick a random color.  If text is a list, it will pick a random
                color for each item in the list.
                Default: bright_green
            pad_len (int, optional): Number of spaces to pad each entry with.  Defaults to 0.
            italic (bool, optional): Wheather to apply italic to text.
                Default False if str is provided for text True if bool is provided.
            bold (bool, optional): Wheather to apply bold to text. Default None/False
            blink (bool, optional): Wheather to blink the text. Default None/False
            sep (str, optional): Seperator used when list of str converted to str.
                Defaults to ', '
        """
        if isinstance(text, bool):
            italic = True if italic is None else italic
            text = str(text)

        def get_color_str(color: str):
            if color == "random":
                color = choice(list([c for c in ANSI_COLOR_NAMES.keys() if "black" not in c]))

            if not any([italic, bold, blink]):
                return color

            _color = color if not italic else f"italic {color}"
            _color = color if not bold else f"bold {color}"
            _color = color if not blink else f"blink {color}"

            return _color

        if isinstance(text, str):
            color = get_color_str(color_str)
            text = f"{' ' if pad_len else '':{pad_len or 1}}[{color}]{text}[/{color}]"
            return text if not pad_len else text.lstrip()  # workaround for py < 3.10 ... '=' alignment not allowed in string format specifier (pad_len or 1 above to avoid, then lstrip here to strip)
        elif isinstance(text, list) and all([isinstance(x, str) for x in text]):
            colors = [get_color_str(color_str) for _ in range(len(text))]
            text = [f"{' ' if pad_len else '':{pad_len or 1}}[{c}]{t}[/{c}]" for t, c in zip(text, colors)]
            text = text if pad_len else [t.lstrip() for t in text]  # workaround for py < 3.10 ... '=' alignment not allowed in string format specifier (pad_len or 1 above to avoid, then lstrip here to strip)
            return sep.join(text)
        else:
            raise TypeError(f"{type(text)}: text attribute should be str, bool, or list of str.")

    @staticmethod
    def chunker(seq: Iterable, size: int):
        return [seq[pos:pos + size] for pos in range(0, len(seq), size)]


    @staticmethod
    def generate_template(template_file: Path | str, var_file: Path | str | None,) -> str:
        """Generate configuration files based on j2 templates and provided variables."""
        template_file = Path(str(template_file)) if not isinstance(template_file, Path) else template_file
        if var_file is not None:
            var_file = Path(str(var_file)) if not isinstance(var_file, Path) else var_file

        if template_file.suffix == ".j2":
            config_data = yaml.load(var_file.read_text(), Loader=yaml.SafeLoader)

            env = Environment(loader=FileSystemLoader(str(template_file.parent)), trim_blocks=True, lstrip_blocks=True)
            template = env.get_template(template_file.name)

            config_out = template.render(config_data)
        else:
            config_out = template_file.read_text()

        return config_out

    @staticmethod
    def validate_config(data: str) -> List[str]:
        """Validator for resulting config after j2 conversion

        Args:
            data (str): str representing the final configuration.

        Raises:
            typer.Exit: If no commands remain after formatting.

        Returns:
            Original list of str with each line rstrip.
        """
        cli_cmds = [out for out in [line.rstrip() for line in data.splitlines()] if out]

        if not cli_cmds:
            print(":x: [bright_red]Error:[/] No cli commands.")
            raise typer.Exit(1)

        return cli_cmds

    @staticmethod
    def update_dict(dict_to_update: Dict[str, List[Any]], key: str, value: Any) -> Dict[str, List[Any]]:
        """Add key to dict or append to existing key if it already exists

        TODO probably an itertools or other builtin that does this.

        Args:
            dict_to_update (Dict[str, list]): The dict to update
            key (str): The key, will ensure value is in dict under that key, or append if already there
            value (Any): value to be added to list

        Returns:
            Dict[str, list]: Orinal dict is returned updated with provided value
        """
        if key not in dict_to_update:
            dict_to_update[key] = value if isinstance(value, list) else [value]
        else:
            dict_to_update[key] += value if isinstance(value, list) else [value]

        return dict_to_update

    def get_interfaces_from_range(self, interfaces: str | List[str]) -> List[str]:
        econsole = Console(stderr=True)
        interfaces = self.listify(interfaces)

        def expand_range(interface_range: str) -> List[str]:
            if "-" not in interface_range:
                return self.listify(interface_range)
            elif interface_range.count("-") > 1:
                econsole.print("[dark_orange3]:warning:[/]  Invalid Interface Range, expected a single '-'")
                raise typer.Exit(1)
            _start, _end = interface_range.split("-")
            if "/".join(_start.split("/")[0:-1]) != "/".join(_end.split("/")[0:-1]):
                econsole.print(
                    f'[dark_orange3]:warning:[/]  Interface range can not go beyond the same stack-member/module [cyan]{"/".join(_start.split("/")[0:-1])}[/]'
                    f' in start or range should match [cyan]{"/".join(_end.split("/")[0:-1])}[/] specified as end of range.'
                )
                raise typer.Exit(1)
            prefix = "/".join(_start.split("/")[0:-1])
            return [f"{prefix}/{p}" for p in range(int(_start.split("/")[-1]), int(_end.split("/")[-1]) + 1)]

        return [iface for port in interfaces for p in port.split(",") for iface in expand_range(p)]

    @staticmethod
    def convert_bytes_to_human(size: int | float | Dict[str, int | float] | None, precision: int = 2, throughput: bool = False, speed: bool = False, return_size: Literal['B','KB','MB','GB','TB', 'PB'] = None) -> str | None:
        if size is None:
            return size

        def _number_to_human(_size: int | float, precision: int = precision, throughput: bool = throughput, speed: bool = speed, return_size: Literal['B','KB','MB','GB','TB', 'PB'] = return_size) -> str:
            factor = 1000 if throughput or speed else 1024
            suffixes=['B','KB','MB','GB','TB', 'PB'] if not speed else ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Pbps"]
            suffix_idx = 0
            while _size > factor and suffix_idx < 5:
                suffix_idx += 1  # increment the index of the suffix
                _size = _size/float(factor)  # apply the division
                if return_size and suffixes[suffix_idx].upper().startswith(return_size.upper()):
                    break

            out = f"{round(_size, precision):.2f}"
            out = out if not int(out.split(".")[-1]) == 0 else out.split(".")[0]

            return f"{out} {suffixes[suffix_idx]}"

        if isinstance(size, (int, float)):
            return _number_to_human(size)

        if isinstance(size, dict) and all([isinstance(v, (int, float)) for v in size.values()]):
            return {k: _number_to_human(v) for k, v in size.items()}
        else:
            return size

    @staticmethod
    def parse_time_options(
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        in_milliseconds: bool = False,
    ) -> Tuple[int | None, int | None]:
        """parse time options (from_time, to_time) from user if any provided and return int timestamp for each.

        Args:
            from_time (int | float | datetime, optional): from time. Defaults to None.
            to_time (int | float | datetime, optional): to time. Defaults to None.
            in_milliseconds (bool, optional): Convert response timestamps to milliseconds.  Default is Seconds.

        Returns:
            Tuple(int | None, int | None): returns Tuple with int timestamps for from_time
            and to_time or None (user didn't use the option).
        """
        if isinstance(from_time, datetime):
            from_time = round(from_time.timestamp())
        elif isinstance(from_time, float):
            from_time = round(from_time)

        if isinstance(to_time, datetime):
            to_time = round(to_time.timestamp())
        elif isinstance(to_time, float):
            to_time = round(to_time)

        if in_milliseconds:
            return from_time * 1000, (to_time or pendulum.now(tz="UTC").int_timestamp) * 1000

        return from_time, to_time

    @staticmethod
    def summarize_list(items: List[str], max: int = 6, pad: int = 4, sep: str = '\n', color: str | None = 'cyan', italic: bool = False, bold: bool = False) -> str:
        if not items:
            return ""

        max = max if max and max + 1 != len(items) else len(items)  # if max is 1 less than the items sent we display all as we'd just be swapping one item for ... anyway.
        bot = int(max / 2)
        top = max - bot
        if any([bold, italic, color is not None]):
            fmt = f'[{"" if not bold else "bold "}{"" if not italic else "italic "}{color or ""}]'.replace(' ]', ']')
            item_sep = f'{"" if not pad else " " * pad}[dark_orange3]...[/]'
        else:
            fmt = ""
            item_sep = "...".rjust(pad + 3)

        items = [f'{"" if not pad else " " * pad}{fmt}{item}{"[/]" if fmt else ""}' for item in items]
        if len(items) == 1:  # If there is only 1 item we return it with just the formatting and strip the pad
            return items[0].lstrip()

        if sep == "\n":
            items[0] = f"\n{items[0]}"

        if len(items) > max:
            confirm_str = sep.join([*items[0:top], item_sep, *items[-bot:]])
        else:
            confirm_str = sep.join(items)

        return confirm_str

    @staticmethod
    def older_than(ts: int | float | datetime, time_frame: int, unit: Literal["days", "hours", "minutes", "seconds", "weeks", "months"] = "days", tz: str = "UTC") -> bool:
        if str(ts).isdigit() and len(str(int(ts))) > 10:  # if ts in milliseconds convert to seconds
            ts = ts / 1000
        dt = ts if isinstance(ts, datetime) else pendulum.from_timestamp(ts, tz=tz)
        diff = pendulum.now(tz=tz) - dt
        return getattr(diff, f'in_{unit}')() > time_frame

    @staticmethod
    def singular_plural_sfx(items: Iterable | int, singular: str = None, plural: str = None) -> str:
        cnt = items if isinstance(items, int) else len(items)
        singular = singular or ''
        plural = plural or 's'
        return plural if cnt > 1 else singular

    @staticmethod
    def remove_time_params(params: dict[str, Any]) -> dict[str, Any]:
        time_params = ["start_time", "end_time", "from_timestamp", "to_timestamp", "from", "to"]
        return {k: v for k, v in params.items() if k not in time_params}

    @staticmethod
    def clean_validation_errors(exc) -> str:
        """strip off the 'for further information ... part of a pydantic ValidationError"""
        return ''.join([line for line in str(exc).splitlines(keepends=True) if not line.lstrip().startswith("For further")])

    @staticmethod  # HACK # REQUESTS still using requests/prepared to build the multi-part form data, as have not been able to get it to work with aiohttp
    def build_multipart_form_data(url: StrOrURL, method: str = "POST", *, files: dict, params: dict[str, str] = None, base_url: StrOrURL = None) -> dict[str, bytes, dict[str, str]]:
        import requests
        req_url = f"{base_url or ''}{url}"
        req = requests.Request(method, url=req_url, params=params, files=files)
        prepared = req.prepare()
        return {"params": params, "payload": prepared.body, "headers": prepared.headers}

    @staticmethod
    def parse_phone_number(phone_number: int | str, strict: bool = True) -> str:
        phone_orig, phone = phone_number, str(phone_number)
        _phone_strip = list("()-. ")
        phone = "".join([p for p in list(phone) if p not in _phone_strip])
        if not phone.startswith("+"):
            if not len(phone) == 10 and strict:
                econsole = Console(stderr=True)
                econsole.print(f"phone number provided {phone_orig} appears to be [bright_red]invalid[/]")
                raise typer.Exit(code=1)
            phone = f"+1{phone}"

        return phone

if __name__ == "__main__":
    utils = Utils()
    x = ["[dark_orange2]:warning:[/] This is a test.", "[bright_green]:recycle:[/]This is also a test"]
    from centralcli import cache
    from centralcli.cache import CacheDevice
    cache_devs = [CacheDevice(d) for d in cache.devices]
    y = [*x, *[d.rich_help_text for d in cache_devs]]
    console = Console()

    console.print(f"{utils.summarize_list(y, color=None, max=40, emoji=False)}")
    ...

