#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path
from typing import List

import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import clibatch, clicaas, clido, clishow, cli, log, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import (clibatch, clicaas, clido, clishow, cli, log,
                                utils)
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi  # noqa
from centralcli.constants import RefreshWhat, arg_to_what  # noqa


STRIP_KEYS = ["data", "devices", "mcs", "group", "clients", "sites", "switches", "aps"]
SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()
app.add_typer(clishow.app, name="show")
app.add_typer(clido.app, name="do")
app.add_typer(clibatch.app, name="batch")
app.add_typer(clicaas.app, name="caas", hidden=True)


args_metavar_dev = "[name|ip|mac-address|serial]"
args_metavar_site = "[name|site_id|address|city|state|zip]"
args_metavar = f"""Optional Identifying Attribute: device: {args_metavar_dev} site: {args_metavar_site}"""


@app.command(hidden=True)
def refresh(what: RefreshWhat = typer.Argument(...),
            debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                       callback=cli.debug_callback),
            default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                         callback=cli.default_callback),
            account: str = typer.Option("central_info",
                                        envvar="ARUBACLI_ACCOUNT",
                                        help="The Aruba Central Account to use (must be defined in the config)",
                                        callback=cli.account_name_callback),):
    """refresh <'token'|'cache'>"""

    central = CentralApi(account)

    if what.startswith("token"):
        from centralcli.response import Session
        Session(central.auth).refresh_token()
    else:  # cache is only other option
        cli.cache(central=cli.central, refresh=True)


@app.command(hidden=True)
def method_test(method: str = typer.Argument(...),
                kwargs: List[str] = typer.Argument(None),
                do_json: bool = typer.Option(True, "--json", is_flag=True, help="Output in JSON"),
                do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
                do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
                do_table: bool = typer.Option(False, "--simple", is_flag=True, help="Output in Table"),
                do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
                outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
                no_pager: bool = typer.Option(True, "--pager", help="Enable Paged Output"),
                update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
                default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                             callback=cli.default_callback),
                debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                           callback=cli.debug_callback),
                account: str = typer.Option("central_info",
                                            envvar="ARUBACLI_ACCOUNT",
                                            help="The Aruba Central Account to use (must be defined in the config)",
                                            callback=cli.account_name_callback),
                ) -> None:
    """dev testing commands to run CentralApi methods from command line

    Args:
        method (str, optional): CentralAPI method to test.
        kwargs (List[str], optional): list of args kwargs to pass to function.

    format: arg1 arg2 keyword=value keyword2=value
        or  arg1, arg2, keyword = value, keyword2=value

    Displays all attributes of Response object
    """
    central = CentralApi(account)
    if not hasattr(central, method):
        typer.secho(f"{method} does not exist", fg="red")
        raise typer.Exit(1)
    args = [k for k in kwargs if "=" not in k]
    kwargs = [k.replace(" =", "=").replace("= ", "=").replace(",", " ").replace("  ", " ") for k in kwargs]
    kwargs = [k.split("=") for k in kwargs if "=" in k]
    kwargs = {k[0]: k[1] for k in kwargs}

    typer.secho(f"session.{method}({', '.join(a for a in args)}, "
                f"{', '.join([f'{k}={kwargs[k]}' for k in kwargs]) if kwargs else ''})", fg="cyan")
    resp = central.request(getattr(central, method), *args, **kwargs)

    for k, v in resp.__dict__.items():
        if k != "output":
            if debug or not k.startswith("_"):
                typer.echo(f"  {typer.style(k, fg='cyan')}: {v}")

    data = cli.eval_resp(resp, pad=2)
    tablefmt = cli.get_format(
        do_json, do_yaml, do_csv, do_rich,
    )

    typer.echo(f"\n{typer.style('CentralCLI Response Output', fg='cyan')}:")
    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)
    data = asyncio.run(resp._response.json())
    if data:
        typer.echo(f"\n{typer.style('Raw Response Output', fg='cyan')}:")
        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.callback()
def callback():
    """
    Aruba Central API CLI
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    # allow singular form and common synonyms for the defined show commands
    # show switches / show switch ...
    if len(sys.argv) > 2 and sys.argv[1] == 'show':
        sys.argv[2] = arg_to_what(sys.argv[2])

    app()
