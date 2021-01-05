#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Any
import pycentral.base
import typer

from .utils import Utils
from .config import Config
from pathlib import Path
from typing import Union
import sys
import logging
from . import constants
utils = Utils()


ArubaCentralBase = pycentral.base.ArubaCentralBase


# Not Used
class ArubaCentralException(Exception):
    pass


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
        self._exit_caught = False
        self._exit = None

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

    def no_exit(self, exit_msg_code: Union[str, int] = None, *args, **kwargs) -> None:
        # try:
        #     msg = ', '.join(*args)
        # except TypeError:
        #     msg = str(*args)
        if self._exit_caught and self._exit is not None:
            self._exit()
        else:
            self._log.warning(f"ArubaCentralBase Tried to exit. ({exit_msg_code}) Exit Overriden")
            self._exit_caught = True


def _refresh_token(central: ArubaCentralBase, token_data: dict = None) -> bool:
    if not token_data:
        token_data = central.central_info.get("token")

    if not token_data:
        return False

    token = None
    try:
        # token = central.refreshToken(central.central_info["token"])
        token = utils.spinner("Attempting to Refresh Token", central.refreshToken, token_data)
        if token:
            central.storeToken(token)
            central.central_info["token"] = token
    except Exception as e:
        log.error(f"Attempt to refresh internal returned {e.__class__} {e}")

    return token is not None


def handle_invalid_token(central: ArubaCentralBase) -> None:
    """Handle invalid or expired tokens

    For prod cluster it leverages ArubaCentralBase.handleTokenExpiry()
    For internal cluster it extends functionality to support user input
    copy paste of Download Token dict from Aruba Central GUI.

    Args:
        central (ArubaCentralBase): ArubaCentralBase class
    """
    internal = "internal" in central.central_info["base_url"]
    if internal:
        prompt = f"\nRefresh Failed Please Generate a new Token for:" \
                 f"\n    customer_id: {central.central_info['customer_id']}" \
                 f"\n    client_id: {central.central_info['client_id']}" \
                 "\nand paste result of `Download Tokens` Use CTRL-D on empty line to submit." \
                 "\n > "

        # typer.launch(f'{central.central_info["base_url"]}/platform/frontend/#!/APIGATEWAY')
        # TODO exception handling graceful exit for invalid json pasted
        token_data = utils.get_multiline_input(prompt, end="", return_type="dict")
        typer.clear()
        # central.central_info["token"]["access_token"] = token_data.get("access_token")
        # central.central_info["token"]["refresh_token"] = token_data.get("refresh_token")
        _refresh_token(central, token_data)
        # try:
        #     # token = central.refreshToken(central.central_info["token"])
        #     token = central.refreshToken(token_data)
        #     if token:
        #         central.storeToken(token)
        #         central.central_info["token"] = token
        # except Exception as e:
        #     log.error(f"Attempt to refresh internal returned {e.__class__} {e}")
    else:
        central.handleTokenExpiry()

    return central


