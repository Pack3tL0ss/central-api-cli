#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pragma: exclude file
from __future__ import annotations

import typer
from pathlib import Path

from centralcli import common, render
from .batch import examples

app = typer.Typer()

@app.command()
def devices(
    to_workspace: str = common.arguments.dest_workspace,
    import_file: Path = common.arguments.get("import_file", help="A file containing devices to migrate"),
    import_sites: bool = typer.Option(False, "--import-sites", help=f"indicates import file contains sites.  Devices associated withthose sites will be migrated. {render.help_block('import is expected to contain devices')}"),
    site: str = common.options.get("site", help="Migrate all devices associated with a given site"),
    cx_no_retain: bool = typer.Option(True, "--no-cx-retain", help="Pre-provision CX to group by same name in dest workspace.  [dim red]CX existing config will [bold]NOT[/] be retained[/]"),
    show_example: bool = common.options.show_example,
    no_group: bool = typer.Option(False, "--no-group", help="Do not pre-provision any devices to groups"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Migrate devices to a different [green]GreenLake[/] WorkSpace.

    This command will
      remove the association with the Aruba Central app in [green]GreenLake[/] for the existing workspace.
      Add the devices to the destination workspace using the same subscription type.

      By default devices (other than CX) are also pre-provisioned to a group by the same name if it exists in the destination workspace.
      Pre-provisioning CX to a group results in any device level overrides being removed, which is normally not desired.
      To also pre-provision CX use --cx-no-retain

      To forgo group pre-provisioning for all devices use --no-group

    :warning:  Use caution. Test on lab equipment before doing anything with production:bangbang:
    """
    if show_example:
        if import_sites:
            render.console.print(examples.migrate_devs_by_site)
        else:
            render.console.print(examples.migrate_devices)
        return





@app.callback()
def callback():
    """
    Migrate items from one [green]GreenLake[/] Workspace to another.
    """
    pass


if __name__ == "__main__":
    app()
