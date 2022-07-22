#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List
import typer
from rich import print


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

from centralcli.cache import CentralObject
from centralcli.constants import LicenseTypes, IdenMetaVars
iden = IdenMetaVars()

app = typer.Typer()


@app.command(help="unassign License from device(s)")
def license(
    license: LicenseTypes = typer.Argument(..., help="License type to unassign from device(s)."),
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    try:
        devices: CentralObject = [cli.cache.get_dev_identifier(dev) for dev in devices]
    except typer.Exit:  # allows un-assignment of devices that never checked into Central
        print("[bright_green]Checking full Inventory[/]")
        inv = cli.central.request(cli.central.get_device_inventory)
        serials_in_inventory = [i.get("serial", "ERROR") for i in inv.output]
        class Device:
            def __init__(self, serial):
                self.serial = serial
                self.summary_text = f"Device with serial {serial}"
        dev_out = []
        for dev in devices:
            if dev.upper() not in serials_in_inventory:
                print(f"{dev} not found in inventory.")
                raise typer.Exit(1)
            else:
                dev_out += [Device(dev)]
        devices = dev_out

    _msg = f"Unassign [bright_green]{license}[/bright_green] from"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([dev.summary_text for dev in devices])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.summary_text}"
    print(_msg)

    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.request(cli.central.unassign_licenses, [d.serial for d in devices], services=license.name)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Unassign label from device(s)", hidden=False)
def label(
    label: str = typer.Argument(..., help="Label to remove from device(s)", autocompletion=cli.cache.label_completion,),
    devices: List[str] = typer.Argument(..., autocompletion=cli.cache.dev_completion),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    label = cli.cache.get_label_identifier(label)
    devices = [cli.cache.get_dev_identifier(dev) for dev in devices]

    _msg = f"Unassign [bright_green]{label.name}[/bright_green] from"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([f'{dev.rich_help_text}' for dev in devices])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.rich_help_text}"
    print(_msg)

    aps = [dev for dev in devices if dev.generic_type == "ap"]
    switches = [dev for dev in devices if dev.generic_type == "switch"]
    gws = [dev for dev in devices if dev.generic_type == "gw"]

    br = cli.central.BatchRequest
    reqs = []
    for dev_type, devs in zip(["IAP", "SWITCH", "CONTROLLER"], [aps, switches, gws]):
        if devs:
            reqs += [br(cli.central.remove_label_from_devices, label.id, device_type=dev_type, serial_nums=[dev.serial for dev in devs])]

    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Unassign licenses / labels
    """
    pass


if __name__ == "__main__":
    app()
