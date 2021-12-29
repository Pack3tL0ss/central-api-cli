#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print
import asyncio


# Detect if called from pypi installed package or via cloned github repo (development)
# TODO should be able to do this in __init__
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
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes

    print(f"Clone group: {color(clone_group)} to new group {color(new_group)}")
    if aos10:
        print(f"    Upgrade cloned group to AOS10: {color(True)}")
        print(
            "\n    [dark_orange]WARNING[/dark_orange]: [italic]Upgrade doesn't always work despite "
            f"returning {color('success')},\n    Group is cloned if {color('success')} is returned "
            "but upgrade to AOS10 may not occur.\n    API method appears to have some caveats."
        )

    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.request(cli.central.clone_group, clone_group, new_group)
        if resp:
            groups = cli.cache.groups
            if groups:
                groups = {g["name"]: {"template group": g["template group"]} for g in groups}
                # TODO put non async it async wrapper in cache.py
                asyncio.run(
                    cli.cache.update_group_db({"name": new_group,  **groups[clone_group]})
                )

        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Clone Aruba Central Groups
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
