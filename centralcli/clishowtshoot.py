#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import time
import pendulum
import asyncio
import sys
from typing import List, Union
from pathlib import Path
from rich import print
from rich.console import Console

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cleaner, cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cleaner, cli, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    IdenMetaVars, DevTypes, SortTsCmdOptions, TSDevTypes, lib_to_api  # noqa
)

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


@app.command(short_help="Show Troubleshooting output")
def results(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        help="Aruba Central Device",
        autocompletion=cli.cache.dev_completion,
    ),
    session_id: str = typer.Argument(
        None,
        help="The troubleshooting session id.",
    ),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
    ),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output",),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        show_default=False,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """
    [cyan]Show Troubleshooting results from an existing session.[/]

    Use [cyan]cencli tshoot...[/] to start a troubleshooting session.

    """
    central = cli.central
    con = Console(emoji=False)
    dev = cli.cache.get_dev_identifier(device)

    # Fetch session ID if not provided
    if not session_id:
        resp = central.request(central.get_ts_session_id, dev.serial)
        if resp.ok and "session_id" in resp.output:
            session_id = resp.output["session_id"]
        else:
            print(f"No session id provided, unable to find active session id for {dev.name}")
            cli.display_results(resp)
            raise typer.Exit(1)

    title = f"Troubleshooting output for {dev.name} session {session_id}"
    resp = central.request(central.get_ts_output, dev.serial, session_id=session_id)
    if not resp or resp.output.get("status", "") != "COMPLETED":
        cli.display_results(resp, title=title, tablefmt="rich",)
    elif verbose2:
        cli.display_results(resp)
    else:
        con.print(resp)
        con.print(f"\n   {resp.rl}")


@app.command(short_help="Show available troubleshooting commands")
def commands(
    device_type: TSDevTypes = typer.Argument(..., metavar=iden_meta.dev_types_w_mas, show_default=False,),
    sort_by: SortTsCmdOptions = typer.Option("id", "--sort",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
    ),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output",),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        show_default=False,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """
    [cyan]Show available troubleshooting commands for a given device type.[/]

    Use [cyan]cencli tshoot...[/] to start a troubleshooting session.

    """
    if sort_by == "id":
        sort_by = None
    central = cli.central
    con = Console(emoji=False)
    dev_type = lib_to_api("tshoot", device_type)

    resp = central.request(central.get_ts_commands, device_type=dev_type,)
    cli.display_results(resp, tablefmt="rich", sort_by=sort_by, reverse=reverse, cleaner=cleaner.show_ts_commands)
    # con.print(f"\n   {resp.rl}")





@app.callback()
def callback():
    """
    Show troubleshooting session details or available commands
    """
    pass


if __name__ == "__main__":
    app()
