#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
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

from centralcli.constants import iden_meta
from centralcli.cache import CentralObject

app = typer.Typer()


# TODO consider removing auto option as we've added enable/disable auto-sub ...
# TODO update cache for device after successful assignment
@app.command()
def license(
    license: cli.cache.LicenseTypes = typer.Argument(..., show_default=False),  # type: ignore
    serial_nums: List[str] = typer.Argument(..., help="device serial numbers or 'auto' to enable auto-subscribe.", show_default=False),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Assign Licenses to devices by serial number(s) or enable auto-subscribe for the license type.

    Device must already be added to Central.  Use '[cyan]cencli show inventory[/]' to see devices that have been added.
    Use '--license' option with '[cyan]cencli add device ...[/]' to add device and assign license in one command.
    """
    # TODO add confirmation method builder to output class
    do_auto = True if "auto" in [s.lower() for s in serial_nums] else False
    if do_auto:
        _msg = f"Enable Auto-assignment of [bright_green]{license.value}[/bright_green] to applicable devices."
        if len(serial_nums) > 1:
            cli.econsole.print('[cyan]auto[/] keyword provided remaining entries will be [bright_red]ignored[/]')
    else:
        _msg = f"Assign [bright_green]{license.value}[/bright_green] to"
        try:
            _serial_nums = [s if utils.is_serial(s) else cli.cache.get_dev_identifier(s).serial for s in serial_nums]
        except Exception:
            _serial_nums = serial_nums
        if len(_serial_nums) > 1:
            _dev_msg = '\n    '.join([f'[cyan]{dev}[/]' for dev in _serial_nums])
            _msg = f"{_msg}:\n    {_dev_msg}"
        else:
            dev = _serial_nums[0]
            _msg = f"{_msg} [cyan]{dev}[/]"

    cli.econsole.print(_msg)
    if cli.confirm(yes):
        if not do_auto:
            resp = cli.central.request(cli.central.assign_licenses, _serial_nums, services=license.name)
        else:
            resp = cli.central.request(cli.central.enable_auto_subscribe, services=license.name)

        cli.display_results(resp, tablefmt="action")
        # TODO cache update similar to batch unsubscribe


@app.command(name="label")
def label_(
    label: str = typer.Argument(..., metavar=iden_meta.label, help="Label to assign to device(s)", autocompletion=cli.cache.label_completion, show_default=False,),
    devices: List[str] = cli.arguments.devices,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    "Assign label to device(s)"
    label: CentralObject = cli.cache.get_label_identifier(label)
    devices: List[CentralObject] = [cli.cache.get_dev_identifier(dev) for dev in devices]

    _msg = f"Assign [bright_green]{label.name}[/bright_green] to"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([f'{dev.rich_help_text}' for dev in devices])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.rich_help_text}"
    cli.econsole.print(_msg, emoji=False)

    aps = [dev for dev in devices if dev.generic_type == "ap"]
    switches = [dev for dev in devices if dev.generic_type == "switch"]
    gws = [dev for dev in devices if dev.generic_type == "gw"]

    br = cli.central.BatchRequest
    reqs = []
    for dev_type, devs in zip(["IAP", "SWITCH", "CONTROLLER"], [aps, switches, gws]):
        if devs:
            reqs += [br(cli.central.assign_label_to_devices, label.id, serials=[dev.serial for dev in devs], device_type=dev_type)]

    if cli.confirm(yes):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")
        # We don't cache device label assignments


@app.callback()
def callback():
    """
    Assign licenses / labels
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
