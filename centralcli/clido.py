#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, cli, cliupdate
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, cli, cliupdate
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (BlinkArgs, BounceArgs, arg_to_what) # noqa


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()
app.add_typer(cliupdate.app, name="update")


@app.command(short_help="Bounce Interface or PoE on Interface")
def bounce(
    what: BounceArgs = typer.Argument(...),
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    port: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    command = 'bounce_poe_port' if what == 'poe' else 'bounce_interface'
    if yes or typer.confirm(typer.style(f"Please Confirm bounce {what} on {dev.name} port {port}", fg="cyan")):
        resp = cli.central.request(cli.central.send_bounce_command_to_device, dev.serial, command, port)
        typer.secho(str(resp), fg="green" if resp else "red")
        # !! removing this for now Central ALWAYS returns:
        # !!   reason: Sending command to device. state: QUEUED, even after command execution.
        # if resp and resp.get('task_id'):
        #     resp = cli.central.request(session.get_task_status, resp.task_id)
        #     typer.secho(str(resp), fg="green" if resp else "red")

    else:
        raise typer.Abort()


@app.command(short_help="Reboot a device")
def reboot(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    reboot_msg = f"{typer.style('*reboot*', fg='red')} {typer.style(f'{dev.name}|{dev.serial}', fg='cyan')}"
    if yes or typer.confirm(typer.style(f"Please Confirm: {reboot_msg}", fg="cyan")):
        resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'reboot')
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="Blink LED")
def blink(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    action: BlinkArgs = typer.Argument(..., ),  # metavar="Device: [on|off|<# of secs to blink>]"),
    secs: int = typer.Argument(None, metavar="SECONDS", help="Blink for _ seconds."),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    command = f'blink_led_{action}'
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, command, duration=secs)
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Factory Default A Device")
def nuke(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    nuke_msg = f"{typer.style('*Factory Default*', fg='red')} {typer.style(f'{dev.name}|{dev.serial}', fg='cyan')}"
    if yes or typer.confirm(typer.style(f"Please Confirm: {nuke_msg}", fg="cyan")):
        resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'erase_configuration')
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="Save Device Running Config to Startup")
def save(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'save_configuration')
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Sync/Refresh device config with Aruba Central")
def sync(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'config_sync')
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Update existing or add new Variables for a device/template")
def update_vars(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    var_value: List[str] = typer.Argument(..., help="comma seperated list 'variable = value, variable2 = value2'"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    serial = dev.serial
    vars, vals, get_next = [], [], False
    for var in var_value:
        if var == '=':
            continue
        if '=' not in var:
            if get_next:
                vals += [var]
                get_next = False
            else:
                vars += [var]
                get_next = True
        else:
            _ = var.split('=')
            vars += _[0]
            vals += _[1]
            get_next = False

    if len(vars) != len(vals):
        typer.secho("something went wrong parsing variables.  Unequal length for Variables vs Values")
        raise typer.Exit(1)

    var_dict = {k: v for k, v in zip(vars, vals)}

    typer.secho(f"Please Confirm: Update {dev.name}|{dev.serial}", fg="cyan")
    [typer.echo(f'    {k}: {v}') for k, v in var_dict.items()]
    if typer.confirm(typer.style("Proceed with these values", fg="cyan")):
        resp = cli.central.request(cli.central.update_variables, serial, **var_dict)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Move device to a defined group")
def move(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    group: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    group = cli.cache.get_group_identifier(group)
    if yes or typer.confirm(typer.style(f"Please Confirm: move {dev.name} to group {group.name}", fg="cyan")):
        resp = cli.central.request(cli.central.move_dev_to_group, group.name, dev.serial)
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="kick a client (disconnect)")
def kick(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'save_configuration')
    typer.secho(str(resp), fg="green" if resp else "red")


@app.callback()
def callback():
    """
    Perform device / interface / client actions.
    """
    pass


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == 'show':
        sys.argv[2] = arg_to_what(sys.argv[2])

    app()
