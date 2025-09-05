#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import typer

from centralcli import common, render, utils
from centralcli.cache import api

app = typer.Typer()


@app.command()
def group(
    clone_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CLONE]", autocompletion=common.cache.group_completion),
    new_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CREATE]"),
    aos10: bool = typer.Option(None, "--aos10", help="Upgrade new cloned group to AOS10"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Clone a group

    [dark_orange3]:warning:[/]  Tunneled SSIDs are not included in clone operation.
    """
    color = utils.color
    render.econsole.print(f"Clone group: {color(clone_group)} to new group {color(new_group)}")
    if aos10:
        render.econsole.print(f"    Upgrade cloned group to AOS10: {color(True)}")
        render.econsole.print(
            "\n    [dark_orange3]:warning:[/dark_orange3]  [italic]Upgrade doesn't always work despite "
            f"returning {color('success')},\n    Group is cloned if {color('success')} is returned "
            "but upgrade to AOS10 may not occur.\n    API method appears to have some caveats."
            "\n    Use [cyan]cencli show groups[/] after clone to verify."
        )

    if render.confirm(yes):
        resp = api.session.request(api.configuration.clone_group, clone_group, new_group)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)
        groups = common.cache.groups_by_name

        # API-FLAW clone and upgrade to aos10 does not work via the API
        new_data = {**dict(groups[clone_group]), "name": new_group} if not aos10 else {**groups[clone_group], "name": new_group, "AOSVersion": "AOS10", "Architecture": "AOS10"}
        if groups:
            api.session.request(common.cache.update_group_db, new_data)



@app.callback()
def callback():
    """
    Clone Aruba Central Groups
    """
    ...


if __name__ == "__main__":
    app()
