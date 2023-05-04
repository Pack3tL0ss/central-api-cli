#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import typer

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
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False),
    sort_by: SortOspfNeighborOptions = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Show OSPF Neighbors for a device
    """
    central = cli.central
    cli.cache(refresh=update_cache)

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_neighbor, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    cf = "[reset][italic dark_olive_green2]"
    caption = ""

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            print(f"OSPF is not enabled on {dev.name}")
            raise typer.Exit(0)
        else:
            caption = [
                f'{cf} Router ID:[/] {summary["router_id"]} | {cf}OSPF Neigbors:[/] {summary["neighbor_count"]} | {cf}OSPF Interfaces:[/] {summary["interface_count"]}',
                f'{cf}OSPF Areas:[/] {summary["area_count"]} | {cf}active LSA:[/] {summary["active_lsa_count"]} | {cf}rexmt LSA:[/] {summary["rexmt_lsa_count"]}'
            ]
            caption = "\n   ".join(caption)

    title = f"{dev.name} OSPF Neighbors"

    cli.display_results(\
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_neighbor if not verbose else None,
        caption=f"{caption}\n"
    )


@app.command()
def interfaces(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False),
    sort_by: SortOspfInterfaceOptions = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Show OSPF Interfaces for a device
    """
    sort_by = "ip/mask" if sort_by and sort_by == "ip" else sort_by

    central = cli.central
    cli.cache(refresh=update_cache)

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_interface, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    cf = "[reset][italic dark_olive_green2]"
    caption = ""

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            print(f"OSPF is not enabled on {dev.name}")
            raise typer.Exit(0)
        else:
            caption = [
                f'{cf} Router ID:[/] {summary["router_id"]} | {cf}OSPF Neigbors:[/] {summary["neighbor_count"]} | {cf}OSPF Interfaces:[/] {summary["interface_count"]}',
                f'{cf}OSPF Areas:[/] {summary["area_count"]} | {cf}active LSA:[/] {summary["active_lsa_count"]} | {cf}rexmt LSA:[/] {summary["rexmt_lsa_count"]}'
            ]
            caption = "\n   ".join(caption)

    title = f"{dev.name} OSPF Interfaces"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_interface if not verbose else None,
        caption=f"{caption}\n",
        full_cols=["ip/mask", "DR IP", "BDR IP", "DR rtr id", "BDR rtr id"]
    )


@app.command()
def area(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    sort_by: SortOspfAreaOptions = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Show OSPF area information for a device
    """
    central = cli.central
    cli.cache(refresh=update_cache)

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_area, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    cf = "[reset][italic dark_olive_green2]"
    caption = ""

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            print(f"OSPF is not enabled on {dev.name}")
            raise typer.Exit(0)
        else:
            caption = [
                f'{cf} Router ID:[/] {summary["router_id"]} | {cf}OSPF Neigbors:[/] {summary["neighbor_count"]} | {cf}OSPF Interfaces:[/] {summary["interface_count"]}',
                f'{cf}OSPF Areas:[/] {summary["area_count"]} | {cf}active LSA:[/] {summary["active_lsa_count"]} | {cf}rexmt LSA:[/] {summary["rexmt_lsa_count"]}'
            ]
            caption = "\n   ".join(caption)

    title = f"{dev.name} OSPF Area Details"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_neighbor if not verbose else None,  # ospf_neighbor cleaner is sufficient here
        caption=f"{caption}\n",
        full_cols=["ip/mask", "DR IP", "BDR IP", "DR rtr id", "BDR rtr id"]
    )


@app.command()
def database(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
    sort_by: SortOspfDatabaseOptions = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    """Show OSPF database for a device
    """
    central = cli.central
    cli.cache(refresh=update_cache)

    dev = cli.cache.get_dev_identifier(device)
    resp = central.request(central.get_ospf_database, dev.serial)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    cf = "[reset][italic dark_olive_green2]"
    caption = ""

    if resp.raw.get("summary"):
        summary = resp.raw["summary"]
        if summary["admin_status"] is False:
            print(f"OSPF is not enabled on {dev.name}")
            raise typer.Exit(0)
        else:
            caption = [
                f'{cf} Router ID:[/] {summary["router_id"]} | {cf}OSPF Neigbors:[/] {summary["neighbor_count"]} | {cf}OSPF Interfaces:[/] {summary["interface_count"]}',
                f'{cf}OSPF Areas:[/] {summary["area_count"]} | {cf}active LSA:[/] {summary["active_lsa_count"]} | {cf}rexmt LSA:[/] {summary["rexmt_lsa_count"]}'
            ]
            caption = "\n   ".join(caption)

    title = f"{dev.name} OSPF Database Details"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_ospf_neighbor if not verbose else None,  # ospf_neighbor cleaner is sufficient here
        caption=f"{caption}\n",
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