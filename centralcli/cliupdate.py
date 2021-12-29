#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List
# from typing import List
import typer
from rich import print

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

from centralcli.constants import IdenMetaVars, TemplateDevIdens, GatewayRole


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty
iden_meta = IdenMetaVars()

app = typer.Typer()


@app.command(short_help="Update an existing template")
def template(
    # identifier: template_iden_args = typer.Argument(...,),
    name: str = typer.Argument(
        ...,
        help=f"Template: [name] or Device: {iden_meta.dev}",
        autocompletion=cli.cache.dev_template_completion,
    ),
    # device: str = typer.Argument(None, metavar=iden_meta.dev, help="The device associated with the template"),
    # variable: str = typer.Argument(None, help="[Variable operations] What Variable To Update"),
    # value: str = typer.Argument(None, help="[Variable operations] The Value to assign"),
    template: Path = typer.Argument(None, help="Path to file containing new template", exists=True),
    group: str = typer.Option(
        None,
        help="The template group the template belongs to",
        autocompletion=cli.cache.group_completion
    ),
    device_type: TemplateDevIdens = typer.Option(
        None, "--dev-type",
        help="Filter by Device Type",
    ),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by version"),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    if group:
        group = cli.cache.get_group_identifier(group).name

    obj = cli.cache.get_identifier(
        name, ("template", "dev"), device_type=device_type, group=group
    )

    kwargs = {
        "group": group or obj.group,
        "name": obj.name,
        "device_type": device_type,
        "version": version,
        "model": model
    }

    do_prompt = False
    if template:
        if not template.is_file() or not template.stat().st_size > 0:
            typer.secho(f"{template} not found or invalid.", fg="red")
            do_prompt = True
    else:
        typer.secho("template file not provided.", fg="cyan")
        do_prompt = True

    payload = None
    if do_prompt:
        payload = utils.get_multiline_input(
            "Paste in new template contents then press CTRL-D to proceed. Type 'abort!' to abort",
            print_func=typer.secho, fg="cyan", abort_str="abort!"
        )
        payload = "\n".join(payload).encode()

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
    hidden=True,
)
def group_new(
    group: str = typer.Argument(..., metavar="[GROUP NAME]", autocompletion=cli.cache.group_completion),
    # group_password: str = typer.Argument(
    #     None,
    #     show_default=False,
    #     help="Group password is required. You will be prompted for password if not provided.",
    #     autocompletion=lambda incomplete: incomplete
    # ),
    wired_tg: bool = typer.Option(None, help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(None, help="Manage AP configurations via templates"),
    gw_role: GatewayRole = typer.Option(None,),
    aos10: bool = typer.Option(None, "--aos10", is_flag=True, help="Create AOS10 Group (default Instant)", show_default=False),
    mb: bool = typer.Option(None, is_flag=True, help="Configure Group for MicroBranch APs (AOS10 only"),
    ap: bool = typer.Option(None, help="Allow APs in group"),
    sw: bool = typer.Option(None, help="Allow ArubaOS-SW switches in group."),
    cx: bool = typer.Option(None, help="Allow ArubaOS-CX switches in group."),
    gw: bool = typer.Option(None, help=f"Allow gateways in group.\n{' ':34}If No device types specified all are allowed."),
    mon_only_sw: bool = typer.Option(None, help="Monitor Only for ArubaOS-SW"),
    mon_only_cx: bool = typer.Option(None, help="Monitor Only for ArubaOS-CX", hidden=True),
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

    if all(x is None for x in [wired_tg, wlan_tg, gw_role, aos10, mb, ap, sw, cx, gw, mon_only_sw, mon_only_cx]):
        print(
            "[bright_red]Missing required options.[/bright_red] "
            "Use [italic bright_green]cencli update group ?[/italic bright_green] to see available options"
        )  # TODO is there a way to trigger help text
        raise typer.Exit(1)
    if not aos10 and mb:
        print("[bright_red]Error: Microbranch is only valid if group is configured as AOS10 group.")
        raise typer.Exit(1)
    if (mon_only_sw or mon_only_cx) and wired_tg:
        print("[bright_red]Error: Monitor only is not valid for template group.")
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
    if not all(x is None for x in [ap, sw, cx, gw]):
        pass
        # Need to get current allowed types to determine what changed

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
    if mon_only_sw is not None:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-SW: [bright_green]{mon_only_sw is True}[/bright_green]"
    if mon_only_cx is not None:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-CX: [bright_green]{mon_only_cx is True}[/bright_green]"
    print(f"{_msg}\n")

    kwargs = {
        "group": group.name,
        "wired_tg": wired_tg,
        "wlan_tg": wlan_tg,
        "allowed_types": allowed_types,
        "aos10": aos10,
        "microbranch": mb,
        "gw_role": gw_role,
        "monitor_only_sw": mon_only_sw,
    }
    # kwargs = utils.strip_none(kwargs)

    if yes or typer.confirm("Proceed with values?"):
        resp = cli.central.request(
            cli.central.update_group_properties,
            **kwargs
        )
        cli.display_results(resp, tablefmt="action")
        # if resp:  # resp:
        #     asyncio.run(
        #         cli.cache.update_group_db({'name': group.name, 'template group': {'Wired': wired_tg, 'Wireless': wlan_tg}})
        #     )


@app.command(
    short_help="Update group properties",
    help="Update group properties (AOS8 vs AOS10 & Monitor Only Switch enabled/disabled)",
)
def group(
    group_name: str = typer.Argument(..., autocompletion=cli.cache.group_completion),
    aos_version: int = typer.Argument(None, metavar="[10]", help="Set to 10 to Upgrade group to AOS 10"),
    mos: bool = typer.Option(None, help="Enable monitor only for switches in the group"),
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
    cli.cache(refresh=update_cache)
    group = cli.cache.get_group_identifier(group_name)

    _msg = [
        typer.style("Update group", fg="cyan"),
        typer.style(group.name, fg="bright_green"),
    ]
    if aos_version:
        _msg += [
            typer.style("AOS version", fg="cyan"),
            typer.style(str(aos_version), fg="bright_green"),
            typer.style("[Note: AOS10 groups can not be downgraded back to AOS8]", fg="red"),
        ]

    _msg = " ".join(_msg)

    if mos is not None:
        _msg = f'{_msg}{", " if aos_version else ": "}{typer.style("monitor only switch", fg="cyan")}'
        _msg = f'{_msg} {typer.style("enabled" if mos else "disabled", fg="bright_green")}'

    _msg = f'{_msg}{typer.style("?", fg="cyan")}'

    if yes or typer.confirm(_msg, abort=True):
        resp = cli.central.request(cli.central.update_group_properties_v1, group.name, aos_version, monitor_only_switch=mos)
        cli.display_results(resp)


@app.command(
    short_help="Replace AP configuration",
    help="Update/Replace AP configuration by group or AP"
)
def ap_config(
    group_dev: str = typer.Argument(
        ...,
        autocompletion=lambda incomplete: [
            m for m in [*cli.cache.group_completion(incomplete), *cli.cache.dev_completion(incomplete, args=["ap"])]
        ],
    ),
    # autocompletion=lambda i: [*cli.cache.group_completion(i), cli.cach.dev_completion(i, dev_) ),
    cli_file: Path = typer.Argument(..., help="File containing desired config in CLI format.", exists=True),
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
    cli.cache(refresh=update_cache)
    group_dev: cli.cache.CentralObject = cli.cache.get_identifier(group_dev, qry_funcs=["group", "dev"], device_type="ap")
    if cli_file:
        cli_list = []
        with cli_file.open() as f:
            for line in f:
                cli_list += [line.rstrip()]
                if "******" in line:
                    typer.secho("Masked credential found in file.", fg="red")
                    typer.secho(
                        f"Replace:\n{' ':4}{line.strip()}\n    with cleartext{' or actual hash.' if 'hash' in line else '.'}",
                        fg="red",
                        )
                    raise typer.Exit(1)
    if not cli_list:
        typer.echo("Error No cli provided. No clis.", fg="bright red")
        raise typer.Exit(1)

    _cfg_str = [
        typer.style("\nConfiguration to be sent:", fg=None),
        *[typer.style(line, fg="green") for line in cli_list],
    ]
    _cfg_str = "\n".join(_cfg_str)
    _msg = [
        typer.style(f"Update {'group' if group_dev.is_group else 'AP'}", fg="cyan"),
        typer.style(group_dev.name, fg="bright_green"),
    ]
    _msg = " ".join(_msg)
    _msg = f'{_cfg_str}\n{_msg}{typer.style("?", fg="cyan")}'

    if yes or typer.confirm(_msg, abort=True):
        resp = cli.central.request(
            cli.central.replace_ap_config,
            group_dev.name if group_dev.is_group else group_dev.serial,
            cli_list
        )
        typer.secho(str(resp), fg="green" if resp else "red")


@app.callback()
def callback():
    """
    Update existing Aruba Central objects.
    """
    pass


if __name__ == "__main__":
    app()
