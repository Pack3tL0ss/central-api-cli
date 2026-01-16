#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

import typer

from centralcli import api_clients, common, config, log, render, utils
from centralcli.cache import CacheDevice, CacheLabel, CacheSub
from centralcli.client import BatchRequest
from centralcli.constants import iden_meta
from centralcli.objects import DateTime

app = typer.Typer()


@app.command("subscription" if not config.glp.ok else "_subscription", hidden=config.glp.ok)
def classic_subscription(
    license: common.cache.LicenseTypes = typer.Argument(..., show_default=False),  # type: ignore
    devices: list[str] = common.arguments.devices,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover
    """Assign (or reassign) Licenses to devices by serial number(s).

    If multiple valid subscriptions of a given type exist.  The subscription with the longest term remaining will be assigned.

    [deep_sky_blue1]:information:[/]  Device must already be added to Central (GreenLake inventory).  Use '[cyan]cencli show inventory[/]' to see devices that have been added.
    Use '--sub' option with '[cyan]cencli add device ...[/]' to add device and assign subscription/license in one command.

    [deep_sky_blue1]:information:[/]  Use [cyan]cencli enable[/]|[cyan]disable auto-sub[/] to enable/disable auto subscription.
    """
    api = api_clients.classic
    _msg = f"Assign [bright_green]{license.value}[/bright_green] to"
    try:
        _serial_nums = [s if utils.is_serial(s) else common.cache.get_dev_identifier(s).serial for s in devices]
    except Exception:
        _serial_nums = devices
    _msg = f"{_msg} {utils.summarize_list(_serial_nums)}"

    render.econsole.print(_msg)
    render.confirm(yes)
    resp = api.session.request(api.platform.assign_licenses, _serial_nums, services=license.name)
    render.display_results(resp, tablefmt="action")
    # CACHE update cache for device after successful assignment


@app.command("subscription" if config.glp.ok else "_subscription", hidden=not config.glp.ok)
def glp_subscription(
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
    api = api_clients.glp
    if not api:  # pragma: no cover
        common.exit("This command uses [green]GreenLake[/] API endpoint, The configuration does not appear to have the details required.")

    sub: CacheSub = common.cache.get_sub_identifier(sub_name_or_id, end_date=end_date, best_match=True)  # TODO add qty param and return list of sub objects if best sub object can not satisfy the qty necessary
    if len(devices) > sub.available:
        log.warning(f"{len(devices)} devices exceeds {sub.available}... the number of available subscriptions for [bright_green]{sub.name}[/bright_green]|[medium_spring_green]{sub.key}[/].  [dim italic]As of last Subscription cache update[/]", show=True)

    _msg = f"Assign{'ing' if yes else ''} [bright_green]{sub.name}[/bright_green]|[medium_spring_green]{sub.key}[/], end date: [sea_green2]{DateTime(sub.end_date, format='date-string')}[/], and [cyan]{sub.available}[/] available subscriptions"

    devs = [r if utils.is_resource_id(r) else common.cache.get_combined_inv_dev_identifier(r, retry_dev=False, exit_on_dev_fail=False) for r in devices]
    res_ids = [d.id for d in devs]

    _msg = f"{_msg} to device:" if len(res_ids) == 1 else f"{_msg} to the following {len(res_ids)} devices:"
    _msg = f"{_msg} {utils.summarize_list([d.summary_text for d in devs], max=12)}"

    render.econsole.print(_msg)
    render.confirm(yes)
    resp = api.session.request(api.devices.update_devices, res_ids, subscription_ids=sub.id)
    render.display_results(resp, tablefmt="action")

    # UPDATE CACHE
    try:
        already_subscribed = len([dev for dev in devs if dev.subscription_key == sub.key])
        cache_update_data = [{**dict(dev), "services": sub.name, "subscription_expires": sub.end_date, "subscription_key": sub.key} for dev in devs]
        api.session.request(common.cache.update_inv_db, cache_update_data)
    except Exception as e:  # pragma: no cover
        already_subscribed = 0
        log.exception(
            f"{repr(e)} while trying to update inventory cache after subscription assignment(s)\n"
            "[deep_sky_blue]:information:[/]  Running [cyan]cencli show inventory[/]  Will refresh the inventory cache.",
            show=True
        )
    try:
        # API will return success even if the sub was already subscribed to the device.  So we evaluate cache and only subtract # of devs that were not already associated with the subscription
        # There is still potential for the cache to have an inaccurate available count if the cache was outdated, but unlikely and not a critical cache field anyway
        reduce_by = len(devs) - already_subscribed
        if reduce_by:
            sub_update_data = {**common.cache.subscriptions_by_key, sub.key: {**dict(sub), "available": sub.available - reduce_by}}
            api.session.request(common.cache.update_db, common.cache.SubDB, list(sub_update_data.values()))
    except Exception as e:  # pragma: no cover
        log.exception(
            f"{repr(e)} while trying to update subscription cache (increase available qty after sub(s) unassigned)\n"
            "[deep_sky_blue]:information:[/]  Running [cyan]cencli show subsciptions[/]  Will refresh the subscription cache.",
            show=True
        )



@app.command(name="label")
def label_(
    label: str = typer.Argument(..., metavar=iden_meta.label, help="Label to assign to device(s)", autocompletion=common.cache.label_completion, show_default=False,),
    devices: list[str] = common.arguments.devices,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Assign label to device(s)"""
    api = api_clients.classic
    label: CacheLabel = common.cache.get_label_identifier(label)
    devices: list[CacheDevice] = [common.cache.get_dev_identifier(dev) for dev in devices]

    _msg = f"Assign [bright_green]{label.name}[/bright_green] to"
    _msg = f"{_msg} {utils.summarize_list(devices, color=None)}"
    render.econsole.print(_msg, emoji=False)

    aps = [dev for dev in devices if dev.generic_type == "ap"]
    switches = [dev for dev in devices if dev.generic_type == "switch"]
    gws = [dev for dev in devices if dev.generic_type == "gw"]

    br = BatchRequest
    reqs = []
    for dev_type, devs in zip(["IAP", "SWITCH", "CONTROLLER"], [aps, switches, gws]):
        if devs:
            reqs += [br(api.central.assign_label_to_devices, label.id, serials=[dev.serial for dev in devs], device_type=dev_type)]

    render.confirm(yes)
    resp = api.session.batch_request(reqs)
    render.display_results(resp, tablefmt="action")
    # We don't cache device label assignments


@app.callback()
def callback():
    """Assign Subscriptions / labels"""
    pass


if __name__ == "__main__":
    app()
