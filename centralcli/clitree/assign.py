#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

import typer

from centralcli import common, log, render, utils
from centralcli.cache import CacheDevice, CacheLabel, CacheSub
from centralcli.clicommon import APIClients
from centralcli.client import BatchRequest
from centralcli.constants import iden_meta
from centralcli.objects import DateTime

api_clients = APIClients()
api = api_clients.classic
glp_api = api_clients.glp

app = typer.Typer()


# TODO consider removing auto option as we've added enable/disable auto-sub ...
# TODO update cache for device after successful assignment
# TOGLP
@app.command(deprecated=True, hidden=glp_api is not None)
def license(
    license: common.cache.LicenseTypes = typer.Argument(..., show_default=False),  # type: ignore
    devices: list[str] = typer.Argument(..., metavar=iden_meta.dev_many, help="device serial numbers or 'auto' to enable auto-subscribe.", show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover
    """Assign (or reassign) Licenses to devices by serial number(s) or enable auto-subscribe for the license type.

    :warning:  This command is deprecated, and will be replaced by [cyan]assign subscription[/] which is available now if Greenlake (glp)
    details are provided in the config.

    If multiple valid subscriptions of a given type exist.  The subscription with the longest term remaining will be assigned.

    Device must already be added to Central.  Use '[cyan]cencli show inventory[/]' to see devices that have been added.
    Use '--license' option with '[cyan]cencli add device ...[/]' to add device and assign license in one command.
    """
    # TODO add confirmation method builder to output class
    do_auto = True if "auto" in [s.lower() for s in devices] else False
    if do_auto:
        _msg = f"Enable Auto-assignment of [bright_green]{license.value}[/bright_green] to applicable devices."
        if len(devices) > 1:
            render.econsole.print('[cyan]auto[/] keyword provided remaining entries will be [bright_red]ignored[/]')
    else:
        _msg = f"Assign [bright_green]{license.value}[/bright_green] to"
        try:
            _serial_nums = [s if utils.is_serial(s) else common.cache.get_dev_identifier(s).serial for s in devices]
        except Exception:
            _serial_nums = devices
        if len(_serial_nums) > 1:
            _dev_msg = '\n    '.join([f'[cyan]{dev}[/]' for dev in _serial_nums])
            _msg = f"{_msg}:\n    {_dev_msg}"
        else:
            dev = _serial_nums[0]
            _msg = f"{_msg} [cyan]{dev}[/]"

    render.econsole.print(_msg)
    if render.confirm(yes):
        if not do_auto:
            resp = api.session.request(api.platform.assign_licenses, _serial_nums, services=license.name)
        else:
            resp = api.session.request(api.platform.enable_auto_subscribe, services=license.name)

        render.display_results(resp, tablefmt="action")
        # TODO cache update similar to batch unsubscribe


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
    """Assign (or reassign) Subscription to devices by serial number(s).

    Device must exist in [green]GreenLake[/] inventory.  Use '[cyan]cencli show inventory[/]' to see devices that have been added.
    Use '--sub' option with '[cyan]cencli add device ...[/]' to add device and assign subscription in one command.
    """
    if not glp_api:  # pragma: no cover
        common.exit("This command uses [green]GreenLake[/] API endpoint, The configuration does not appear to have the details required.")

    sub: CacheSub = common.cache.get_sub_identifier(sub_name_or_id, end_date=end_date)
    if len(devices) > sub.available:
        log.warning(f"{len(devices)} devices exceeds {sub.available}... the number of available subscriptions for [bright_green]{sub.name}[/bright_green]|[medium_spring_green]{sub.key}[/].  [dim italic]As of last Subscription cache update[/]", show=True)

    _msg = f"Assign{'ing' if yes else ''} [bright_green]{sub.name}[/bright_green]|[medium_spring_green]{sub.key}[/], end date: [sea_green2]{DateTime(sub.end_date, format='date-string')}[/], and [cyan]{sub.available}[/] available subscriptions"

    devs = [r if utils.is_resource_id(r) else common.cache.get_combined_inv_dev_identifier(r) for r in devices]
    res_ids = [d.id for d in devs]

    _msg = f"{_msg} to device:" if len(res_ids) == 1 else f"{_msg} to the following {len(res_ids)} devices:"
    _msg = f"{_msg} {utils.summarize_list([d.summary_text for d in devs], max=12)}"
    render.econsole.print(_msg)
    if render.confirm(yes):
        resp = glp_api.session.request(glp_api.devices.update_devices, res_ids, subscription_ids=sub.id)
        render.display_results(resp, tablefmt="action")


@app.command(name="label")
def label_(
    label: str = typer.Argument(..., metavar=iden_meta.label, help="Label to assign to device(s)", autocompletion=common.cache.label_completion, show_default=False,),
    devices: list[str] = common.arguments.devices,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    "Assign label to device(s)"
    label: CacheLabel = common.cache.get_label_identifier(label)
    devices: list[CacheDevice] = [common.cache.get_dev_identifier(dev) for dev in devices]

    _msg = f"Assign [bright_green]{label.name}[/bright_green] to"
    _msg = f"{_msg} {utils.summarize_list([dev.summary_text for dev in devices], color=None)}"
    render.econsole.print(_msg, emoji=False)

    aps = [dev for dev in devices if dev.generic_type == "ap"]
    switches = [dev for dev in devices if dev.generic_type == "switch"]
    gws = [dev for dev in devices if dev.generic_type == "gw"]

    br = BatchRequest
    reqs = []
    for dev_type, devs in zip(["IAP", "SWITCH", "CONTROLLER"], [aps, switches, gws]):
        if devs:
            reqs += [br(api.central.assign_label_to_devices, label.id, serials=[dev.serial for dev in devs], device_type=dev_type)]

    if render.confirm(yes):
        resp = api.session.batch_request(reqs)
        render.display_results(resp, tablefmt="action")
        # We don't cache device label assignments


@app.callback()
def callback():
    """Assign Subscriptions / labels"""
    pass


if __name__ == "__main__":
    app()
