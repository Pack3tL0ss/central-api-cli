#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import common, render

from . import examples

app = typer.Typer()


@app.command()
def subscriptions(
    import_file: Path = common.arguments.import_file,
    _tags: list[str] = typer.Argument(hidden=True),  # HACK because list[str] does not work for typer.Option
    tags: list[str] = typer.Option(None, "-t", "--tags", help="tags to be assigned to all imported devices in format [cyan]tagname1 = tagvalue1, tagname2 = tagvalue2[/]"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Assign Subscriptions to devices."""
    if show_example:
        render.console.print(examples.assign_subscriptions, emoji=False)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch assign subscriptions [OPTIONS] [IMPORT_FILE]"))

    tag_dict = None if not tags else common.parse_var_value_list([*tags, *_tags], error_name="tags")

    data = common._get_import_file(import_file, import_type="devices", subscriptions=True)
    resp = common.batch_assign_subscriptions(data, tags=tag_dict, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """Batch assign subscriptions [dim italic](based on data from import file)[/]"""
    pass


if __name__ == "__main__":
    app()
