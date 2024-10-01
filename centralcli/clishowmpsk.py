#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
from pathlib import Path


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, SortNamedMpskOptions

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


@app.command()
def networks(
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
    """Show all MPSK networks (SSIDs)
    """
    resp = cli.central.request(cli.cache.refresh_mpsk_db)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    cli.display_results(resp, tablefmt=tablefmt, title="MPSK Networks", pager=pager, outfile=outfile, full_cols=["id", "accessURL"])


@app.command()
def named(
    ssid: str = typer.Argument(..., help="The SSID to gather named MPSK definitions for", autocompletion=cli.cache.mpsk_completion, show_default=False,),
    name: str = typer.Option(None, help="Filter by MPSK name (name contains)", show_default=False, rich_help_panel="Filtering Options",),
    role: str = typer.Option(None, help="Filter by user role associated with the MPSK (role name contains)", show_default=False, rich_help_panel="Filtering Options",),
    enabled: bool = typer.Option(None, "-E", "--enabled", help="Show enabled named MPSKs", show_default=False, rich_help_panel="Filtering Options",),
    disabled: bool = typer.Option(None, "-D", "--disabled", help="Show disabled named MPSKs", show_default=False, rich_help_panel="Filtering Options",),
    csv_import: bool = typer.Option(False, "--import", help="Output named MPSKs using format required for import into Cloud-Auth [grey42 italic]implies --csv[/]", show_default=False, rich_help_panel="Formatting",),
    verbose: int = cli.options.verbose,
    sort_by: SortNamedMpskOptions = cli.options.sort_by,
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
    """Show named MPSK definitions for a provided network (SSID)
    """
    status = None
    if enabled:
        status = "enabled"
    elif disabled:
        status = "disabled"

    ssid = cli.cache.get_mpsk_identifier(ssid)
    if not csv_import:
        resp = cli.central.request(cli.central.cloudauth_get_namedmpsk, ssid.id, name=name, role=role, status=status)
        _cleaner = cleaner.cloudauth_get_namedmpsk
    else:
        resp = cli.central.request(cli.central.cloudauth_download_mpsk_csv, ssid.name, name=name, filename=outfile, role=role, status=status)
        _cleaner = None

    tablefmt = "csv" if csv_import else cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    caption = None if not resp.ok else f"{'' if tablefmt == 'rich' else '  '}Total Named MPSKs for [cyan]{ssid.name}[/]: [bright_green]{len(resp)}[/]"
    cli.display_results(resp, tablefmt=tablefmt, title="MPSK Networks", caption=caption, sort_by=sort_by, reverse=reverse, pager=pager, outfile=outfile, cleaner=_cleaner, verbosity=verbose)


@app.callback()
def callback():
    """
    Show MPSK details
    """
    pass


if __name__ == "__main__":
    app()
