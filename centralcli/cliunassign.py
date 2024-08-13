#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List
import typer
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.cache import CentralObject
from centralcli.constants import IdenMetaVars
iden = IdenMetaVars()

app = typer.Typer()


@app.command()
def license(
    license: cli.cache.LicenseTypes = typer.Argument(..., help="License type to unassign from device(s).", show_default=False),  # type: ignore
    devices: List[str] = typer.Argument(..., help="device serial numbers or 'auto' to disable auto-subscribe.", metavar=f"{iden.dev_many} or 'auto'", autocompletion=cli.cache.dev_completion, show_default=False),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Unssign Licenses from devices by serial number(s) or disable auto-subscribe for the license type.
    """
    do_auto = True if "auto" in [s.lower() for s in devices] else False
    if do_auto:
        _msg = f"Disable Auto-assignment of [bright_green]{license}[/bright_green] to applicable devices."
        if len(devices) > 1:
            print('[cyan]auto[/] keyword provided remaining entries will be [bright_red]ignored[/]')
        print(_msg)
        if yes or typer.confirm("\nProceed?"):
            resp = cli.central.request(cli.central.disable_auto_subscribe, services=license.name)
            cli.display_results(resp, tablefmt="action")
            return

    devices: List[CentralObject] = [cli.cache.get_dev_identifier(dev, include_inventory=True) for dev in devices]

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
    label: str = typer.Argument(..., help="Label to remove from device(s)", autocompletion=cli.cache.label_completion, show_default=False,),
    devices: List[str] = typer.Argument(..., autocompletion=cli.cache.dev_completion, show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
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
