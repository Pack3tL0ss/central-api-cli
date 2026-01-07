#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import partial
from pathlib import Path
from time import sleep
from typing import Any

import typer
from rich.progress import track

from centralcli import api_clients, cleaner, common, render, utils
from centralcli.cache import CacheDevice
from centralcli.constants import iden_meta, lib_to_api

try:
    from fuzzywuzzy import process  # type: ignore noqa
    FUZZ = True
except Exception:  # pragma: no cover
    FUZZ = False


api = api_clients.classic
app = typer.Typer()
typer.Argument = partial(typer.Argument, show_default=False)
typer.Option = partial(typer.Option, show_default=False)


def send_cmds_by_id(device: CacheDevice, commands: list[int] | list[dict[str, Any]] | dict[str, Any], pager: bool = False, outfile: Path = None, exit_on_fail: bool = False) -> None:
    _type = lib_to_api(device.type, "tshoot")
    commands = utils.listify(commands)

    resp = api.session.request(api.tshooting.start_ts_session, device.serial, device_type=_type, commands=commands)
    render.display_results(resp, tablefmt="action", exit_on_fail=exit_on_fail)

    if not resp:
        return  # TODO verify implications of removing exit_on_fail and always letting display_results exit if POST fails here.

    complete = False
    while not complete:
        for _ in range(3):
            _delay = 15 if device.type == "cx" else 10
            for _ in track(range(_delay), description="[green]Allowing time for commands to complete[/]..."):
                sleep(1)

            ts_resp = api.session.request(api.tshooting.get_ts_output, device.serial, resp.session_id)

            if ts_resp.output.get("status", "") == "COMPLETED":
                lines = "\n".join([line for line in ts_resp.output["output"].splitlines() if line != " "])
                ts_resp.raw = ts_resp.output["output"]
                ts_resp.output = lines
                show_tech_ap = [115, 369, 465]
                tablefmt = "clean" if sorted(commands) != show_tech_ap else "raw"

                render.display_results(ts_resp, pager=pager, outfile=outfile, tablefmt=tablefmt)
                complete = True
                break
            else:
                render.econsole.print(f'{ts_resp.output.get("message", " . ").split(".")[0]}. [cyan]Waiting...[/]')


        if not complete:  # pragma: no cover requires tty
            render.econsole.print(f'[dark_orange3]:warning:[/] Central is still waiting on response from [cyan]{device.name}[/]')
            if not render.confirm(prompt="Continue to wait/retry?", abort=False):
                render.display_results(ts_resp, tablefmt="action", pager=pager, outfile=outfile)
                break

    if exit_on_fail:
        common.exit(code=0 if complete else 1)

def ts_send_command(device: CacheDevice, cmd: list[str], outfile: Path, pager: bool,) -> None:
    """Helper command to send troubleshooting output (user provides command) and print results

    Args:
        device (CacheDevice): Device Object
        cmd (list[str]): User provided command
        outfile (Path): Optional output to file
        pager (bool): Optional Use Pager
    """
    dev: CacheDevice = common.cache.get_dev_identifier(device)
    dev_type = lib_to_api(dev.type, "tshoot")
    if all(c.isdigit() for c in cmd):  # allows user to enter cmd id from show ts commands output.
        send_cmds_by_id(dev, commands=[int(c) for c in cmd], pager=pager, outfile=outfile, exit_on_fail=True)
    if len(cmd) == 1:
        cmd = cmd[0].split()
    cmd = " ".join(cmd)
    cmd = cmd.replace("  ", " ").strip().lower()
    resp = api.session.request(api.tshooting.get_ts_commands, dev_type)
    if not resp:
        render.econsole.print('[dark_orange3]:warning:[/]  [bright_red]Unable to get troubleshooting command list')
        render.display_results(resp, exit_on_fail=True)
    else:
        cmd_list = resp.output
        cmd_id = [c["command_id"] for c in cmd_list if c["command"].strip() == cmd]
        if not cmd_id:
            if FUZZ:  # pragma: no cover requires tty
                fuzz_match, fuzz_confidence = process.extract(cmd, [c["command"].strip() for c in cmd_list], limit=1)[0]
                render.econsole.print(f"[bright_red]{cmd}[/] is not a valid troubleshooting command (supported by API) for {dev.type}.")
                if fuzz_confidence >= 70 and render.confirm(prompt=f"Did you mean [green3]{fuzz_match}[/]?", abort=False):
                    cmd_id = [c["command_id"] for c in cmd_list if c["command"].strip() == fuzz_match]

        if not cmd_id:
            caption = [
                f'[dark_orange3]\u26a0[/]  [bright_red]Error[/]: [cyan]{cmd}[/] not found in available troubleshooting commands for [cyan]{dev.type}[/].',
                '[bright_green]See available commands above.[/]'
            ]
            render.display_results(resp, caption=caption, title=f"Available troubleshooting commands for {dev.type}", cleaner=cleaner.show_ts_commands)
            common.exit(code=1)
        else:
            send_cmds_by_id(dev, commands=cmd_id, pager=pager, outfile=outfile, exit_on_fail=True)

@app.command()
def overlay(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_gw_sw_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
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
    dev = common.cache.get_dev_identifier(device, dev_type=["ap", "gw", "sw"])

    commands = ids_by_dev_type[dev.type]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)

