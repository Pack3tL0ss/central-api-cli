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
from rich.console import Console
import typer
from typing import List

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

from centralcli.cache import CentralObject
cache = cli.cache

tty = utils.tty
iden = constants.IdenMetaVars()
app = typer.Typer()
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."

console = Console(emoji=False)


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
    import_file: str = cli.arguments.import_file,
    file: Path = typer.Option(None, help="Same as providing IMPORT_FILE argument", exists=True,),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Add VLAN from stored_tasks file.

    This is the same as `cencli batch add-vlan key`, but command: add_vlan
    is implied only need to provide key
    """
    import_file = file or import_file or config.stored_tasks_file
    if import_file == config.stored_tasks_file and not key:
        cli.exit("key is required when using the default import file")

    data = config.get_file_data(import_file)
    if key:
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


@app.command("batch")
def caas_batch(
    key: str = typer.Argument(None, help="The parent key in sthe stored-tasks file containing the arguments/options to supply to the command.", show_default=False,),
    file: Path = typer.Option(config.stored_tasks_file, exists=True,),
    command: str = typer.Option(None, help="The cencli batch command to run with the arguments/options from the stored-tasks file", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Run Supported caas commands providing parameters via stored-tasks file

    :warning:  [bright_red]Use Caution[/]  This command is not tested often, as other options are available to accomplish similar tasks.
        [dark_orange3 italic]Always test against non-production gear before production[/]
    This command is primarily used for demo/re-use of the other [cyan]cencli batch...[/] commands
    These commands can take a lot of arguments options.  This command allows you to store those
    arguments/options in a stored-tasks file (yaml/json).

    The [cyan]key[/] references the parent key in the stored-tasks file.
    Positional [cyan]arguments[/] for the command are provided via the [cyan]arguments[/] key.
    All options (command line flags in the form [cyan]--option-name[/]) are provided as key/value pairs under an [cyan]options[/] key.
    [cyan]-- OR --[/]
        To send commands to the GW.  Simply provide the list of commands under the [cyan]cmds[/] key.
        This implies [cyan]--command send-cmds[/]

    [bright_green]Examples[/]:
    [cyan]cencli caas test-acl /path/to/stored-tasks.yaml[/]

    [italic]Then within stored-tasks.yaml[/]
    test-acl:
      arguments:
        - 20:4C:03:AA:BB:CC
      cmds:
        - netdestination star-dot-facebook
        - name *.facebook.com
        - "!"
        - ip access-list session dmz-firewall
        - any alias star-dot-facebook any deny
        - any any any permit
        - "!"
        - user-role dmz-firewall-role
        - access-list session apprf-authenticated-sacl
        - access-list session ra-guard
        - access-list session dmz-firewall
        - "!"
    """
    caasapi = caas.CaasAPI(central=cli.central)
    if file == config.stored_tasks_file and not key:
        cli.exit("key is required when using the default import file")

    data = config.get_file_data(file)
    data = data.get(key, data)

    if not data:
        cli.exit(f"[cyan]{key}[/] not found in [cyan]{file}[/].  No Data to Process")
    else:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        cmds = data.get("cmds", [])

        if not args:
            cli.exit("import data requires an argument specifying the group / device")

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
                print("  [bold]cli cmds:[/]")
            _ = [print(f"    [cyan]{c}[/]") for c in cmds]
            if typer.confirm("Proceed:"):
                kwargs = {**kwargs, **{"cli_cmds": cmds}}
                resp = cli.central.request(caasapi.send_commands, *args, **kwargs)
                caas.eval_caas_response(resp)


