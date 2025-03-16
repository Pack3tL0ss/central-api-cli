from __future__ import annotations

from os import environ
from pathlib import Path
from typing import Union, List, Any
from logging.handlers import RotatingFileHandler
from time import sleep
from rich.console import Console
# from rich.logging import RichHandler

import logging
import typer


log_colors = {
    "error": typer.colors.RED,
    "exception": typer.colors.RED,
    "critical": typer.colors.RED,
    "fatal": typer.colors.RED,
    "warning": typer.colors.YELLOW,
}
# log_colors = {
#     "error": "[bright_red]",
#     "exception": "[bright_red]",
#     "critical": "[bright_red]",
#     "fatal": "[bright_red]",
#     "warning": "[dark_orange4]",
# }
console = Console(emoji=False, markup=False)
emoji_console = Console(markup=False)
default_console = Console()
DEBUG_ONLY_MSGS = [
    "Loaded token from storage from file"
]


class MyLogger:
    def __init__(self, log_file: Union[str, Path], debug: bool = False, show: bool = False, verbose: bool = False):
        self._DEBUG: bool = debug
        self.log_msgs: List[str] = []
        self.verbose: bool = verbose
        if isinstance(log_file, Path):
            self.log_file: Path = log_file
        else:
            self.log_file: Path = Path(log_file)
        self._log: logging.Logger = self.get_logger()
        self.name: str = self._log.name
        self.show: bool = show  # Sets default log behavior (other than debug)
        self._caption: List[str] = []  # Log messages will be logged and displayed in caption output

    def __getattr__(self, name: str) -> Any:
        if hasattr(self, "_log") and hasattr(self._log, name):
            return getattr(self._log, name)
        else:
            raise AttributeError(f"'MyLogger' object has no attribute '{name}'")

    def get_logger(self) -> logging.Logger:
        '''Return custom log object.'''
        fmtStr = "%(asctime)s [%(process)d][%(levelname)s]: %(message)s"
        # fmtStr = "%(asctime)s [%(process)d][%(levelname)s]{%(pathname)s:%(lineno)d}: %(message)s"
        dateStr = "%m/%d/%Y %I:%M:%S %p"
        # fmtStr = "%(message)s"
        # dateStr = "[%X]"
        logging.basicConfig(
            # filename=self.log_file.absolute(),
            level=logging.DEBUG if self.DEBUG else logging.INFO,
            format=fmtStr,
            datefmt=dateStr,
            handlers=[
                # RichHandler(rich_tracebacks=True, tracebacks_show_locals=True, show_path=False),
                RotatingFileHandler(self.log_file.absolute(),  maxBytes=250000, backupCount=5,),
            ],
        )
        return logging.getLogger(self.log_file.stem)

    def print_file(self) -> None:
        console.print(self.log_file.read_text(),)

    def follow(self) -> None:
        '''generator function that yields new lines in log file
        '''
        with self.log_file.open("r") as lf:
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
        """render log messages queued for display in output caption.
        """
        if not self._caption:
            return
        else:
            return "\n".join([f' {msg}' for msg in self._caption])

    @staticmethod
    def _remove_rich_markups(log_msg: str) -> str:
        # Need to include [/] as closing markup style to print color for log messages.  Logs with API endpoints ... [/configuration/v2...] will cause MarkupError otherwise
        if "[/]" not in log_msg:
            return log_msg

        console = Console(force_terminal=False)
        with console.capture() as cap:
            console.print(log_msg, end="")

        return cap.get()

    def log_print(self, msgs, log: bool = False, show: bool = False, caption: bool = False, level: str = 'info', *args, **kwargs) -> None:
        msgs = [msgs] if not isinstance(msgs, list) else msgs
        _msgs = []
        _logged = []
        for i in msgs:
            i = str(i)
            if not self.DEBUG and [i for d in DEBUG_ONLY_MSGS if d in i]:  # messages we ignore if debug is not enabled.
                continue

            if i not in _logged:
                if log:
                    getattr(self._log, level)(self._remove_rich_markups(i), *args, **kwargs)
                    _logged.append(i)
                if i and i not in self.log_msgs:
                    _msgs.append(i)

        if show is not False and True in [show, self.show]:
            self.log_msgs += _msgs
            for m in self.log_msgs:
                if console.is_terminal or environ.get("PYTEST_CURRENT_TEST"):
                    _pfx = '' if not self.DEBUG else '\n'  # Add a CR before showing log when in debug due to spinners
                    con = emoji_console if "[/]" not in m else default_console
                    con.print(f"{_pfx}{':warning:  ' if level not in ['info', 'debug'] else ''}{m}")

            self.log_msgs = []

        if caption:
            _warn = "\u26a0"
            self._caption = [*self._caption, *[f"{f'{_warn}  ' if level not in ['info', 'debug'] else ''}{m}" for m in msgs]]

    @property
    def level_name(self) -> str | int:
        return logging.getLevelName(self._log.level)

    @property
    def DEBUG(self) -> bool:
        return self._DEBUG

    @DEBUG.setter
    def DEBUG(self, value: bool = False):
        self._DEBUG = value
        self.show = value
        self.setLevel(logging.DEBUG if value else logging.INFO)

    # If caption=True we assume log=False unless you specify log=True, default it to log, no caption.
    def debug(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, level='debug', *args, **kwargs)

    def debugv(self, msgs: Union[list, str], log: bool = True, show: bool = None, *args, **kwargs) -> None:
        """More verbose debugging - set via debugv: True in config
        """
        if self.DEBUG and self.verbose:
            self.log_print(msgs, log=log, show=show, level='debug', *args, **kwargs)

    def info(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, *args, **kwargs)

    def warning(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, level='warning', *args, **kwargs)

    def error(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, level='error', *args, **kwargs)

    def exception(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, level='exception', *args, **kwargs)

    def critical(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, level='critical', *args, **kwargs)

    def fatal(self, msgs: Union[list, str], log: bool = None, show: bool = None, caption: bool = False, *args, **kwargs) -> None:
        log = log if log is not None else not caption
        self.log_print(msgs, log=log, show=show, caption=caption, level='fatal', *args, **kwargs)

    def setLevel(self, level):
        getattr(self._log, 'setLevel')(level)
