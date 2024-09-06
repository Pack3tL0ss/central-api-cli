#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print
from typing import List


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

from centralcli.constants import DevTypes # noqa
from centralcli.cache import CentralObject

app = typer.Typer()

@app.command(short_help="Delete/Clear firmware compliance")
def compliance(
    device_type: DevTypes = typer.Argument(..., show_default=False,),
    group: List[str] = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    group_name: str = typer.Option(None, "--group", help="Filter by group", autocompletion=cli.cache.group_completion),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Delete/Clear firmware compliance
    """
    # TODO is global complaince really a thing?  API returns 404 with no group
    # Allows user to add unnecessary "group" keyword before the group
    if group and len(group) > 2:
        typer.echo(f"Unknown extra arguments in {[x for x in list(group)[0:-1] if x.lower() != 'group']}")
        raise typer.Exit(1)

    group = None if not group else group[-1]
    group = group or group_name
    if group:
        group: CentralObject = cli.cache.get_group_identifier(group)

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

    print(f"Delete firmware complaince for [cyan]{_dev_msg}[/] {'Globally?' if not group else f'in group [cyan]{group.name}[/]'}")

    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.delete_firmware_compliance, **kwargs)
        if resp.status == 404 and resp.output.lower() == "not found":
            resp.output = (
                f"Invalid URL or No compliance set for {device_type.lower()} "
                f"{'Globally' if not group else f'in group {group.name}'}"
            )
            typer.echo(str(resp).replace("404", typer.style("404", fg="red")))
        else:
            cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Remove Firmware Compliance
    """
    pass


if __name__ == "__main__":
    app()
