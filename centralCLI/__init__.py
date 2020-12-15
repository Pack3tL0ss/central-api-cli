#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any
from .utils import Utils
from .config import Config
from pathlib import Path
from typing import Union
from sys import argv
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


class Response:
    '''wrapper for requests.response object

    Assigns commonly evaluated attributes regardless of success
    Otherwise resp.ok will always be assigned and will be True or False
    '''
    def __init__(self, function, *args: Any, **kwargs: Any) -> Any:
        self.url = '' if not args else args[0]
        log.debug(f"request url: {self.url}\nkwargs: {kwargs}")
        try:
            r = function(*args, **kwargs)
            self.ok = r.ok
            try:
                self.output = r.json()
            except Exception:
                self.output = r.text
            self.error = r.reason
            self.status_code = r.status_code
        except Exception as e:
            self.output = {}
            self.ok = False
            self.error = f"Exception occurred {e.__class__}\n\t{e}"
            self.status_code = 418
        if not self.ok:
            log.error(f"API Call Returned Failure ({self.status_code})\n\toutput: {self.output}\n\terror: {self.error}")

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
        else:
            print(f"More wrapping keys than expected from return {_keys}")


_calling_script = Path(argv[0])
# print(f"\t\t\t--- {_calling_script} ---")
_calling_script = Path.cwd() / "cli.py" if str(_calling_script) == "." else _calling_script  # vscode run in python shell
# print(f"\t\t\t--- {str(_calling_script) == '.'} ---")
# print(f"\t\t\t--- {_calling_script} ---")
log_file = _calling_script.joinpath(_calling_script.resolve().parent, "logs", f"{_calling_script.stem}.log")

config = Config(base_dir=_calling_script.resolve().parent)
log = MyLogger(log_file, debug=config.DEBUG, show=config.DEBUG)
