#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import clisetfirmware
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import clisetfirmware
    else:
        print(pkg_dir.parts)
        raise e

app = typer.Typer()
app.add_typer(clisetfirmware.app, name="firmware")


@app.callback()
def callback():
    """
    Set Firmware Compliance
    """
    pass


if __name__ == "__main__":
    app()
