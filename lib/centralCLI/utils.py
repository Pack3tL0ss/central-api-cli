#!/usr/bin/env python3

import json
import os
import shutil
import socket
import string
import sys
import urllib.parse
from pprint import pprint
from typing import Union

import yaml
from halo import Halo
from pygments import formatters, highlight, lexers
from tabulate import tabulate

# removed from output and placed at top (provided with each item returned)
CUST_KEYS = ["customer_id", "customer_name"]


class Convert:
    def __init__(self, mac):
        self.orig = mac
        if not mac:
            mac = '0'
        self.clean = ''.join([c for c in list(mac) if c in string.hexdigits])
        self.ok = True if len(self.clean) == 12 else False
        cols = ':'.join(self.clean[i:i+2] for i in range(0, 12, 2))
        if cols.strip().endswith(':'):  # handle macs starting with 00 for oobm
            cols = f"00:{cols.strip().rstrip(':')}"
        self.dashes = '-'.join(self.clean[i:i+2] for i in range(0, 12, 2))
        self.dots = '.'.join(self.clean[i:i+4] for i in range(0, 12, 4))
        self.tag = f"ztp-{self.clean[-4:]}"
        self.dec = int(self.clean, 16) if self.ok else 0
        self.url = urllib.parse.quote(mac)


class Mac(Convert):
    def __init__(self, mac):
        super().__init__(mac)
        oobm = hex(self.dec + 1).lstrip('0x')
        self.oobm = Convert(oobm)


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

    @staticmethod
    def spinner(spin_txt, function, *args, **kwargs):
        spinner = kwargs.get("spinner", "dots")
        if sys.stdin.isatty():
            with Halo(text=spin_txt, spinner=spinner):
                return function(*args, **kwargs)

    class Output:
        def __init__(self, rawdata: str = "", prettydata: str = ""):
            self.file = rawdata    # found typer.unstyle AFTER I built this
            self.tty = prettydata

        def __len__(self):
            return len(str(self.file).splitlines())

        def __str__(self):
            return self.tty or self.file

    def output(self, outdata, tablefmt):
        # log.debugv(f"data passed to output():\n{pprint(outdata, indent=4)}")
        raw_data = outdata
        _lexer = table_data = None

        if tablefmt == "json":
            # from pygments import highlight, lexers, formatters
            raw_data = json.dumps(outdata, sort_keys=True, indent=2)
            _lexer = lexers.JsonLexer

        elif tablefmt in ["yml", "yaml"]:
            raw_data = yaml.dump(outdata, sort_keys=True, )
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

        else:
            customer_id = customer_name = ""
            outdata = self.listify(outdata)

            # -- // List[dict, ...] \\ --
            if outdata and all(isinstance(x, dict) for x in outdata):
                customer_id = outdata[0].get("customer_id", "")
                customer_name = outdata[0].get("customer_name", "")
                outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]
                table_data = tabulate(outdata, headers="keys", tablefmt=tablefmt)

                data_header = f"--\n{'Customer ID:':15}{customer_id}\n" \
                              f"{'Customer Name:':15} {customer_name}\n--\n"
                raw_data = table_data = f"{data_header}{table_data}" if customer_id else f"{table_data}"

            # -- // List[str, ...] \\ --
            elif outdata and (isinstance(x, str) for x in outdata):
                raw_data = table_data = "{}{}{}".format("--\n", '\n'.join(outdata), "\n--")

        if _lexer and raw_data:
            table_data = highlight(bytes(raw_data, 'UTF-8'),
                                   _lexer(),
                                   formatters.Terminal256Formatter(style='solarized-dark')
                                   )

        return self.Output(rawdata=raw_data, prettydata=table_data)
