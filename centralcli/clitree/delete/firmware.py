#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import typer

from centralcli import common, render
from centralcli.cache import CacheGroup, api
from centralcli.constants import DevTypes

app = typer.Typer()

@app.command()
def compliance(
    device_type: DevTypes = typer.Argument(..., show_default=False,),
    group: list[str] = common.arguments.get("group", default=None, help=f"[red1]Delete[/] compliance for group {common.help_block('Global Compliance')}"),
    group_: str = common.options.get("group", "--group", "-G", help=f"[red1]Delete[/] compliance for group {common.help_block('Global Compliance')}"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete/Clear firmware compliance
    """
    # TODO is global complaince really a thing?  API returns 404 with no group

    # All this is to allow either group as argument or as flag --group|-G
    group = group or []
    group_ = [] if not group_ else [group_]
    group = [*group, *group_]

    if group:
        if len(group) > 1:
            common.exit(f"Unknown extra arguments in {[x for x in list(group)[0:-1] if x.lower() != 'group']}")
        group = group[-1]
        group: CacheGroup = common.cache.get_group_identifier(group)

    kwargs = {
        'device_type': device_type,
        'group': None if not group else group.name
    }

    _type_to_msg = {
        "ap": "APs",
        "sw": "AOS-SW switches",
        "cx": "CX switches",
        "gw": "gateways"
    }
    _dev_msg = _type_to_msg.get(device_type, f"{device_type} devices")

    render.econsole.print(f"Delet{'e' if not yes else 'ing'} firmware complaince for [cyan]{_dev_msg}[/] {'Globally' if not group else f'in group [cyan]{group.name}[/]'}")

    render.confirm(yes)
    resp = api.session.request(api.firmware.delete_firmware_compliance, **kwargs)
    if resp.status == 404:
        resp.output = (
            f"Invalid URL or No compliance set for {device_type.lower()} "
            f"{'Globally' if not group else f'in group {group.name}'}"
        )

    render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Remove Firmware Compliance
    """
    pass


if __name__ == "__main__":
    app()
