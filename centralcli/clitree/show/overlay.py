#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

import pendulum
import typer

from centralcli import cleaner, common, render
from centralcli.cache import api
from centralcli.constants import SortOverlayInterfaceOptions, SortRouteOptions, iden_meta
from centralcli.response import Response

app = typer.Typer()


# TODO need to build SortBy classes
# TODO Verify aps are not valid for these and remove from completion dev_types.  Testing against MB AP returns 500 request to ce failed timeout after 10s

def _build_caption(resp: Response) -> str | None:

    color_status = {
        "Up": "[bright_green]Up[/]",
        "Down": "[bright_red]Down[/]"
    }

    caption = None
    if resp and "summary" in resp.raw:
        s = resp.raw["summary"]
        oper_state = s.get("oper_state", "").split("_")[-1].title()
        caption = '[cyan]Overlay Connection Summary[/]:'
        caption = f'{caption} Last State Change: {" ".join(pendulum.from_timestamp(s.get("last_state_change", 0), tz="local").to_day_datetime_string().split()[1:])}'
        caption = f'{caption}\n  Admin Status: {"[bright_green]Up[/]" if s.get("admin_status") else "[bright_red]Down[/]"}'
        caption = f'{caption}, Oper State: {color_status.get(oper_state, oper_state)}'
        caption = f'{caption}, interfaces: {s.get("num_interfaces")}'
        caption = f'{caption}\n  [cyan]Routes[/]: Advertised: {s.get("advertised_routes")}, Learned: {s.get("learned_routes")}'

    return caption


@app.command()
def routes(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_gw_completion, show_default=False,),
    advertised: bool = typer.Option(False, "--advertised", "-a", help=f"Show advertised routes {common.help_block('show learned routes')}"),
    best: bool = typer.Option(False, "--best", "-b", help="Return only best/preferred route for each destination"),
    sort_by: SortRouteOptions = common.options.sort_by,
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
    """Show gateway routes advertised or learned from route/tunnel orchestrator
    """
    dev = common.cache.get_dev_identifier(device, dev_type=("gw", "ap",))
    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    what = "advertised" if advertised else "learned"

    if what == "learned":
        resp = api.session.request(api.routing.get_overlay_routes_learned, dev.serial, best=best)
        title = f'{dev.name} {"Preferred " if best else ""}overlay routes [italic](site: {dev.site})[/]'
    elif what == "advertised":
        resp = api.session.request(api.routing.get_overlay_routes_advertised, dev.serial)
        title = f'{dev.name} Advertised routes [italic](site: {dev.site})[/]'

    if resp and "routes" in resp.output:
        resp.output = resp.output["routes"]

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=_build_caption(resp),
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_overlay_routes,
        format=tablefmt,
        simplify=sort_by is None and tablefmt == "rich" and not reverse
    )


@app.command()
def interfaces(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_gw_completion, show_default=False,),
    sort_by: SortOverlayInterfaceOptions = common.options.sort_by,
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
    """Show overlay interfaces
    """
    dev = common.cache.get_dev_identifier(device, dev_type=("gw", "ap",))
    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    resp = api.session.request(api.routing.get_overlay_interfaces, dev.serial)

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=f'{dev.name} Overlay Interfaces [italic](site: {dev.site})[/]',
        caption=_build_caption(resp),
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        set_width_cols={"name": 60},
        cleaner=cleaner.get_overlay_interfaces,
    )


# single entry output, no need to sort
@app.command()
def connection(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_gw_completion, show_default=False,),
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
    """Show overlay connection (OTO/ORO) details (Valid on SD-Branch GWs/ VPNCs Only)

    For additional details use [cyan]cencli tshoot overlay DEVICE[/] (which also works on APs).
    """
    dev = common.cache.get_dev_identifier(device, dev_type="gw")
    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    resp = api.session.request(api.routing.get_overlay_connection, dev.serial)

    set_width_cols = {}
    caption = None
    if "connection" in resp.output:
        resp.output = resp.output["connection"]
        caption=_build_caption(resp)
    elif "summary" in resp.output:  # For Mobility GWs this endpoint only shows Overlay for SD-Branch
        resp.output = resp.output["summary"]
        if resp.output.get("admin_status") is False:
            caption = [
                "This command only shows Overlay connection status for SD-Branch/VPNC GWs",
                "Use [cyan]cencli tshoot overlay DEVICE[/] for Mobility GWs/APs"
            ]
            set_width_cols = {"admin status": {"min": 72, "max": 100}}


    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=f'{dev.name} Overlay Connection Information [italic](site: {dev.site})[/]',
        caption=caption,
        pager=pager,
        outfile=outfile,
        set_width_cols=set_width_cols,
        cleaner=cleaner.simple_kv_formatter,
    )

@app.callback()
def callback():
    """
    Show Overlay (OTO/ORO) Information
    """
    pass


if __name__ == "__main__":
    app()
