#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, cli
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (BlinkArgs, BounceArgs, IdenMetaVars, KickArgs, RenameArgs, arg_to_what) # noqa


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()


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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    # TODO add swarm cache and support for central.send_command_to_swarm
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    nuke_msg = f"{typer.style('*Factory Default*', fg='red')} {typer.style(f'{dev.name}|{dev.serial}', fg='cyan')}"
    if yes or typer.confirm(typer.style(f"Please Confirm: {nuke_msg}", fg="cyan"), abort=True):
        resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'erase_configuration')
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Save Device Running Config to Startup")
def save(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'config_sync')
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Move device to a defined group")
def move(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    group: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
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


@app.command(short_help="Rename a Group")
def rename(
    what: RenameArgs = typer.Argument(...,),
    group: str = typer.Argument(..., ),
    new_name: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    group = cli.cache.get_group_identifier(group)
    if yes or typer.confirm(typer.style(f"Please Confirm: rename group {group.name} -> {new_name}", fg="cyan")):
        resp = cli.central.request(cli.central.update_group_name, group.name, new_name)
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="kick a client (disconnect)",)
def kick(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    what: KickArgs = typer.Argument(...,),
    who: str = typer.Argument(None, help="[<mac>|<wlan/ssid>]",),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    if device in ["all", "mac", "wlan"]:
        typer.secho(f"Missing device parameter required before keyword {device}", fg="red")
        raise typer.Exit(1)
    dev = cli.cache.get_dev_identifier(device)
    if what == "mac":
        if not who:
            typer.secho("Missing argument <mac address>", fg="red")
            raise typer.Exit(1)
        mac = utils.Mac(who)
        who = mac.cols
        if not mac:
            typer.secho(f"{mac.orig} does not appear to be a valid mac address", fg="red")
            raise typer.Exit(1)

    _who = f" {who}" if who else " "
    if yes or typer.confirm(typer.style(f"Please Confirm: kick {what}{_who} on {dev.name}", fg="cyan")):
        resp = cli.central.request(
            cli.central.kick_users,
            dev.serial,
            kick_all=True if what == "all" else False,
            mac=None if what != "mac" else mac.cols,
            ssid=None if what != "wlan" else who,
            )
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.callback()
def callback():
    """
    Perform device / interface / client actions.
    """
    pass


if __name__ == "__main__":
    app()
