#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from time import sleep
from typing import List

import typer
from rich import print
from rich.console import Console
from rich.progress import track

try:
    from fuzzywuzzy import process # type: ignore noqa
    FUZZ = True
except Exception:
    FUZZ = False
    pass

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, cleaner, render, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, cleaner, render, Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, lib_to_api
from centralcli.cache import CentralObject

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


def send_cmds_by_id(device: CentralObject, commands: List[int], pager: bool = False, outfile: Path = None) -> Response:
    console = Console(emoji=False)
    # dev = cli.cache.get_dev_identifier(device)
    _type = lib_to_api("tshoot", device.type)
    commands = utils.listify(commands)

    resp = cli.central.request(cli.central.start_ts_session, device.serial, dev_type=_type, commands=commands)
    cli.display_results(resp, tablefmt="action")

    complete = False
    while not complete:
        for x in range(3):
            with console.status("Waiting for Troubleshooting Response..."):
                sleep(10)
            ts_resp = cli.central.request(cli.central.get_ts_output, device.serial, resp.session_id)

            if ts_resp.output.get("status", "") == "COMPLETED":
                lines = "\n".join([line for line in ts_resp.output["output"].splitlines() if line != " "])
                print(lines) if not cli.raw_out else print(ts_resp.output["output"])
                complete = True
                break
            else:
                print(f'{ts_resp.output.get("message", " . ").split(".")[0]}. [cyan]Waiting...[/]')


        if not complete:
            print(f'[dark_orange3]WARNING[/] Central is still waiting on response from [cyan]{device.name}[/]')
            if not typer.confirm("Continue to wait/retry?"):
                cli.display_results(ts_resp, tablefmt="action", pager=pager, outfile=outfile)
                break

@app.command()
def ap_overlay(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show AP Overlay details

    [cyan]Returns the output of the following commands useful in troubleshooting overlay AP / gateway tunnels.[/]

    [cyan]-[/] show ata endpoint
    [cyan]-[/] show show overlay tunnel config
    [cyan]-[/] show overlay ssid-cluster status
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=("ap"))
    commands = [201, 203, 218]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def ap_dpi(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show DPI (valid on APs)

    [cyan]Returns the output of the following DPI related commands.[/]

    [cyan]-[/] show dpi-stats session
    [cyan]-[/] show dpi debug status
    [cyan]-[/] show datapath session dpi
    [cyan]-[/] show datapath dpi-classification-cache
    [cyan]-[/] show dpi-classification-cache
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=("ap"))
    commands = [190, 210, 211, 317, 318]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def inventory(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show Inventory (valid on Gateways)
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=("gw"))
    commands = [2013]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command(short_help="Ping a host from a Central managed device")
