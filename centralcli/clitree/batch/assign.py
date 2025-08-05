#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from centralcli import cli
from centralcli.strings import ImportExamples

app = typer.Typer()


@app.command()
def subscriptions(
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    workspace: str = cli.options.workspace,
) -> None:
    """Assign Subscriptions to devices
    """
    if show_example:
        examples = ImportExamples()
        print(examples.assign_subscriptions)
        return

    if not import_file:
        cli.exit(cli._batch_invalid_msg("cencli batch assign subscriptions [OPTIONS] [IMPORT_FILE]"))

    data = cli._get_import_file(import_file, import_type="devices")
    resp = cli.batch_assign_subscriptions(data, yes=yes)
    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """Batch assign subscriptions [dim italic](based on data from import file)[/]"""
    pass


if __name__ == "__main__":
    app()
