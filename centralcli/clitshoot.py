#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from time import sleep

import typer
from rich import print
from rich.console import Console

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, lib_to_api

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


# TODO AP only completion
@app.command(short_help="Show AP Overlay details")
def ap_overlay(
    device: str = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    console = Console(emoji=False)
    dev = cli.cache.get_dev_identifier(device, dev_type=("ap"))
    commands = [201, 203, 218]
    resp = cli.central.request(cli.central.start_ts_session, dev.serial, dev_type="IAP", commands=commands)
    cli.display_results(resp, tablefmt="action")

    complete = False
    while not complete:
        for x in range(3):
            with console.status("Waiting for Troubleshooting Response..."):
                sleep(10)
            ts_resp = cli.central.request(cli.central.get_ts_output, dev.serial, resp.session_id)

            if ts_resp.output.get("status", "") == "COMPLETED":
                print(ts_resp.output["output"])
                complete = True
                break
            else:
                print(f'{ts_resp.output.get("message", " . ").split(".")[0]}. [cyan]Waiting...[/]')


        if not complete:
            print(f'[dark_orange3]WARNING[/] Central is still waiting on response from [cyan]{dev.name}[/]')
            if not typer.confirm("Continue to wait/retry?"):
                cli.display_results(ts_resp, tablefmt="action", pager=pager, outfile=outfile)
                break


@app.command(short_help="Ping a host from a Central managed device")
def ping(
    device: str = typer.Argument(..., metavar=iden_meta.dev, help="Aruba Central device to ping from", autocompletion=cli.cache.dev_completion),
    host: str = typer.Argument(..., help="host to ping (IP of FQDN)"),
    mgmt: bool = typer.Option(None, "-m", help="ping using VRF mgmt, (only applies to cx)"),
    repititions: int = typer.Option(3, "-r", help="repititions (only applies to switches)"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    command_ids = {
        "ap": 165,
        "gw": 2369,
        "cx": 6006,
        "sw": 1036
    }
    console = Console()
    dev = cli.cache.get_dev_identifier(device)
    cmd_id = command_ids[dev.type]
    cmd_args = {"Host": host}

    if dev.generic_type == "switch":
        cmd_args["Repititions"] = str(repititions)
        if dev.type == "cx" and mgmt:
            cmd_args["Is_Mgmt"] = True

    commands = {cmd_id: cmd_args}
    dev_type = lib_to_api("tshoot", dev.type)

    resp = cli.central.request(cli.central.start_ts_session, dev.serial, dev_type=dev_type, commands=commands)
    cli.display_results(resp, tablefmt="action", exit_on_fail=True)

    complete = False
    while not complete:
        for x in range(3):
            with console.status("Waiting for Troubleshooting Response..."):
                sleep(10)
            ts_resp = cli.central.request(cli.central.get_ts_output, dev.serial, resp.session_id)

            if ts_resp.output.get("status", "") == "COMPLETED":
                print(ts_resp.output["output"])
                complete = True
                break
            else:
                print(f'{ts_resp.output.get("message", " . ").split(".")[0]}. [cyan]Waiting...[/]')


        if not complete:
            console.print(f'[dark_orange3]:warning: WARNING[/] Central is still waiting on response from [cyan]{dev.name}[/]')
            console.print(f"Use [cyan]cencli show tshoot {dev.name} {resp.session_id}[/] after some time, or continue to check for response now.")
            if not typer.confirm("Continue to wait/retry?"):
                cli.display_results(ts_resp, tablefmt="action", pager=pager, outfile=outfile)
                break


@app.callback()
def callback():
    """
    Run Troubleshooting commands on devices
    """
    pass


if __name__ == "__main__":
    app()
