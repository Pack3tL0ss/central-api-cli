#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print
import asyncio


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils
    else:
        print(pkg_dir.parts)
        raise e

app = typer.Typer()
color = utils.color


@app.command(short_help="Clone a group")
def group(
    clone_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CLONE]", autocompletion=cli.cache.group_completion),
    new_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CREATE]"),
    aos10: bool = typer.Option(None, "--aos10", help="Upgrade new cloned group to AOS10"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    print(f"Clone group: {color(clone_group)} to new group {color(new_group)}")
    if aos10:
        print(f"    Upgrade cloned group to AOS10: {color(True)}")
        print(
            "\n    [dark_orange]:warning:[/dark_orange]  [italic]Upgrade doesn't always work despite "
            f"returning {color('success')},\n    Group is cloned if {color('success')} is returned "
            "but upgrade to AOS10 may not occur.\n    API method appears to have some caveats."
            "\n    Use [cyan]cencli show groups[/] after clone to verify."
        )

    if cli.confirm(yes):
        resp = cli.central.request(cli.central.clone_group, clone_group, new_group)
        cli.display_results(resp, tablefmt="action", exit_on_fail=True)
        groups = cli.cache.groups_by_name
        # API-FLAW clone and upgrade to aos10 does not work via the API
        new_data = {**groups[clone_group], "name": new_group} if not aos10 else {**groups[clone_group], "name": new_group, "AOSVersion": "AOS10", "Architecture": "AOS10"}
        if groups:
            asyncio.run(
                cli.cache.update_group_db(new_data)
            )



@app.callback()
def callback():
    """
    Clone Aruba Central Groups
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
