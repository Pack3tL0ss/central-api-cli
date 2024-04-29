#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
import asyncio
from pathlib import Path
from typing import List


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, config
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi  # noqa
from rich.console import Console

app = typer.Typer()

tty = utils.tty


@app.command(short_help="Refresh access token")
def token(
    account_list: List[str] = typer.Argument(
        None,
        help="A list of accounts to refresh tokens for (must be defined in the config).  This is useful automated for cron/task-scheduler refresh.",
        autocompletion=cli.cache.account_completion,
        show_default=False,
    ),
    all: bool = typer.Option(False, "-A", "--all", help="Refresh Tokens for all defined workspaces in config.",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Debug Logging", callback=cli.debug_callback),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion
    ),
):
    """Refresh Central API access/refresh tokens.

    This is not necessary under normal circumstances as the cli will automatically refresh the tokens if they are expired.
    This can be useful for automated runs via cron/task-scheduler.  Ensuring the access token does not expire even if the
    cli is not used.
    """
    # TODO expand help text to include URL with example
    if not all and not account_list:
        cli.central.refresh_token()
    else:
        console = Console()
        if account_list:
            verified_account_list = []
            for account in account_list:
                if account in config.defined_accounts:
                    verified_account_list += [account]
                else:
                    console.print(f":warning:  Ignoring account {account} as it's not defined in the config.")
                    console.print(f"  [italic]Update config @ {config.file}[/]")
            if len(verified_account_list) != len(account_list):
                console.print(f"Performing token refresh for {len(verified_account_list)} of {len(account_list)} provided accounts.")

            account_list = [config.default_account,  *verified_account_list]
        else:
            account_list = [config.default_account,  *config.defined_accounts]

        async def refresh_multi(account_list: List[str]):
            success_list = await asyncio.gather(*[
                asyncio.to_thread(CentralApi(account_name=account).refresh_token, silent=True)
                for account in account_list
                ]
            )

            return success_list

        with console.status(f"Refreshing Tokens for {len(account_list)} accounts defined in config", spinner="runner",):
            success_list = asyncio.run(refresh_multi(account_list))

        for account, success in zip(account_list, success_list):
            console.print(f"{':x:' if not success else ':heavy_check_mark:'}  {account}")
        console.print(f"\nSuccessfully refreshed tokens for {success_list.count(True)} of {len(success_list)} accounts.")

@app.command(short_help="Refresh local cache")
def cache(
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Debug Logging", callback=cli.debug_callback),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion
    ),
):
    """Refresh friendly identifier cache.

    The cache is the data that is stored locally so you can reference a device by name, ip, or mac vs just serial number.

    This is not necessary under normal circumstances as the cli will automatically refresh the cache if you provide an identifier
    that doesn't have a match.
    """
    cli.cache(refresh=True)


# TODO add cache for webhooks
@app.command(short_help="Refresh (regenerate) webhook token")
def webhook(
    wid: str = typer.Option(..., help="WebHook ID",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Refresh WebHook Token (generate a new token).

    Use `cencli show webhooks` to get the required webhook id (wid).
    """
    resp = cli.central.request(cli.central.refresh_webhook_token, wid)
    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Refresh tokens / cache
    """
    pass

if __name__ == "__main__":
    app()