class Response:
    '''wrapper for requests.response object

    Assigns commonly evaluated attributes regardless of success
    Otherwise resp.ok will always be assigned and will be True or False
    '''
    def __init__(self, function, *args: Any, central: ArubaCentralBase = None, callback: callable = None,
                 callback_kwargs: Any = {}, **kwargs: Any):
        self.url = '' if not args else args[0]
        log.debug(f"request url: {self.url}\nkwargs: {kwargs}")
        try:
            if central:
                r = self.api_call(central, function, *args, **kwargs)
            else:
                _data_msg = '' if not args or " arubanetworks.com" not in args[0] \
                    else (f'({args[0].split("arubanetworks.com/")[-1]})')
                spin_txt_data = f"Collecting Data{_data_msg}from Aruba Central API Gateway..."
                r = utils.spinner(spin_txt_data, function, *args, **kwargs)
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
            log.error(f"API Call ({self.url}) Returned Failure ({self.status_code})\n\t"
                      f"output: {self.output}\n\terror: {self.error}")
        # data cleaner methods to strip any useless columns, change key names, etc.
        elif callback is not None:
            self.output = callback(self.output, **callback_kwargs)

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
        for _dict in self.output:
            for k, v in _dict.items():
                yield k, v

    def get(self, key, default: Any = None):
        if isinstance(self.output, dict):
            return self.output.get(key, default)

    def keys(self):
        return self.output.keys()

    def clean_response(self):
        _keys = [k for k in constants.STRIP_KEYS if k in self.output]
        if len(_keys) == 1:
            return self.output[_keys[0]]
        elif _keys:
            print(f"More wrapping keys than expected from return {_keys}")
        return self.output

    @staticmethod
    def api_call(central: ArubaCentralBase, function: callable, *args, **kwargs):
        central_info = central.central_info
        resp, token = None, None
        _data_msg = '' if not args or "arubanetworks.com" not in args[0] else (f' ({args[0].split("arubanetworks.com/")[-1]})')
        spin_txt_data = f"Collecting Data{_data_msg} from Aruba Central API Gateway..."
        for _ in range(1, 3):
            if _ > 1:
                spin_txt_data = spin_txt_data + " retry"
            try:
                resp = utils.spinner(f"{spin_txt_data}", function, *args, **kwargs)
                if resp.status_code == 401 and "invalid_token" in resp.text:
                    # log.error(f"Received error 401 on requesting url {resp.url}: {resp.reason}")

                    if central_info.get("retry_token") and not central_info["token"] == central_info["retry_token"]:
                        token = _refresh_token(central, central.central_info["retry_token"])
                    else:
                        token = _refresh_token(central)
                    # token = central.refreshToken(central.central_info["token"])
                    # if token:
                    #     central.storeToken(token)
                    #     central.central_info["token"] = token
                else:
                    token = True
                    break
            except Exception as e:
                log.error(f"Attempt to refresh returned {e.__class__} {e}")

            if not token:
                handle_invalid_token(central)
                _ += 1

            log.debug(f"api_call pass {_}")

        return resp


_calling_script = Path(sys.argv[0])
# print(f"\t\t\t--- {_calling_script} ---")
if str(_calling_script) == "." and os.environ.get("TERM_PROGRAM") == "vscode":
    _calling_script = Path.cwd() / "cli.py"   # vscode run in python shell

if _calling_script.name == "cencli":
    base_dir = Path(typer.get_app_dir(__name__))
else:
    base_dir = _calling_script.resolve().parent  # .joinpath("config")
    if base_dir.name == "centralcli":
        base_dir = base_dir.parent
    else:
        print("Warning Logic Error in git/pypi detection")
        print(f"base_dir Parts: {base_dir.parts}")

# print(f"\t\t\t--- {str(_calling_script) == '.'} ---")
# print(f"\t\t\t--- {_calling_script} ---")
# log_file = _calling_script.joinpath(_calling_script.resolve().parent, "logs", f"{_calling_script.stem}.log")
log_dir = base_dir / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
# log_file = log_dir / f"{_calling_script.stem}.log"
log_file = log_dir / f"{__name__}.log"

config = Config(base_dir=base_dir)
log = MyLogger(log_file, debug=config.debug, show=config.debug)

log.debug(f"{__name__} __init__ calling script: {_calling_script}, base_dir: {base_dir}")
log.debugv(f"config attributes: {json.dumps({k: str(v) for k, v in config.__dict__.items()})}")

# override sys.exit prevent ArubaCentralBase from exiting when unable to refresh internal
# log._exit = pycentral.base.sys.exit
# pycentral.base.sys.exit = log.no_exit
# pycentral.base.createToken = createToken


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

# # TODO TEMP DEBUG REMOVE ------------------------------------------------!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# print(json.dumps({k: str(v) for k, v in locals().items() if k != "__builtins__"}, indent=4, sort_keys=True))
# print(json.dumps({k: str(v) for k, v in globals().items() if k != "__builtins__"},  indent=4, sort_keys=True))
