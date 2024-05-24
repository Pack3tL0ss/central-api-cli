#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import sys
import pendulum
from pathlib import Path

import typer
from rich import print

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

from centralcli.constants import IdenMetaVars, SortRouteOptions, SortOverlayInterfaceOptions
from centralcli.response import Response

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()

# TODO need to build SortBy classes
# TODO Verify aps are not valid for these and remove from completion dev_types.  Testing against MB AP returns 500 request to ce failed timeout after 10s

def _build_caption(resp: Response) -> str | None:

    color_status = {
        "Up": "[bright_green]Up[/]",
        "Down": "[bright_red]Down[/]"
    }

    if resp and "summary" in resp.raw:
        s = resp.raw["summary"]
        oper_state = s.get("oper_state", "").split("_")[-1].title()
        caption = '[cyan]Overlay Connection Summary[/]:'
        caption = f'{caption} Last State Change: {" ".join(pendulum.from_timestamp(s.get("last_state_change", 0), tz="local").to_day_datetime_string().split()[1:])}'
        caption = f'{caption}\n  Admin Status: {"[bright_green]Up[/]" if s.get("admin_status") else "[bright_red]Down[/]"}'
        caption = f'{caption}, Oper State: {color_status.get(oper_state, oper_state)}'
        # caption = f'{caption}\n  [cyan]Counts[/]: Up: [bright_green]{s.get("up_count")}[/], Down: [bright_red]{s.get("down_count")}[/]'
        caption = f'{caption}, interfaces: {s.get("num_interfaces")}'
        caption = f'{caption}\n  [cyan]Routes[/]: Advertised: {s.get("advertised_routes")}, Learned: {s.get("learned_routes")}'
    else:
        caption = None

    return caption


@app.command()
def routes(
    # what: OverlayRoutesArgs = typer.Argument("learned", case_sensitive=False, show_default=True),
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_completion, show_default=False,),
    advertised: bool = typer.Option(False, "--advertised", "-a", help="Show advertised routes [grey42]\[default: show learned routes][/]"),
    best: bool = typer.Option(False, "--best", "-b", help="Return only best/preferred route for each destination"),
    sort_by: SortRouteOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", rich_help_panel="Common Options", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show gateway routes advertised or learned from route/tunnel orchestrator
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=("gw", "ap",))
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    what = "advertised" if advertised else "learned"

    if what == "learned":
        resp = cli.central.request(cli.central.get_overlay_routes_learned, dev.serial, best=best)
        title = f'{dev.name} {"Preferred " if best else ""}overlay routes [italic](site: {dev.site})[/]'
    elif what == "advertised":
        resp = cli.central.request(cli.central.get_overlay_routes_advertised, dev.serial)
        title = f'{dev.name} Advertised routes [italic](site: {dev.site})[/]'

    if resp and "routes" in resp.output:
        resp.output = resp.output["routes"]

    cli.display_results(
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
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_completion, show_default=False,),
    sort_by: SortOverlayInterfaceOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", rich_help_panel="Common Options", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show overlay interfaces
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=("gw", "ap",))
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    resp = cli.central.request(cli.central.get_overlay_interfaces, dev.serial)

    cli.display_results(
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


@app.command()
def connection(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_gw_completion, show_default=False,),
    # sort_by: str = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),  # single entry output, no need to sort
    # reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in alternate table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", rich_help_panel="Common Options", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show overlay connection (OTO/ORO) details (GWs & APs)

    In testing this API endpoint always returned an error (request to ce failed... timed out) for APs.
    You can get similar details using [cyan]cencli tshoot overlay DEVICE[/].
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=("gw", "ap",))
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    resp = cli.central.request(cli.central.get_overlay_connection, dev.serial)

    set_width_cols = {"name": 60}
    caption = None
    if "connection" in resp.output:
        resp.output = resp.output["connection"]
        caption=_build_caption(resp)
    elif "summary" in resp.output:
        resp.output = resp.output["summary"]
        if resp.output.get("admin_status") is False:
            set_width_cols = {"admin status": {"min": 55, "max": 100}}


    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f'{dev.name} Overlay Connection Information [italic](site: {dev.site})[/]',
        caption=caption,
        pager=pager,
        outfile=outfile,
        # sort_by=sort_by,
        # reverse=reverse,
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