@app.command()
def send_cmds(
    kw1: constants.SendCmdArgs = typer.Argument(
        ...,
        help="What to send the commands to, [grey42]use 'file' to send_cmds to nodes based on import file.[/]",
        show_default=False
    ),
    nodes: str = typer.Argument(
        None,
        autocompletion=cache.send_cmds_completion,
        help="The device/group/site identifier, [grey42]or 'all' for all gateways in the environment[/] :warning:  [bright_red]Use Caution[/]",
        metavar=iden.group_or_dev_or_site,
        show_default=False,
        # callback=cli.send_cmds_node_callback,
        # is_eager=True,
    ),
    kw2: str = typer.Argument(
        None,
        autocompletion=cache.send_cmds_completion,
        metavar="commands",
        show_default=False,
        # callback=cli.send_cmds_node_callback,
    ),
    commands: List[str] = typer.Argument(
        None,
        help="The commands to send.  ([grey42]space seperated, with each command wrapped in quotes[/]).",
        callback=cli.send_cmds_node_callback,
        show_default=False,
    ),
    cmd_file: Path = typer.Option(None, help="Path to file containing commands (1 per line) to be sent to device", exists=True, show_default=False,),
    all: bool = typer.Option(False, "-A", "--all", help="Send command(s) to all gateways (device level update) when group is provided"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Send commands to gateway(s) (group or device level)

    :warning:  [bright_red]Use Caution[/]
    Do not push to production without first testing in a lab.
    """
    commands = commands or []
    action = ""
    if kw1 == "group":
        if all:
            g = cache.get_group_identifier(nodes)
            nodes = [CentralObject("dev", d) for d in cache.devices if d["type"] == "gw" and d["group"] == g.name]
            action = f"all devices in {g.name} group."
        else:
            nodes = cache.get_group_identifier(nodes)
            action = f"group level gateway config for {nodes.name} group."
    elif kw1 == "site":
        s = cache.get_group_identifier(nodes)
        nodes = [CentralObject("dev", d) for d in cache.devices if d["type"] == "gw" and d["site"] == s.name]
        action = f"all devices in site: {s.name}"
    elif kw1 == "file":  # TODO break this out into sep func
        dev_file = Path(nodes)
        file_data = config.get_file_data(dev_file, text_ok=True)
        if not file_data:
            cli.exit(f"No data parsed from file {dev_file.name}.")

        if isinstance(file_data, list):
            nodes: List[CentralObject] = [cache.get_identifier(d.strip(), qry_funcs=["dev", "group", "site"], device_type="gw") for d in file_data]
        else:
            devices = file_data.get("devices", file_data.get("gateways"))
            if devices:
                nodes = [cache.get_identifier(d.strip(), ["dev", "group", "site"], device_type="gw") for d in file_data["devices"]]
            elif "groups" in file_data:
                nodes = [CentralObject("dev", d) for d in cache.devices if d["type"] == "gw" and d["group"] in file_data["groups"]]
            elif "sites" in file_data:
                nodes = [CentralObject("dev", d) for d in cache.devices if d["type"] == "gw" and d["site"] in file_data["sites"]]
            else:
                cli.exit(f"Expected 'gateways', 'groups', or 'sites' key in {dev_file.name}.")

            if "cmds" in file_data or "commands" in file_data:
                if commands:
                    cli.exit("Providing commands on the command line and in the import file is a strange thing to do.")

                commands = file_data.get("cmds", file_data.get("commands"))
        action = f'{", ".join(n.name for n in nodes)} defined in {dev_file.name}'
    elif kw1 == "device":
        if not isinstance(nodes, str):
            print(f"nodes is of type {type(nodes)} this is unexpected.")

        nodes: List[CentralObject] = [cache.get_identifier(nodes, qry_funcs=["dev"], device_type="gw")]
        action = f'{", ".join(n.name for n in nodes)}'

    if cmd_file:
        if commands:
            cli.exit("Providing commands on the command line and in the import file is a strange thing to do.")
        else:
            commands = [line.rstrip() for line in cmd_file.read_text().splitlines()]

    # TODO common command confirmation func
    if not commands:
        cli.exit("Error No commands provided")
    else:
        console.print(f"Sending the following to [cyan]{action}[/]")
        _ = [console.print(f"    [cyan]{c}[/]") for c in commands]

    if cli.confirm(yes):
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

@app.callback()
def callback():
    """
    Interact with Aruba Central CAAS API (Gateways)
    """
    pass


if __name__ == "__main__":
    app()
