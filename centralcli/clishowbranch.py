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

from centralcli.constants import IdenMetaVars  # noqa

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


@app.command(help="Show Branch Health statistics", short_help="Show Branch Health statistics")
def health(
    site: str = typer.Argument(None, metavar=iden_meta.site, autocompletion=cli.cache.site_completion, show_default=False,),
    wan_down: bool = typer.Option(False, "--wan-down", help="Show branches with wan uplinks or tunnels Down."),
    down: bool = typer.Option(None, "--down", help="Show branches with down devices."),
    verbose: int = cli.options.verbose,
    sort_by: str = cli.options.sort_by,
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
    central = cli.central

    resp = central.request(central.get_branch_health, name=site)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

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

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_branch_health if not verbose else None,
        # wan_down=wan_down,
        # down=down,
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
