#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
from pathlib import Path
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import CloudAuthMacSortBy

app = typer.Typer()


@app.command("registered-macs")
def registered_macs(
    search: str = typer.Argument(None, help="Optional search string (name/mac contains)", show_default=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: CloudAuthMacSortBy = typer.Option(None, "--sort", show_default=False,),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        False, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
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
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show Cloud-Auth MAC registrations.
    """
    if sort_by:
        sort_full_names = {
            "name": "Client Name",
            "mac": "Mac Address"
        }
        sort_by = sort_full_names.get(sort_by, sort_by)

    resp = cli.central.request(cli.central.cloudauth_get_registered_macs, search=search)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich")
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Cloud-Auth Registered Mac Addresses",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse
    )

@app.callback()
def callback():
    """
    Show Aruba Cloud-Auth details
    """
    pass


if __name__ == "__main__":
    app()