#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import typer

from centralcli import cli
from centralcli.cache import api
from centralcli.constants import DevTypes

app = typer.Typer()


@app.command()
def firmware_available(
    device_type: DevTypes = typer.Argument(..., show_default=False,),
    version: str = typer.Argument(..., show_default=False,),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    workspace: str = cli.options.workspace,
) -> None:
    """Check if a firmware version is available for a given device type"""
    resp = api.session.request(api.firmware.check_firmware_available, device_type=device_type, firmware_version=version)
    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Check if firmware version is available
    """
    ...


if __name__ == "__main__":
    app()
