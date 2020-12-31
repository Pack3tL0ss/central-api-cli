#!/usr/bin/env python3

import typer
import sys
import cli
from pathlib import Path

from centralcli.central import utils

# _config_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config")
_config_dir = Path.joinpath(Path(__file__).parent, "config")
# _def_import_file = os.path.join(_config_dir, "stored-tasks.yaml")


# -- break up arguments passed as single string from vscode promptString --
def get_arguments_from_import(import_file: str, key: str = None):
    args = utils.read_yaml(_import_file)
    if key and key in args:
        args = args[key]

    sys.argv += args

    return sys.argv


import sys  # NoQA
sys.argv[0] = 'ana-cli'
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
        if sys.argv[2].endswith((".yaml", ".yml")):
            _import_file = sys.argv.pop(2)
            if not utils.valid_file(_import_file):
                # if utils.valid_file(os.path.join(_config_dir, _import_file)):
                #     _import_file = os.path.join(_config_dir, _import_file)
                if utils.valid_file(_config_dir.joinpath(_import_file)):
                    _import_file = _config_dir.joinpath(_import_file)

            if len(sys.argv) > 2:
                _import_key = sys.argv.pop(2)

        sys.argv = get_arguments_from_import(_import_file, key=_import_key)
except Exception:
    pass

app = typer.Typer()
app = app.add_typer(cli.app, name="central")

if __name__ == "__main__":
    app()
    print(__name__)
