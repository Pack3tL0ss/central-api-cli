#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
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

from centralcli.constants import IdenMetaVars


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty
iden_meta = IdenMetaVars()
# template_iden_args = Literal["template-name", "device"]

app = typer.Typer()


@app.command(short_help="Update an existing template")
def template(
    # identifier: template_iden_args = typer.Argument(...,),
    name: str = typer.Argument(..., hidden=False, help=f"Template: [name] or Device: {iden_meta.dev}"),
    # device: str = typer.Argument(None, metavar=iden_meta.dev, help="The device associated with the template"),
    # variable: str = typer.Argument(None, help="[Variable operations] What Variable To Update"),
    # value: str = typer.Argument(None, help="[Variable operations] The Value to assign"),
    template: Path = typer.Argument(None, help="Path to file containing new template"),
    group: str = typer.Option(None, help="The template group associated with the template"),
    device_type: str = typer.Option(None, "--dev-type", metavar="[IAP|ArubaSwitch|MobilityController|CX]>",
                                    help="[Templates] Filter by Device Type"),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by version"),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:

    # if operation == "update":
    #     if what == "variable":
    #         if variable and value and device:
    #             device = cli.cache.get_dev_identifier(device)
    #             payload = {"variables": {variable: value}}
    #             _resp = cli.central.update_variables(device, payload)
    #             if _resp:
    #                 log.info(f"Template Variable Updated {variable} -> {value}", show=False)
    #                 typer.echo(f"{typer.style('Success', fg=typer.colors.GREEN)}")
    #             else:
    #                 log.error(f"Template Update Variables {variable} -> {value} retuned error\n{_resp.output}", show=False)
    #                 typer.echo(f"{typer.style('Error Returned', fg=typer.colors.RED)} {_resp.error}")
    #     else:  # delete or add template, what becomes device/template identifier
    cli.cache(refresh=update_cache)

    obj = cli.cache.get_template_identifier(name)
    if not obj:
        obj = cli.cache.get_dev_identifier(name, dev_type=device_type)

    kwargs = {
        "group": obj.group,
        "name": obj.name,
        "device_type": device_type,
        "version": version,
        "model": model
    }
    payload = None
    do_prompt = False
    if template:
        if not template.is_file() or template.stat().st_size > 0:
            typer.secho(f"{template} not found or invalid.", fg="red")
            do_prompt = True
    else:
        typer.secho("template file not provided.", fg="cyan")
        do_prompt = True

    if do_prompt:
        payload = utils.get_multiline_input(
            "Paste in new template contents then press CTRL-D to proceed. Type 'abort!' to abort",
            print_func=typer.secho, fg="cyan", abort_str="abort!"
        )
        payload = "\n".join(payload).encode()

    _resp = cli.central.update_existing_template(**kwargs, template=template, payload=payload)
    typer.secho(str(_resp), fg="green" if _resp else "red")

    # if _resp:
    #     log.info(f"Template {what} Updated {_resp.output}", show=False)
    #     typer.secho(_resp.output, fg="green")
    # else:
    #     log.error(f"Template {what} Update from {template} Failed. {_resp.error}", show=False)
    #     typer.secho(_resp.output, fg="red")


@app.callback()
def callback():
    """
    Update existing Aruba Central objects.
    """
    pass


if __name__ == "__main__":
    app()
