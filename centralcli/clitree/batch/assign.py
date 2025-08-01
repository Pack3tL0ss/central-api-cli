#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich import print

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

from centralcli.strings import ImportExamples

tty = utils.tty
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
    """Perform batch operations"""
    pass


if __name__ == "__main__":
    app()
