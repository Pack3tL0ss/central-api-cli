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
    _type = lib_to_api("tshoot", device.type)
    commands = utils.listify(commands)

    resp = cli.central.request(cli.central.start_ts_session, device.serial, dev_type=_type, commands=commands)
    cli.display_results(resp, tablefmt="action")

    if not resp:
        return

    complete = False
    while not complete:
        for x in range(3):
            _delay = 15 if device.type == "cx" else 10
            for _ in track(range(_delay), description="[green]Allowing time for commands to complete[/]..."):
                sleep(1)

            ts_resp = cli.central.request(cli.central.get_ts_output, device.serial, resp.session_id)

            if ts_resp.output.get("status", "") == "COMPLETED":
                lines = "\n".join([line for line in ts_resp.output["output"].splitlines() if line != " "])
                ts_resp.raw = ts_resp.output["output"]
                ts_resp.output = lines
                show_tech_ap = [115, 369, 465]
                tablefmt = "clean" if sorted(commands) != show_tech_ap else "raw"

                cli.display_results(ts_resp, pager=pager, outfile=outfile, tablefmt=tablefmt)
                complete = True
                break
            else:
                print(f'{ts_resp.output.get("message", " . ").split(".")[0]}. [cyan]Waiting...[/]')


        if not complete:
            print(f'[dark_orange3]WARNING[/] Central is still waiting on response from [cyan]{device.name}[/]')
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
    dev: CentralObject = cli.cache.get_dev_identifier(device)
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
            send_cmds_by_id(dev, commands=cmd_id, pager=pager, outfile=outfile)

@app.command()
def overlay(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_sw_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show GW or AP Overlay details (Tunneled SSIDs) or AOS-SW User Based Tunneling  (valid on AP, GW, and AOS-SW)

    [cyan]Returns the output of the following commands useful in troubleshooting overlay AP / gateway / ubt tunnels.[/]

    [bright_green]APs[/]
    [cyan]-[/] show ata current-cfg
    [cyan]-[/] show overlay tunnel config
    [cyan]-[/] show ata endpoint
    [cyan]-[/] show crypto ipsec stats
    [cyan]-[/] show datapath bridge
    [cyan]-[/] show overlay ssid-cluster status

    [bright_green]GWs[/]
    [cyan]-[/] show aruba-central control-channel
    [cyan]-[/] show show aruba-central control-channel-counters
    [cyan]-[/] show crypto oto
    [cyan]-[/] show crypto ipsec
    [cyan]-[/] show crypto-local ipsec-map
    [cyan]-[/] show tunnelmgr tunnel-list
    [cyan]-[/] show tunnelmgr counters

    [bright_green]AOS-SW (User Based Tunneling)[/]
    [cyan]-[/] show tunneled-node-server
    [cyan]-[/] show tunneled node server state
    [cyan]-[/] show tunneled node server statistics
    [cyan]-[/] show tunneled-node-users all
    """
    ids_by_dev_type = {
        "ap": [208, 203, 201, 300, 39, 218],
        "gw": [2452, 2515, 2453, 2131, 2441, 2454, 2455],
        "sw": [1189, 1195, 1196, 1191]
    }
    dev = cli.cache.get_dev_identifier(device, dev_type=["ap", "gw", "sw"])

    commands = ids_by_dev_type[dev.type]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)

@app.command()
def clients(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_sw_completion, show_default=False,),
    wired: bool = typer.Option(False, "-w", "--wired", help="Include [cyan]show clients wired[/] (applies to AP)",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show output of client related commands  (valid on AP, GW, and AOS-SW)

    [cyan]Returns the output of the following client related commands. Valid for AP, GW, and AOS-SW.[/]

    [bright_green]APs[/]
    [cyan]-[/] show clients
    [cyan]-[/] show clients debug advanced
    [cyan]-[/] show datapath user

    Use of [cyan]--wired[/] option will also include
    [cyan]-[/] show clients wired


    [bright_green]GWs[/]
    [cyan]-[/] show user-table verbose
    [cyan]-[/] show datapath user table

    [bright_green]AOS-SW[/]
    [cyan]-[/] show port-access clients
    [cyan]-[/] show port-access summary
    """
    ids_by_dev_type = {
        "ap": [117, 257, 47],
        "sw": [1028, 1089],
        "gw": [2163, 2095],
    }
    dev: CentralObject = cli.cache.get_dev_identifier(device, dev_type=["ap", "gw", "sw"])

    commands = ids_by_dev_type[dev.type]
    if wired:
        if dev.type == "ap":
            commands += [123]
        else:
            print(f":warning:  [cyan]--wired[/] flag ignored, only applies to APs, not {dev.type}.")

    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def dpi(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show DPI output (valid on APs and GWs)

    [cyan]Returns the output of the following DPI related commands.[/]

    [bright_green]APs[/]
    [cyan]-[/] show dpi-stats session
    [cyan]-[/] show dpi debug status
    [cyan]-[/] show datapath session dpi
    [cyan]-[/] show datapath dpi-classification-cache
    [cyan]-[/] show dpi-classification-cache

    [bright_green]GWs[/]
    [cyan]-[/] show datapath session dpi table
    [cyan]-[/] show datapath session dpi counters
    [cyan]-[/] show dpi application all
    """
    ids_by_dev_type = {
        "ap": [190, 210, 211, 317, 318],
        "gw": [2394, 2395, 2553]
    }
    dev: CentralObject = cli.cache.get_dev_identifier(device, dev_type=("ap", "gw"))
    commands = ids_by_dev_type[dev.type]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def ssid(
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
    """Show output of commands to help troubleshoot SSIDs/broadcasting (APs Only)

    [cyan]Returns the output of the following commands.[/]

    [cyan]-[/] show aps
    [cyan]-[/] show ap bss-table
    [cyan]-[/] show cluster bss-table
    [cyan]-[/] show ap-env
    """
    dev: CentralObject = cli.cache.get_dev_identifier(device, dev_type=("ap"))
    commands = [4, 24, 177, 53]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def show_tech(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show Tech Support

    [cyan]Returns the output of show tech.[/]

    [cyan]-[/] APs include show tech-support supplemental and show tech-support memory.
    """
    dev: CentralObject = cli.cache.get_dev_identifier(device)
    ids_by_dev_type = {
        "ap": [115, 369, 465],
        "sw": [1032],
        "gw": [2408],
        "cx": [6001]
    }
    commands = ids_by_dev_type[dev.type]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def images(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_sw_completion, show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
):
    """Show image versions (Valid for AP, GW, and AOS-SW)

    [cyan]Returns the output of the following image related commands.[/]

    [bright_green]APs[/]
    [cyan]-[/] show version
    [cyan]-[/] show image version

    [bright_green]GWs[/]
    [cyan]-[/] show version
    [cyan]-[/] show image version

    [bright_green]AOS-SW[/]
    [cyan]-[/] show flash
    """
    dev: CentralObject = cli.cache.get_dev_identifier(device, dev_type=["ap", "gw", "sw"])

    ids_by_dev_type = {
        "ap": [119, 213],
        "gw": [2002, 2007],
        "sw": [1046]
    }
    commands = ids_by_dev_type[dev.type]
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
    repititions: int = typer.Option(None, "-r", help="repititions (only applies to AOS-SW)"),
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
            for _ in track(range(_delay), description="[green]Allowing time for commands to complete[/]..."):
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

    [bright_green]Example:[/] [cyan]cencli tshoot command barn.518.2816-ap show ap-env[/]
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
