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
    site: str = typer.Argument(None, metavar=iden_meta.site, autocompletion=cli.cache.site_completion),
    wan_down: bool = typer.Option(False, "--wan-down", help="Show branches with wan uplinks or tunnels Down."),
    down: bool = typer.Option(None, "--down", help="Show branches with down devices."),
    sort_by: str = typer.Option(None, "--sort",),  # Uses post formatting field headers
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
    central = cli.central
    cli.cache(refresh=update_cache)

    resp = central.request(central.get_brach_health, name=site)
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
