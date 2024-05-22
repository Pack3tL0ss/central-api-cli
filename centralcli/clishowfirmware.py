#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
import typer
import sys
from typing import List
from pathlib import Path
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, lib_to_api, DevTypes  # noqa
from centralcli.cache import CentralObject

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()



class ShowFirmwareKwags(str, Enum):
    group = "group"
    type = "type"


@app.command(short_help="Show firmware compliance details")
def compliance(
    device_type: DevTypes = typer.Argument(..., show_default=False,),
    group: List[str] = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion, show_default=False,),
    group_name: str = typer.Option(None, "--group", help="Filter by group", autocompletion=cli.cache.group_completion, show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", show_default=False, writable=True,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    """Show firmware compliance details for a group/device type
    """
    central = cli.central

    # Allows user to add unnecessary "group" keyword before the group
    if len(group) > 2:
        typer.echo(f"Unknown extra arguments in {[x for x in list(group)[0:-1] if x.lower() != 'group']}")
        raise typer.Exit(1)
    group = None if not group else group[-1]
    group = group or group_name
    if group:
        group: CentralObject = cli.cache.get_group_identifier(group)

    # TODO make device_type optional add 'all' keyword and implied 'all' if no device_type
    #      add macro method to get compliance for all device_types.
    kwargs = {
        'device_type': device_type,
        'group': group.name
    }

    resp = central.request(central.get_firmware_compliance, **kwargs)
    if resp.status == 404 and resp.output.lower() == "not found":
        resp.output = (
            f"Invalid URL or No compliance set for {device_type.lower()} "
            f"{'Globally' if group is None else f'in group {group.name}'}"
        )
        typer.echo(str(resp).replace("404", typer.style("404", fg="red")))
    else:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=f"{'Global ' if not group else f'{group.name} '}Firmware Compliance",
            pager=pager,
            outfile=outfile
        )

@app.command("list")
def _list(
    device: str = typer.Argument(None, help="Device to get firmware list for", metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    dev_type: DevTypes = typer.Option(None, help="Get firmware list for a device type", show_default=False,),
    swarm: bool = typer.Option(False, "--swarm", "-s", help="Get available firmware for IAP cluster associated with provided device", show_default=False,),
    swarm_id: str = typer.Option(None, help="Get available firmware for specified IAP cluster", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", show_default=False, writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Show available firmware list for a specific device or a type of device
    """
    dev: CentralObject = device if not device else cli.cache.get_dev_identifier(device, conductor_only=True,)
    _dev_type = dev_type if dev_type is None else lib_to_api("firmware", dev_type)

    # API-FLAW # HACK API at least for AOS10 APs returns Invalid Value for device <serial>, convert to --dev-type
    if dev and dev.type == "ap":
        if swarm:
            swarm_id = dev.swack_id
        else:
            dev_type = "ap"
            _dev_type = "IAP"
        dev = None

    kwargs = {
        "device_type": _dev_type,
        "swarm_id": swarm_id,
        "serial": None if dev is None else dev.serial
    }

    kwargs = utils.strip_none(kwargs)

    _error = ""
    if not kwargs:
        _error += "\n[dark_orange]:warning:[/]  [bright_red]Missing Argument / Option[/].  One of [cyan]<device(name|serial|mac|ip)>[/] (argument), [cyan]--dev-type <ap|gw|switch>[/], or [cyan]--swarm_id <id>[/] is required."
    elif len(kwargs) > 1:
        _error += "\n[dark_orange]:warning:[/]  [bright_red]Invalid combination[/] specify only [bold]one[/] of device (argument), --dev-type, [bold]OR[/] --swarm-id."
    if _error:
        print(_error)
        raise typer.Exit(1)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    title = f"Available firmware versions for {list(kwargs.keys())[0].replace('_', ' ')}: {list(kwargs.values())[0]}"
    if "device_type" in kwargs:
        title = f'{title.split(":")[0]} {dev_type}'
    elif dev:
        title = f'{title.split("serial")[0]} device [cyan]{dev.name}[/]'


    resp = cli.central.request(cli.central.get_fw_version_list, **kwargs)
    cli.display_results(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, cleaner=cleaner.get_fw_version_list, format=tablefmt)


@app.callback()
def callback():
    """
    Show Firmware / compliance details
    """
    pass


if __name__ == "__main__":
    app()
