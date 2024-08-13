#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
import sys
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

from centralcli.constants import IdenMetaVars, DevTypes # noqa

iden = IdenMetaVars()
app = typer.Typer()


# TODO validate if complaince can be set globally and refactor to allow without specifying group or by specifying "global"
@app.command()
def compliance(
    device_type: DevTypes = typer.Argument(
        ...,
        show_default=False,
    ),
    group: str = typer.Argument(
        ...,
        metavar=iden.group,
        help="group to set complaince for",
        autocompletion=cli.cache.group_completion,
        show_default=False,
    ),
    version: str = typer.Argument(
        None,
        help="Version to set compliance to",
        show_default=False,
        autocompletion=lambda incomplete: [
            m for m in [
                ("<firmware version>", "The version of firmware to upgrade to."),
                *[m for m in cli.cache.null_completion(incomplete)]
            ]
        ],
    ),
    at: datetime = typer.Option(
        None,
        help="When to schedule upgrade. format: 'mm/dd/yyyy_hh:mm' or 'dd_hh:mm' (implies current month) [default: Now]",
        show_default=False,
        formats=["%m/%d/%Y_%H:%M", "%d_%H:%M"],
        ),
    allow_unsupported: bool = typer.Option(False, "--allow-unsupported", "-U", help="Allow Unsupported (custom) version."),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download [green3](Only applies to MAS, others will reboot regardless)[/]", hidden=True),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Set firmware compiance
    """
    group = cli.cache.get_group_identifier(group)
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

    print(f'Set firmware complaince for [cyan]{_dev_msg}[/] in group [cyan]{group.name}[/] to [bright_green]{version}[/]')

    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.set_firmware_compliance, **kwargs)
        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Set Firmware Compliance
    """
    pass


if __name__ == "__main__":
    app()