def ping(
    device: str = typer.Argument(..., metavar=iden_meta.dev, help="Aruba Central device to ping from", autocompletion=cli.cache.dev_completion),
    host: str = typer.Argument(..., help="host to ping (IP of FQDN)"),
    mgmt: bool = typer.Option(None, "-m", help="ping using VRF mgmt, (only applies to cx)"),
    repititions: int = typer.Option(None, "-r", help="repititions (only applies to switches)"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
        is_flag=True,
    ),
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
        if repititions:
            cmd_args["Repetitions"] = str(repititions)
        if dev.type == "cx" and mgmt:
            cmd_args["Is_Mgmt"] = str(mgmt)

    commands = {cmd_id: cmd_args}
    dev_type = lib_to_api("tshoot", dev.type)

    resp = cli.central.request(cli.central.start_ts_session, dev.serial, dev_type=dev_type, commands=commands)
    cli.display_results(resp, tablefmt="action", exit_on_fail=True)

    complete = False
    while not complete:
        for x in range(3):
            _delay = 15 if dev.type == "cx" else 10
            for _ in track(range(_delay), description=f"[green]Allowing time for commands to complete[/]..."):
                sleep(1)
            ts_resp = cli.central.request(cli.central.get_ts_output, dev.serial, resp.session_id)

            if ts_resp.output.get("status", "") == "COMPLETED":
                # if not verbose2:  # FIXME is verbose2 not working on any of these???
                if not cli.raw_out:
                    print(ts_resp.output["output"])
                else:
                    cli.display_results(resp)
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


def ts_send_command(device: CentralObject, cmd: str, outfile: Path, pager: bool,) -> None:
    """Helper command to send troubleshooting output (user provides command) and print results

    Args:
        device (CentralObject): Device Object
        cmd (str): User provided command
        outfile (Path): Optional output to file
        pager (bool): Optional Use Pager
    """
    console = Console(emoji=False)
    dev = cli.cache.get_dev_identifier(device)
    dev_type = lib_to_api("tshoot", dev.type)
    if len(cmd) == 1:
        cmd = cmd[0].split()
    cmd = " ".join(cmd)
    cmd = cmd.replace("  ", " ").strip().lower()
    resp = cli.central.request(cli.central.get_ts_commands, dev_type)
    if not resp:
        print('[bright_red]Unable to get troubleshooting command list')
        cli.display_results(resp)
    else:
        cmd_list = resp.output
        cmd_id = [c["command_id"] for c in cmd_list if c["command"].strip() == cmd]
        if not cmd_id:
            if FUZZ:
                fuzz_match, fuzz_confidence = process.extract(cmd, [c["command"].strip() for c in cmd_list], limit=1)[0]
                print(f"[bright_red]{cmd}[/] is not a valid troubleshooting command (supported by API) for {dev.type}.")
                confirm_str = render.rich_capture(f"Did you mean [green3]{fuzz_match}[/]?")
                if fuzz_confidence >= 70 and typer.confirm(confirm_str):
                    cmd_id = [c["command_id"] for c in cmd_list if c["command"].strip() == fuzz_match]

        if not cmd_id:
            caption = f'[bright_red]Error[/]: [cyan]{cmd}[/] not found in available troubleshooting commands for {dev.type}. See available commands above.'
            cli.display_results(resp, tablefmt="rich", caption=caption, title=f"Available troubleshooting commands for {dev.type}", cleaner=cleaner.show_ts_commands)
        else:
            resp = cli.central.request(cli.central.start_ts_session, dev.serial, dev_type=dev_type, commands=cmd_id)
            cli.display_results(resp, tablefmt="action", exit_on_fail=True)

            complete = False
            while not complete:
                for x in range(3):
                    with console.status("Waiting for Troubleshooting Response..."):
                        sleep(10)
                    ts_resp = cli.central.request(cli.central.get_ts_output, dev.serial, resp.session_id)

                    if ts_resp.output.get("status", "") == "COMPLETED":
                        console.print(ts_resp.output["output"])
                        complete = True
                        break
                    else:
                        print(f'{ts_resp.output.get("message", " . ").split(".")[0]}. [cyan]Waiting...[/]')


                if not complete:
                    print(f'[dark_orange3]WARNING[/] Central is still waiting on response from [cyan]{dev.name}[/]')
                    if not typer.confirm("Continue to wait/retry?"):
                        cli.display_results(ts_resp, tablefmt="action", pager=pager, outfile=outfile)
                        break

@app.command(short_help="Send troubleshooting command to a device")
def command(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    cmd: List[str] = typer.Argument(..., help="command to send to switch, must be supported by API.", show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """
    [cyan]Send a user provided troubleshooting commands to a device and wait for results.[/]

    Returns response (from device) to troubleshooting commands.
    Commands must be supported by the API, use [cyan]show tshoot commands <dev-type>[/] to see available commands
    """
    ts_send_command(device, cmd, outfile, pager)


@app.callback()
def callback():
    """
    Run Troubleshooting commands on devices
    """
    pass


if __name__ == "__main__":
    app()
