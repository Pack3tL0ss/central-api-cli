#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

import typer

from centralcli import common, render
from centralcli.cache import CacheGroup, api
from centralcli.constants import DevTypes

app = typer.Typer()


# TODO validate if complaince can be set globally and refactor to allow without specifying group or by specifying "global"
@app.command()
def compliance(
    device_type: DevTypes = typer.Argument(
        ...,
        show_default=False,
    ),
    group: str = common.arguments.get("group", help="group to set complaince for"),
    version: str = typer.Argument(
        None,
        help="Version to set compliance to",
        show_default=False,
        autocompletion=lambda incomplete: [
            m for m in [
                ("<firmware version>", "The version of firmware to upgrade to."),
                *[m for m in common.cache.null_completion(incomplete)]
            ]
        ],
    ),
    at: datetime = common.options.get("at", help=f"When to schedule upgrade. {common.help_block('Now')}",),
    allow_unsupported: bool = typer.Option(False, "--allow-unsupported", "-u", help="Allow Unsupported (custom) version."),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download [green3](Only applies to Switches, others will reboot regardless)[/]", hidden=True),  # TODO why hidden?
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Set firmware compiance
    """
    group: CacheGroup = common.cache.get_group_identifier(group)
    at = None if not at else int(round(at.timestamp()))

    kwargs = {
        'device_type': device_type,
        'group': group.name,
        'version': version,
        'compliance_scheduled_at': at,
        'reboot': reboot,
        'allow_unsupported_version': allow_unsupported,
    }
    _type_to_msg = {
        "ap": "APs",
        "sw": "AOS-SW switches",
        "cx": "CX switches",
        "gw": "gateways"
    }
    _dev_msg = _type_to_msg.get(device_type, f"{device_type} devices")

    render.econsole.print(f'Set firmware complaince for [cyan]{_dev_msg}[/] in group [cyan]{group.name}[/] to [bright_green]{version}[/]')

    render.confirm(yes)
    resp = api.session.request(api.firmware.set_firmware_compliance, **kwargs)
    render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Set Firmware Compliance
    """
    pass


if __name__ == "__main__":
    app()
