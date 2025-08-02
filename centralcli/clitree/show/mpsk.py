#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
from pathlib import Path
from typing import TYPE_CHECKING


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, log, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, log, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, SortNamedMpskOptions
from ...cache import api

if TYPE_CHECKING:
    from ...cache import CacheMpsk

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
    workspace: str = cli.options.workspace,
) -> None:
    """Show all MPSK networks (SSIDs)
    """
    resp = api.session.request(cli.cache.refresh_mpsk_networks_db)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    cli.display_results(resp, tablefmt=tablefmt, title="MPSK Networks", pager=pager, outfile=outfile, full_cols=["id", "accessURL"])


@app.command()
def named(
    ssid: str = typer.Argument(None, help=f"The SSID to gather named MPSK definitions for.  {cli.help_block('fetch MPSKs for all MPSK SSIDs')}", autocompletion=cli.cache.mpsk_network_completion, show_default=False,),
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
    workspace: str = cli.options.workspace,
) -> None:
    """Show named MPSK definitions for a provided network (SSID)
    """
    status = None
    if enabled:
        status = "enabled"
    elif disabled:
        status = "disabled"

    title="PSKs"
    if ssid:
        ssid: CacheMpsk = cli.cache.get_mpsk_network_identifier(ssid)
        title = f"{title} associated with [bright_green]{ssid.name}[/] MPSK Network"
    else:
        title = f"{title} associated with [bright_green]all[/] MPSK Networks"

    _cleaner = cleaner.cloudauth_get_namedmpsk
    group_by = None

    if not ssid:
        resp = api.session.request(cli.cache.refresh_mpsk_db)
        if resp.ok and len(set([r["ssid"] for r in resp.output])) > 1:  # It looks odd to do group_by if there is only 1 SSID, it's not obvious that all in the grouping are the same SSID.
            group_by = "ssid"

        if csv_import:
            log.warning("[cyan]--import[/] option is only supported when MPSK ssid is provided", caption=True)
    elif csv_import:
        resp = api.session.request(api.cloudauth.cloudauth_download_mpsk_csv, ssid.name, name=name, filename=outfile, role=role, status=status)
        _cleaner = None
    else:
        resp = api.session.request(cli.cache.refresh_mpsk_db, ssid.id, name=name, role=role, status=status)


    tablefmt = "csv" if csv_import and ssid else cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    caption = None if not resp.ok else f"{'' if tablefmt == 'rich' else '  '}Total Named MPSKs for [cyan]{'ALL SSIDs' if not ssid else ssid.name}[/]: [bright_green]{len(resp)}[/]"
    cli.display_results(resp, tablefmt=tablefmt, title=title, caption=caption, sort_by=sort_by, group_by=group_by, reverse=reverse, pager=pager, outfile=outfile, cleaner=_cleaner, verbosity=verbose)


@app.callback()
def callback():
    """
    Show MPSK details
    """
    pass


if __name__ == "__main__":
    app()
