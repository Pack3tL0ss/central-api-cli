#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import common, render

from . import examples

app = typer.Typer()


@app.command()
def aps(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    reboot: bool = typer.Option(False, "--reboot", "-R", help="Automatically reboot device if IP or VLAN is changed [dim italic]Reboot is required for changes to take effect when IP or VLAN settings are changed[/]"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update per-ap-settings or ap-altitude (at AP level) in mass based on settings from import file

    Use [cyan]--example[/] to see expected import file format and required fields.
    """
    if show_example:
        print(examples.update_aps)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch update aps [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, "devices")
    common.batch_update_aps(data, yes=yes, reboot=reboot)


@app.command()
def devices(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    reboot: bool = typer.Option(False, "--reboot", "-R", help="Automatically reboot device if IP or VLAN is changed [dim italic]Reboot is required for changes to take effect when IP or VLAN settings are changed[/]"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update devices in GreenLake

    Use [cyan]--example[/] to see expected import file format and required fields.
    """
    if show_example:
        print(examples.update_aps)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch update aps [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, "devices")
    common.batch_update_aps(data, yes=yes, reboot=reboot)


@app.callback()
def callback():
    """Batch update devices (GreenLake Inventory) / aps."""
    pass


if __name__ == "__main__":
    app()
