#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pragma: exclude file
from __future__ import annotations

import csv
from pathlib import Path
from time import sleep

import pendulum
import typer

from centralcli import common, config, render, utils
from centralcli.cache import Cache
from centralcli.classic.api import ClassicAPI
from centralcli.client import Session
from centralcli.constants import AllDevTypes

from .batch import examples

app = typer.Typer()


def _write_migrate_file(data: list[dict[str, str]], cx_no_retain: bool = False, no_group: bool = False) -> Path:
    migrate_keys = ["name", "status", "type", "model", "ip", "mac", "serial", "site", "services"]
    if not no_group:
        data = [{k if k != "group_name" else "group": v for k, v in dev.items()} for dev in data]
        migrate_keys.insert(7, "group")

    out_data = [{key: dev.get(key) for key in migrate_keys} for dev in data]
    _has_cx = bool([d for d in data if d["type"] == "cx"])
    if _has_cx and not cx_no_retain:
        out_data = [{**dev, "retain_config": None if dev["type"] != "cx" else True} for dev in out_data]

    timestamp = pendulum.now().format("MMDDYY-HHmmss")
    outfile = config.outdir / f"migrate-{timestamp}.csv"

    with outfile.open('w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=out_data[0].keys())
        writer.writeheader()
        writer.writerows(out_data)

    return outfile


@app.command()
def devices(
    to_workspace: str = common.arguments.dest_workspace,
    import_file: Path = common.arguments.get("import_file", help="A file containing devices to migrate"),
    import_sites: bool = typer.Option(False, "--import-sites", help=f"indicates import file contains sites.  Devices associated with those sites will be migrated. {render.help_block('import is expected to contain devices')}"),
    site: str = common.options.get("site", help="Migrate all devices associated with a given site"),
    group: str = common.options.get("group", help="Migrate all devices associated with a given group"),
    dev_type: AllDevTypes = typer.Option(None, "--dev-type", help="Only migrate devices of a given type. [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]", show_default=False,),
    no_cx_retain: bool = typer.Option(False, "--no-cx-retain", help="Pre-provision CX to group by same name in dest workspace.  [dim red]CX existing config will [bold]NOT[/] be retained[/]"),
    show_example: bool = common.options.show_example,
    not_type: AllDevTypes = typer.Option(None, "--not-type", help="Exclude a specific device type [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]"),
    not_group: str = typer.Option(None, "--not-group", help="Exclude devices belonging to a specific group [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]"),
    no_group: bool = typer.Option(False, "--no-group", help="Do not pre-provision any devices to groups"),
    no_refresh: bool = common.options.get("no_refresh", help="Forgo pre-command cache refresh, [dim italic]Applies when --site, --group, or --import-sites :triangular_flag: is provided[/]"),
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
        if import_sites:  # TODO one example string explaining both
            render.console.print(examples.migrate_devs_by_site)
        else:
            render.console.print(examples.migrate_devices)
        return
    if (site or group) and import_file:
        common.exit("Invalid combination of Options/Arguments provide IMPORT_FILE (argument) or one of [cyan]--site[/], [cyan]--group[/].  Not both.")
    if group and not_group:
        common.exit("Invalid combination of Options/Arguments provide [cyan]--group[/] or [cyan]--not-group[/].  Not both.")
    if not to_workspace:
        provide_str = (
            "Provide [cyan]--example[/] to see example import file. [red blink]-or-[/]\n"
            "Provide required [bright_red]to_workspace[/] argument along with either [bright_green]IMPORT_FILE[/] or at least one of [cyan]--site[/], [cyan]--group[/]"
        )
        common.exit(render._batch_invalid_msg("cencli migrate devices [OPTIONS] [IMPORT_FILE]", provide=provide_str))

    dest_workspace = config.workspaces.get(to_workspace)
    if not dest_workspace:
        common.exit(f"Destination Workspace [magenta]{to_workspace}[/] not found in the config")

    cache_site = None if not site else common.cache.get_site_identifier(site)
    cache_group = None if not group else common.cache.get_group_identifier(group)
    _not_group  = None if not not_group else common.cache.get_group_identifier(not_group)

    if cache_site or cache_group or (import_file and import_sites):
        data = common.get_filtered_devices_w_inventory(refresh=not no_refresh, site=cache_site, group=cache_group, not_group=_not_group, dev_type=dev_type, not_dev_type=not_type, site_import=None if not import_file and import_sites else import_file)
    elif import_file:
        data = common._get_import_file(import_file, import_type="devices")
    else:
        common.exit(render._batch_invalid_msg("cencli migrate devices [OPTIONS] [IMPORT_FILE]"))

    if not data:
        common.exit("No devices found to migrate given the provided filters / import file.")

    migrate_file = import_file if (import_file and not import_sites) else _write_migrate_file(data, cx_no_retain=no_cx_retain, no_group=no_group)

    devs = utils.format_table(common._get_import_file(migrate_file, "devices"))

    render.display_results(data=devs, title=f"Migrat{'ing' if yes else 'e'} the following {len(devs)} device{'s' if len(devs) > 1 else ''} from {config.workspace} workspace to {to_workspace} workspace", caption=f"Devices will be pre-assigned to group with same name in {to_workspace} workspace. (unless retain_config marked True)")
    yes = render.confirm(yes)
    resp = common.batch_delete_devices(data, yes=yes)
    render.display_results(
        resp,
        title=f"Delete devices from [cyan]{config.workspace}[/] workspace [dim italic]([green]GreenLake[/green] Inventory Only)[/]",
        tablefmt="action",
        exit_on_fail=False,
        caption=f"Devices will remain in UI use [cyan]cencli batch delete devices {migrate_file} --ui-only[/] to delete from ui after the devices have gone offline."
    )

    with render.Spinner(f"Allowing time for [green]GreenLake[/] to free up devices for addition to {to_workspace}"):
        sleep(3)
    with render.Spinner(f"Adding devices to {to_workspace} Workspace"):
        sleep(3)

    # need to set up here as we flip the config object to the destination workspace below meaning config.workspace and to_workspace are the same thing
    caption = [
        f"Run [cyan]cencli batch delete devices {migrate_file} --ui-only --ws {config.workspace}[/] to remove devices from UI monitoring views in [cyan]{config.workspace}[/] WorkSpace [italic](Once they've gone offline)[/].",
        f"Run [cyan]cencli batch move devices {migrate_file} --ws {to_workspace}[/] to move devices to site and move any cx switches to the final group [dim](with retain configuration option)[/] in the [cyan]{to_workspace}[/] workspace."
    ]
    title = f"Add Devices to [green]GreenLake[/] inventory in [cyan]{to_workspace}[/] workspace. Assign Subscriptions.  Pre-provision devices to groups (outside of CX switches they need to be moved after to retain current config)"

    # TODO need less convoluted way to flip auth to new workspace in existing session
    # TODO need to verify pre-provisioned group exists on dest side
    # dest_config = Config(config.dir, workspace=to_workspace)
    # common.cache = Cache(config=dest_config)
    # dest_api_clients = APIClients(config=config)
    config.workspace = to_workspace
    # cache.set_config(config)
    common.cache = Cache(config=config)
    dest_session = Session(config.classic.base_url, workspace_name=to_workspace)
    dest_api = ClassicAPI(config=config)
    dest_api.session = dest_session

    add_resp = common.batch_add_devices(migrate_file, yes=True, migrate=True, api=dest_api)  # they already confirmed when delete was performed
    render.display_results(add_resp, title=title, tablefmt="action", caption=caption)



@app.callback()
def callback():
    """
    Migrate items from one [green]GreenLake[/] Workspace to another.
    """
    pass


if __name__ == "__main__":
    app()
