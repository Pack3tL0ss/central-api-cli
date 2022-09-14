#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from pathlib import Path
import shutil
import socket
import string
import sys
import urllib.parse
# from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple, Union
import typer
import logging

import yaml
from halo import Halo
import threading
from pygments import formatters, highlight, lexers
from tabulate import tabulate
from rich import print_json
from rich.console import Console
from rich.prompt import Prompt
from rich.pretty import pprint
from jinja2 import FileSystemLoader, Environment

# removed from output and placed at top (provided with each item returned)
CUST_KEYS = ["customer_id", "customer_name"]
log = logging.getLogger()


class Convert:
    def __init__(self, mac, fuzzy: bool = False):
        self.orig = mac
        if not mac:
            mac = '0'
        if not fuzzy:
            self.clean = ''.join([c for c in list(mac) if c in string.hexdigits])
            self.ok = True if len(self.clean) == 12 else False
        else:
            for delim in ['.', '-', ':']:
                mac = mac.replace(delim, '')

            self.clean = mac
            if len([c for c in list(self.clean) if c in string.hexdigits]) == len(self):
                self.ok = True
            else:
                self.ok = False

        cols = ':'.join(self.clean[i:i+2] for i in range(0, len(self), 2))
        if cols.strip().endswith(':'):  # handle macs starting with 00 for oobm
            cols = f"00:{cols.strip().rstrip(':')}"
        self.cols = cols
        self.dashes = '-'.join(self.clean[i:i+2] for i in range(0, len(self), 2))
        self.dots = '.'.join(self.clean[i:i+4] for i in range(0, len(self), 4))
        self.dec = int(self.clean, 16) if self.ok else 0
        self.url = urllib.parse.quote_plus(cols)

    def __len__(self):
        return len(self.clean)


class Mac(Convert):
    def __init__(self, mac, fuzzy: bool = False):
        super().__init__(mac, fuzzy=fuzzy)
        oobm = hex(self.dec + 1).lstrip('0x')
        self.oobm = Convert(oobm)

    def __str__(self):
        return self.orig

    def __bool__(self):
        return self.ok


