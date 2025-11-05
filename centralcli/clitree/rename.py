#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich import print

from centralcli import common, render
from centralcli.cache import api
from centralcli.constants import iden_meta

from . import update

if TYPE_CHECKING:
    from centralcli.cache import CacheDevice, CacheGroup, CacheSite

app = typer.Typer()


@app.command()
def site(
    site: str = common.arguments.get("site", help="[green3]current[/] site name"),
    new_name: str = typer.Argument(..., show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """
    :office: [bright_green]Rename A Site.[/] :office:
    """
    site: CacheSite = common.cache.get_site_identifier(site)
    print(f"Please Confirm: rename site [red]{site.name}[/red] -> [bright_green]{new_name}[/bright_green]")
    render.confirm(yes)
    print()
    update.site(site.name, address=None, city=None, state=None, zip=None, country=None, new_name=new_name, lat=None, lon=None, yes=True, debug=debug, default=default, workspace=workspace)


@app.command()
def ap(
    ap: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_ap_completion, show_default=False,),
    new_name: str = typer.Argument(..., show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """
    [bright_green]Rename an Access Point[/]
    """
    ap: CacheDevice = common.cache.get_dev_identifier(ap, dev_type="ap")
    print(f"Please Confirm: rename ap [bright_red]{ap.name}[/] -> [bright_green]{new_name}[/]")
    print("    [italic]Will result in 2 API calls[/italic]\n")
    render.confirm(yes)
    resp = api.session.request(api.configuration.update_ap_settings, ap.serial, new_name)
    render.display_results(resp, tablefmt="action")
    if resp.status == 200:  # we don't just check for OK because 299 (no call performed) is returned if the old and new name match according to central
        common.cache.DevDB.update({"name": new_name}, doc_ids=[ap.doc_id])


@app.command()
def group(
    group: str = typer.Argument(..., metavar=iden_meta.group, autocompletion=common.cache.group_completion, show_default=False,),
    new_name: str = typer.Argument(..., show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """
    [green3]Rename a group.[/] [red]AOS8 Only use clone for AOS10 groups[/]

    :pile_of_poo:[red]WARNING: the API endpoint has limited scope where this command will work.[/]:pile_of_poo:
    :pile_of_poo:[red]Clone (or build a new group) are the only options if it does not work.[/]:pile_of_poo:
    """
    group: CacheGroup = common.cache.get_group_identifier(group)

    render.econsole.print(f"Please Confirm: rename group [red]{group.name}[/red] -> [bright_green]{new_name}[/bright_green]")
    render.confirm(yes)
    resp = api.session.request(api.configuration.update_group_name, group.name, new_name)

    # API-FLAW Doesn't actually appear to be valid for any group type
    if not resp and "group already has AOS_10X version set" in resp.output.get("description", ""):  # pragma: no cover  Don't think this message is ever returned now.
        resp.output["description"] = f"{group.name} is an AOS_10X group, " \
            "rename only supported on AOS_8X groups. Use clone."

    render.display_results(resp, tablefmt="action")
    common.exit(code=int(not resp.ok))


@app.callback()
def callback():
    """
    Rename Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()