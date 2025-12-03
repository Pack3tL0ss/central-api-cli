from __future__ import annotations

import logging
from functools import partial
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import sleep
from typing import Any

from rich.console import Console

from . import env, utils

console = Console(emoji=False, markup=False)
econsole = Console(stderr=True)


# These are pycentral logs that we ignore unless DEBUG is enabled
DEBUG_ONLY_MSGS = [
    "Loaded token from storage from file"
]


# pycentral has a number of sys.exit that are logged, but not displayed.  So it's a silent exit for cencli.  log_print will change the log to show=True so they display
PYCENTRAL_SILENT_EXIT = [
    "OAUTH2.0 Step1 login API call failed",
    "OAUTH2.0 Step1 failed",
    "OAUTH2.0 Step2 obtaining Auth code API call failed",
    "Central Login Step2 failed with error",
    "OAUTH2.0 Step3 creating access token API call failed",
    "Central Login Step3 failed with error"
]


class MyLogger:
    def __init__(self, log_file: str | Path, debug: bool = False, show: bool = False, verbose: bool = False, deprecation_warnings: str | list[str] = None):
        self._DEBUG: bool = debug
        self.log_msgs: list[str] = []
        self.verbose: bool = verbose
        self.log_file: Path = log_file if isinstance(log_file, Path) else Path(log_file)
        if env.is_pytest:
            self.log_file = self.log_file.parent / "pytest.log"
        self._log: logging.Logger = self.get_logger()
        self.name: str = self._log.name
        self.show: bool = show  # Sets default log behavior (other than debug)
        self._caption: list[str] = utils.listify(deprecation_warnings) or []  # Log messages will be logged and displayed in caption output

        # base logger methods
        self.debug = partial(self.log_print, level="debug")
        self.info = partial(self.log_print, level="info")
        self.warning = partial(self.log_print, level="warning")
        self.error = partial(self.log_print, level="error")
        self.exception = partial(self.log_print, level="exception", exc_info=True)
        self.critical  = partial(self.log_print, level="critical")
        self.fatal  = partial(self.log_print, level="fatal")

    def __getattr__(self, name: str) -> Any:  # pragma: no cover Exists only as a convenience when debugging
        if hasattr(self, "_log") and hasattr(self._log, name):
            return getattr(self._log, name)
        else:
            raise AttributeError(f"'MyLogger' object has no attribute '{name}'")

    def get_logger(self) -> logging.Logger:
        '''Return custom log object.'''
        fmtStr = "%(asctime)s [%(process)d][%(levelname)s]: %(message)s"
        dateStr = "%m/%d/%Y %I:%M:%S %p"
        logging.basicConfig(
            level=logging.DEBUG if self.DEBUG else logging.INFO,
            format=fmtStr,
            datefmt=dateStr,
            handlers=[
                RotatingFileHandler(self.log_file.absolute(),  maxBytes=250000, backupCount=5,),
            ],
        )
        return logging.getLogger(self.log_file.stem)

    def print_file(self, pytest: bool = False, show_all: bool = False, unused_mocks: bool = False) -> None:
        if unused_mocks:  # pragma: no cover
            unused_mock_file = self.log_file.parent / "pytest-unused-mocks.log"
            logs = unused_mock_file.read_text()
        elif not pytest:
            logs = self.log_file.read_text()
        else:
            pytest_log_file = self.log_file.parent / "pytest.log"
            logs = pytest_log_file.read_text()
            if not show_all:
                lines = logs.splitlines(keepends=True)
                for idx, line in enumerate(lines[::-1], start=1):
                    if "test run start" in line.lower():  # pragma: no cover
                        break
                logs = "".join(lines[len(lines) - idx:])

        console.print(logs)





    def follow(self, pytest: bool = False) -> None:  # pragma: no cover requires a tty
        """generator function that yields new lines in log file"""
        file = self.log_file if not pytest else self.log_file.parent / "pytest.log"
        with file.open("r") as lf:
            lines = lf.readlines()
            console.print("".join(lines[int(f"-{len(lines) if len(lines) <= 20 else 20}"):]).rstrip())

            while True:
                try:
                    line = lf.readline()
                    if not line:
                        sleep(1)
                        continue

                    console.print(line.rstrip())
                except (KeyboardInterrupt, EOFError):
                    break

    @property
    def caption(self) -> None | str:
        """render log messages queued for display in output caption."""
        if self._caption:
            return "\n".join([f' {msg}' for msg in self._caption])

    @caption.setter
    def caption(self, caption: str | list[str]):
        caption = caption if not isinstance(caption, str) else [caption]
        self._caption += caption

    @staticmethod
    def _remove_rich_markups(log_msg: str) -> str:
        # Need to include [/] as closing markup style to print color for log messages.  Logs with API endpoints ... [/configuration/v2...] will cause MarkupError otherwise
        if "[/]" not in log_msg:
            return log_msg

        console = Console(force_terminal=False)
        with console.capture() as cap:
            console.print(log_msg, end="")

        return cap.get()

    def log_print(
            self, msgs: str | list[str], *args, log: bool = None, show: bool = None, caption: bool = False, level: str = 'info',
            exc_info: bool = None, extra: bool = None, stack_info: bool = False, stacklevel: int = 1, **kwargs
        ) -> None:
        log = log if log is not None else not caption  # we log by default unless caption=True then the msg is displayed in caption, but not logged (unless log=True)
        msgs = [msgs] if not isinstance(msgs, list) else msgs
        _msgs, _logged = [], []

        for i in msgs:
            i = str(i)
            if not show and any([i.startswith(silent_exit) for silent_exit in PYCENTRAL_SILENT_EXIT]):  # pragma: no cover
                show = True
            if not self.DEBUG and [i for d in DEBUG_ONLY_MSGS if d in i]:  # messages we ignore if debug is not enabled.
                continue

            if i not in _logged:  # prevents errant duplicates.
                if log:
                    getattr(self._log, level)(self._remove_rich_markups(i.lstrip()).replace(r'\[', '['), *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)
                    _logged.append(i)
                if i and i not in self.log_msgs:
                    _msgs.append(i)

        warning_emoji = "[dark_orange3]\u26a0[/]  "
        if show is not False and any([show, self.show]):
            self.log_msgs += _msgs
            for m in self.log_msgs:
                if console.is_terminal or env.is_pytest:
                    _pfx = '' if not self.DEBUG else '\n'  # Add a CR before showing log when in debug due to spinners
                    econsole.print(f"{_pfx}{warning_emoji if level not in ['info', 'debug'] else ''}{m}", emoji=":cd:" not in m.lower())  # avoid :cd: emoji common in mac addresses

            self.log_msgs = []

        if caption:
            msgs = [line for m in msgs for line in str(m).splitlines()]
            self._caption = [*self._caption, *[f"{warning_emoji if level not in ['info', 'debug'] else ''}{m}" for m in msgs]]

    @property
    def level_name(self) -> str | int:  # pragma: no cover
        return logging.getLevelName(self._log.level)

    @property
    def DEBUG(self) -> bool:
        return self._DEBUG

    @DEBUG.setter
    def DEBUG(self, value: bool = False):
        self._DEBUG = value
        self.show = value
        self.setLevel(logging.DEBUG if value else logging.INFO)

    def debugv(self, msgs: list[str] | str, log: bool = True, show: bool = None, *args, **kwargs) -> None:
        """More verbose debugging - set via debugv: True in config
        """
        if self.DEBUG and self.verbose:
            self.log_print(msgs, log=log, show=show, level='debug', *args, **kwargs)

    def setLevel(self, level):
        getattr(self._log, 'setLevel')(level)