class Utils:
    def __init__(self):
        self.Mac = Mac

    def user_input_bool(self, question):

        """Ask User Y/N Question require Y/N answer

        Error and re-prompt if user's response is not valid
        Appends '? (y/n): ' to question/prompt provided

        Params:
            question (str): The Question to ask

        Returns:
            answer (bool): Users Response yes=True
        """
        valid_answer = ["yes", "y", "no", "n"]
        try:
            answer = input(question + "? (y/n): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("")  # prevents header printing on same line when in debug
            return False
        while answer.lower() not in valid_answer:
            if answer != "":
                print(
                    f" \033[1;33m!!\033[0m Invalid Response '{answer}' Valid Responses: {valid_answer}"
                )
            answer = input(question + "? (y/n): ").strip()
        if answer[0].lower() == "y":
            return True
        else:
            return False

    def json_print(self, obj):
        try:
            print_json(data=obj)
        except Exception:
            pprint(obj)

    class TTY:
        def __init__(self):
            self._rows, self._cols = self.get_tty_size()

        def get_tty_size(self):
            s = shutil.get_terminal_size()
            return s.lines, s.columns

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

    @staticmethod
    def unique(_list: list, sort: bool = False) -> list:
        out = []
        [out.append(i) for i in _list if i not in out and i is not None]
        return out if not sort else sorted(out)


    @staticmethod
    def isserial(serial: Union[str, List[str]]) -> bool:
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
    def is_reachable(host: str, port: Union[str, list], timeout: int = 3, silent: bool = False):
        s = socket.socket()
        try:
            s.settimeout(timeout)
            s.connect((host, port))
            _reachable = True
        except Exception as e:
            if not silent:
                print("something's wrong with %s:%d. Exception is %s" % (host, port, e))
            _reachable = False
        finally:
            s.close()
        return _reachable

    def valid_file(self, filepath):
        return os.path.isfile(filepath) and os.stat(filepath).st_size > 0

    def listify(self, var):
        if isinstance(var, tuple):
            return list(var)
        return var if isinstance(var, list) or var is None else [var]

    @staticmethod
    def unlistify(data: Any):
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

    # TODO depricated will remove.  Spinner moved to Response
    @staticmethod
    def spinner(spin_txt: str, function: callable, url: str = None, *args, name: str = None,
                spinner: str = "dots", debug: bool = False, **kwargs) -> Any:
        name = name or spin_txt.replace(" ", "_").rstrip(".").lower()
        if not name.startswith("spinner_"):
            name = f"spinner_{name}"

        spin = None
        if sys.stdin.isatty():
            # If a spinner is already running, update that spinner vs creating new
            active_spinners = [t for t in threading.enumerate()[::-1] if t.name.startswith("spinner")]
            if active_spinners:
                spin = active_spinners[0]._target.__self__
                if debug:
                    spin.stop()
                else:
                    log.warning(f"A Spinner was already running '{spin.text}' updating to '{spin_txt}'")
                    spin.text == spin_txt
                    spin.spinner == "dots12" if spin.spinner == spinner else spinner
            elif not debug:
                spin = Halo(text=spin_txt, spinner=spinner)
                spin.start()
                threading.enumerate()[-1].name = spin._spinner_id = name

        if url:
            args = (url, *args)

        r = function(*args, **kwargs)

        if spin:
            # determine pass if request successful
            _spin_fail_msg = spin_txt
            ok = None
            if hasattr(r, "ok"):
                ok = r.ok
            if "refreshToken" in str(function):
                ok = r is not None
                if hasattr(r, "json"):
                    _spin_fail_msg = f"spin_text\n   {r.json().get('error_description', spin_txt)}"

            if ok is True:
                spin.succeed()
            elif ok is False:
                spin.fail(_spin_fail_msg)
            else:
                spin.stop_and_persist()

        return r

    # TODO deprecated validate not used, moved to Response
    @staticmethod
    def get_multiline_input(prompt: str = None, print_func: callable = print,
                            return_type: str = None, abort_str: str = "exit", **kwargs) -> Union[List[str], dict, str]:
        def _get_multiline_sub(prompt: str = prompt, print_func: callable = print_func, **kwargs):
            prompt = prompt or \
                "Enter/Paste your content. Then Ctrl-D or Ctrl-Z -> Enter ( windows ) to submit.\n Enter 'exit' to abort"
            print_func(prompt, **kwargs)
            contents, line = [], ''
            while line.strip().lower() != abort_str:
                try:
                    line = input()
                    contents.append(line)
                except EOFError:
                    break

            if line.strip().lower() == abort_str:
                print("Aborted")
                exit()

            return contents

        contents = _get_multiline_sub(**kwargs)
        if return_type:
            if return_type == "dict":
                for _ in range(1, 3):
                    try:
                        contents = json.loads("\n".join(contents))
                        break
                    except Exception as e:
                        log.exception(f"get_multiline_input: Exception caught {e.__class__}\n{e}")
                        typer.secho("\n !!! Input appears to be invalid.  Please re-input "
                                    "or Enter `exit` to exit !!! \n", fg="red")
                        contents = _get_multiline_sub(**kwargs)
            elif return_type == "str":
                contents = "\n".join(contents)

        return contents

    @staticmethod
    def strip_none(data: Union[dict, list, None], strip_empty_obj: bool = False) -> Any:
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
                return {k: v for k, v in data.items() if not isinstance(v, bool) and v}
        elif isinstance(data, (list, tuple)):
            if strip_empty_obj:
                return type(data)(d for d in data if d)
            return type(data)(d for d in data if d is not None)
        else:
            return data


    class Output:
        def __init__(self, rawdata: str = "", prettydata: str = "", config=None):
            self.config = config
            self._file = rawdata    # found typer.unstyle AFTER I built this
            self.tty = prettydata

        def __len__(self):
            return len(str(self).splitlines())

        def __str__(self):
            pretty_up = typer.style("Up\n", fg="green")
            pretty_down = typer.style("Down\n", fg="red")
            if self.tty:
                out = self.tty.replace("Up\n", pretty_up).replace("Down\n", pretty_down)
            else:
                out = self.file
            if self.config and self.config.sanitize:
                out = self.sanitize_strings(out)
            return out

        def __iter__(self):
            out = self.tty or self.file
            out = out.splitlines(keepends=True)
            out = self.sanitize_strings(out)
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
            if config and config.sanitize and config.sanatize_file.is_file():
                sanitize_data = config.get_file_data(config.sanatize_file)
                for s in sanitize_data.get("redact_strings", {}):
                    strings = strings.replace(s, f"{'--redacted--':{len(s)}}")
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
            return "" if not self._file else typer.unstyle(self._file)


    @staticmethod
    def do_pretty(key: str, value: str) -> str:
        """Apply coloring to tty output

        Applies color to certain columns/values prior to formatting
        """
        color = "green" if value.lower() == "up" else "red"
        # return value if key != "status" else typer.style(value, fg=color)
        return value if key != "status" else f'[b {color}]{value.title()}[/b {color}]'

    def output(
        self,
        outdata: Union[List[str], Dict[str, Any]],
        tablefmt: str = "rich",
        title: str = None,
        caption: str = None,
        account: str = None,
        config=None,
        set_width_cols: dict = None,
        full_cols: Union[List[str], str] = [],
        fold_cols: Union[List[str], str] = [],
        ok_status: Union[int, List[int], Tuple[int, str], List[Tuple[int, str]]] = None,
    ) -> str:
        # log.debugv(f"data passed to output():\n{pprint(outdata, indent=4)}")
        def _do_subtables(data: list, tablefmt: str = "rich"):
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
                                inner_dict[key] = Text(str(val), style=None)
                            else:
                                inner_dict[key] = str(val)
                    else:
                        val = self.listify(val)
                        if val and tablefmt == "rich" and hasattr(val[0], 'keys'):
                            inner_table = Table(*(k for k in val[0].keys()),
                                                show_header=True,
                                                # padding=(0, 0),
                                                pad_edge=False,
                                                collapse_padding=True,
                                                show_edge=False,
                                                header_style="bold cyan",
                                                box=SIMPLE
                                                )
                            _ = [inner_table.add_row(*[self.do_pretty(kk, str(vv)) for kk, vv in v.items()]) for v in val]
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

        raw_data = outdata
        _lexer = table_data = None

        if config and config.sanitize and raw_data and all(isinstance(x, dict) for x in raw_data):
            redact = ["mac", "serial", "neighborMac", "neighborSerial", "neighborPortMac", "longitude", "latitude"]
            outdata = [{k: d[k] if k not in redact else "--redacted--" for k in d} for d in raw_data]

        # -- // List[str, ...] \\ --  Bypass all formatters, (config file output, etc...)
        if outdata and all(isinstance(x, str) for x in outdata):
            tablefmt = "strings"

        # -- convert List[dict] --> Dict[dev_name: dict] for yaml/json outputs
        if tablefmt in ['json', 'yaml', 'yml']:
            outdata = self.listify(outdata)
            if outdata and isinstance(outdata[0], dict) and 'name' in outdata[0]:
                outdata: Dict[str, Dict[str, Any]] = {
                    item['name']: {k: v for k, v in item.items() if k != 'name'}
                    for item in outdata
                }

        if tablefmt == "json":
            outdata = self.unlistify(outdata)
            raw_data = json.dumps(outdata, indent=4)
            _lexer = lexers.JsonLexer

        elif tablefmt in ["yml", "yaml"]:
            outdata = self.unlistify(outdata)
            raw_data = yaml.dump(outdata, sort_keys=False)
            _lexer = lexers.YamlLexer

        elif tablefmt == "csv":
            raw_data = table_data = "\n".join(
                            [
                                ",".join(
                                    [
                                        k if outdata.index(d) == 0 else str(v)
                                        for k, v in d.items()
                                        if k not in CUST_KEYS
                                    ])
                                for d in outdata
                            ])

        elif tablefmt == "rich":
            from rich.console import Console
            from rich.table import Table
            from rich.box import HORIZONTALS, SIMPLE
            from rich.text import Text
            # from rich.progress import Progress
            from centralcli import constants
            console = Console(record=True, emoji=False)

            customer_id, customer_name = "", ""
            # outdata = self.listify(outdata)

            # -- // List[dict, ...] \\ --
            if outdata and all(isinstance(x, dict) for x in outdata):
                customer_id = outdata[0].get("customer_id", "")
                customer_name = outdata[0].get("customer_name", "")
                outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]

                table = Table(
                    # show_edge=False,
                    show_header=True,
                    title=title,
                    header_style='magenta',
                    show_lines=False,
                    box=HORIZONTALS,
                    row_styles=['none', 'dark_sea_green']
                )

                fold_cols = [*fold_cols, 'description']
                _min_max = {'min': 10, 'max': 30}
                set_width_cols = set_width_cols or {'name': _min_max, 'model': _min_max}
                # default full cols #TODO clean this up
                _full_cols = ['mac', 'serial', 'ip', 'public ip', 'version', 'radio', 'id']
                full_cols = [*full_cols, *_full_cols]

                for k in outdata[0].keys():
                    if k in fold_cols:
                        table.add_column(k, overflow='fold', max_width=115, justify='left')
                    elif k in set_width_cols:
                        table.add_column(
                            k, min_width=set_width_cols[k]['min'],
                            max_width=set_width_cols[k]['max'],
                            justify='left'
                        )
                    elif k in full_cols:
                        table.add_column(k, no_wrap=True, justify='left')
                    else:
                        table.add_column(k, justify='left')

                formatted = _do_subtables(outdata)
                [table.add_row(*list(in_dict.values())) for in_dict in formatted]

                if title:
                    table.title = f'[italic cornflower_blue]{constants.what_to_pretty(title)}'
                if account or caption:
                    table.caption_justify = 'left'
                    table.caption = '' if not account else f'[italic dark_olive_green2] Account: {account}'
                    if caption:
                        table.caption = f"[italic dark_olive_green2]{table.caption}  {caption}"

                data_header = f"--\n{'Customer ID:':15}{customer_id}\n{'Customer Name:':15} {customer_name}\n--\n"

                # TODO look into this. console.capture stopped working reliably this works
                console.begin_capture()
                console.print(table)
                table_data = console.end_capture()
                raw_data = typer.unstyle(table_data)

                if customer_id:
                    raw_data = f"{data_header}{raw_data}"
                    table_data = f"{data_header}{table_data}"

        elif tablefmt == "tabulate":
            customer_id = customer_name = ""
            outdata = self.listify(outdata)

            # -- // List[dict, ...] \\ --
            if outdata and all(isinstance(x, dict) for x in outdata):
                customer_id = outdata[0].get("customer_id", "")
                customer_name = outdata[0].get("customer_name", "")
                outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]
                raw_data = outdata

                outdata = _do_subtables(outdata, tablefmt=tablefmt)
                # outdata = [dict((k, v) for k, v in zip(outdata[0].keys(), val)) for val in outdata]

                table_data = tabulate(outdata, headers="keys", tablefmt=tablefmt)
                td = table_data.splitlines(keepends=True)
                if td:
                    table_data = f"{typer.style(td[0], fg='cyan')}{''.join(td[1:])}"

                data_header = f"--\n{'Customer ID:':15}{customer_id}\n" \
                              f"{'Customer Name:':15} {customer_name}\n--\n"
                table_data = f"{data_header}{table_data}" if customer_id else f"{table_data}"
                raw_data = f"{data_header}{raw_data}" if customer_id else f"{raw_data}"

        else:  # strings output No formatting
            # -- // List[str, ...] \\ --
            if len(outdata) == 1:
                if "\n" not in outdata[0]:
                    # we can format green as only success output is sent through formatter.
                    table_data = typer.style(f"  {outdata[0]}", fg="green")
                    raw_data = outdata[0]
                else:  # template / config file output
                    # get rid of double nl @ EoF (configs)
                    raw_data = table_data = "{}\n".format('\n'.join(outdata).rstrip('\n'))
            else:
                raw_data = table_data = '\n'.join(outdata)
                # Not sure what hit's this, but it was created so something must
                log.debug("List[str] else hit")

        if _lexer and raw_data:
            table_data = highlight(bytes(raw_data, 'UTF-8'),
                                   _lexer(),
                                   formatters.Terminal256Formatter(style='solarized-dark')
                                   )

        return self.Output(rawdata=raw_data, prettydata=table_data, config=config)

    @staticmethod
    def color(
        text: Union[str, bool, List[str]],
        color_str: str = "bright_green",
        italic: bool = None,
        bold: bool = None,
        blink: bool = None,
    ) -> str:
        """Helper method to wrap text in rich formatting tags

        Applies standard default formatting.

        args:
            text (str|bool|list): The text to be formmated.  If a bool is provided
                it is converted to string and italics applied.  If list of strings
                is provided it is converted to str and formatted.
            color_str (str optional): Text is formatted with this color.
                Default: bright_green
            italic (bool): Wheather to apply italic to text.
                Default False if str is provided for text True if bool is provided.
            bold (bool): Wheather to apply bold to text. Default None/False
            blink (bool): Wheather to blink the text. Default None/False
        """
        if isinstance(text, bool):
            italic = True if italic is None else italic
            text = str(text)

        color_str = color_str if not italic else f"italic {color_str}"
        color_str = color_str if not bold else f"bold {color_str}"
        color_str = color_str if not blink else f"blink {color_str}"

        if isinstance(text, str):
            return f"[{color_str}]{text}[/{color_str}]"
        elif isinstance(text, list) and all([isinstance(x, str) for x in text]):
            text = [f"[{color_str}]{t}[/{color_str}]" for t in text]
            return ", ".join(text)
        else:
            raise TypeError(f"{type(text)}: text attribute should be str, bool, or list of str.")

    @staticmethod
    def chunker(seq, size):
        return [seq[pos:pos + size] for pos in range(0, len(seq), size)]

    # TODO decorator func
    @staticmethod
    def ask(
        prompt: str = "",
        *,
        console: Optional[Console] = None,
        password: bool = False,
        choices: Optional[List[str]] = None,
        show_default: bool = True,
        show_choices: bool = True,
        default: Any = ...,
    ) -> str:
        """wrapper function for rich.Prompt().ask()

        Handles KeyBoardInterrupt, EoFError, and exits if user inputs "abort"

        """
        def abort():
            print("Aborted")
            sys.exit()

        choices = choices if choices is not None and "abort" in choices else ["abort", *choices]

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

        if choice.lower() == "abort":
            abort()

        return choice

    @staticmethod
    def generate_template(template_file: Union[Path, str], var_file: Union[Path, str, None],) -> str:
        '''Generate configuration files based on j2 templates and provided variables
        '''
        template_file = Path(str(template_file)) if not isinstance(template_file, Path) else template_file
        var_file = Path(str(var_file)) if not isinstance(var_file, Path) else var_file

        valid_ext = ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf', '.xls', '.xlsx']
        if template_file.suffix == ".j2":
            if var_file is None or not var_file.exists():
                _var_files = [template_file.parent / f"{template_file.stem}{sfx}" for sfx in valid_ext]
                _var_files = [f for f in _var_files if f.exists()]
                if _var_files:
                    var_file = _var_files[0]
                else:
                    print(f":x: No variable file found for {template_file}")
                    raise typer.Exit(1)

            # TODO refactor to use helper function in utils
            # cli_file = generate_template(cli_file, var_file, group_dev=group_dev)
            config_data = yaml.load(var_file.read_text(), Loader=yaml.SafeLoader)

            env = Environment(loader=FileSystemLoader(str(template_file.parent)), trim_blocks=True, lstrip_blocks=True)
            template = env.get_template(template_file.name)

            config_out = template.render(config_data)
        else:
            config_out = template.read_text()

        return config_out

    @staticmethod
    def validate_config(data: str) -> List[str]:
        """Validator for resulting config after j2 conversion

        Args:
            data (str): str representing the final configuration.

        Raises:
            typer.Exit: If masked creds found

        Returns:
            Original list of str with each line rstrip.
        """
        cli_cmds = []
        for line in data.splitlines():
            cli_cmds += [line.rstrip()]
            if "******" in line:
                typer.secho("Masked credential found in file.", fg="red")
                typer.secho(
                    f"Replace:\n{' ':4}{line.strip()}\n    with cleartext{' or actual hash.' if 'hash' in line else '.'}",
                    fg="red",
                    )
                raise typer.Exit(1)

        if not cli_cmds:
            print(":x: [bright_red]Error:[/] No cli commands.")
            raise typer.Exit(1)

        return cli_cmds