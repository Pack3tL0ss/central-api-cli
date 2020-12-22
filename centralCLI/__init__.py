#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Any
from pycentral.base import ArubaCentralBase

from .utils import Utils
from .config import Config
from pathlib import Path
from typing import Union
# from sys import argv
import sys
import logging
from . import constants  # NoQA
utils = Utils()


class MyLogger:
    def __init__(self, log_file: Union[str, Path], debug: bool = False, show: bool = False):
        self.log_msgs = []
        self.DEBUG = debug
        self.verbose = False
        if isinstance(log_file, Path):
            self.log_file = log_file
        else:
            self.log_file = Path(log_file)
        self._log = self.get_logger()
        self.name = self._log.name
        self.show = show  # Sets default log behavior (other than debug)

    def __getattr__(self, name):
        if hasattr(self, "_log") and hasattr(self._log, name):
            return getattr(self._log, name)
        else:
            raise AttributeError(f"'MyLogger' object has no attribute '{name}'")

    def get_logger(self):
        '''Return custom log object.'''
        fmtStr = "%(asctime)s [%(process)d][%(levelname)s]: %(message)s"
        dateStr = "%m/%d/%Y %I:%M:%S %p"
        logging.basicConfig(filename=self.log_file.absolute(),
                            level=logging.DEBUG if self.DEBUG else logging.INFO,
                            format=fmtStr,
                            datefmt=dateStr)
        return logging.getLogger(self.log_file.stem)

    def log_print(self, msgs, log: bool = False, show: bool = False, level: str = 'info', *args, **kwargs):
        msgs = [msgs] if not isinstance(msgs, list) else msgs
        _msgs = []
        _logged = []
        for i in msgs:
            i = str(i)
            if log and i not in _logged:
                getattr(self._log, level)(i, *args, **kwargs)
                _logged.append(i)
                if i and i not in self.log_msgs:
                    _msgs.append(i)

        if show:
            self.log_msgs += _msgs
            for m in self.log_msgs:
                print(m)
            self.log_msgs = []

    def show(self, msgs: Union[list, str], log: bool = False, show: bool = True, *args, **kwargs) -> None:
        self.log_print(msgs, show=show, log=log, *args, **kwargs)

    def debug(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, level='debug', *args, **kwargs)

    # -- more verbose debugging - primarily to get json dumps
    def debugv(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        if self.DEBUG and self.verbose:
            self.log_print(msgs, log=log, show=show, level='debug', *args, **kwargs)

    def info(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, *args, **kwargs)

    def warning(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, level='warning', *args, **kwargs)

    def error(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, level='error', *args, **kwargs)

    def exception(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, level='exception', *args, **kwargs)

    def critical(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, level='critical', *args, **kwargs)

    def fatal(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        show = show or self.show
        self.log_print(msgs, log=log, show=show, level='fatal', *args, **kwargs)

    def setLevel(self, level):
        getattr(self._log, 'setLevel')(level)
        pass


SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."


class Response:
    '''wrapper for requests.response object

    Assigns commonly evaluated attributes regardless of success
    Otherwise resp.ok will always be assigned and will be True or False
    '''
    def __init__(self, function, *args: Any, central: ArubaCentralBase = None, **kwargs: Any) -> Any:
        self.url = '' if not args else args[0]
        log.debug(f"request url: {self.url}\nkwargs: {kwargs}")
        try:
            if central:
                r = self.api_call(central, function, *args, **kwargs)
            else:
                r = utils.spinner(SPIN_TXT_DATA, function, *args, **kwargs)
            self.ok = r.ok
            try:
                self.output = r.json()
            except Exception:
                self.output = r.text
            self.output = self.clean_response()
            self.error = r.reason
            self.status_code = r.status_code
        except Exception as e:
            self.ok = False
            self.error = f"Exception occurred: {e.__class__}\n\t{e}"
            self.output = e
            self.status_code = 418
        if not self.ok:
            log.error(f"API Call Returned Failure ({self.status_code})\n\toutput: {self.output}\n\terror: {self.error}")

    def api_call(self, central: ArubaCentralBase, function: callable, *args, **kwargs):
        if "internal" in central.central_info["base_url"]:
            internal = True
        else:
            internal = False

        resp, token = None, None
        for _ in range(0, 2):
            try:
                resp = utils.spinner(SPIN_TXT_DATA, function, *args, **kwargs)
                if resp.status_code == 401 and "invalid_token" in resp.text:
                    log.error(f"Received error 401 on requesting url {resp.url}: {resp.reason}")
                    token = central.refreshToken(central.central_info["token"])
                    if token:
                        central.storeToken(token)
                        central.central_info["token"] = token
                else:
                    token = True
            except Exception as e:
                log.error(f"Attempt to refresh returned {e.__class__} {e}")

            if not token:
                if internal:
                    prompt = f"\nRefresh Failed Please Generate a new Token for:" \
                             f"\n    customer_id: {central.central_info['customer_id']}" \
                             f"\n    client_id: {central.central_info['client_id']}" \
                             "\nand paste result of `Download Tokens` Use CTRL-D to submit." \
                             "\n > "

                    token_data = utils.get_multiline_input(prompt, end="", return_type="dict")
                    central.central_info["token"]["access_token"] = token_data.get("access_token")
                    central.central_info["token"]["refresh_token"] = token_data.get("refresh_token")

                    try:
                        token = central.refreshToken(central.central_info["token"])
                        if token:
                            central.storeToken(token)
                            central.central_info["token"] = token
                        _ += 1
                    except Exception as e:
                        log.error(f"Attempt to refresh internal returned {e.__class__} {e}")
                else:
                    central.handleTokenExpiry()

            log.debug(f"api_call pass {_}")

        return resp

    def __bool__(self):
        return self.ok

    def __repr__(self):
        f"<{self.__module__}.{type(self).__name__} ({'OK' if self.ok else 'ERROR'}) object at {hex(id(self))}>"

    def __str__(self):
        return str(self.output) if self.output else self.error

    def __setitem__(self, name: str, value: Any) -> None:
        if isinstance(name, (str, int)) and hasattr(self, "output") and name in self.output:
            self.output[name] = value

    def __getitem__(self, key):
        return self.output[key]

    def __getattr__(self, name: str) -> Any:
        # print(f"hit {name}")
        if hasattr(self, "output") and self.output:
            if name in self.output:
                return self.output[name]
            else:
                # return from 2nd level of dict
                _keys = [k for k in constants.STRIP_KEYS if k in self.output]
                if _keys and name in self.output[_keys[0]] and isinstance(self.output[_keys[0]], dict):
                    return self.output[_keys[0]]

        raise AttributeError(f"'Response' object has no attribute '{name}'")

    def __iter__(self):
        for k, v in self.output.items():
            yield k, v

    def get(self, key, default: Any = None):
        return self.output.get(key, default)

    def keys(self):
        return self.output.keys()

    # not implemented yet
    def clean_response(self):
        _keys = [k for k in constants.STRIP_KEYS if k in self.output]
        if len(_keys) == 1:
            return self.output[_keys[0]]
        elif _keys:
            print(f"More wrapping keys than expected from return {_keys}")

        return self.output


_calling_script = Path(sys.argv[0])
# print(f"\t\t\t--- {_calling_script} ---")
_calling_script = Path.cwd() / "cli.py" if str(_calling_script) == "." else _calling_script  # vscode run in python shell
# print(f"\t\t\t--- {str(_calling_script) == '.'} ---")
# print(f"\t\t\t--- {_calling_script} ---")
log_file = _calling_script.joinpath(_calling_script.resolve().parent, "logs", f"{_calling_script.stem}.log")

config = Config(base_dir=_calling_script.resolve().parent)
log = MyLogger(log_file, debug=config.DEBUG, show=config.DEBUG)


# -- break up arguments passed as single string from vscode promptString --
def vscode_arg_handler():

    def get_arguments_from_import(import_file: str, key: str = None) -> list:
        """Get arguments from default import_file (stored_tasks.yaml)

        Args:
            import_file (str): name of import file
            key (str, optional): return single value for specific key if provided. Defaults to None.

        Returns:
            list: updated sys.argv list.
        """
        # args = utils.read_yaml(import_file)
        args = config.get_config_data(Path(import_file))
        if key and key in args:
            args = args[key]

        sys.argv += args

        return sys.argv

    try:
        if len(sys.argv) > 1:
            if " " in sys.argv[1] or not sys.argv[1]:
                vsc_args = sys.argv.pop(1)
                if vsc_args:
                    if "\\'" in vsc_args:
                        _loc = vsc_args.find("\\'")
                        _before = vsc_args[:_loc - 1]
                        _str_end = vsc_args.find("\\'", _loc + 1)
                        sys.argv += _before.split()
                        sys.argv += [f"{vsc_args[_loc + 2:_str_end]}"]
                        sys.argv += vsc_args[_str_end + 2:].split()
                    else:
                        sys.argv += vsc_args.split()

        if len(sys.argv) > 2:
            _import_file, _import_key = None, None
            if sys.argv[2].endswith((".yaml", ".yml", "json")):
                _import_file = sys.argv.pop(2)
                if not utils.valid_file(_import_file):
                    if utils.valid_file(config.dir.joinpath(_import_file)):
                        _import_file = config.dir.joinpath(_import_file)

                if len(sys.argv) > 2:
                    _import_key = sys.argv.pop(2)

                sys.argv = get_arguments_from_import(_import_file, key=_import_key)

    except Exception as e:
        log.exception(f"Exception in vscode arg handler (arg split) {e.__class__}.{e}", show=True)
        return

    # update launch.json default if launched by vscode debugger
    try:
        history_lines = None
        history_file = config.base_dir / ".vscode" / "prev_args"
        this_args = " ".join(sys.argv[1:])
        if history_file.is_file():
            history_lines = history_file.read_text().splitlines()

            if this_args in history_lines:
                _ = history_lines.pop(history_lines.index(this_args))
                history_lines.insert(0, _)
            else:
                history_lines.insert(0, this_args)
                if len(history_lines) > 10:
                    _ = history_lines.pop(10)
            history_file.write_text("\n".join(history_lines) + "\n")

        do_update = False
        launch_data = None
        launch_file = config.base_dir / ".vscode" / "launch.json"
        launch_file_bak = config.base_dir / ".vscode" / "launch.json.bak"
        if launch_file.is_file():
            launch_data = launch_file.read_text()
            launch_data = launch_data.splitlines()
            for idx, line in enumerate(launch_data):
                if "default" in line and "// VSC_PREV_ARGS" in line:
                    _spaces = len(line) - len(line.lstrip(" "))
                    new_line = f'{" ":{_spaces}}"default": "{this_args}"  // VSC_PREV_ARGS'
                    if line != new_line:
                        do_update = True
                        log.debug(f"changing default arg for promptString:\n"
                                  f"\t from: {line}\n"
                                  f"\t to: {new_line}"
                                  )
                        launch_data[idx] = new_line

                elif history_lines and "options" in line and "// VSC_ARG_HISTORY" in line:
                    import json
                    _spaces = len(line) - len(line.lstrip(" "))
                    new_line = f'{" ":{_spaces}}"options": {json.dumps(history_lines)},  // VSC_ARG_HISTORY'
                    if line != new_line:
                        do_update = True
                        log.debug(f"changing options arg for promptString:\n"
                                  f"\t from: {line}\n"
                                  f"\t to: {new_line}"
                                  )
                        launch_data[idx] = new_line

        if do_update and launch_data:
            # backup launch.json only if backup doesn't exist already
            if not launch_file_bak.is_file():
                import shutil
                shutil.copy(launch_file, launch_file_bak)

            # update launch.json
            launch_file.write_text("\n".join(launch_data) + "\n")

    except Exception as e:
        log.exception(f"Exception in vscode arg handler (launch.json update) {e.__class__}.{e}", show=True)
        return


if os.environ.get("TERM_PROGRAM") == "vscode":
    vscode_arg_handler()
