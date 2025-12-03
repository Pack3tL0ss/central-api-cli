#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

import typer

from centralcli import cleaner, common, render
from centralcli.cache import api
from centralcli.constants import SortOspfAreaOptions, SortOspfDatabaseOptions, SortOspfInterfaceOptions, SortOspfNeighborOptions, iden_meta

app = typer.Typer()


@app.command()
def neighbors(
    device: str = common.arguments.device,
    verbose: int = common.options.verbose,
    sort_by: SortOspfNeighborOptions = common.options.sort_by,
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
):
    """Show OSPF Neighbors for a device."""
    dev = common.cache.get_dev_identifier(device)
    resp = api.session.request(api.routing.get_ospf_neighbor, dev.serial)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    caption = None

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            common.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    render.display_results(
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
    device: str = common.arguments.device,
    verbose: int = common.options.verbose,
    sort_by: SortOspfInterfaceOptions = common.options.sort_by,
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
):
    """Show OSPF Interfaces for a device."""
    sort_by = "ip/mask" if sort_by and sort_by == "ip" else sort_by

    dev = common.cache.get_dev_identifier(device)
    resp = api.session.request(api.routing.get_ospf_interface, dev.serial)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    caption = None

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            common.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    render.display_results(
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
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_completion, show_default=False,),
    verbose: int = common.options.verbose,
    sort_by: SortOspfAreaOptions = common.options.sort_by,
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
):
    """Show OSPF area information for a device."""
    dev = common.cache.get_dev_identifier(device)
    resp = api.session.request(api.routing.get_ospf_area, dev.serial)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    caption = None

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            common.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    render.display_results(
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
    device: str = common.arguments.device,
    verbose: int = common.options.verbose,
    sort_by: SortOspfDatabaseOptions = common.options.sort_by,
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
):
    """Show OSPF database for a device."""

    dev = common.cache.get_dev_identifier(device)
    resp = api.session.request(api.routing.get_ospf_database, dev.serial)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    caption = None
    pad = "  " if tablefmt == "yaml" else ""

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            common.exit(f"OSPF is not enabled on {dev.name}", code=0)
        else:
            caption = [
                f'[cyan]{pad}Router ID[/]: {summary["router_id"]} | [cyan]OSPF Neigbors[/]: {summary["neighbor_count"]} | [cyan]OSPF Interfaces[/]: {summary["interface_count"]}',
                f'[cyan]OSPF Areas[/]: {summary["area_count"]} | [cyan]active LSA[/]: {summary["active_lsa_count"]} | [cyan]rexmt LSA[/]: {summary["rexmt_lsa_count"]}'
            ]

    render.display_results(
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