#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

import typer

from centralcli import cache, cleaner, common, render
from centralcli.cache import api

app = typer.Typer()


@app.command()
def health(
    site: str = common.arguments.get("site", default=None, help=f"Show branch health for a specific site. {render.help_block('All Sites')}"),
    wan_down: bool = typer.Option(False, "--wan-down", help="Show branches with wan uplinks or tunnels Down."),
    down: bool = typer.Option(None, "--down", help="Show branches with down devices."),
    verbose: int = common.options.verbose,
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
):
    """Show Branch Health statistics"""
    _site = None if not site else cache.get_site_identifier(site)
    resp = api.session.request(api.other.get_branch_health, name=None if not site else _site.name)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cf = "[italic dark_olive_green2]"
    caption = f"[reset]{cf}Branch Count: [reset][cyan italic]{len(resp)}[/]"
    title = "Branch Health"
    if down:
        data = [d for d in resp.output if d["device_down"] > 0]
        caption = f"{caption}{cf} Showing [/][cyan]{len(data)}[/]{cf} branches that have [/][bright_red]down[/] {cf}devices."
        title = f"{title} - Branches with [bright_red]down[/] devices"
        resp.output = data
    elif wan_down:
        data = [d for d in resp.output if d["wan_tunnels_down"] > 0 or d["wan_uplinks_down"] > 0]
        caption = f"{caption}{cf} Showing [/][cyan]{len(data)}[/]{cf} branches that have tunnels or uplinks [/][bright_red]down[/]."
        title = f"{title} - Branches with [bright_red]down[/] WAN links"
        resp.output = data

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_branch_health if not verbose else None,
        caption=f"{caption}\n"
    )


@app.callback()
def callback():
    """
    Show branch health
    """
    pass


if __name__ == "__main__":
    app()
