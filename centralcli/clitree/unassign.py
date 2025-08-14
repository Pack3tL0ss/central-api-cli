#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import typer

from centralcli import common, log, render
from centralcli.cache import CacheDevice, CacheLabel, api
from centralcli.client import BatchRequest
from centralcli.constants import iden_meta

app = typer.Typer()


# TOGLP
@app.command()
def license(
    license: common.cache.LicenseTypes = typer.Argument(..., help="License type to unassign from device(s).", show_default=False),  # type: ignore
    devices: list[str] = typer.Argument(..., help="device serial numbers or 'auto' to disable auto-subscribe.", metavar=f"{iden_meta.dev_many} or 'auto'", autocompletion=common.cache.dev_completion, show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Unssign Licenses from devices by serial number(s) or disable auto-subscribe for the license type."""
    do_auto = True if "auto" in [s.lower() for s in devices] else False
    if do_auto:
        _msg = f"Disable Auto-assignment of [bright_green]{license.value}[/bright_green] to applicable devices."
        if len(devices) > 1:
            render.econsole.print('[cyan]auto[/] keyword provided remaining entries will be [bright_red]ignored[/]')
        render.econsole.print(_msg)
        if render.confirm(yes):
            resp = api.session.request(api.platform.disable_auto_subscribe, services=license.name)
            render.display_results(resp, tablefmt="action")
            return

    devices: list[CacheDevice] = [common.cache.get_dev_identifier(dev, include_inventory=True) for dev in devices]

    _msg = f"Unassign [bright_green]{license.value}[/bright_green] from"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([dev.summary_text for dev in devices])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.summary_text}"
    render.console.print(_msg, emoji=False)

    if render.confirm(yes):
        resp = api.session.request(api.platform.unassign_licenses, [d.serial for d in devices], services=license.name)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)  # exits if call failed to avoid cache update
        inv_devs = [{**d, "services": None} for d in devices]
        cache_resp = common.cache.InvDB.update_multiple([(dev, common.cache.Q.serial == dev["serial"]) for dev in inv_devs])
        if len(inv_devs) != len(cache_resp):
            log.warning(
                f'Inventory cache update may have failed.  Expected {len(inv_devs)} records to be updated, cache update resulted in {len(cache_resp)} records being updated'
                )


@app.command()
def label(
    label: str = typer.Argument(..., help="Label to remove from device(s)", autocompletion=common.cache.label_completion, show_default=False,),
    devices: list[str] = common.arguments.devices,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Unassign label from device(s)."""
    label: CacheLabel = common.cache.get_label_identifier(label)
    devices: list[CacheDevice] = [common.cache.get_dev_identifier(dev) for dev in devices]

    _msg = f"Unassign [bright_green]{label.name}[/bright_green] from"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([f'{dev.rich_help_text}' for dev in devices])
        _msg = f"{_msg}:\n    {_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.rich_help_text}"
    render.econsole.print(_msg)

    aps = [dev for dev in devices if dev.generic_type == "ap"]
    switches = [dev for dev in devices if dev.generic_type == "switch"]
    gws = [dev for dev in devices if dev.generic_type == "gw"]

    br = BatchRequest
    reqs = []
    for dev_type, devs in zip(["IAP", "SWITCH", "CONTROLLER"], [aps, switches, gws]):
        if devs:
            reqs += [br(api.central.remove_label_from_devices, label.id, serials=[dev.serial for dev in devs], device_type=dev_type)]

    if render.confirm(yes):
        resp = api.session.batch_request(reqs)
        render.display_results(resp, tablefmt="action")
        # we don't cache device/label associations (monitoring/.../aps doesn't provide it)


@app.callback()
def callback():
    """
    Unassign licenses / labels
    """
    pass


if __name__ == "__main__":
    app()
