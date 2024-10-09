#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
from pathlib import Path
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, cleaner, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, cleaner, log
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import CloudAuthMacSortBy, CloudAuthUploadType

app = typer.Typer()


@app.command("registered-macs")
def registered_macs(
    search: str = typer.Argument(None, help="Optional search string (name/mac contains)", show_default=False),
    sort_by: CloudAuthMacSortBy = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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
    caption = None if not resp.ok else f"[cyan]{len(resp.output)}[/] Registered MAC Addresses"
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich")
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Cloud-Auth Registered Mac Addresses",
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse
    )


@app.command()
def upload(
    what: CloudAuthUploadType = typer.Argument(CloudAuthUploadType.mac, show_default=True),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show Cloud-Auth Upload Status.

    This command can be ran after [cyan]cencli batch add <macs|mpsk> to see the status of the upload.
    """
    resp = cli.central.request(cli.central.cloudauth_upload_status, upload_type=what.value)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="action")
    if resp.ok:
        try:
            resp.output = cleaner.cloudauth_upload_status(resp.output)
        except Exception as e:
            log.error(f"Error cleaning output of cloud auth mac upload {repr(e)}")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"Cloud-Auth Upload [cyan]{what.upper()}s[/] Status",
        caption=None,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
    )

@app.callback()
def callback():
    """
    Show Aruba Cloud-Auth details
    """
    pass


if __name__ == "__main__":
    app()