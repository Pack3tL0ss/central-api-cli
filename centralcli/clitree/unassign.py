#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

import typer

from centralcli import api_clients, common, log, render, utils
from centralcli.cache import CacheDevice, CacheLabel, CacheSub
from centralcli.client import BatchRequest
from centralcli.constants import iden_meta
from centralcli.objects import DateTime

app = typer.Typer()
api = api_clients.classic
glp_api = api_clients.glp


# TOGLP
@app.command(deprecated=True, hidden=glp_api is not None)
def license(
    license: common.cache.LicenseTypes = typer.Argument(..., help="License type to unassign from device(s).", show_default=False),  # type: ignore
    devices: list[str] = typer.Argument(..., help="device serial numbers or 'auto' to disable auto-subscribe.", metavar=f"{iden_meta.dev_many} or 'auto'", autocompletion=common.cache.dev_completion, show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover
    """Unssign Licenses from devices by serial number(s) or disable auto-subscribe for the license type.

    :warning:  This command is deprecated, and will be replaced by [cyan]unassign subscription[/] which is available now if Greenlake (glp)
    details are provided in the config.
    """
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


@app.command(hidden=not glp_api)
def subscription(
    sub_name_or_id: str = typer.Argument(..., help="subscription id or key from [cyan]cencli show subscriptions[/] output, or the subscription name [dim italic](i.e.: advanced-ap)[/]", autocompletion=common.cache.sub_completion, show_default=False),  # type: ignore
    devices: list[str] = common.arguments.get("devices", help="device serial numbers [dim italic](can use name/ip/mac if device has connected to Central)[/]"),
    end_date: datetime = common.options.get("end", help=f"Select subscription with this expiration date [dim italic](24 hour format, Time not required, will select subscription that expires on the date provided)[/] {common.help_block('The subscription with the most time remaining will be selected')}",),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Unassign subscription from device(s) by serial number(s).

    :warning:  Removing a subscription from a device will eventually cause it to disconnect from Aruba Central.
    :information: It is not necessary to unassign the existing subscription if the goal is to assign a different subscription.
    This can be done in one step using [cyan]assign subscription[/] or [cyan]batch assign subscriptions[/]
    """
    if not glp_api:  # pragma: no cover
        common.exit("This command uses [green]GreenLake[/] API endpoint, The configuration does not appear to have the details required.")

    sub: CacheSub = common.cache.get_sub_identifier(sub_name_or_id, end_date=end_date)
    _msg = f"Unassign{'ing' if yes else ''} [bright_green]{sub.name}[/bright_green]|[medium_spring_green]{sub.key}[/], end date: [sea_green2]{DateTime(sub.end_date, format='date-string')}[/], and [cyan]{sub.available}[/] available subscriptions"

    devs = [r if utils.is_resource_id(r) else common.cache.get_combined_inv_dev_identifier(r) for r in devices]
    res_ids = [d.id for d in devs]

    _msg = f"{_msg} from device:" if len(res_ids) == 1 else f"{_msg} from the following {len(res_ids)} devices:"
    _msg = f"{_msg} {utils.summarize_list([d.summary_text for d in devs], max=12)}"
    render.econsole.print(_msg)
    render.confirm(yes)
    resp = glp_api.session.request(glp_api.devices.update_devices, res_ids, subscription_ids=None)
    render.display_results(resp, tablefmt="action")
    # CACHE update available subs in sub cache


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

    render.confirm(yes)
    resp = api.session.batch_request(reqs)
    render.display_results(resp, tablefmt="action")
    # we don't cache device/label associations (monitoring/.../aps doesn't provide it)


@app.callback()
def callback():
    """
    Unassign Subscriptions / labels
    """
    pass


if __name__ == "__main__":
    app()
