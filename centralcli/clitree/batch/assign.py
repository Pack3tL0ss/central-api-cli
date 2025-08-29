#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import cache, common, render

from . import examples

app = typer.Typer()


@app.command()
def subscriptions(
    import_file: Path = common.arguments.import_file,
    _tags: list[str] = typer.Argument(None, metavar="", hidden=True),  # HACK because list[str] does not work for typer.Option
    tags: list[str] = typer.Option(None, "-t", "--tags", help="Tags to be assigned to [bright_green]all[/] imported devices in format [cyan]tagname1 = tagvalue1, tagname2 = tagvalue2[/]"),
    sub: str = common.options.get(
        "subscription",
        help="Assign this subscription to [bright_green]all[/] devices found in import [red italic](overrides subscription in import if defined)[/]",
        autocompletion=cache.sub_completion,
    ),  # TODO sub_completion ... get_sub_identifier add match capability based on subscription key, this is what is visible in GLP
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Assign Subscriptions to devices.

    [cyan]--sub <subscription name|key|glp_id>[/] can be used to specify the subscription.  It will be applied to [bright_green]all[/] devices found in import [red italic](even if the device has a subsciption defined in the import)[/]
    [cyan]--tags ...[/] can also be used to assign tags to all devices in import.  This in addition to any per-device tags found within the import, it's cumulative, not an override.
    """
    if show_example:
        render.console.print(examples.assign_subscriptions, emoji=False)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch assign subscriptions [OPTIONS] [IMPORT_FILE]"))

    _tags = _tags or []  # in case they use the form --tags tagname=tagvalue which would not populate _tags
    tag_dict = None if not tags else common.parse_var_value_list([*tags, *_tags], error_name="tags")

    data = common._get_import_file(import_file, import_type="devices", subscriptions=True)
    resp = common.batch_assign_subscriptions(data, tags=tag_dict, subscription=sub, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """Batch assign subscriptions [dim italic](based on data from import file)[/]"""
    pass


if __name__ == "__main__":
    app()
