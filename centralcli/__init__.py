#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# flake8: noqa

import json
import os
import typer

from pathlib import Path
from typing import Iterable, List
import sys

import click

from rich.traceback import install
install(show_locals=True, suppress=[click])

# TODO after install if you --install-completion prior to configuration completion will freeze the terminal (first_run is running with no interactive prompt)
# TODO first command after config is provided updates the cache but returns no output.  Bug.  Works fine from then on.

_calling_script = Path(sys.argv[0])
if str(_calling_script) == "." and os.environ.get("TERM_PROGRAM") == "vscode":
    _calling_script = Path.cwd() / "cli.py"   # vscode run in python shell

if _calling_script.name == "cencli":
    base_dir = Path(typer.get_app_dir(__name__))
elif _calling_script.name.startswith("test_"):
    base_dir = _calling_script.parent.parent
elif "centralcli" in Path(__file__).parts:
    base_dir = Path(__file__).parent
    while base_dir.name != "centralcli":
        base_dir = base_dir.parent
    base_dir = base_dir.parent
else:
    base_dir = _calling_script.resolve().parent
    if base_dir.name == "centralcli":
        base_dir = base_dir.parent
    else:
        print("Warning Logic Error in git/pypi detection")
        print(f"base_dir Parts: {base_dir.parts}")

from .logger import MyLogger
from . import constants
from .config import Config
config = Config(base_dir=base_dir)

log_dir = config.base_dir / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"{__name__}.log"

if '--debug' in str(sys.argv) or os.environ.get("ARUBACLI_DEBUG", "").lower() in ["1", "true"]:
    config.debug = True  # for the benefit of the 2 log messages below
if '--debugv' in str(sys.argv):
    config.debug = config.debugv = True
    try:
        _ = sys.argv.pop(sys.argv.index("--debugv"))
    except ValueError:
        # handles vscode issue as arg parsing for vscode is below
        sys.argv = [arg.replace("--debugv", "").rstrip().replace("  ", " ") for arg in sys.argv]

log = MyLogger(log_file, debug=config.debug, show=config.debug, verbose=config.debugv)

log.debug(f"{__name__} __init__ calling script: {_calling_script}, base_dir: {config.base_dir}")
log.debugv(f"config attributes: {json.dumps({k: str(v) for k, v in config.__dict__.items()}, indent=4)}")


# HACK completion has gotten jacked up.  typer calls click.utils._expand_args in Windows which was added in click 8, but completion is broken in click 8 so cencli is pinned to 7.1.2 until I can investigate further
# This hack manually adds the _expand_args functionality to click.utils which is pinned to 7.1.2  Otherwise an exception is thrown on Windows.
if os.name == "nt":  # pragma: no cover
    def _expand_args(
        args: Iterable[str],
        *,
        user: bool = True,
        env: bool = True,
        glob_recursive: bool = True,
    ) -> List[str]:
        """Simulate Unix shell expansion with Python functions.

        See :func:`glob.glob`, :func:`os.path.expanduser`, and
        :func:`os.path.expandvars`.

        This is intended for use on Windows, where the shell does not do any
        expansion. It may not exactly match what a Unix shell would do.

        :param args: List of command line arguments to expand.
        :param user: Expand user home directory.
        :param env: Expand environment variables.
        :param glob_recursive: ``**`` matches directories recursively.

        :meta private:
        """
        from glob import glob
        import re

        out = []

        for arg in args:
            if user:
                arg = os.path.expanduser(arg)

            if env:
                arg = os.path.expandvars(arg)

            try:
                matches = glob(arg, recursive=glob_recursive)
            except re.error:
                matches = []

            if not matches:
                out.append(arg)
            else:
                out.extend(matches)

        return out

    import click
    if not hasattr(click.utils, "_expand_args"):
        click.utils._expand_args = _expand_args


from pycentral.base import ArubaCentralBase
from .utils import Utils
utils = Utils()
from .response import Response, BatchRequest
from .central import CentralApi
from .cache import Cache, CentralObject
from .clicommon import CLICommon
from . import cleaner

# if no environ vars set for LESS command line options
# set -X to retain scroll-back after quitting less
#     -R for color output (default for the pager but defaults are not used if LESS is set)
#     +G so (start with output scrolled to end) so scroll-back contains all contents
# if not os.environ.get("LESS"):
os.environ["LESS"] = "-RX +G"

if os.environ.get("TERM_PROGRAM") == "vscode":
    from .vscodeargs import vscode_arg_handler
    vscode_arg_handler()

raw_out = False
if "--raw" in sys.argv:
    raw_out = True
    _ = sys.argv.pop(sys.argv.index("--raw"))
if "--debug-limit" in sys.argv:
    _idx = sys.argv.index("--debug-limit")
    _ = sys.argv.pop(sys.argv.index("--debug-limit"))
    if len(sys.argv) - 1 >= _idx and sys.argv[_idx].isdigit():
        config.limit = int(sys.argv[_idx])
        _ = sys.argv.pop(_idx)
if "--sanitize" in sys.argv:
    _ = sys.argv.pop(sys.argv.index("--sanitize"))
    config.sanitize = True


central = CentralApi(config.account)
cache = Cache(central)
cli = CLICommon(config.account, cache, central, raw_out=raw_out)

# allow singular form and common synonyms for the defined show commands
# show switches / show switch ...
if len(sys.argv) > 2:
    sys.argv[2] = constants.arg_to_what(sys.argv[2], cmd=sys.argv[1])

if "?" in sys.argv:
    sys.argv[sys.argv.index("?")] = "--help"
