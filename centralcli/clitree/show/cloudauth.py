#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import cleaner, common, log, render
from centralcli.cache import api
from centralcli.constants import CloudAuthMacSortBy, CloudAuthUploadType

app = typer.Typer()


@app.command()
def registered_macs(
    search: str = typer.Argument(None, help="Optional search string (name/mac contains)", show_default=False),
    sort_by: CloudAuthMacSortBy = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Show Cloud-Auth MAC registrations."""
    if sort_by:
        sort_full_names = {
            "name": "Client Name",
            "mac": "Mac Address"
        }
        sort_by = sort_full_names.get(sort_by, sort_by)

    resp = api.session.request(api.cloudauth.cloudauth_get_registered_macs, search=search)
    caption = None if not resp.ok else f"[cyan]{len(resp.output)}[/] Registered MAC Addresses"
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich")
    render.display_results(
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
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Show Cloud-Auth Upload Status.

    This command can be ran after [cyan]cencli batch add <macs|mpsk> to see the status of the upload.
    """
    resp = api.session.request(api.cloudauth.cloudauth_upload_status, upload_type=what.value)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="action")
    if resp.ok:
        try:
            resp.output = cleaner.cloudauth_upload_status(resp.output)
        except Exception as e:
            log.error(f"Error cleaning output of cloud auth mac upload {repr(e)}")

    render.display_results(
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