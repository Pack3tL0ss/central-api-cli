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
      name: my_name
      description: my_description

Then run via
  cencli batch add-vlan addvlan10  [--file <alternate import file>]

"""
# from enum import auto
from pathlib import Path
import sys
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

cache = cli.cache

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
        print("[bright_red]ERROR:[/] key is required when using the default import file")
        raise typer.Exit(1)

    data = config.get_file_data(file)
    if hasattr(data, "dict"):  # csv
        data = data.dict
        data = {k: data[k] for k in data if data.get("key", "") == key}
    else:
        data = data.get(key)

    if not data:
        print(f"[bright_red]ERROR:[/] [cyan]{key}[/] not found in [cyan]{file}[/].  No Data to Process")
        raise typer.Exit(1)
    else:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        cmds = data.get("cmds", [])

        if not args:
            print("[bright_red]ERROR:[/] import data requires an argument specifying the group / device")
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
            print(f"\nSending the following to [cyan]{utils.unlistify(args)}[/]")
            if kwargs:
                print("\n  With the following options:")
                _ = [print(f"    {k} : {v}") for k, v in kwargs.items()]
                print(f"  [bold]cli cmds:[/]")
            _ = [print(f"    [cyan]{c}[/]") for c in cmds]
            if typer.confirm("Proceed:"):
                kwargs = {**kwargs, **{"cli_cmds": cmds}}
                resp = cli.central.request(caasapi.send_commands, *args, **kwargs)
                caas.eval_caas_response(resp)



    # Determine devices to send commands to.
    # if dev_file:
    #     devices = [
    #         cache.get_dev_identifier(d, dev_type="gw") for d in dev_file.read_text().splitlines()
    #     ]
    #     if node:
    #         devices += [cache.get_dev_identifier(node)]
    # elif node:
    #     devices = [cache.get_dev_identifier(node, dev_type="gw")]

    # if group:
    #     group = cache.get_group_identifier(group)
    #     if all:
    #         devices = [cache.CentralObject(d) for d in cache.devices if d["type"] == "gw" and d["group"] == group.name]
    #         action = f"all devices in {group.name} group."
    #     elif devices:
    #         devices = [d for d in devices if d.group == group.name]
    #         action = "\n".join(node)
    #     else:
    #         devices = [group.name]
    # elif site:
    #     site = cache.get_site_identifier(site)
    #     if all:
    #         devices = [cache.CentralObject(d) for d in cache.devices if d["type"] == "gw" and d["site"] == site.name]
    #     elif devices:
    #         devices = [d for d in devices if d.site == site.name]

@app.command(help="Send commands to gateway(s) (group or device level)", short_help="Send commands to gateways", hidden=False,)
def send_cmds(
    kw1: constants.SendCmdArgs = typer.Argument(
        ...,
    ),
    nodes: str = typer.Argument(
        None,
        autocompletion=cache.send_cmds_completion,
        metavar=iden.group_or_dev_or_site,
        # callback=cli.send_cmds_node_callback,
        # is_eager=True,
    ),
    kw2: str = typer.Argument(
        None,
        autocompletion=cache.send_cmds_completion,
        # callback=cli.send_cmds_node_callback,
    ),
    commands: List[str] = typer.Argument(None, callback=cli.send_cmds_node_callback),
    cmd_file: Path = typer.Option(None, help="Path to file containing commands (1 per line) to be sent to device", exists=True),
    # dev_file: Path = typer.Option(None, help="Path to file containing iden for devices to send commands to", exists=True),
    # group: bool = typer.Option(None, help="Send commands to all gateways in a group", autocompletion=cli.cache.group_completion),
    # site: bool = typer.Option(None, help="Send commands to all gateways in a site", autocompletion=cli.cache.site_completion),
    all: bool = typer.Option(False, "-A", help="Send command(s) to all gateways (device level update) when group is provided"),
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
    if kw1 == "group":
        if all:
            g = cache.get_group_identifier(nodes)
            nodes = [cache.CentralObject(d) for d in cache.devices if d["type"] == "gw" and d["group"] == g.name]
            action = f"all devices in {g.name} group."
        else:
            nodes = cache.get_group_identifier(nodes)
            action = f"group level gateway config for {nodes.name} group."
    elif kw1 == "site":
        s = cache.get_group_identifier(nodes)
        nodes = [cache.CentralObject(d) for d in cache.devices if d["type"] == "gw" and d["site"] == s.name]
        action = f"all devices in site: {s.name}"
    elif kw1 == "file":
        dev_file = Path(nodes)
        file_data = config.get_file_data(dev_file, text_ok=True)
        if not file_data:
            print(f"No data parsed from file {dev_file.name}.")
            raise typer.Exit(1)

        if isinstance(file_data, list):
            nodes = [cache.get_identifier(d.strip(), ["dev", "group", "site"], device_type="gw") for d in file_data]
        else:
            devices = file_data.get("devices", file_data.get("gateways"))
            if devices:
                nodes = [cache.get_identifier(d.strip(), ["dev", "group", "site"], device_type="gw") for d in file_data["devices"]]
            elif "groups" in file_data:
                nodes = [cache.CentralObject(d) for d in cache.devices if d["type"] == "gw" and d["group"] in file_data["groups"]]
            elif "sites" in file_data:
                nodes = [cache.CentralObject(d) for d in cache.devices if d["type"] == "gw" and d["site"] in file_data["sites"]]
            else:
                print(f"Expected 'gateways', 'groups', or 'sites' key in {dev_file.name}.")
                raise typer.Exit(1)

            if "cmds" in file_data or "commands" in file_data:
                if commands:
                    print("Providing commands on the command line and in the import file is a strange thing to do.")
                    raise typer.Exit(1)
                commands = file_data.get("cmds", file_data.get("commands"))
    elif kw1 == "device":
        if not isinstance(nodes, str):
            print(f"nodes is of type {type(nodes)} this is unexpected.")

        nodes = [cache.get_identifier(nodes, ["dev"], "gw")]

    if cmd_file:
        if commands:
            print("Providing commands on the command line and in the import file is a strange thing to do.")
            raise typer.Exit(1)
        else:
            commands = [line.rstrip() for line in cmd_file.read_text().splitlines()]

    if not commands:
        print("Error No commands provided")
        raise typer.Exit(1)

    if yes or typer.confirm("\nProceed?", abort=True):
        caasapi = caas.CaasAPI(central=cli.central)
        _reqs = [
            cli.central.BatchRequest(
                caasapi.send_commands,
                n.name if not n.is_dev else n.mac,
                cli_cmds=commands
            )
            for n in utils.listify(nodes)
        ]
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
