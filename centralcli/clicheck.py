#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import DevTypes

app = typer.Typer()
color = utils.color


@app.command()
def firmware_available(
    device_type: DevTypes = typer.Argument(..., show_default=False,),
    version: str = typer.Argument(..., show_default=False,),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Check if a firmware version is available for a given device type"""
    resp = cli.central.request(cli.central.check_firmware_available, device_type=device_type, firmware_version=version)
    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Check if firmware version is available
    """
    pass


if __name__ == "__main__":
    app()
