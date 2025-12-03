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
    aos10: bool = typer.Option(False, "--aos10", help="Upgrade new cloned group to AOS10"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Clone a group

    [dark_orange3]:warning:[/]  Tunneled SSIDs are not included in clone operation.
    """
    color = utils.color
    cache_group = common.cache.get_group_identifier(clone_group)
    render.econsole.print(f"Clone group: {color(cache_group.name)} to new group {color(new_group)}")
    if aos10:
        if "gw" not in cache_group.allowed_types:
            common.exit(f"Clone + Upgrade to AOS10 only applies to gateways, Gateways don't appear to be allowed in group {cache_group.name}.  Currently Allowed (according to cache) {cache_group.allowed_types}")
        elif "ap" in cache_group.allowed_types:
            render.econsole.print(
                f"\n:warning:  Clone + Upgrade to AOS10 will result in 'ap' device type being [red]removed/not-cloned[/] from the resulting group [cyan]{new_group}[/], as upgrade to AOS10 for APs is not supported\n"
                f"[cyan]{new_group}[/] can be updated to re-add APs as an allowed device type once it is cloned."
            )

    render.confirm(yes)
    resp = api.session.request(api.configuration.clone_group, cache_group.name, new_group, upgrade_aos10=aos10)
    render.display_results(resp, tablefmt="action", exit_on_fail=True)

    # cache update
    new_data = {**dict(cache_group), "name": new_group} if not aos10 else {**dict(cache_group), "name": new_group, "aos10": True}
    api.session.request(common.cache.update_group_db, new_data)



@app.callback()
def callback():
    """Clone Aruba Central Groups"""
    ...


if __name__ == "__main__":
    app()
