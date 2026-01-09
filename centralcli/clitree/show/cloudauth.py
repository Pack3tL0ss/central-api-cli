#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import cleaner, common, render
from centralcli.cache import api
from centralcli.constants import CloudAuthMacSortBy, CloudAuthUploadType, TimeRange

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

    resp = api.session.request(api.cloudauth.get_registered_macs, search=search)
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
        reverse=reverse,
        exit_on_fail=True
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
    resp = api.session.request(api.cloudauth.get_upload_status, upload_type=what.value)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="action")

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"Cloud-Auth Upload [cyan]{what.upper()}s[/] Status",
        caption=None,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.cloudauth_upload_status
    )


@app.command()
def authentications(
    past: str = typer.Option(None, "--past", help=f"An integer value (1-90) ending with d/h/m for day/hour/minute respectively.  i.e. [cyan]3h[/] {common.help_block('1h')}", show_default=False,),
    time_window: TimeRange = typer.Option(None),
    airpass: bool = typer.Option(False, "-a", "--airpass", help=f"Show airpass authentications.  {common.help_block('cloud identity authentications')}"),
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
    """Show Cloud-Auth authentications / access history."""
    resp = api.session.request(api.cloudauth.get_authentications, from_time=past, time_window=time_window, airpass=airpass)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    caption = None
    if resp.ok:
        resp.output = resp.raw["records"]
        caption = f"[cyan]{len(resp)}[/] authentication records"

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"Cloud-Auth {'cloud-identity' if not airpass else 'airpass'} authentications",
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        exit_on_fail=True
    )


@app.command()
def sessions(
    past: str = typer.Option(None, "--past", help=f"An integer value (1-90) ending with d/h/m for day/hour/minute respectively.  i.e. [cyan]3h[/] {common.help_block('1h')}", show_default=False,),
    time_window: TimeRange = typer.Option(None),
    airpass: bool = typer.Option(False, "-a", "--airpass", help=f"Show airpass authentications.  {common.help_block('cloud identity authentications')}"),
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
    """Show Cloud-Auth sessions."""
    resp = api.session.request(api.cloudauth.get_sessions, from_time=past, time_window=time_window, airpass=airpass)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    caption = None
    if resp.ok:
        resp.output = resp.raw["records"]
        caption = f"[cyan]{len(resp)}[/] sessions"

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"Cloud-Auth {'cloud-identity' if not airpass else 'airpass'} sessions",
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        exit_on_fail=True
    )

@app.callback()
def callback():
    """
    Show Aruba Cloud-Auth details
    """
    pass


if __name__ == "__main__":
    app()