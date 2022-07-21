#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List, Union
# from typing import List
import typer
from rich import print
from rich.console import Console
from jinja2 import FileSystemLoader, Environment
import yaml

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, cli, caas, cleaner, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, cli, caas, cleaner, config
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, DevTypes, GatewayRole
from centralcli import CentralObject


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty
iden_meta = IdenMetaVars()

app = typer.Typer()


# TODO add support for j2 / variable conversion as with cencli update config
# FIXME pushing template via API returned 200 but template was not updated??
@app.command(short_help="Update an existing template")
def template(
    name: str = typer.Argument(
        ...,
        metavar="IDENTIFIER",
        help=f"Template: [name] or Device: {iden_meta.dev}",
        autocompletion=cli.cache.dev_template_completion,
    ),
    template: Path = typer.Argument(
        None,
        help="Path to file containing new template",
        exists=True,
        autocompletion=lambda incomplete: [],
    ),
    group: str = typer.Option(
        None,
        help="The template group the template belongs to",
        autocompletion=cli.cache.group_completion
    ),
    device_type: DevTypes = typer.Option(
        None, "--dev-type",
        help="Filter by Device Type",
    ),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by version"),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    if group:
        group = cli.cache.get_group_identifier(group).name

    obj = cli.cache.get_identifier(
        name, ("template", "dev"), device_type=device_type, group=group
    )
    if obj.is_dev:
        _tmplt = [t for t in cli.cache.templates if t["group"] == obj.group and t["model"] in obj.model]

        if version:
            _tmplt = [t for t in cli.cache.templates if t["version"] in ["ALL", version]]

        if len(_tmplt) != 1:
            print(f"Failed to determine template for {obj.name}.  Found: {len(_tmplt)}")
            raise typer.Exit(1)
        else:
            obj = CentralObject("template", _tmplt[0])

    kwargs = {
        "group": group or obj.group,
        "name": obj.name,
        "device_type": device_type,
        "version": version,
        "model": model
    }

    do_prompt = False
    if template:
        if not template.stat().st_size > 0:
            typer.secho(f"{template} not found or invalid.", fg="red")
            do_prompt = True
    else:
        typer.secho("template file not provided.", fg="cyan")
        do_prompt = True

    payload = None
    if do_prompt:
        payload = utils.get_multiline_input(
            "Paste in new template contents then press CTRL-D to proceed. Type 'abort' to abort",
            print_func=typer.secho, fg="cyan", abort_str="abort"
        )
        payload = "\n".join(payload).encode()

    # TODO add confirmation message
    _resp = cli.central.request(cli.central.update_existing_template, **kwargs, template=template, payload=payload)
    typer.secho(str(_resp), fg="green" if _resp else "red")


@app.command(short_help="Update existing or add new Variables for a device/template")
def variables(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
    var_value: List[str] = typer.Argument(..., help="comma seperated list 'variable = value, variable2 = value2'"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
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

    msg = "Sending Update" if yes else "Please Confirm: Update"
    typer.secho(f"{msg} {dev.name}|{dev.serial}", fg="cyan")
    [typer.echo(f'    {k}: {v}') for k, v in var_dict.items()]
    if yes or typer.confirm(typer.style("Proceed with these values", fg="cyan")):
        resp = cli.central.request(
            cli.central.update_device_template_variables,
            serial,
            dev.mac,
            var_dict=var_dict)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(
    short_help="Update group properties.",
    help="Update group properties.",
)
def group(
    group: str = typer.Argument(..., metavar="[GROUP NAME]", autocompletion=cli.cache.group_completion),
    # group_password: str = typer.Argument(
    #     None,
    #     show_default=False,
    #     help="Group password is required. You will be prompted for password if not provided.",
    #     autocompletion=lambda incomplete: incomplete
    # ),
    wired_tg: bool = typer.Option(None, "--wired-tg", help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(None, "--wlan-tg", help="Manage AP configurations via templates"),
    gw_role: GatewayRole = typer.Option(None,),
    aos10: bool = typer.Option(None, "--aos10", is_flag=True, help="Create AOS10 Group (default AOS8/IAP)", show_default=False),
    mb: bool = typer.Option(None, "--mb", help="Configure Group for MicroBranch APs (AOS10 only"),
    ap: bool = typer.Option(None, "--ap", help="Allow APs in group"),
    sw: bool = typer.Option(None, "--sw", help="Allow ArubaOS-SW switches in group."),
    cx: bool = typer.Option(None, "--cx", help="Allow ArubaOS-CX switches in group."),
    gw: bool = typer.Option(None, "--gw", help=f"Allow gateways in group.\n{' ':34}If No device types specified all are allowed."),
    mo_sw: bool = typer.Option(None, is_flag=True, help="Monitor Only for ArubaOS-SW"),
    mo_cx: bool = typer.Option(None, help="Monitor Only for ArubaOS-CX", hidden=True),
    # ap_user: str = typer.Option("admin", help="Provide user for AP group"),  # TODO build func to update group pass
    # ap_passwd: str = typer.Option(None, help="Provide password for AP group (use single quotes)"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    debugv: bool = typer.Option(
        False, "--debugv",
        envvar="ARUBACLI_VERBOSE_DEBUG",
        help="Enable verbose Debug Logging",
        callback=cli.verbose_debug_callback,
        hidden=True,
    ),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    # if not group_password:
    #     group_password = typer.prompt("Group Password", confirmation_prompt=True, hide_input=True,)

    # else:
    #     _msg = f'{_msg}{typer.style(f"?", fg="cyan")}'
    group = cli.cache.get_group_identifier(group)

    if all(x is None for x in [wired_tg, wlan_tg, gw_role, aos10, mb, ap, sw, cx, gw, mo_sw, mo_cx]):
        print(
            "[bright_red]Missing required options.[/bright_red] "
            "Use [italic bright_green]cencli update group ?[/italic bright_green] to see available options"
        )  # TODO is there a way to trigger help text
        raise typer.Exit(1)
    if not aos10 and mb:
        print("[bright_red]Error: Microbranch is only valid if group is configured as AOS10 group.")
        raise typer.Exit(1)
    if (mo_sw or mo_cx) and wired_tg:
        print("[bright_red]Error: Monitor only is not valid for template group.")
        raise typer.Exit(1)
    if mo_sw is not None and not sw:
        print("Invalid combination --mo-sw not valid without --sw")
        print("[bright_red]Error: Monitor only can only be set when initially adding AOS-SW as allowed to group.")
        raise typer.Exit(1)
    if mo_cx is not None and not cx:
        print("Invalid combination --mo-cx not valid without --cx")
        print("[bright_red]Error: Monitor only can only be set when initially adding AOS-CX as allowed to group.")
        raise typer.Exit(1)

    allowed_types = []
    if ap:
        allowed_types += ["ap"]
    if sw:
        allowed_types += ["sw"]
    if cx:
        allowed_types += ["cx"]
    if gw:
        allowed_types += ["gw"]

    _msg = f"[cyan]Update [cyan]group [bright_green]{group.name}[/bright_green]"
    if aos10 is not None:
        _msg = f"{_msg}\n    [cyan]AOS10[/cyan]: [bright_green]{aos10 is True}[/bright_green]"
    if allowed_types:
        _msg = f"{_msg}\n    [cyan]Allowed Device Types[/cyan]: [bright_green]{allowed_types}[/bright_green]"
    if wired_tg is not None:
        _msg = f"{_msg}\n    [cyan]wired Template Group[/cyan]: [bright_green]{wired_tg is True}[/bright_green]"
    if wlan_tg is not None:
        _msg = f"{_msg}\n    [cyan]WLAN Template Group[/cyan]: [bright_green]{wlan_tg is True}[/bright_green]"
    if gw_role is not None:
        _msg = f"{_msg}\n    [cyan]Gateway Role[/cyan]: [bright_green]{gw_role or 'branch'}[/bright_green]"
    if mb is not None:
        _msg = f"{_msg}\n    [cyan]MicroBranch[/cyan]: [bright_green]{mb is True}[/bright_green]"
    if mo_sw is not None:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-SW: [bright_green]{mo_sw is True}[/bright_green]"
    if mo_cx is not None:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-CX: [bright_green]{mo_cx is True}[/bright_green]"
    print(f"{_msg}\n")

    kwargs = {
        "group": group.name,
        "wired_tg": wired_tg,
        "wlan_tg": wlan_tg,
        "allowed_types": allowed_types,
        "aos10": aos10,
        "microbranch": mb,
        "gw_role": gw_role,
        "monitor_only_sw": mo_sw,
    }

    if yes or typer.confirm("Proceed with values?"):
        resp = cli.central.request(
            cli.central.update_group_properties,
            **kwargs
        )
        cli.display_results(resp, tablefmt="action")

def generate_template(template_file: Union[Path, str], var_file: Union[Path, str], group_dev: str):
    '''Generate configuration files based on j2 templates and provided variables
    '''
    template_file = Path(str(template_file)) if not isinstance(template_file, Path) else template_file
    var_file = Path(str(var_file)) if not isinstance(var_file, Path) else var_file

    config_data = yaml.load(var_file.read_text(), Loader=yaml.SafeLoader)

    env = Environment(loader=FileSystemLoader(str(template_file.parent)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_file.name)

    # TODO output to temp or out dir cwd could be non-writable
    group_dev = Path.cwd() / f"{group_dev}.cfg"
    group_dev.write_text(template.render(config_data))

    return group_dev



@app.command("config",
    short_help="Update Group or Device level config",
    help="Update/Replace Group or Device level Configuration (ap or gw)"
)
def config_(
    group_dev: str = typer.Argument(
        ...,
        metavar="GROUP|DEVICE",
        help="Group or device to update.",
        autocompletion=cli.cache.group_dev_ap_gw_completion
    ),
    # TODO simplify structure can just remove device arg
    # device: str = typer.Argument(
    #     None,
    #     autocompletion=cli.cache.dev_ap_gw_completion
    #     # TODO dev type gw or ap only
    #     # autocompletion=lambda incomplete: [
    #     #    c for c in cli.cache.dev_completion(incomplete, dev_type="gw") if c.lower().startswith(incomplete.lower())
    #     # ]
    # ),
    # TODO collect multi-line input as option to paste in config
    cli_file: Path = typer.Argument(..., help="File containing desired config/template in CLI format.", exists=True, autocompletion=lambda incomplete: tuple()),
    var_file: Path = typer.Argument(None, help="File containing variables for j2 config template.", exists=True, autocompletion=lambda incomplete: tuple()),
    # TODO --vars PATH  help="File containing variables to convert jinja2 template."
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    do_gw: bool = typer.Option(None, "--gw", help="Show group level config for gateways."),
    do_ap: bool = typer.Option(None, "--ap", help="Show group level config for APs."),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    group_dev: CentralObject = cli.cache.get_identifier(group_dev, qry_funcs=["group", "dev"], device_type=["ap", "gw"])
    config_out = utils.generate_template(cli_file, var_file=var_file)
    cli_cmds = utils.validate_config(config_out)

    # TODO render.py module with helper function to return styled rule/line
    console = Console(record=True, emoji=False)
    console.begin_capture()
    console.rule("Configuration to be sent")
    console.print("\n".join([f"[green]{line}[/green]" for line in cli_cmds]))
    console.rule()
    console.print(f"\nUpdating {'group' if group_dev.is_group else group_dev.generic_type.upper()} [cyan]{group_dev.name}")
    _msg = console.end_capture()

    if group_dev.is_group:
        device = None
        if not do_ap and not do_gw:
            print("Invalid Input, --gw or --ap option must be supplied for group level config.")
            raise typer.Exit(1)
    else:  # group_dev is a device iden
        device = group_dev

    if do_gw or (device and device.generic_type == "gw"):
        if device and device.generic_type != "gw":
            print(f"Invalid input: --gw option conflicts with {device.name} which is an {device.generic_type}")
            raise typer.Exit(1)
        use_caas = True
        caasapi = caas.CaasAPI(central=cli.central)  # XXX Burried import
        node_iden = group_dev.name if group_dev.is_group else group_dev.mac
    elif do_ap or (device and device.generic_type == "ap"):
        if device and device.generic_type != "ap":
            print(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
            raise typer.Exit(1)
        use_caas = False
        node_iden = group_dev.name if group_dev.is_group else group_dev.serial

    typer.echo(_msg)
    if yes or typer.confirm("Proceed?", abort=True):
        if use_caas:
            resp = cli.central.request(caasapi.send_commands, node_iden, cli_cmds)
            cli.display_results(resp, cleaner=cleaner.parse_caas_response)
        else:
            # FIXME this is OK for group level ap config , for AP this method is not valid
            if group_dev.is_dev:
                print("Not Implemented yet for AP device level updates")
                raise typer.Exit(1)
            resp = cli.central.request(cli.central.replace_ap_config, node_iden, cli_cmds)
            cli.display_results(resp, tablefmt="action")


@app.command(
    short_help="Update webhook details",
    help="Update webhook details (name/urls)"
)
def webhook(
    wid: str = typer.Argument(..., help="Use show webhooks to get the wid"),
    # TODO need completion for id_
    name: str = typer.Argument(...,),
    urls: List[str] = typer.Argument(..., help="webhook URLs"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    print("Updating WebHook: [cyan]{}[/cyan] with urls:\n  {}".format(name, '\n  '.join(urls)))
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.update_webhook, wid, name, urls)

        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Update existing Aruba Central objects.
    """
    pass


if __name__ == "__main__":
    app()
