#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uses caas api to send commands to devices

You can run the commands ad-hoc, or for more complex operations

you can store them in a file and import.  The file takes a similar format
as the command.  Default import file <config dir>/stored-tasks.yaml

EXAMPLES:
    cencli add-vlan <device> <pvid> <ip> <mask> [name] [description] ...

can be stored in yaml as

addvlan10:
  command: add-vlan
    args:
      - <device>
      - <pvid>
      - <ip>
      - <mask>
    options:
      name: myname
      description: mydescription

Then run via
  cencli batch add-vlan addvlan10  [--file <alternate import file>]

"""
# from enum import auto
from pathlib import Path
import sys
from threading import get_ident
from rich import print
import typer
from typing import List
from rich.console import Console

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, config, utils, caas, constants, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, config, utils, caas, constants, cleaner
    else:
        print(pkg_dir.parts)
        raise e

tty = utils.tty
iden = constants.IdenMetaVars()
app = typer.Typer()
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."


@app.command(short_help="Import Apply settings from bulk-edit.csv")
def bulk_edit(
    input_file: Path = typer.Argument(config.bulk_edit_file,),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    caasapi = caas.CaasAPI(central=cli.central)
    cmds = caasapi.build_cmds(file=input_file)
    # TODO log cli
    if cmds:
        typer.secho("Commands:", fg="bright_green")
        typer.echo("\n".join(cmds))
        if typer.confirm("Send Commands"):
            for dev in caasapi.data:
                group_dev = f"{caasapi.data[dev]['_common'].get('group')}/{dev}"
                resp = cli.central.request(caasapi.send_commands, group_dev, cmds)
                caas.eval_caas_response(resp)
        else:
            raise typer.Abort()


# FIXME
@app.command(hidden=True)
def add_vlan(
    group_dev: str = typer.Argument(...),
    pvid: str = typer.Argument(...),
    ip: str = typer.Argument(None),
    mask: str = typer.Argument("255.255.255.0"),
    name: str = None, description: str = None,
    interface: str = None,
    vrid: str = None,
    vrrp_ip: str = None,
    vrrp_pri: int = None,
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    caasapi = caas.CaasAPI(central=cli.central)
    cmds = []
    cmds += [f"vlan {pvid}", "!"]
    if name:
        cmds += [f"vlan-name {name}", "!", f"vlan {name} {pvid}", "!"]
    if ip:
        _fallback_desc = f"VLAN{pvid}-SVI"
        cmds += [f"interface vlan {pvid}", f"description {description or name or _fallback_desc}", f"ip address {ip} {mask}", "!"]
    if vrid:
        cmds += [f"vrrp {vrid}", f"ip address {vrrp_ip}", f"vlan {pvid}"]
        if vrrp_pri:
            cmds += [f"priority {vrrp_pri}"]
        cmds += ["no shutdown", "!"]

    resp = cli.central.request(caasapi.send_commands, group_dev, cmds)
    caas.eval_caas_response(resp)


@app.command(short_help="import VLAN from Stored Tasks File")
def import_vlan(
    key: str = typer.Argument(..., help="The Key from stored_tasks with vlan details to import"),
    import_file: str = typer.Argument(None, exists=True),
    file: Path = typer.Option(None, exists=True,),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    """Add VLAN from stored_tasks file.

    This is the same as `cencli batch add-vlan key`, but command: add_vlan
    is implied only need to provide key

    """
    import_file = file or import_file or config.stored_tasks_file
    if import_file == config.stored_tasks_file and not key:
        typer.echo("key is required when using the default import file")

    data = config.get_file_data(import_file)
    if key:
        if hasattr(data, "dict"):  # csv
            data = data.dict  # TODO not tested in csv form
            data = {k: data[k] for k in data if data.get("key", "") == key}
        else:
            data = data.get(key)

    if data:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        _msg = (
            f"\n{typer.style('add-vlan', fg='bright_green')}"
            f'\n{typer.style("  settings:", fg="cyan")}'
            f"\n    args: {', '.join(args)}\n    kwargs: {', '.join([f'{k}={v}' for k, v in kwargs.items()])}"
        )
        typer.echo(f"{_msg}")
        confirm_msg = typer.style("Proceed?", fg="bright_green")
        if typer.confirm(confirm_msg):
            add_vlan(*args, **kwargs)
        else:
            raise typer.Abort()
    else:
        typer.secho(f"{key} Not found in {import_file}")
        raise typer.Exit(1)


@app.command("batch", short_help="Run Supported caas commands providing parameters via stored-tasks file")
def caas_batch(
    key: str = typer.Argument(None,),
    file: Path = typer.Option(config.stored_tasks_file, exists=True,),
    command: str = typer.Option(None,),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    """cencli caas batch add-vlan add-vlan-99"""
    caasapi = caas.CaasAPI(central=cli.central)
    if file == config.stored_tasks_file and not key:
        typer.echo("key is required when using the default import file")
        raise typer.Exit(1)

    data = config.get_file_data(file)
    if hasattr(data, "dict"):  # csv
        data = data.dict
        data = {k: data[k] for k in data if data.get("key", "") == key}
    else:
        data = data.get(key)

    if not data:
        _msg = typer.style(f"{key} not found in {file}.  No Data to Process", fg="red")
        typer.echo(_msg)
    else:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        cmds = data.get("cmds", [])

        if not args:
            typer.secho("import data requires an argument specifying the group / device")
            raise typer.Exit(1)

        if command:
            command = command.replace('-', '_')
            _msg1 = typer.style(
                f"Proceed with {command}:",
                fg="cyan"
            )
            _msg2 = f"{', '.join(args)} {', '.join([f'{k}={v}' for k, v in kwargs.items()])}"
            confirm_msg = typer.style(f"{_msg1} {_msg2}?", fg="bright_green")

            if command in globals():
                fn = globals()[command]
                if typer.confirm(confirm_msg):
                    fn(*args, **kwargs)  # type: ignore # NoQA
                else:
                    raise typer.Abort()
            else:
                typer.echo(f"{command} doesn't appear to be valid")

        elif cmds:
            kwargs = {**kwargs, **{"cli_cmds": cmds}}
            resp = cli.central.request(caasapi.send_commands, *args, **kwargs)
            caas.eval_caas_response(resp)


@app.command(help="Send commands to gateway(s) (group or device level)", short_help="Send commands to gateways", hidden=True)
def send_cmds(
    device: str = typer.Argument(
        None,
        autocompletion=cli.cache.dev_gw_completion,
        hidden=True,
        is_eager=True,
    ),
    commands: List[str] = typer.Argument(None),
    cmd_file: Path = typer.Option(None, help="Path to file containing commands (1 per line) to be sent to device", exists=True),
    dev_file: Path = typer.Option(None, help="Path to file containing iden for devices to send commands to", exists=True),
    # devices: List[str] = typer.Option(
    #     None,
    #     metavar=iden.dev,
    #     autocompletion=cli.cache.dev_gw_completion,
    #     help="Gateways to send commands to",
    #     is_eager=True,
    # ),
    group: str = typer.Option(None, help="Send commands to all gateways in a group", autocompletion=cli.cache.group_completion),
    site: str = typer.Option(None, help="Send commands to all gateways in a site", autocompletion=cli.cache.site_completion),
    # file: Path = typer.Option(None, exists=True,),
    # all: bool = typer.Option(False, "--all", help="Send command to all gateways in the site or group.  Requires --site or --group option"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    console = Console(emoji=False)
    yes = yes if yes else yes_
    commands = commands or []
    if dev_file and device:
        commands.insert(0, device)
        device = None
    elif group or site and device:
        commands = [device, *commands]
        device = None
    # devices = devices if devices else device
    error = None
    if not commands and (not cmd_file and dev_file and not device):
        error = "Error: No commands provided, provide as arguments or with --cmd-file <Path> option."
    elif commands and cmd_file:
        error = "Invalid combination, provide commands as arguments or --cmd-file <path> not both."
    if all([x is None for x in [device, dev_file, group, site]]):
        error = "Error: You must provide one --device --dev-file <Path> --group <group> --site <site>"
    if site and group:
        error = "Error: Invalid combination, provide only 1 of --site <site> --group <group>"

    if error:
        print(error)
        raise typer.Exit(1)

    # Determine devices to send commands to.
    all_group, all_site = False, False
    if dev_file:
        devices = [
            cli.cache.get_dev_identifier(d, dev_type="gw") for d in dev_file.read_text().splitlines()
        ]
    if device:
        # devices = [cli.cache.get_dev_identifier(d, dev_type="gw") for d in devices]
        devices = [cli.cache.get_dev_identifier(device, dev_type="gw")]
    if group:
        group = cli.cache.get_group_identifier(group)
        devices = [d for d in cli.cache.devices if d["type"] == "gw" and d["group"] == group.name]
        all_group = True
        # if devices:
        #     devices = [d for d in devices if d.group == group.name]
        # else:
        #     devices = [d for d in cli.cache.devices if d.generic_type == "gw" and d.group == group.name]
        #     all_group = True
    if site:
        site = cli.cache.get_site_identifier(site)
        devices = [d for d in cli.cache.devices if d["type"] == "gw" and d["site"] == site.name]
        all_site = True
        # if devices:
        #     devices = [d for d in devices if d.site == site.name]
        # else:
        #     devices = [d for d in cli.cache.devices if d.generic_type == "gw" and d.site == site.name]
        #     all_site = True

    if not devices:
        print(f"Error: This command has a logic error, no devices based on current options")
        raise typer.Exit(1)

    if cmd_file:
        commands = cmd_file.read_text().splitlines()

    _cmds = "\n".join(commands)
    console.print()
    console.rule(f"Sending the following commands")
    console.print(f"[bright_green]{_cmds}")
    console.rule()
    if all_group:
        print(f"To all {len(devices)} gateways in {group.name} group.")
    elif all_site:
        print(f"To all {len(devices)} gateways in {site.name} branch.")
    else:
        print(f"\nTo the following {len(devices)} Gateways")
        print(
            "\n".join([f"[cyan]{d.name}[/cyan]|{typer.unstyle(d.help_text).replace('GW|', '')}" for d in devices])
        )
    if yes or typer.confirm("\nProceed?", abort=True):
        caasapi = caas.CaasAPI(central=cli.central)
        _reqs = [cli.central.BatchRequest(caasapi.send_commands, dev["mac"], cli_cmds=commands) for dev in devices]
        batch_res = cli.central.batch_request(_reqs)
        cli.display_results(batch_res, cleaner=cleaner.parse_caas_response)
        # caas.
        # Rich progress bar here


@app.callback()
def callback():
    """
    Interact with Aruba Central CAAS API (Gateways)
    """
    pass


if __name__ == "__main__":
    app()
