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

from centralcli.constants import IdenMetaVars, lib_to_api  # noqa

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


class ShowFirmwareDevType(str, Enum):
    ap = "ap"
    # gateway = "gateway"
    gw = "gw"
    switch = "switch"


class ShowFirmwareKwags(str, Enum):
    group = "group"
    type = "type"


@app.command(short_help="Show firmware compliance details")
def compliance(
    device_type: ShowFirmwareDevType = typer.Argument(..., metavar="[ap|gw|switch]",),
    _group: List[str] = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    group_name: str = typer.Option(None, "--group", help="Filter by group", autocompletion=cli.cache.group_completion),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    central = cli.central
    cli.cache(refresh=update_cache)
    _type_to_name = {
        "AP": "IAP",
        "GATEWAY": "CONTROLLER",
        "GW": "CONTROLLER",
        "SWITCH": "HP"
    }
    # Allows both:
    # show firmware compliance <dev-type> <group iden>
    # show firmware compliance <dev-type> group <group iden>
    if len(_group) > 2:
        typer.echo(f"Unknown extra arguments in {[x for x in list(_group)[0:-1] if x.lower() != 'group']}")
        raise typer.Exit(1)
    _group = None if not _group else _group[-1]
    group = _group or group_name
    if group:
        group = cli.cache.get_group_identifier(group).name

    # TODO make device_type optional add 'all' keyword and implied 'all' if no device_type
    #      add macro method to get compliance for all device_types.
    kwargs = {
        'device_type': _type_to_name.get(device_type.upper(), device_type),
        'group': group
    }

    resp = central.request(central.get_firmware_compliance, **kwargs)
    if resp.status == 404 and resp.output.lower() == "not found":
        resp.output = (
            f"Invalid URL or No compliance set for {device_type.lower()} "
            f"{'Globally' if not group else f'in group {group}'}"
        )
        typer.echo(str(resp).replace("404", typer.style("404", fg="red")))
    else:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=f"{'Global ' if not group else f'{group} '}Firmware Compliance",
            pager=pager,
            outfile=outfile
        )

@app.command("list")
def _list(
    device: str = typer.Argument(None, help="Device to get firmware list for", metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
    dev_type: ShowFirmwareDevType = typer.Option(None, metavar="[ap|gw|switch]", help="Get firmware list for a device type (CX not suppoted, specify a CX device to see list)"),
    swarm_id: str = typer.Option(None, help="Get available firmware for IAP cluster.",),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Show available firmware list for a specific device or a type of device

    Note: Currently to get list for CX switches you need to specify a CX device.  --dev-type cx is not supported
    by the API endpoint yet.
    """
    dev = device if not device else cli.cache.get_dev_identifier(device)
    _dev_type = dev_type if dev_type is None else lib_to_api("firmware", dev_type)

    # HACK API at least for AOS10 APs returns Invalid Value for device <serial>, convert to --dev-type
    if dev and dev.type == "ap":
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
        _error += "\n[dark_orange]:warning:[/] Missing Argument / Option.  One of [cyan]<device(name|serial|mac|ip)>[/] (argument), [cyan]--dev-type <ap|gw|switch>[/], or [cyan]--swarm_id <id>[/] is required."
    elif len(kwargs) > 1:
        _error += "\n[dark_orange]:warning:[/] Invalid combination specify only [bold]one[/] of device (argument), --dev-type, [bold]OR[/] --swarm-id."
    if dev_type and dev_type == "cx":
        _error += "\nCX is not supported by the API Endpoint as device_type parameter.  To see available releases for CX provide as CX device as argument."
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
