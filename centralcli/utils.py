#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import socket
import string
import sys
import urllib.parse
from pprint import pprint
from typing import Any, Dict, List, Union
import typer
import logging

import yaml
from halo import Halo
import threading
from pygments import formatters, highlight, lexers
from tabulate import tabulate

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
        self.url = urllib.parse.quote(mac)

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

        Error and reprompt if user's response is not valid
        Appends '? (y/n): ' to question/prompt provided

        Params:
            question:str, The Question to ask
        Returns:
            answer:bool, Users Response yes=True
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
            ret = json.dumps(obj, indent=4, sort_keys=True)
        except Exception:
            ret = pprint(obj, indent=4, sort_dicts=True)
        finally:
            print(ret)

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
    def read_yaml(filename):
        """Read variables from local yaml file

        :param filename: local yaml file, defaults to 'vars.yaml'
        :type filename: str
        :return: Required variables
        :rtype: Python dictionary
        """
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        with open(filename, "r") as input_file:
            data = yaml.load(input_file, Loader=yaml.FullLoader)
        return data

    @staticmethod
    def get_host_short(host):
        """Extract hostname from fqdn

        Arguments:
            host {str} -- hostname. If ip address is provided it's returned as is

        Returns:
            str -- host_short (lab1.example.com becomes lab1)
        """
        return (
            host.split(".")[0]
            if "." in host and not host.split(".")[0].isdigit()
            else host
        )

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

    # TODO depricated validate not used, moved to Response
    @staticmethod
    def get_multiline_input(prompt: str = None, print_func: callable = print,
                            return_type: str = None, abort_str: str = "exit", **kwargs) -> Union[List[str], dict, str]:
        def _get_multiline_sub(prompt: str = prompt, print_func: callable = print_func, **kwargs):
            prompt = prompt or \
                "Enter/Paste your content. Then Ctrl-D or Ctrl-Z ( windows ) to submit.\n Enter 'exit' to abort"
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
    def strip_none(_dict: Union[dict, None]) -> Union[dict, None]:
        """strip all keys from a dict where value is NoneType"""

        return _dict if _dict is None else {k: v for k, v in _dict.items() if v is not None}

    class Output:
        def __init__(self, rawdata: str = "", prettydata: str = ""):
            self._file = rawdata    # found typer.unstyle AFTER I built this
            self.tty = prettydata

        def __len__(self):
            return len(str(self).splitlines())

        def __str__(self):
            pretty_up = typer.style(" Up", fg="green")
            pretty_down = typer.style(" Down", fg="red")
            if self.tty:
                return self.tty.replace(" Up", pretty_up).replace(" Down", pretty_down)
            else:
                return self.file

        def __iter__(self):
            out = self.tty or self.file
            out = out.splitlines(keepends=True)
            for line in out:
                yield line

        def menu(self, data_len: int = None) -> str:
            out = self.tty or self.file
            out = out.splitlines(keepends=True)
            _out = []
            if data_len:
                data_start = len(self) - data_len
            else:
                data_start = 2
                data_len = len(self) - 2
            for idx, line in enumerate(out):
                i = idx - data_start + 1
                pad = len(str(len(out[data_start:])))
                _out += [
                    f"  {' ':{pad}}{line}" if idx < data_start else f"{i}.{' ':{pad}}{line}"
                ]
            return "".join(_out)

        @property
        def file(self):
            return typer.unstyle(self._file)

    # Not used moved to __str__ method of Output class
    @staticmethod
    def do_pretty(key: str, value: str) -> str:
        """Apply coloring to tty output

        Applies color to certian columns/values prior to formatting
        """
        color = "green" if value.lower() == "up" else "red"
        # return value if key != "status" else typer.style(value, fg=color)
        return value if key != "status" else f'[b {color}]{value.title()}[/b {color}]'

    def output(
        self,
        outdata: Union[List[str], Dict[str, Any]],
        tablefmt: str = None,
        title: str = None,
        account: str = None
    ) -> str:
        # log.debugv(f"data passed to output():\n{pprint(outdata, indent=4)}")
        def _do_subtables(data: list, tablefmt: str = "rich"):
            out = []
            for inner_dict in data:
                # inner_list = []
                for key, val in inner_dict.items():
                    if not isinstance(val, (list, dict, tuple)):
                        if val is None:
                            # inner_list.append('')
                            inner_dict[key] = ''
                        elif isinstance(val, str) and val.lower() in ['up', 'down']:
                            color = 'red' if val.lower() == 'down' else 'green'
                            if tablefmt == 'rich':
                                inner_dict[key] = f'[b {color}]{val.title()}[/b {color}]'
                            else:
                                inner_dict[key] = typer.style(val.title(), fg=color)
                        else:
                            # inner_list.append(str(val))
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
                            # _ = [inner_table.add_row(*[json.dumps(vv) for vv in v.values()]) for v in val]
                            _ = [inner_table.add_row(*[self.do_pretty(kk, str(vv)) for kk, vv in v.items()]) for v in val]
                            with console.capture():
                                console.print(inner_table)
                            inner_dict[key] = console.export_text()
                        else:
                            inner_table = tabulate(val, headers="keys", tablefmt=tablefmt)
                            inner_dict[key] = inner_table

                        # inner_list.append(inner_table)
                out.append(inner_dict)
            return out

        raw_data = outdata
        _lexer = table_data = None

        if tablefmt in ['json', 'yaml', 'yml']:
            # convert List[dict] to Dict[dev_name: dict]
            outdata = self.listify(outdata)
            if outdata and 'name' in outdata[0]:
                outdata: Dict[str, dict] = {item['name']: {k: v for k, v in item.items() if k != 'name'} for item in outdata}

        if tablefmt == "json":
            raw_data = json.dumps(outdata, indent=4)
            _lexer = lexers.JsonLexer

        elif tablefmt in ["yml", "yaml"]:
            raw_data = yaml.dump(outdata)
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

        elif tablefmt == "rich":  # TODO Temporary Testing ***
            from rich.console import Console
            from rich.table import Table
            # from rich.tabulate import Table
            # from rich.columns import Columns
            # from rich.style import Style
            # from rich.segment import Segment
            # from rich.measure import Measurement
            from rich.box import HORIZONTALS, SIMPLE
            # from rich.rule import Rule
            from rich.text import Text
            from centralcli import constants
            console = Console(record=True)

            customer_id, customer_name = "", ""
            outdata = self.listify(outdata)

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

                fold_cols = ['description']
                _min_max = {'min': 10, 'max': 20}
                set_width_cols = {'name': _min_max, 'model': _min_max}
                full_cols = ['mac', 'serial', 'ip', 'public ip', 'version', 'radio']

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
                if account:
                    table.caption = f'[italic dark_olive_green2]{account}'
                    table.caption_justify = 'left'

                # table_data = tabulate(outdata, headers="keys", tablefmt="simple")

                data_header = f"--\n{'Customer ID:':15}{customer_id}\n" \
                              f"{'Customer Name:':15} {customer_name}\n--\n"

                with console.capture():
                    console.print(table)

                raw_data = console.export_text(clear=False)
                table_data = console.export_text(styles=True)

                raw_data = f"{data_header}{raw_data}" if customer_id else f"{raw_data}"
                table_data = f"{data_header}{table_data}" if customer_id else f"{table_data}"

            # -- // List[str, ...] \\ --
            elif outdata and [isinstance(x, str) for x in outdata].count(False) == 0:
                if len(outdata) > 1:
                    raw_data = table_data = "{}{}{}".format("--\n", '\n'.join(outdata), "\n--")
                else:
                    raw_data = table_data = '\n'.join(outdata)

        else:
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
                table_data = f"{typer.style(td[0], fg='cyan')}{''.join(td[1:])}"

                data_header = f"--\n{'Customer ID:':15}{customer_id}\n" \
                              f"{'Customer Name:':15} {customer_name}\n--\n"
                table_data = f"{data_header}{table_data}" if customer_id else f"{table_data}"
                raw_data = f"{data_header}{raw_data}" if customer_id else f"{raw_data}"

            # -- // List[str, ...] \\ --
            elif outdata and [isinstance(x, str) for x in outdata].count(False) == 0:
                if len(outdata) > 1:
                    raw_data = table_data = "{}{}{}".format("--\n", '\n'.join(outdata), "\n--")
                else:
                    # template / config file output
                    raw_data = table_data = '\n'.join(outdata)

        if _lexer and raw_data:
            table_data = highlight(bytes(raw_data, 'UTF-8'),
                                   _lexer(),
                                   formatters.Terminal256Formatter(style='solarized-dark')
                                   )

        return self.Output(rawdata=raw_data, prettydata=table_data)
