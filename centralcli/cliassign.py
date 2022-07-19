#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List
import typer
from rich import print
from rich.console import Console


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


from centralcli.constants import LicenseTypes
app = typer.Typer()


@app.command(short_help="Assign License to device(s)", hidden=False)
def license(
    license: LicenseTypes = typer.Argument(..., help="License type to apply to device(s)."),
    serial_nums: List[str] = typer.Argument(...,),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Assign Licenses to devices by serial number.

    Device must already be added to Central.  Use 'cencli show inventory' to see devices that have been added.
    Use '--license' option with 'cencli add device ...' to add device and assign license in one command.
    """
    yes = yes_ if yes_ else yes
    # devices = [cli.cache.get_dev_identifier(dev) for dev in devices]

    # TODO add confirmation method builder to output class
    _msg = f"Assign [bright_green]{license}[/bright_green] to"
    if len(serial_nums) > 1:
        _dev_msg = '\n    '.join([f'[cyan]{dev}[/]' for dev in serial_nums])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = serial_nums[0]
        _msg = f"{_msg} [cyan]{dev}[/]"
    print(_msg)
    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.request(cli.central.assign_licenses, serial_nums, services=license.name)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Assign label to device(s)", hidden=False)
def label(
    label: str = typer.Argument(..., help="Label to assign to device(s)", autocompletion=cli.cache.label_completion,),
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

    _msg = f"Assign [bright_green]{label.name}[/bright_green] to"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([f'{dev.rich_help_text}' for dev in devices])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.rich_help_text}"
    Console(emoji=False).print(_msg)

    aps = [dev for dev in devices if dev.generic_type == "ap"]
    switches = [dev for dev in devices if dev.generic_type == "switch"]
    gws = [dev for dev in devices if dev.generic_type == "gw"]

    br = cli.central.BatchRequest
    reqs = []
    for dev_type, devs in zip(["IAP", "SWITCH", "CONTROLLER"], [aps, switches, gws]):
        if devs:
            reqs += [br(cli.central.assign_label_to_devices, label.id, device_type=dev_type, serial_nums=[dev.serial for dev in devs])]

    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Assign licenses / labels
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