@app.command()
def clients(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_gw_sw_completion, show_default=False,),
    wired: bool = typer.Option(False, "-w", "--wired", help="Include [cyan]show clients wired[/] (applies to AP)",),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
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
    dev: CacheDevice = common.cache.get_dev_identifier(device, dev_type=["ap", "gw", "sw"])

    commands = ids_by_dev_type[dev.type]
    if wired:
        if dev.type == "ap":
            commands += [123]
        else:
            render.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]--wired[/] flag ignored, only applies to APs, not {dev.type}.")

    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def dpi(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_gw_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
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
    dev: CacheDevice = common.cache.get_dev_identifier(device, dev_type=("ap", "gw"))
    commands = ids_by_dev_type[dev.type]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def ssid(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show output of commands to help troubleshoot SSIDs/broadcasting (APs Only)

    [cyan]Returns the output of the following commands.[/]

    [cyan]-[/] show aps
    [cyan]-[/] show ap bss-table
    [cyan]-[/] show cluster bss-table
    [cyan]-[/] show ap-env
    """
    dev: CacheDevice = common.cache.get_dev_identifier(device, dev_type=("ap"))
    commands = [4, 24, 177, 53]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def mesh(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show output of commands to help troubleshoot Mesh/Bridge links (APs Only)

    [cyan]Returns the output of the following commands.[/]

    [cyan]-[/] show ap mesh link
    [cyan]-[/] show ap mesh neighbours
    [cyan]-[/] show ap mesh counters
    [cyan]-[/] show ap mesh cluster active
    [cyan]-[/] show ap mesh cluster configuration
    [cyan]-[/] show ap mesh cluster topology
    [cyan]-[/] show ap mesh cluster status
    [cyan]-[/] show ap mesh debug status
    """
    dev: CacheDevice = common.cache.get_dev_identifier(device, dev_type=("ap"))
    commands = [87, 88, 86, 468, 469, 470, 471, 472]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def show_tech(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show Tech Support

    Returns the output of show tech.

    [cyan]-[/] APs include show tech-support supplemental and show tech-support memory.
    """
    dev: CacheDevice = common.cache.get_dev_identifier(device)
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
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_gw_sw_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
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
    dev: CacheDevice = common.cache.get_dev_identifier(device, dev_type=["ap", "gw", "sw"])

    ids_by_dev_type = {
        "ap": [119, 213],
        "gw": [2002, 2007],
        "sw": [1046]
    }
    commands = ids_by_dev_type[dev.type]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def inventory(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_gw_completion, show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show Inventory (valid on Gateways)
    """
    dev = common.cache.get_dev_identifier(device, dev_type=("gw"))
    commands = [2013]
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


@app.command()
def ping(
    device: str = common.arguments.get("device", help="Aruba Central device to ping from",),
    host: str = typer.Argument(..., help="host to ping (IP or FQDN)"),
    mgmt: bool = typer.Option(None, "-m", help="ping using VRF mgmt, (only applies to cx)"),
    repititions: int = typer.Option(None, "-r", help="repititions (only applies to AOS-SW)"),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Ping a host from a Central managed device."""
    command_ids = {
        "ap": 165,
        "gw": 2369,
        "cx": 6006,
        "sw": 1036
    }
    dev = common.cache.get_dev_identifier(device)
    cmd_id = command_ids[dev.type]
    cmd_args = {"Host": host}

    if dev.generic_type == "switch":
        if repititions:
            cmd_args["Repetitions"] = str(repititions)
        if dev.type == "cx" and mgmt:
            cmd_args["Is_Mgmt"] = str(mgmt)

    commands = {cmd_id: cmd_args}
    send_cmds_by_id(dev, commands=commands, pager=pager, outfile=outfile)


# API-FLAW gw returns a success response with no task_id, aos8 ap returns success with task_id but call to /device_management/v1/status/{task_id} just returns success lacks the actual details
@app.command(hidden=True)  # hidden due to above
def speed_test(
    device: str = typer.Argument(..., metavar=iden_meta.dev, help="Aruba Central device to run speedtest from", autocompletion=common.cache.dev_ap_gw_completion),
    host: str = typer.Argument("ndt-iupui-mlab1-den04.mlab-oti.measurement-lab.org", help="speedtest host (IP of FQDN)"),
    options: str = typer.Option(None, "-o", help="Formatted string of optional arguments"),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):  # pragma: no cover  Useless given API flaw noted above
    """Initiate a speedtest from a device (Gateways and AOS8 IAP)."""
    dev = common.cache.get_dev_identifier(device)
    if dev.type == "ap" and dev.is_aos10:
        common.exit("This command is not supported on AOS10 APs")
    if dev.type not in ["ap", "gw"]:
        common.exit(f"This command is supported on Gateways and AOS8 IAP not {dev.type}")

    resp = api.session.request(api.device_management.run_speedtest, dev.serial, host=host, options=options)
    render.display_results(resp, tablefmt="action", exit_on_fail=True)


@app.command()
def command(
    device: str = common.arguments.device,
    cmd: list[str] = typer.Argument(..., help="command to send to switch, must be supported by API.", show_default=False,),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
):
    """
    Send user provided troubleshooting commands to a device and wait for the results.

    Returns response (from device) to troubleshooting commands.
    :information:  Commands must be supported by the API, use [cyan]cencli show ts commands <dev-type>[/] to see available commands

    [bright_green]Example:[/] [cyan]cencli ts command barn.518.2816-ap show ap-env[/]
    """
    ts_send_command(device, cmd, outfile, pager)


@app.command()
def clear(
    device: str = common.arguments.device,
    session_id: str = common.arguments.session_id,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
):
    """Clear previously ran troubleshooting session and output for a device."""
    dev = common.cache.get_dev_identifier(device)
    session_id = session_id or dev.get_ts_session_id()
    resp = api.session.request(api.tshooting.clear_ts_session, dev.serial, session_id=session_id)
    render.display_results(resp, tablefmt="action", outfile=outfile, pager=pager)


@app.callback()
def callback():
    """Run Troubleshooting commands on devices."""
    ...


if __name__ == "__main__":
    app()
