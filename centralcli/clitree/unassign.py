#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import typer

from centralcli import api_clients, common, log, render, utils, config
from centralcli.cache import CacheDevice, CacheInvMonDevice, CacheLabel
from centralcli.client import BatchRequest
from centralcli.constants import iden_meta

app = typer.Typer()
api = api_clients.classic

sub_help = """Unssign Licenses from devices by serial number(s).

    :warning:  Removing a subscription from a device will eventually cause it to disconnect from Aruba Central.
    :information: It is not necessary to unassign the existing subscription if the goal is to assign a different subscription.
    This can be done in one step using [cyan]assign subscription[/] or [cyan]batch assign subscriptions[/]
"""

@app.command("subscription" if not config.glp.ok else "_subscription", hidden=config.glp.ok, help=sub_help)
def classic_subscription(
    subscription: common.cache.LicenseTypes = typer.Argument(..., help="License type to unassign from device(s).", show_default=False),  # type: ignore
    devices: list[str] = typer.Argument(..., help="device serial numbers or 'auto' to disable auto-subscribe.", metavar=f"{iden_meta.dev_many} or 'auto'", autocompletion=common.cache.dev_completion, show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    devices: list[CacheInvMonDevice] = [common.cache.get_combined_inv_dev_identifier(dev, retry_dev=False) for dev in devices]
    word = "device" if len(devices) == 1 else f"{len(devices)} devices"
    _msg = f"Unassign [bright_green]{subscription.value}[/bright_green] from {word}:\n    {utils.summarize_list(devices, color=None).lstrip()}"

    render.console.print(_msg, emoji=False)
    render.confirm(yes)
    resp = api.session.request(api.platform.unassign_licenses, [d.serial for d in devices], services=subscription.name)
    render.display_results(resp, tablefmt="action", exit_on_fail=True)  # exits if call failed to avoid cache update

    # cache updates
    inv_devs = [{**d, "services": None} for d in devices]
    api.session.request(common.cache.update_inv_db, inv_devs)



@app.command("subscription" if config.glp.ok else "_subscription", hidden=not config.glp.ok, help=sub_help)
def glp_subscription(
    devices: list[str] = common.arguments.get("devices", help="device serial numbers [dim italic](can use name/ip/mac if device has connected to Central)[/]"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    glp_api = api_clients.glp
    if not glp_api:  # pragma: no cover
        common.exit("This command uses [green]GreenLake[/] API endpoint, The configuration does not appear to have the details required.")

    _msg = f"[red]Unassign{'ing' if yes else ''}[/] current subscription"

    devs = [r if utils.is_resource_id(r) else common.cache.get_combined_inv_dev_identifier(r, retry_dev=False) for r in devices]  # TODO assign has exit_on_fail=False... test to see impact add coverage for partial failure (some devs not found in inv or dev cache)
    res_ids = [d.id for d in devs]

    _msg = f"{_msg} from device:" if len(res_ids) == 1 else f"{_msg} from the following {len(res_ids)} devices:"
    _msg = f"{_msg} {utils.summarize_list([d.summary_text for d in devs], max=12)}"
    _msg += f"\n[dark_orange3]:warning:[/]  [italic][red bold blink]This will result in {'devices' if len(res_ids) > 1 else 'the device'} disconnecting from[/] [dark_orange3]Aruba Central[/][/italic][bright_red]:bangbang:[/]  [dark_orange3]:warning:[/]"

    render.econsole.print(_msg)
    render.confirm(yes)
    resp = glp_api.session.request(glp_api.devices.update_devices, res_ids, subscription_ids=None)
    render.display_results(resp, tablefmt="action")

    # UPDATE CACHE
    # CACHE # TODO Need batch assign and batch unassign to also get cache update.  Likely refactor to send this (and assign) to common batch_[un]assign_subscriptions (with cache update) or break below out to common sub update funcs in clicommon
    try:
        cache_update_data = [{**dict(dev), "services": None, "subscription_expires": None, "subscription_key": None} for dev in devs]
        glp_api.session.request(common.cache.update_inv_db, cache_update_data)
    except Exception as e:  # pragma: no cover
        log.exception(
            f"{repr(e)} while trying to update inventory cache after subscription unassignment(s)",
            "[deep_sky_blue]:information:[/]  Running [cyan]cencli show inventory[/]  Will refresh the inventory cache.",
            show=True
        )

    try:
        sub_keys = [d.subscription_key for d in devs if d.subscription_key is not None]
        if sub_keys:
            unique_sub_keys = utils.unique(sub_keys)
            cache_subs = common.cache.subscriptions_by_key
            sub_update_data = {**common.cache.subscriptions_by_key, **{k: {**dict(cache_subs[k]), "available": cache_subs[k].available + sub_keys.count(k)} for k in unique_sub_keys}}
            glp_api.session.request(common.cache.update_db, common.cache.SubDB, list(sub_update_data.values()))
        else:  # pragma: no cover
            ...
    except Exception as e:  # pragma: no cover
        log.exception(
            f"{repr(e)} while trying to update subscription cache (increase available qty after sub(s) unassigned)"
            "[deep_sky_blue]:information:[/]  Running [cyan]cencli show subsciptions[/]  Will refresh the subscription cache.",
            show=True
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
