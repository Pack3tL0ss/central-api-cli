#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import common, render
from centralcli.strings import ImportExamples

app = typer.Typer()


@app.command()
def subscriptions(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Assign Subscriptions to devices
    """
    if show_example:
        examples = ImportExamples()
        render.console.print(examples.assign_subscriptions)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch assign subscriptions [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, import_type="devices")
    resp = common.batch_assign_subscriptions(data, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """Batch assign subscriptions [dim italic](based on data from import file)[/]"""
    pass


if __name__ == "__main__":
    app()
