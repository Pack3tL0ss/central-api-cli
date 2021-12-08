#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List
# from typing import List
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

from centralcli.constants import IdenMetaVars, TemplateDevIdens


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
    short_help="Update group properties",
    help="Update group properties (AOS8 vs AOS10 & Monitor Only Switch enabled/disabled)"
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
        resp = cli.central.request(cli.central.update_group_properties, group.name, aos_version, monitor_only_switch=mos)
        cli.display_results(resp)


@app.callback()
def callback():
    """
    Update existing Aruba Central objects.
    """
    pass


if __name__ == "__main__":
    app()
