#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import typer
from pathlib import Path

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

from centralcli.constants import IdenMetaVars, SortOspfAreaOptions, SortOspfInterfaceOptions, SortOspfNeighborOptions, SortOspfDatabaseOptions  # noqa

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


@app.command()
def neighbors(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortOspfNeighborOptions = cli.options.sort_by,
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
):
    """Show OSPF Neighbors for a device
    """
    central = cli.central

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_neighbor, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    caption = None

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            print(f"OSPF is not enabled on {dev.name}")
            raise typer.Exit(0)
        else:
            caption = [
                f'[cyan]Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{dev.name} OSPF Neighbors",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_neighbor if not verbose else None,
        caption=caption
    )


@app.command()
def interfaces(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortOspfInterfaceOptions = cli.options.sort_by,
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
):
    """Show OSPF Interfaces for a device
    """
    sort_by = "ip/mask" if sort_by and sort_by == "ip" else sort_by

    central = cli.central

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_interface, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    caption = None

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            cli.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{dev.name} OSPF Interfaces",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_interface if not verbose else None,
        caption=caption,
        full_cols=["ip/mask", "DR IP", "BDR IP", "DR rtr id", "BDR rtr id"]
    )


@app.command()
def area(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortOspfAreaOptions = cli.options.sort_by,
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
):
    """Show OSPF area information for a device
    """
    central = cli.central

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_area, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    caption = None

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            cli.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{dev.name} OSPF Area Details",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_neighbor if not verbose else None,  # ospf_neighbor cleaner is sufficient here
        caption=caption,
        full_cols=["ip/mask", "DR IP", "BDR IP", "DR rtr id", "BDR rtr id"]
    )


@app.command()
def database(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortOspfDatabaseOptions = cli.options.sort_by,
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
):
    """Show OSPF database for a device
    """
    central = cli.central

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_database, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    caption = None
    pad = "  " if tablefmt == "yaml" else ""

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            cli.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]{pad}Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{dev.name} OSPF Database Details",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_neighbor if not verbose else None,  # ospf_neighbor cleaner is sufficient here
        caption=caption,
        full_cols=["ip/mask", "DR IP", "BDR IP", "DR rtr id", "BDR rtr id"]
    )


@app.callback()
def callback():
    """
    Show OSPF details
    """
    pass


if __name__ == "__main__":
    app()