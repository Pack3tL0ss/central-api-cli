#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
from pathlib import Path
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cleaner, cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cleaner, cli
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    IdenMetaVars, SortTsCmdOptions, TSDevTypes, lib_to_api  # noqa
)

app = typer.Typer()

iden_meta = IdenMetaVars()


@app.command(short_help="Show Troubleshooting output")
def results(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        help="Aruba Central Device or the session id of a previously run troubleshooting session",
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    session_id: str = typer.Argument(
        None,
        help="The troubleshooting session id.",
        show_default=False,
    ),
    clean: bool = typer.Option(
        False,
        "--clean",
        help="Clean response, don't send through any formatters.  [grey42 italic]Useful for excessively long output[/]",
        show_default=False,
    ),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
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
    [cyan]Show Troubleshooting results from a previously run troubleshooting session.[/]

    Use [cyan]cencli tshoot...[/] to start a troubleshooting session.

    """
    central = cli.central
    dev = cli.cache.get_dev_identifier(device)

    # Fetch session ID if not provided
    if not session_id:
        resp = central.request(central.get_ts_session_id, dev.serial)
        if resp.ok and "session_id" in resp.output:
            session_id = resp.output["session_id"]
        else:
            print(f"No session id provided, unable to find active session id for {dev.name}")
            cli.display_results(resp, exit_on_fail=True)

    title = f"Troubleshooting output for {dev.name} session {session_id}"

    resp = central.request(central.get_ts_output, dev.serial, session_id=session_id)
    if not resp or resp.output.get("status", "") != "COMPLETED":
        cli.display_results(resp, title=title, tablefmt="rich",)
    else:
        if "output" in resp.output:
            _output = resp.output["output"]
            del resp.output["output"]
            cli.display_results(resp, tablefmt="action")
            resp.output = _output

        cli.display_results(resp, pager=pager, outfile=outfile, tablefmt="simple" if not clean else "clean")


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
