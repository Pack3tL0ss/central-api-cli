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
from pathlib import Path
from typing import List

import typer
from rich import print
from rich.console import Console

from centralcli import caas, cache, cleaner, common, config, constants, render, utils
from centralcli.cache import CacheDevice, CacheGroup, CacheSite, api
from centralcli.client import BatchRequest

iden_meta = constants.iden_meta

app = typer.Typer()
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."

console = Console(emoji=False)


@app.command()
def bulk_edit(
    input_file: Path = typer.Argument(config.bulk_edit_file,),
    yes: bool = common.options.yes,
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover
    """Import and Apply settings from bulk-edit.csv"""
    caasapi = caas.CaasAPI()
    cmds = caasapi.build_cmds(file=input_file)
    # TODO log cli
    if cmds:
        render.console.print(f"[bright_green]Send{'ing' if yes else ''} Commands[/]:")
        render.console.print("\n".join(cmds))

        render.confirm(yes)
        for dev in caasapi.data:
            group_dev = f"{caasapi.data[dev]['_common'].get('group')}/{dev}"
            resp = api.session.request(caasapi.send_commands, group_dev, cmds)
            # caas.eval_caas_response(resp)  # TODO test below
            render.display_results(resp, cleaner=cleaner.parse_caas_response)



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
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover  hidden
    caasapi = caas.CaasAPI()
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

    resp = api.session.request(caasapi.send_commands, group_dev, cmds)
    # caas.eval_caas_response(resp)  # TODO Test below
    render.display_results(resp, cleaner=cleaner.parse_caas_response)


@app.command()
def import_vlan(
    key: str = typer.Argument(..., help="The Key from stored_tasks file with vlan details to import", show_default=False),
    import_file: Path = common.arguments.import_file,
    file: Path = typer.Option(None, help="Same as providing IMPORT_FILE argument", exists=True, show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add VLAN from stored_tasks file.

    This is the same as `cencli batch add-vlan key`, but command: add_vlan
    is implied only need to provide key
    """
    import_file = file or import_file or config.stored_tasks_file

    data = config.get_file_data(import_file)
    data = data.get(key)

    if not data:  # pragma: no cover
        common.exit(f"[cyan]{key}[/] Not found in [cyan]{import_file}[/]")

    args = data.get("arguments", [])
    kwargs = data.get("options", {})
    _msg = (
        f"\n[bright_green]Add{'' if not yes else 'ing'} VLAN[/]"
        '\n  [cyan]settings[/]:'
        f"\n    [magenta]args[/]: {', '.join(args)}\n    [magenta]kwargs[/]: {', '.join([f'{k}=[deep_sky_blue1]{v}[/]' for k, v in kwargs.items()])}"
    )
    render.econsole.print(_msg)
    render.confirm(yes)
    add_vlan(*args, **kwargs)




@app.command("batch")
def caas_batch(
    key: str = typer.Argument(None, help="The parent key in sthe stored-tasks file containing the arguments/options to supply to the command.", show_default=False,),
    file: Path = typer.Option(config.stored_tasks_file, exists=True,),
    command: str = typer.Option(None, help="The cencli batch command to run with the arguments/options from the stored-tasks file", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover  Not used by any CLI command
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
    caasapi = caas.CaasAPI()
    if file == config.stored_tasks_file and not key:
        common.exit("key is required when using the default import file")

    data = config.get_file_data(file)
    data = data.get(key, data)

    if not data:
        common.exit(f"[cyan]{key}[/] not found in [cyan]{file}[/].  No Data to Process")

    args = data.get("arguments", [])
    kwargs = data.get("options", {})
    cmds = data.get("cmds", [])

    if not args:
        common.exit("import data requires an argument specifying the group / device")

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
            print("  [bold]cli cmds[/]:")
        _ = [print(f"    [cyan]{c}[/]") for c in cmds]

        render.confirm()
        kwargs = {**kwargs, **{"cli_cmds": cmds}}
        resp = api.session.request(caasapi.send_commands, *args, **kwargs)
        # caas.eval_caas_response(resp)  # TODO test below
        render.display_results(resp, tablefmt="simple", cleaner=cleaner.parse_caas_response)


@app.command()
def send_cmds(
    kw1: constants.SendCmdArgs = typer.Argument(
        ...,
        help="What to send the commands to, [dim]use 'file' to send_cmds to nodes based on import file.[/]",
        show_default=False
    ),
    nodes: str = typer.Argument(
        None,
        autocompletion=cache.send_cmds_completion,
        help="The device/group/site identifier, [dim]or 'all' for all gateways in the environment[/] :warning:  [bright_red]Use Caution[/]",
        metavar=iden_meta.group_or_dev_or_site,
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
        help="The commands to send.  ([dim]space seperated, with each command wrapped in quotes[/]).",
        callback=common.send_cmds_node_callback,
        show_default=False,
    ),
    cmd_file: Path = typer.Option(None, help="Path to file containing commands (1 per line) to be sent to device", exists=True, show_default=False,),
    all: bool = typer.Option(False, "-A", "--all", help="Send command(s) to all gateways (device level update) when group is provided"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Send commands to gateway(s) (group or device level)

    :warning:  [bright_red]Use Caution[/]
    Do not push to production without first testing in a lab.
    """
    commands = commands or []
    action = ""
    if kw1 == "group":
        if all:
            g = cache.get_group_identifier(nodes, dev_type="gw")
            nodes = [CacheDevice(d) for d in cache.devices if d["type"] == "gw" and d["group"] == g.name]
            if not nodes:
                common.exit(f"No gateways found in group {g.name}")
            action = f"all devices in {g.name} group."
        else:
            nodes = cache.get_group_identifier(nodes)
            action = f"group level gateway config for {nodes.name} group."
    elif kw1 == "site":
        s = cache.get_site_identifier(nodes)
        nodes = [CacheDevice(d) for d in cache.devices if d["type"] == "gw" and d["site"] == s.name]
        action = f"all devices in site: {s.name}"
    elif kw1 == "file":  # TODO break this out into sep func
        dev_file = Path(nodes)
        file_data = config.get_file_data(dev_file, text_ok=True)
        if not file_data:
            common.exit(f"No data parsed from file {dev_file.name}.")

        if isinstance(file_data, list):
            nodes: list[CacheDevice] | list[CacheGroup] | list[CacheSite] = [cache.get_identifier(d.strip(), qry_funcs=["dev", "group", "site"], device_type="gw") for d in file_data]
        else:
            devices = file_data.get("devices", file_data.get("gateways"))
            if devices:
                nodes = [cache.get_identifier(d.strip(), ["dev", "group", "site"], device_type="gw") for d in devices]
            elif "groups" in file_data:
                nodes = [CacheDevice(d) for d in cache.devices if d["type"] == "gw" and d["group"] in file_data["groups"]]
            elif "sites" in file_data:
                nodes = [CacheDevice(d) for d in cache.devices if d["type"] == "gw" and d["site"] in file_data["sites"]]
            else:
                common.exit(f"Expected 'gateways', 'groups', or 'sites' key in {dev_file.name}.")

            if "cmds" in file_data or "commands" in file_data:
                if commands:
                    common.exit("Providing commands on the command line and in the import file is a strange thing to do.")

                commands = file_data.get("cmds", file_data.get("commands"))
        action = f'{", ".join(n.name for n in nodes)} defined in {dev_file.name}'
    elif kw1 == "device":
        if not isinstance(nodes, str):
            render.econsole.print(f":warning:  nodes is of type {type(nodes)} this is unexpected.", emoji=False)

        nodes: List[CacheDevice] = [cache.get_identifier(nodes, qry_funcs=["dev"], device_type="gw")]
        action = f'{", ".join(n.name for n in nodes)}'

    if cmd_file:
        if commands:
            common.exit("Providing commands on the command line and in the import file is a strange thing to do.")
        else:
            commands = [line.rstrip() for line in cmd_file.read_text().splitlines()]

    # TODO common command confirmation func
    if not commands:
        common.exit("Error No commands provided")

    console.print(f"Sending the following to [cyan]{action}[/]")
    _ = [console.print(f"    [cyan]{c}[/]") for c in commands]

    render.confirm(yes)
    caasapi = caas.CaasAPI()
    _reqs = [
        BatchRequest(
            caasapi.send_commands,
            n.name if not n.is_dev else n.mac,
            cli_cmds=commands
        )
        for n in utils.listify(nodes)
    ]
    batch_res = api.session.batch_request(_reqs)
    render.display_results(batch_res, cleaner=cleaner.parse_caas_response)

@app.callback()
def callback():
    """
    Interact with Aruba Central CAAS API (Gateways)
    """
    pass


if __name__ == "__main__":
    app()
