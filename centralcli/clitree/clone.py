#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio

import typer

from centralcli import cli, utils
from centralcli.cache import api

app = typer.Typer()


@app.command()
def group(
    clone_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CLONE]", autocompletion=cli.cache.group_completion),
    new_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CREATE]"),
    aos10: bool = typer.Option(None, "--aos10", help="Upgrade new cloned group to AOS10"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    workspace: str = cli.options.workspace,
) -> None:
    """Clone a group

    [dark_orange3]:warning:[/]  Tunneled SSIDs are not included in clone operation.
    """
    color = utils.color
    cli.econsole.print(f"Clone group: {color(clone_group)} to new group {color(new_group)}")
    if aos10:
        cli.econsole.print(f"    Upgrade cloned group to AOS10: {color(True)}")
        cli.econsole.print(
            "\n    [dark_orange3]:warning:[/dark_orange]  [italic]Upgrade doesn't always work despite "
            f"returning {color('success')},\n    Group is cloned if {color('success')} is returned "
            "but upgrade to AOS10 may not occur.\n    API method appears to have some caveats."
            "\n    Use [cyan]cencli show groups[/] after clone to verify."
        )

    if cli.confirm(yes):
        resp = api.session.request(api.configuration.clone_group, clone_group, new_group)
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
    ...


if __name__ == "__main__":
    app()
