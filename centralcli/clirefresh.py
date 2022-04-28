#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
from pathlib import Path


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi  # noqa

app = typer.Typer()

tty = utils.tty


@app.command(hidden=True, help="Refresh Tokens", short_help="Refresh Tokens")
def tokens(
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion
    ),
):
    cli.central.refresh_token()

@app.command(hidden=True, help="Refresh Cache", short_help="Refresh Cache")
def cache(
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion
    ),
):
    cli.cache(refresh=True)


# TODO add cache for webhooks
@app.command(help="Refresh WebHook token", short_help="Refresh WebHook token")
def webhook(
    wid: str = typer.Option(..., help="WebHook ID",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    resp = cli.central.request(cli.central.refresh_webhook_token, wid)

    cli.display_results(resp, tablefmt="action")


if __name__ == "__main__":
    app()
