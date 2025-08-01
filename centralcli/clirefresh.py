#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path
from typing import List

import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, config, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, config, utils
    else:
        print(pkg_dir.parts)
        raise e

from rich.console import Console

from . import Session
from .cache import api  # TODO figure out if there is cost to importing/instantiating this numerous times  This is different than most other files

app = typer.Typer()

tty = utils.tty


@app.command()
def token(
    workspace_list: List[str] = typer.Argument(
        None,
        help="A list of workspaces to refresh tokens for (must be defined in the config).  This is useful automated for cron/task-scheduler refresh.",
        autocompletion=cli.cache.account_completion,
        show_default=False,
    ),
    all: bool = typer.Option(False, "-A", "--all", help="Refresh Tokens for all defined workspaces in config.",),
    default: bool = cli.options.default,
    debug: bool = cli.options.debug,
    workspace: str = cli.options.workspace,
):
    """Refresh Classic Central API access/refresh tokens.

    This is not necessary under normal circumstances as the cli will automatically refresh the tokens if they are expired.
    This can be useful for automated runs via cron/task-scheduler.  Ensuring the access token does not expire even if the
    cli is not used.
    """
    if not all and not workspace_list:
        api.session.refresh_token()
    else:
        console = Console()
        if workspace_list:
            verified_workspace_list = []
            for workspace in workspace_list:
                if workspace in config.defined_workspaces:
                    verified_workspace_list += [workspace]
                else:
                    console.print(f":warning:  Ignoring workspace {workspace} as it's not defined in the config.")
                    console.print(f"  [italic]Update config @ {config.file}[/]")
            if len(verified_workspace_list) != len(workspace_list):
                console.print(f"Performing token refresh for {len(verified_workspace_list)} of {len(workspace_list)} provided workspaces.")

            workspace_list = [config.default_workspace,  *verified_workspace_list]
        else:
            workspace_list = [config.default_workspace,  *config.defined_workspaces]

        async def refresh_multi(workspaces: List[str]):
            success_list = await asyncio.gather(*[
                asyncio.to_thread(Session(workspace_name=workspace).refresh_token, silent=True)
                for workspace in workspaces
                ]
            )

            return success_list

        with console.status(f"Refreshing Tokens for {len(workspace_list)} accounts defined in config", spinner="runner",):
            success_list = asyncio.run(refresh_multi(workspace_list))

        for workspace, success in zip(workspace_list, success_list):
            console.print(f"{':x:' if not success else ':heavy_check_mark:'}  {workspace}")
        console.print(f"\nSuccessfully refreshed tokens for {success_list.count(True)} of {len(success_list)} accounts.")

@app.command()
def cache(
    default: bool = cli.options.default,
    debug: bool = cli.options.debug,
    workspace: str = cli.options.workspace,
):
    """Refresh local cache.

    The cache is the data that is stored locally so you can reference a device by name, ip, or mac vs just serial number.
    Has similar benefits for sites, groups, certificates, etc.

    This is not necessary under normal circumstances as the cli will automatically refresh the cache if you provide an identifier
    that doesn't have a match.
    """
    cli.cache(refresh=True)


# CACHE add cache for webhooks
@app.command()
def webhook(
    wid: str = typer.Argument(..., help="WebHook ID. Use [cyan]cencli show webhooks[/] to get the required id.", show_default=False),
    default: bool = cli.options.default,
    debug: bool = cli.options.debug,
    workspace: str = cli.options.workspace,
):
    """Refresh WebHook Token (generate a new token).

    Use [cyan]cencli show webhooks[/] to get the required webhook id (wid).
    """
    resp = api.session.request(api.central.refresh_webhook_token, wid)
    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Refresh tokens / cache
    """
    pass

if __name__ == "__main__":
    app()
