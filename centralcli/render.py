#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This will replace the Output class and output func currently living in utils.py

cleaner.py still normalizes the responses from the API
render.py (this file) takes the normalized data, and displays it (various formats)
'''
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Union, TYPE_CHECKING

from tabulate import tabulate
import typer
import yaml
import json
import time
from pygments import formatters, highlight
from rich.box import HORIZONTALS, SIMPLE
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from centralcli.vendored.csvlexer.csv import CsvLexer
from rich import print
from datetime import datetime

try:  # uniplot depends on numpy which throws an error on rpi
    from uniplot import plot
except ImportError:
    plot = None

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, log
    else:
        print(pkg_dir.parts)
        raise e

from centralcli import constants
from centralcli.config import Config
from centralcli.objects import Encoder, DateTime

if TYPE_CHECKING:
    from . import Response
    from .config import Config

tty = utils.tty
CASE_SENSITIVE_TOKENS = ["R", "U"]
TableFormat = Literal["json", "yaml", "csv", "rich", "tabulate", "simple"]  #, "raw", "action"]
REDACT = ["mac", "serial", "neighborMac", "neighborSerial", "neighborPortMac", "longitude", "latitude"]
RICH_FULL_COLS = ['mac', 'serial', 'ip', 'public ip', 'version', 'radio', 'id']
RICH_FOLD_COLS = ["description"]
console = Console(emoji=False)


CUST_KEYS = ["customer_id", "customer_name", "cid", "cust_id"]

class Output():
    def __init__(self, rawdata: str = "", prettydata: str = "", config: Config = None):
        self.config = config
        self._file = rawdata  # found typer.unstyle AFTER I built this
        self.tty = prettydata

    def __len__(self):
        return len(str(self).splitlines())

    def __str__(self):
        if self.tty:
            pretty_up = typer.style("Up\n", fg="green")
            pretty_down = typer.style("Down\n", fg="red")
            out = self.tty.replace("Up\n", pretty_up).replace("Down\n", pretty_down)
        else:
            out = self.file

        out = self.sanitize_strings(out)
        return out if out else "\u26a0  No Data.  This may be normal."

    def __rich__(self):
        pretty_up = "[green]Up[/]\n"
        pretty_down = "[red]Down[/]\n"
        out = self.tty.replace("Up\n", pretty_up).replace("Down\n", pretty_down)

        out = self.sanitize_strings(out)
        return out if out else "\u26a0  No Data.  This may be normal."

    def __iter__(self):
        out = self.tty or self.file
        out = self.sanitize_strings(out)
        out = out.splitlines(keepends=True)
        for line in out:
            yield line

    def __contains__(self, item):
        return item in self.file

    def sanitize_strings(self, strings: str, config=None) -> str:
        """Sanitize Output for demos

        Args:
            strings (str): Unsanitized command output.
            config (Config, optional): Pass in cencli.Config object.

        Returns:
            str: Sanitized str output with sensitive data redacted.
        """
        config = config or self.config
        if config and config.sanitize and config.sanitize_file.is_file():
            sanitize_data = config.get_file_data(config.sanitize_file)
            for s in sanitize_data.get("redact_strings", {}):
                if len(s) > len("--redacted--"):
                    strings = strings.replace(s, f"{'--redacted--':{len(s)}}")
                else:
                    strings = strings.replace(s, f"{'--redacted--'[1:len(s) + 1]}")
            for s in sanitize_data.get("replace_strings", []):
                if s:
                    for old, new in s.items():
                        strings = strings.replace(old, f"{new:{len(old)}}")
        return strings

    def menu(self, data_len: int = None) -> str:
        def isborder(line: str) -> bool:
            return all(not c.isalnum() for c in list(line))

        out = self.tty or self.file
        out = out.splitlines(keepends=True)
        out = self.sanitize_strings(out)
        _out = []
        data_start = 3
        if data_len:
            data_start = len(self) - data_len - 1
        else:
            for idx, line in enumerate(out):
                if "name" in line:
                    if not isborder(out[idx + 2]):
                        data_start = idx + 2
        for idx, line in enumerate(out):
            i = idx - data_start + 1
            pad = len(str(len(out[data_start:])))  # non indexed lines
            ipad = pad - len(str(i))               # indexed lines
            _out += [
                f"  {' ':{pad}}{line}" if isborder(line) or idx < data_start else f"{i}.{' ' * ipad}{line}"
            ]
        return "".join(_out)

    @property
    def file(self):
        if not self._file:
            return self.tty  # this should not happen

        try:
            return typer.unstyle(self._file)
        except TypeError:
            return self._file


def do_pretty(key: str, value: str) -> str:
    """Apply coloring to tty output

    Applies color to certain columns/values prior to formatting
    """
    color = "green" if value.lower() == "up" else "red"
    value = "" if value is None else value  # testing error on cop
    return value if key != "status" else f'[b {color}]{value.title()}[/b {color}]'

def _do_subtables(data: List[dict], *, tablefmt: str = "rich") -> List[dict]:
    """Parse data and format any values that are dict, list, tuple

    Args:
        data (list): The data
        tablefmt (str, optional): table format. Defaults to "rich"

    Returns:
        List[dict]: Original dict with any inner (dict/list/tuples)
                    formatted to match tablefmt specified.
    """
    out = []
    for inner_dict in data:  # the object: switch/vlan etc dict
        for key, val in inner_dict.items():
            if not isinstance(val, (list, dict, tuple)):
                if val is None:
                    inner_dict[key] = ''
                elif isinstance(val, str) and val.lower() in ['up', 'down']:
                    color = 'red' if val.lower() == 'down' else 'green'
                    if tablefmt == 'rich':
                        inner_dict[key] = f'[b {color}]{val.title()}[/b {color}]'
                    else:
                        inner_dict[key] = typer.style(val.title(), fg=color)
                else:
                    if tablefmt == 'rich':
                        txt = str(val) if not hasattr(val, "__rich__") else val.__rich__()  # HACK For Custom DateTime object.  There is no doubt a more elegant mechanism within rich
                        inner_dict[key] = Text.from_markup(txt, style=None, emoji=False)
                    else:
                        inner_dict[key] = str(val)
            else:
                val = utils.listify(val)
                if val and tablefmt == "rich" and hasattr(val[0], 'keys'):
                    inner_table = Table(*(k for k in val[0].keys()),
                                        show_header=True,
                                        pad_edge=False,
                                        collapse_padding=True,
                                        show_edge=False,
                                        header_style="bold cyan",
                                        box=SIMPLE
                                        )
                    _ = [inner_table.add_row(*[do_pretty(kk, str(vv)) for kk, vv in v.items()]) for v in val]
                    console.begin_capture()
                    console.print(inner_table)
                    inner_dict[key] = console.end_capture()
                elif val and tablefmt == "tabulate" and hasattr(val[0], 'keys'):
                    inner_table = tabulate(val, headers="keys", tablefmt=tablefmt)
                    inner_dict[key] = inner_table
                else:
                    if all(isinstance(v, str) for v in val):
                        inner_dict[key] = ", ".join(val)
        out.append(inner_dict)
    return out

def tabulate_output(outdata: List[dict]) -> tuple:
    customer_id = customer_name = ""
    outdata = utils.listify(outdata)

    # -- // List[dict, ...] \\ --
    if outdata and all(isinstance(x, dict) for x in outdata):
        customer_id = outdata[0].get("customer_id", "")
        customer_name = outdata[0].get("customer_name", "")
        outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]
        raw_data = outdata

        outdata = _do_subtables(outdata, tablefmt="tabulate")

        table_data = tabulate(outdata, headers="keys", tablefmt="tabulate")
        td = table_data.splitlines(keepends=True)
        if td:
            table_data = f"{typer.style(td[0], fg='cyan')}{''.join(td[1:])}"

        data_header = f"--\n{'Customer ID:':15}{customer_id}\n" \
                        f"{'Customer Name:':15} {customer_name}\n--\n"
        table_data = f"{data_header}{table_data}" if customer_id else f"{table_data}"
        raw_data = f"{data_header}{raw_data}" if customer_id else f"{raw_data}"
    else:
        raw_data = table_data = outdata

    return raw_data, table_data

def build_rich_table_rows(data: List[Dict[str, Text | str]], table: Table, group_by: str) -> Table:
    if not group_by:
        [table.add_row(*list(in_dict.values())) for in_dict in data]
        return table

    if not isinstance(data, list) or group_by not in data[0]:
        log.error(f"Error in render.do_group_by_table invalid type {type(data)} or {group_by} not found in header.")
        [table.add_row(*list(in_dict.values())) for in_dict in data]
        return table

    field_idx = list(data[0].keys()).index(group_by)
    this = "_start_"
    for in_dict in data:
        if in_dict[group_by] == this:
            table.add_row(*[v if idx != field_idx else "" for idx, v in enumerate(in_dict.values())])  # only  show value for first entry in group
        else:
            this = in_dict[group_by]  # first entry in group
            table.add_section()
            table.add_row(*list(in_dict.values()))

    return table


def rich_output(
    outdata: List[dict],
    title: str = None,
    caption: str = None,
    account: str = None,
    group_by: str = None,
    set_width_cols: dict = None,
    full_cols: Union[List[str], str] = [],
    fold_cols: Union[List[str], str] = [],
) -> tuple:
    """Render string formatted with rich/table

    Args:
        outdata (List[dict]): The output data to format
        title (str, optional): Table Title. Defaults to None.
        caption (str, optional): Table Caption. Defaults to None.
        account (str, optional): The account (displayed in caption if not the default). Defaults to None.
        group_by (str, optional): Group output by the value of the provided field.  Results in special formatting.  Defaults to None.
        set_width_cols (dict, optional): cols that need to be rendered with a specific width. Defaults to None.
        full_cols (Union[List[str], str], optional): cols that should not be truncated. Defaults to [].
        fold_cols (Union[List[str], str], optional): cols that can be folded (wrapped). Defaults to [].

    Returns:
        tuple: raw_data, table_data
    """
    console = Console(record=True, emoji=False)

    customer_id, customer_name = "", ""

    # -- // List[dict, ...] \\ --
    if outdata and all(isinstance(x, dict) for x in outdata):
        customer_id = outdata[0].get("customer_id", "")
        customer_name = outdata[0].get("customer_name", "")
        outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]

        table = Table(
            show_header=True,
            title=title,
            header_style='magenta',
            show_lines=False,
            box=HORIZONTALS,
            row_styles=['none', 'dark_sea_green']
        )

        fold_cols = [*fold_cols, *RICH_FOLD_COLS]

        _min_max = {'min': 10, 'max': 30}
        if not set_width_cols:
            set_width_cols = {'name': _min_max, 'services': {'min': 20, 'max': 30}}
        else:
            for col, value in set_width_cols.items():
                if isinstance(value, int):  # allow simply specifying max width
                    set_width_cols[col] = {"max": value}

        full_cols = [*full_cols, *RICH_FULL_COLS]

        for k in outdata[0].keys():
            if k == "model":
                table.add_column(k, max_width=10, no_wrap=True)
            elif k in fold_cols:
                table.add_column(k, overflow='fold', max_width=115, justify='left')
            elif k in set_width_cols:
                table.add_column(
                    k, min_width=set_width_cols[k].get('min', 0),
                    max_width=set_width_cols[k].get('max'),
                    justify='left',
                )
            elif k in full_cols:
                table.add_column(k, no_wrap=True, justify='left')
            else:
                table.add_column(k, justify='left', overflow='ellipses')

        _start = time.perf_counter()
        formatted = _do_subtables(outdata)
        log.debug(f"render.rich_output.do_subtables took {time.perf_counter() - _start:.2f} to process {len(outdata)} records")

        table = build_rich_table_rows(formatted, table=table, group_by=group_by)

        if title:
            table.title = f'[italic cornflower_blue]{constants.what_to_pretty(title)}'
        if account or caption:
            table.caption_justify = 'left'
            table.caption = '' if not account else f'[italic dark_olive_green2] Account: {account}[/]'
            table.caption = table.caption if not caption else f"{table.caption} {caption.lstrip()}"

        data_header = f"--\n{'Customer ID:':15}{customer_id}\n{'Customer Name:':15} {customer_name}\n--\n"

        console.begin_capture()
        console.print(table)
        table_data = console.end_capture()

        # rich is adding empty lines (full of spaces) to output on show clients, not sure why.  This will remove them
        # it appears they are lines with just ascii formmating, but no real text.
        table_data = "".join([line for line in str(table_data).splitlines(keepends=True) if typer.unstyle(line).strip()])
        raw_data = typer.unstyle(table_data)

        if customer_id:
            raw_data = f"{data_header}{raw_data}"
            table_data = f"{data_header}{table_data}"

        return raw_data, table_data

    return outdata, outdata


def format_data_by_key(data: List[Dict[str, Any]], output_by_key: str) -> Dict[str, Any]:
    # -- modify keys potentially formatted with \n for narrower rich output to format appropriate for json/yaml
    data = utils.listify(data)
    if isinstance(data[0], dict) and all([isinstance(k, str) for k in list(data[0].keys())]):
        data = [{k.replace(" ", "_").replace("\n", "_"): v for k, v in d.items()} for d in data]

    # -- convert List[dict] --> Dict[dev_name: dict] for yaml/json outputs unless output_dict_by_key is specified, then use the provided key(s) rather than name
    if output_by_key and data and isinstance(data[0], dict):
        if len(output_by_key) == 1 and "+" in output_by_key[0]:
            found_keys = [k for k in output_by_key[0].split("+") if k in data[0]]
            if len(found_keys) == len(output_by_key[0].split("+")):
                data: Dict[dict] = {
                    f"{'-'.join([item[key] for key in found_keys])}": {k: v for k, v in item.items()} for item in data
                }
        else:
            _output_key = [k for k in output_by_key if k in data[0]]
            if _output_key:
                _output_key = _output_key[0]
                data: Dict[dict] = {
                    item[_output_key]: {k: v for k, v in item.items() if k != _output_key}
                    for item in data
                }
    return data


def output(
    outdata: List[str] | List[Dict[str, Any]] | Dict[str, Any],
    tablefmt: TableFormat = "rich",  # "action" and "raw" are not sent through formatter, handled in clicommon.display_output
    title: str = None,
    caption: str = None,
    account: str = None,
    config: Config = None,
    output_by_key: str | List[str] = "name",
    group_by: str = None,
    set_width_cols: dict = None,
    full_cols: Union[List[str], str] = [],
    fold_cols: Union[List[str], str] = [],
) -> Output:
    output_by_key = utils.listify(output_by_key)
    raw_data = outdata
    _lexer = table_data = None

    # sanitize output for demos
    if config and config.sanitize and raw_data and all(isinstance(x, dict) for x in raw_data):
        outdata = [{k: d[k] if k not in REDACT else "--redacted--" for k in d} for d in raw_data]

    # -- // List[str, ...] \\ --  Bypass all formatters, (config file output, etc...)
    if tablefmt != "simple" and outdata and all(isinstance(x, str) for x in outdata):
        tablefmt = "simple"

    if tablefmt in ['json', 'yaml', 'yml']:
        outdata = format_data_by_key(outdata, output_by_key)

    if tablefmt == "json":
        outdata = utils.unlistify(outdata)
        console = Console(record=True, emoji=False)
        console.begin_capture()
        console.print_json(json.dumps(outdata, cls=Encoder))
        table_data = console.end_capture()
        console.begin_capture()
        console.print('[bright_red]"Down"[/],')
        red_down = console.end_capture()
        table_data = table_data.replace('\x1b[32m"Down"\x1b[0m,\n', red_down)
        raw_data = typer.unstyle(table_data)

    elif tablefmt in ["yml", "yaml"]:
        outdata = utils.unlistify(outdata)
        # TODO custom yaml Representer
        raw_data = yaml.safe_dump(json.loads(json.dumps(outdata, cls=Encoder)), sort_keys=False)
        table_data = rich_capture(raw_data)

    elif tablefmt == "csv":
        def normalize_for_csv(value: Any) -> str:
            if value is None:
                return ""
            elif isinstance(value, DateTime):
                return str(value.original)
            else:
                return str(value) if "," not in str(value) else f'"{value}"'
        def normalize_key_for_csv(key: str) -> str:
            if not isinstance(key, str):
                return key
            return key.replace(" ", "_").replace("\n", "_")

        csv_data = "\n".join(
                        [
                            ",".join(
                                [
                                    normalize_for_csv(v) for k, v in d.items() if k not in CUST_KEYS
                                ]
                            )
                            for d in outdata
                        ]
        )
        raw_data = table_data = csv_data if not outdata else f"{','.join([normalize_key_for_csv(k) for k in outdata[0].keys() if k not in CUST_KEYS])}\n{csv_data}\n"
        out = Syntax(code=raw_data, lexer=CsvLexer(ensurenl=False), theme="native")
        table_data = out.highlight(out.code.rstrip()).markup
        table_data = rich_capture(table_data)

    elif tablefmt == "rich":
        raw_data, table_data = rich_output(outdata, title=title, caption=caption, account=account, set_width_cols=set_width_cols, full_cols=full_cols, fold_cols=fold_cols, group_by=group_by)

    elif tablefmt == "tabulate":
        raw_data, table_data = tabulate_output(outdata)

    else:  # strings output No formatting
        # -- // List[str, ...] \\ --
        if len(outdata) == 1:
            if "\n" not in outdata[0]:
                # we can format green as only success output is sent through formatter.
                table_data = typer.style(f"  {outdata[0]}", fg="green")
                raw_data = outdata[0]
            else:  # template / config file output
                # get rid of double nl @ EoF (configs)
                if "\x1b" in outdata[0]:  # already styled (cass_output)
                    raw_data = typer.unstyle("{}\n".format('\n'.join(outdata).rstrip('\n')))
                    table_data = "{}\n".format('\n'.join(outdata).rstrip('\n'))
                else:
                    raw_data = "{}\n".format('\n'.join(outdata).rstrip('\n'))
                    table_data = rich_capture(raw_data)

        else:  # cencli show config <GW> is list of strings
            raw_data = '\n'.join(outdata)
            table_data = rich_capture(raw_data)

    if _lexer and raw_data:
        table_data = highlight(bytes(raw_data, 'UTF-8'),
                                _lexer(),
                                formatters.Terminal256Formatter(style='solarized-dark')
                                )

    if isinstance(raw_data, str):  # HACK replace first pass is to line up cols but if table is tighter second pass will swap them regardless
        raw_data = raw_data.replace('✅  ', 'True').replace('❌   ', 'False').replace('✅', 'True').replace('❌', 'False')   #  TODO handle this better

    return Output(rawdata=raw_data, prettydata=table_data, config=config)


def rich_capture(text: str | List[str], emoji: bool = False, **kwargs) -> str:
    """Accept text or list of text with rich markups and return final colorized text with ascii control chars

    This is temporary as the rich context handler stopped working.  Can revert once fixed upstream

    Args:
        text (str | List[str]): The text or list of text to capture.
            If provided as list it will be converted to string (joined with \n)
        emoji: (bool, Optional): Allow emoji placeholders.  Default: False
        kwargs: additional kwargs passed to rich Console.

    Returns:
        str: text with markups converted to ascii control chars
    """
    if isinstance(text, list):
        "\n".join(text)
    console = Console(record=True, emoji=emoji, **kwargs)
    console.begin_capture()
    console.print(text)
    out = console.end_capture()
    return out if len(out.splitlines()) > 1 else out.rstrip("\n")

def unstyle(text: str | List[str], emoji: bool = False, **kwargs) -> str:
    """Accept text or list of text.  Removes any markups or ascii color codes from text

    Args:
        text (str | List[str]): The text or list of text to capture.
            If provided as list it will be converted to string (joined with \n)
        emoji: (bool, Optional): Allow emoji placeholders.  Default: False
        kwargs: additional kwargs passed to rich Console.

    Returns:
        str: text with markups converted to ascii control chars
    """
    kwargs = {**{"force_terminal": False}, **kwargs}
    console = Console(emoji=emoji, **kwargs)
    with console.capture() as cap:
        console.print(text)
    return cap.get()
    # text = rich_capture(text=text, emoji=emoji, **kwargs)
    # return typer.unstyle(text)


def bandwidth_graph(resp: Response, title: str = "Bandwidth Usage") -> None:
    if not plot:
        print(":warning:  Graphing in the terminal is not available for this platform (numpy C extensions need to be built manually).  Use formatting flags i.e. [cyan]--table[/] to see the timeseries data.")
        raise typer.Exit(1)

    tx_data = [x["tx_data_bytes"] for x in resp.output]
    rx_data = [x["rx_data_bytes"] for x in resp.output]

    lowest = utils.convert_bytes_to_human(min([min(tx_data), min(rx_data)]), speed=True)
    return_size = "B" if lowest.split()[-1] == "bps" else "".join(list(lowest.split()[-1])[0:2]).upper()

    tx_data = [float(utils.convert_bytes_to_human(x, speed=True, return_size=return_size).split()[0]) for x in tx_data]
    rx_data = [float(utils.convert_bytes_to_human(x, speed=True, return_size=return_size).split()[0]) for x in rx_data]

    title = rich_capture(title)
    dates = [datetime.fromtimestamp(bw_data["timestamp"]) for bw_data in resp.output]
    plot(xs=[dates, dates], ys=[tx_data, rx_data], lines=True, title=title, y_unit=f" {return_size}", legend_labels=["TX", "RX"], color=True, height=tty.rows - 10, width=tty.cols - 15)

    if log.caption:
        print(log.caption)
