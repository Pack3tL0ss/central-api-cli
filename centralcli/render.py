#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cleaner.py normalizes the responses from the API
render.py (this module) takes the normalized data, and displays it (various formats)
'''
from __future__ import annotations

import ipaddress
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Type, Union

import typer
import yaml
from pygments import formatters, highlight
from rich import print
from rich.box import HORIZONTALS, SIMPLE
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from tabulate import tabulate

from centralcli import config, constants, log, raw_out, utils
from centralcli.config import Config
from centralcli.objects import DateTime, Encoder
from centralcli.vendored.csvlexer.csv import CsvLexer

if TYPE_CHECKING:
    from rich.console import RenderableType
    from rich.style import StyleType

    from .config import Config
    from .response import Response
    from .typedefs import StrEnum, TableFormat

try:  # uniplot depends on numpy which throws an error on rpi
    from uniplot import plot
except ImportError:  # pragma: no cover
    plot = None


REDACT = ["mac", "serial", "neighborMac", "neighborSerial", "neighborPortMac", "longitude", "latitude"]
RICH_FULL_COLS = ['mac', 'serial', 'ip', 'public ip', 'version', 'radio', 'id']
RICH_FOLD_COLS = ["description"]
CUST_KEYS = ["customer_id", "customer_name", "cid", "cust_id"]

console = Console()
econsole = Console(stderr=True)


class TTY:
    def __init__(self):
        self._rows, self._cols = self.get_tty_size()

    def get_tty_size(self):
        self._rows, self._cols = shutil.get_terminal_size()
        return self._rows, self._cols

    def __bool__(self):
        return sys.stdin.isatty()

    def __call__(self):
        self._rows, self._cols = self.get_tty_size()

    @property
    def rows(self):
        self._rows, self._cols = self.get_tty_size()
        return self._rows

    @property
    def cols(self):
        self._rows, self._cols = self.get_tty_size()
        return self._cols

tty = TTY()


class Spinner(Status):
    """A Spinner Object that adds methods to rich.status.Status object

        Args:
            status (RenderableType): A status renderable (str or Text typically).
            console (Console, optional): Console instance to use, or None for global console. Defaults to Error Console (stderrs).
            spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
            spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
            speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
            refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.
    """
    _instance = None

    def __init__(
        self,
        status: RenderableType,
        *,
        console: Optional[Console] = econsole,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        if not hasattr(self, '_initialized'): # Prevent re-initialization
            super().__init__(status, console=console, spinner=spinner, spinner_style=spinner_style, speed=speed, refresh_per_second=refresh_per_second)
        else:
            self._instance.update(status, spinner=spinner, spinner_style=spinner_style, speed=speed)
        self._initialized = True

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def fail(self, text: RenderableType = None) -> None:
        if self._live.is_started:
            self._live.stop()
        self.console.print(f":x:  {self.status}") if not text else self.console.print(f":x:  {text}")

    def succeed(self, text: RenderableType = None) -> None:
        if self._live.is_started:
            self._live.stop()
        self.console.print(f":heavy_check_mark:  {self.status}") if not text else self.console.print(f":heavy_check_mark:  {text}")

    def start(
            self,
            text: RenderableType = None,
            *,
            spinner: str = None,
            spinner_style: StyleType = None,
            speed: float = None,
        ) -> None:
        if any([text, spinner, spinner_style, speed]):
            self.update(text, spinner=spinner, spinner_style=spinner_style, speed=speed)
        if not self._live.is_started:
            self._live.start()

    def __enter__(self) -> "Spinner":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.stop()


class Output():
    def __init__(self, rawdata: str = "", prettydata: str = "", config: Config = None, tablefmt: TableFormat | None = None):
        self.config = config
        self._file = rawdata  # found typer.unstyle AFTER I built this
        self.tty = prettydata
        self.tablefmt = tablefmt

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

    def __contains__(self, item) -> bool:
        return item in self.file

    def sanitize_strings(self, strings: str, config=None) -> str:  # pragma: no cover
        """Sanitize Output for demos

        Args:
            strings (str): Unsanitized command output.
            config (Config, optional): Pass in cencli.Config object.

        Returns:
            str: Sanitized str output with sensitive data redacted.
        """
        config = config or self.config
        if config and config.dev.sanitize and config.sanitize_file.is_file():
            sanitize_data: dict[str, list[str | dict[str, str]]] = config.get_file_data(config.sanitize_file)
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

def _batch_invalid_msg(usage: str, provide: str = None) -> str:  # referenced in the batch cli modules
        usage = escape(usage)
        provide = provide or "Provide [bright_green]IMPORT_FILE[/] or [cyan]--example[/]"
        _msg = [
            "Invalid combination of arguments / options.",
            provide,
            "",
            f"[yellow]Usage[/]: {usage}",
            f"Use [cyan]{usage.split(' [')[0].split('-')[0].rstrip()} --help[/] for help.",
        ]
        return "\n".join(_msg)

def write_file(outfile: Path, outdata: str) -> None:
    """Output data to file

    Args:
        outfile (Path): The file to write to.
        outdata (str): The text to write.
    """
    if outfile and outdata:
        if config.cwd != config.outdir:
            if (
                outfile.parent.resolve().name == "central-api-cli" and
                Path.joinpath(outfile.parent.resolve() / ".git").is_dir()
            ):
                # outdir = Path.home() / 'cencli-out'
                econsole.print(
                    "\n[bright_green]You appear to be in the development git dir.\n"
                    f"Exporting to[/] [cyan]{config.outdir.relative_to(config.cwd)}[/] directory."
                )
                config.outdir.mkdir(exist_ok=True)
                outfile = config.outdir / outfile

        econsole.print(f"[cyan]Writing output to {outfile}... ", end="")

        if not outfile.parent.is_dir():
            econsole.print(f"[red]Directory Not Found[/]\n[dark_orange3]:warning:[/]  Unable to write output to [cyan]{outfile.name}[/].\nDirectory [cyan]{str(outfile.parent.absolute())}[/] [red]does not exist[/].")
        else:
            out_msg = None
            try:
                if isinstance(outdata, (dict, list)):
                    outdata = json.dumps(outdata, indent=4)
                # ensure LF at EoF
                outdata = f"{outdata.rstrip()}\n"
                outfile.write_text(outdata)  # typer.unstyle(outdata) also works
            except Exception as e:
                outfile.write_text(f"{outdata}")
                out_msg = f"Error ({e.__class__.__name__}) occurred during attempt to output to file.  " \
                    "Used simple string conversion"

            econsole.print("[italic green]Done[/]")
            if out_msg:
                log.warning(out_msg, show=True)


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
                    console.print(inner_table, emoji=False)
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
    workspace: str = None,
    group_by: str = None,
    set_width_cols: dict = None,
    full_cols: Union[List[str], str] = [],
    fold_cols: Union[List[str], str] = [],
    min_width: int = 40  # this is the length of the RateLimit string.
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
        min_width (int, optional): Minimum table width. Defaults to 40.

    Returns:
        tuple: raw_data, table_data
    """
    fold_cols = utils.listify(fold_cols)
    full_cols = utils.listify(full_cols)
    console = Console(record=True, emoji=False)

    customer_id, customer_name = "", ""

    # -- // List[dict, ...] \\ --
    if outdata and all(isinstance(x, dict) for x in outdata):
        customer_id = outdata[0].get("customer_id", "")
        customer_name = outdata[0].get("customer_name", "")
        outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]

        tty_width, _ = console.size
        table = Table(
            show_header=True,
            title=title,
            header_style='magenta',
            show_lines=False,
            box=HORIZONTALS,
            row_styles=['none', 'dark_sea_green'],
            min_width=min_width if min_width is None or min_width < tty_width else None
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
        if workspace or caption:
            table.caption_justify = 'left'
            table.caption = '' if not workspace else f'[italic dark_olive_green2] Account: {workspace}[/]'
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


def format_data_by_key(data: list[dict[str, Any]], output_by_key: str) -> dict[str, Any]:
    # -- modify keys potentially formatted with \n for narrower rich output to format appropriate for json/yaml
    data = utils.listify(data)
    if isinstance(data[0], dict) and all([isinstance(k, str) for k in list(data[0].keys())]):
        data = [{k.replace(" ", "_").replace("\n", "_"): v for k, v in d.items()} for d in data]

    # -- convert List[dict] --> Dict[dev_name: dict] for yaml/json outputs unless output_dict_by_key is specified, then use the provided key(s) rather than name
    if output_by_key and data and isinstance(data[0], dict):
        if len(output_by_key) == 1 and "+" in output_by_key[0]:
            found_keys = [k for k in output_by_key[0].split("+") if k in data[0]]
            if len(found_keys) == len(output_by_key[0].split("+")):
                data: dict[str, dict] = {
                    f"{'-'.join([item[key] for key in found_keys])}": {k: v for k, v in item.items()} for item in data
                }
        else:
            _output_key = [k for k in output_by_key if k in data[0]]
            if _output_key:
                _output_key = _output_key[0]
                data: dict[str, dict] = {
                    item[_output_key]: {k: v for k, v in item.items() if k != _output_key}
                    for item in data
                }
    return data


def output(
    outdata: List[str] | List[Dict[str, Any]] | Dict[str, Any] | str,
    tablefmt: TableFormat = "rich",  # "action" and "raw" are not sent through formatter, handled in display_output
    title: str = None,
    caption: str = None,
    workspace: str = None,
    config: Config = None,
    output_by_key: str | List[str] = "name",
    group_by: str = None,
    set_width_cols: dict = None,
    full_cols: Union[List[str], str] = [],
    fold_cols: Union[List[str], str] = [],
    min_width: int = 40
) -> Output:
    output_by_key = utils.listify(output_by_key)
    raw_data = outdata
    _lexer = table_data = None

    if isinstance(outdata, str):
        outdata = outdata.splitlines()

    # sanitize output for demos
    if config and config.dev.sanitize and raw_data and all(isinstance(x, dict) for x in raw_data):
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
        raw_data, table_data = rich_output(outdata, title=title, caption=caption, workspace=workspace, set_width_cols=set_width_cols, full_cols=full_cols, fold_cols=fold_cols, group_by=group_by, min_width=min_width)

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

    return Output(rawdata=raw_data, prettydata=table_data, config=config, tablefmt=tablefmt)


def ask(
    prompt: str = "",
    *,
    rich_console: Optional[Console] = None,
    password: bool = False,
    choices: Optional[List[str]] = None,
    show_default: bool = True,
    show_choices: bool = True,
    default: Any = ...,
) -> str:  # pragma: no cover Can't test this with automated runs given it requires user input from tty
    """wrapper function for rich.Prompt().ask()

    Handles KeyBoardInterrupt, EoFError, and exits if user inputs "abort".
    """
    con = rich_console or econsole
    def abort():
        con.print("\n[dark_orange3]:warning:[/]  [red]Aborted[/]", emoji=True)
        sys.exit(1)  # Needs to be sys.exit not raise Typer.Exit as that causes an issue when catching KeyboardInterrupt

    choices = choices if choices is None or "abort" in choices else ["abort", *choices]

    try:
        choice = Prompt.ask(
            prompt,
            console=console,
            password=password,
            choices=choices,
            show_default=show_default,
            show_choices=show_choices,
            default=default,
        )
    except (KeyboardInterrupt, EOFError):
        abort()

    if choice == "abort":
        abort()

    return choice


def confirm(yes: bool = False, *, prompt: str = "\nProceed?", abort: bool = True,) -> bool:
    _confirm = Confirm(prompt=prompt, console=econsole,)
    result = yes or _confirm()
    if not result and abort:  # pragma: no cover
        econsole.print("[red]Aborted[/]")
        raise typer.Exit(0)
    elif yes:  # The default prompt has a newline before the prompt, this is so -y without prompt still gets a newline to avoid jamming the response text with the confirmation msg.
        print()

    return result

def pause(prompt: str = "Press Enter to Continue", *, rich_console: Console = None) -> None:  # pragma: no cover
    rich_console = rich_console or econsole
    ask = Prompt(prompt, console=rich_console, password=True, show_default=False, show_choices=False)
    _ = ask()

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
    return out if len(out.splitlines()) > 1 else out.rstrip()

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
    kwargs = {**kwargs, "force_terminal": False}
    console = Console(emoji=emoji, **kwargs)
    with console.capture() as cap:
        console.print(text, end="")
    return cap.get()

def help_block(default_txt: str, help_type: Literal["default", "requires"] = "default") -> str:
    """Helper function that returns properly escaped default text, including rich color markup, for use in CLI help.

    Args:
        default_txt (str): The default value to display in the help text.  Do not include the word 'default: '
        help_type (Literal["default", "requires"], optional): Impacts the coloring/format of the help_block. Defaults to "default".

    Returns:
        str: Formatted default text.  i.e. [default: some value] (with color markups)
    """
    style = "dim" if help_type == "default" else "dim red"
    return f"[{style}]{escape(f'[{help_type}: {default_txt}]')}[/{style}]"


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


def _sort_results(
        data: List[dict] | List[str] | dict | None,
        *,
        sort_by: str | StrEnum,
        reverse: bool,
        tablefmt: TableFormat,
        caption: str = None,
) -> tuple:
    if sort_by and all(isinstance(d, dict) for d in data):
        sort_by: str = sort_by if not hasattr(sort_by, 'value') else sort_by.value
        possible_sort_keys = [sort_by, sort_by.replace("_", " ").replace("-", " "), f'{sort_by.replace("_", " ").replace("-", " ")} %', f'{sort_by.replace("_", " ").replace("-", " ")}%']
        matched_key = [k for k in possible_sort_keys if k in data[0]]
        sort_by = sort_by if not matched_key else matched_key[0]

        sort_msg = None
        if not all([sort_by in d for d in data]):
            sort_msg = [
                    f":warning:  [dark_orange3]Sort Error: [cyan]{sort_by}[reset] does not appear to be a valid field",
                    "Valid Fields: {}".format(", ".join([f'{k.replace(" ", "-")}' for k in data[0].keys()]))
            ]
        else:
            try:
                if sort_by in ["ip", "destination"] or sort_by.endswith(" ip"):
                    data = sorted(data, key=lambda d: ipaddress.IPv4Address("0.0.0.0") if not d[sort_by] or d[sort_by] == "-" else ipaddress.ip_address(d[sort_by].split("/")[0]))
                else:
                    type_ = str
                    for d in data:
                        if d[sort_by] is not None:
                            type_ = type(d[sort_by])
                            break
                    data = sorted(data, key=lambda d: d[sort_by] if d[sort_by] is not None and d[sort_by] != "-" else 0 if type_ in [int, DateTime] else "")
            except TypeError as e:
                sort_msg = [f":warning:  Unable to sort by [cyan]{sort_by}.\n   {e.__class__.__name__}: {e} "]

        if sort_msg:
            _caption = "\n".join([f" {m}" for m in sort_msg])
            _caption = _caption if tablefmt != "rich" else rich_capture(_caption, emoji=True)
            if caption:
                c = caption.splitlines()
                c.insert(-1, _caption)
                caption = "\n".join(c)
            else:
                caption = _caption

    return data if not reverse else data[::-1], caption


def _update_captions(caption: List[str] | str, resp: Response | List[Response] = None, suppress_rl: bool = False) -> tuple[str, str | None]:
    resp = utils.listify(resp)
    resp_captions = [] if resp is None else [str(cap) if not hasattr(cap, "__rich__") else getattr(cap, "__rich__")() for r in resp if r.caption for cap in utils.listify(r.caption)]
    caption = utils.listify(caption) or []
    caption = [*caption, *resp_captions]
    caption = "\n ".join(caption)

    caption = "" if not caption else f"{caption}\n"
    if log.caption:  # rich table is printed with emoji=False need to manually swap the emoji # TODO see if table has option to only do emoji in caption
        _log_caption = log.caption.replace(":warning:", "\u26a0").replace(":information:", "\u2139")  # warning ⚠, information: ℹ
        if resp is not None and len(resp) > 1 and ":warning:" in log.caption:
            caption = f'{caption}[bright_red]  !!! Partial command failure !!!\n{_log_caption}[/]'
        else:
            caption = f'{caption}{_log_caption}'
        log._caption = []  # Prevent it from displaying again if exit_on_fail=True

    rl_str = None
    if resp is not None and not suppress_rl:
        try:
            last_rl = sorted(resp, key=lambda r: r.rl)
            if last_rl:
                rl = last_rl[0].rl
                if rl.has_value:
                    rl_str = f"[reset][italic dark_olive_green2]{rl}[/]".lstrip()
                    caption = f"{caption}\n {rl_str}" if caption else f" {rl_str}"
        except Exception as e:  # pragma: no cover
            rl_str = ""
            log.error(f"Exception when trying to determine last rate-limit str for caption {e.__class__.__name__}", show=True)

    return caption, rl_str

def _display_results(
    data: Union[List[dict], List[str], dict, None] = None,
    tablefmt: str = "rich",
    title: str = None,
    caption: str = None,
    pager: bool = False,
    outfile: Path = None,
    sort_by: str | StrEnum = None,
    reverse: bool = False,
    stash: bool = True,
    output_by_key: str | List[str] = "name",
    group_by: str = None,
    set_width_cols: dict = None,
    full_cols: Union[List[str], str] = [],
    fold_cols: Union[List[str], str] = [],
    min_width: int = 40,
    cleaner: callable = None,
    **cleaner_kwargs,
):
    if not data:  # pragma: no cover
        log.warning(f"No data passed to _display_output {typer.unstyle(rich_capture(title))} {typer.unstyle(rich_capture(caption))}")
        return
    data = utils.listify(data)

    if cleaner and not raw_out:
        with Spinner("Cleaning Output..."):
            _start = time.perf_counter()
            data = cleaner(data, **cleaner_kwargs)
            data = utils.listify(data)
            _duration = time.perf_counter() - _start
            log.debug(f"{cleaner.__name__} took {_duration:.2f} to clean {len(data)} records")

    data, caption = _sort_results(data, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, caption=caption)

    if raw_out and tablefmt in ["simple", "rich"]:
        tablefmt = "json"

    kwargs = {
        "outdata": data,
        "tablefmt": tablefmt,
        "title": title,
        "caption": caption,
        "workspace": None if config.workspace == "default" else config.workspace,
        "config": config,
        "output_by_key": output_by_key,
        "group_by": group_by,
        "set_width_cols": set_width_cols,
        "full_cols": full_cols,
        "fold_cols": fold_cols,
        "min_width": min_width
    }
    with Spinner("Rendering Output..."):
        outdata = output(**kwargs)  # tablefmt may be updated use outdata.tablefmt for final format based on payload.

    if stash:
        config.last_command_file.write_text(
            json.dumps({k: v if not isinstance(v, DateTime) else v.ts for k, v in kwargs.items() if k != "config"}, cls=Encoder)
        )

    typer.echo_via_pager(outdata) if pager and tty and len(outdata) > tty.rows else typer.echo(outdata)

    if caption and outdata.tablefmt != "rich":  # rich prints the caption by default for all others we need to add it to the output
        econsole.print("".join([line.lstrip() for line in caption.splitlines(keepends=True)]))

    if config.is_old_cfg and " ".join(sys.argv[1:]) != "convert config":  # pragma: no cover
        econsole.print(
            ":sparkles: [bright_green]There is a new format for the cencli config[/] [dim italic](config.yaml)[/] file with support for [green]GreenLake[/] and New Central!\n"
            f"   Use [cyan]cencli convert config[/] to convert the existing config @ [turquoise2]{config.file}[/] to the new format."
        )

    if outfile and outdata:
        print()
        write_file(outfile, outdata.file)


def display_results(
    resp: Union[Response, List[Response]] = None,
    data: Union[List[dict], List[str], dict, None] = None,
    tablefmt: TableFormat = "rich",
    title: str | List[str] = None,
    caption: str | List[str] = None,
    pager: bool = False,
    outfile: Path = None,
    sort_by: str | StrEnum = None,
    reverse: bool = False,
    stash: bool = True,
    suppress_rl: bool = False,
    output_by_key: str | List[str] = "name",
    group_by: str = None,
    exit_on_fail: bool = False,  # TODO make default True so failed calls return a failed return code to the shell.  Need to validate everywhere it needs to be set to False
    cache_update_pending: bool = False,
    set_width_cols: dict = None,
    full_cols: Union[List[str], str] = [],
    fold_cols: Union[List[str], str] = [],
    min_width: int = 40,
    cleaner: callable = None,
    **cleaner_kwargs,
) -> None:
    """Output Formatted API Response to display and optionally to file

    one of resp or data attribute is required

    Args:
        resp (Union[Response, List[Response], None], optional): API Response objects.
        data (Union[List[dict], List[str], None], optional): API Response output data.
        tablefmt (str, optional): Format of output. Defaults to "rich" (tabular).
            Valid Values: "json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action", "clean"
            Where "raw" is unformatted raw response and "action" is formatted for POST|PATCH etc.
            where the result is a simple success/error.
            clean bypasses all formatters.
        title: (str | List[str], optional): Title of output table.
            List[str] is allowed if tablefmt is not rich, list should match the # of Responses
            Defaults to None.
        caption: (str | List[str], optional): Caption displayed at bottom of table.
            Only applies to "rich" tablefmt. Defaults to None.
        pager (bool, optional): Page Output / or not. Defaults to True.
        outfile (Path, optional): path/file of output file. Defaults to None.
        sort_by (Union[str, List[str], None] optional): column or columns to sort output on.
        reverse (bool, optional): reverse the output.
        stash (bool, optional): stash (cache) the output of the command.  The CLI can re-display with
            show last.  Default: True
        suppress_rl (bool, optional): Suppress the rate limit caption. Default: False
        output_by_key: For json or yaml output, if any of the provided keys are foound in the List of dicts
            the List will be converted to a Dict[value of provided key, original_inner_dict].  Defaults to name.
        group_by: When provided output will be grouped by this key.  For outputs where multiple entries relate to a common device, and multiple devices exist in the output.
            i.e. interfaces for a device when the output contains multiple devices.  Results in special formatting.  Defaults to None
        exit_on_fail: (bool, optional): If provided resp indicates a failure exit after display.  Defaults to False
        cache_update_pending: (bool, optional): If a cache update is to be performed if resp is success.
            Results in a warning before exit if failure. Defaults to False
        set_width_cols (Dict[str: Dict[str, int]]): Passed to output function defines cols with min/max width
            example: {'details': {'min': 10, 'max': 30}, 'device': {'min': 5, 'max': 15}}.  Applies to tablefmt=rich.
        full_cols (list): columns to ensure are displayed at full length (no wrap no truncate). Applies to tablfmt=rich. Defaults to [].
        fold_cols (Union[List[str], str], optional): columns that will be folded (wrapped within the same column). Applies to tablfmt=rich. Defaults to [].
        min_width (int, optional): Minimum table width for rich table.  Defaults to 40.
        cleaner (callable, optional): The Cleaner function to use.
    """
    caption, rl_str = _update_captions(caption, resp=resp, suppress_rl=suppress_rl)

    if resp is not None:
        resp = utils.listify(resp)

        if raw_out:
            tablefmt = "raw"

        for idx, r in enumerate(resp):
            # Multi request url line (example below)
            # Request 1 [POST: /platform/device_inventory/v1/devices]
            #  Response:
            m_colors = {
                "GET": "bright_green",
                "DELETE": "red",
                "PATCH": "dark_orange3",
                "PUT": "dark_orange3",
                "POST": "dark_orange3"
            }
            fg = "bright_green" if r else "red"

            # last condition below and after this block is for aiops insight details where raw["success"] is bool, but can't rely on that being the case elsewhere.  So converting to str to avoid potential errors elsewhere.
            conditions = [len(resp) > 1, tablefmt in ["action", "raw", "clean"], r.ok and not r.output, not r.ok, (isinstance(r.raw, dict) and str(r.raw.get("success")).capitalize() == "False")]
            if any(conditions):
                if isinstance(title, list) and len(title) == len(resp):
                    print(title[idx])
                else:
                    _url = r.url if not hasattr(r.url, "path") else r.url.path
                    m_color = m_colors.get(r.method, "reset")
                    print(f"Request {idx + 1} [[{m_color}]{r.method}[reset]: [cyan]{_url}[/cyan]]")
                    print(f" [{fg}]Response[reset]:")


            conditions = [tablefmt in ["action", "raw", "clean"], r.ok and not r.output, not r.ok, (isinstance(r.raw, dict) and str(r.raw.get("success")).capitalize() == "False")]
            if any(conditions):
                # raw output (unformatted response from Aruba Central API GW)
                if tablefmt in ["raw", "clean"]:
                    status_code = f"[{fg}]status code: {r.status}[/{fg}]"
                    print(r.url)
                    print(status_code)
                    if not r.ok:
                        print(r.error)

                    if tablefmt == "clean":
                        typer.echo_via_pager(r.output) if pager else typer.echo(r.output)
                    else:
                        print("[bold cyan]Unformatted response from Aruba Central API GW[/bold cyan]")
                        plain_console = Console(color_system=None, emoji=False)
                        if config.dev.sanitize:  # pragma: no cover
                            r.raw = json.loads(Output().sanitize_strings(json.dumps(r.raw), config=config))
                        if pager:  # pragma: no cover
                            with plain_console.pager:
                                plain_console.print(r.raw)
                        else:
                            plain_console.print(r.raw)

                    if outfile:
                        print()
                        write_file(outfile, r.raw if tablefmt != "clean" else r.output)

                # prints the Response objects __str__ method which includes status_code
                # and formatted contents of any payload. example below
                # status code: 201
                # Success
                else:
                    console.print(r, emoji=False)
                    # if not r.url.path == "/caasapi/v1/exec/cmd":
                    #     cli.console.print(r, emoji=False)
                    # else:
                    #     cli.console.print(Text.from_ansi(clean.parse_caas_response(r.output)), emoji=False)  # TODO still need to covert everything from cleaners to rich MarkUp so we can use rich print consistently vs typer.echo
                        # TODO make __rich__ renderable method in Response object with markups

                # For Multi-Response action tablefmt (responses to POST, PUT, etc.) We only display the last rate limit
                if rl_str and idx + 1 == len(resp):
                    if caption.replace(rl_str, "").lstrip():
                        _caption = f"\n{caption.replace(rl_str, '').rstrip()}" if r.output else f'  {unstyle(caption.replace(rl_str, "")).strip()}'
                        if not r.output:  # Formats any caption directly under Empty Response msg
                            _caption = "\n  ".join(f"{'  ' if idx == 0 else ''}[grey42 italic]{line.strip()}[/]" for idx, line in enumerate(_caption.splitlines()))
                        econsole.print(_caption, end="")
                    econsole.print(f"\n{rl_str}")

            # response to single request are sent to _display_results for full output formatting. (rich, json, yaml, csv)
            else:
                _display_results(
                    r.output,
                    tablefmt=tablefmt,
                    title=title,
                    caption=caption if idx == len(resp) - 1 else None,
                    pager=pager,
                    outfile=outfile,
                    sort_by=sort_by,
                    reverse=reverse,
                    stash=stash,
                    output_by_key=output_by_key,
                    group_by=group_by,
                    set_width_cols=set_width_cols,
                    full_cols=full_cols,
                    fold_cols=fold_cols,
                    min_width=min_width,
                    cleaner=cleaner,
                    **cleaner_kwargs
                )

        if exit_on_fail and not all([r.ok for r in resp]):
            if cache_update_pending:
                econsole.print(":warning:  [italic]Cache update skipped due to failed API response(s)[/].")
            sys.exit(1)
            # common.exit(code=1)

    elif data:
        _display_results(
            data,
            tablefmt=tablefmt,
            title=title,
            caption=caption,
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=reverse,
            stash=stash,
            output_by_key=output_by_key,
            set_width_cols=set_width_cols,
            full_cols=full_cols,
            fold_cols=fold_cols,
            min_width=min_width,
            cleaner=cleaner,
            **cleaner_kwargs
        )

def get_pretty_status(status: str | None) -> str:
    if status is None:
        return status
    if status.lower() == "up":
        return f"[bright_green]{status}[/bright_green]"
    if status.lower() == "down":
        return f"[red1]{status}[/red1]"
