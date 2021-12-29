#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# flake8: noqa

import json
import os
import typer

from pathlib import Path
import sys

# try:
#     from icecream import ic
# except Exception:
#     def ic(*_, **__):
#         pass

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

log_dir = base_dir / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"{__name__}.log"

if '--debug' in str(sys.argv):
    config.debug = True  # for the benefit of the 2 log messages below

log = MyLogger(log_file, debug=config.debug, show=config.debug, verbose=config.debugv)

log.debug(f"{__name__} __init__ calling script: {_calling_script}, base_dir: {base_dir}")
log.debugv(f"config attributes: {json.dumps({k: str(v) for k, v in config.__dict__.items()}, indent=4)}")

from pycentral.base import ArubaCentralBase
from .utils import Utils
utils = Utils()
from .response import Response
from .central import CentralApi
from .cache import Cache
from .clicommon import CLICommon

# if no environ vars set for LESS command line options
# set -X to retain scrollback after quiting less
#     -R for color output (default for the pager but defaults are not used if LESS is set)
#     +G so (start with output scrolled to end) so scrollback contains all contents
if not os.environ.get("LESS"):
    os.environ["LESS"] = "-RX +G"

if os.environ.get("TERM_PROGRAM") == "vscode":
    from .vscodeargs import vscode_arg_handler
    vscode_arg_handler()

raw_out = False
if "-vv" in sys.argv:
    raw_out = True
    _ = sys.argv.pop(sys.argv.index("-vv"))


central = CentralApi(config.account)
cache = Cache(central)
cli = CLICommon(config.account, cache, central, raw_out=raw_out)

# allow singular form and common synonyms for the defined show commands
# show switches / show switch ...
if len(sys.argv) > 2:
    sys.argv[2] = constants.arg_to_what(sys.argv[2], cmd=sys.argv[1])

if "?" in sys.argv:
    sys.argv[sys.argv.index("?")] = "--help"
