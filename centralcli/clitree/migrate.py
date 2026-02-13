#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pragma: exclude file
from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from time import sleep

import pendulum
import typer

from centralcli import common, config, render, utils, log
from centralcli.constants import AllDevTypes
from centralcli.cache import Cache
from centralcli.strings import emoji, cli_strings

from .batch import examples

app = typer.Typer()


def _create_migrate_file(data: list[dict[str, str]], no_cx_retain: bool = False, no_group: bool = False, to_group: str = None, retry: bool = False) -> Path:
    migrate_keys = ["name", "status", "type", "model", "ip", "mac", "serial", "site", "services"]
    if not no_group:
        data = [{k if k != "group_name" else "group": v for k, v in dev.items()} for dev in data]
        migrate_keys.insert(7, "group")

    out_data = [{key: dev.get(key) for key in migrate_keys} for dev in data]
    _has_cx = bool([d for d in data if d["type"] == "cx"])
    if _has_cx and not no_cx_retain:
        out_data = [{**dev, "retain_config": None if dev["type"] != "cx" else True} for dev in out_data]
    if to_group:
        out_data = [{**dev, "group": to_group } for dev in out_data]

    timestamp = pendulum.now().format("MMDDYY-HHmmss")
    outfile = config.outdir / f"{'migrate' if not retry else 'retry'}-{timestamp}.csv"

    with outfile.open('w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=out_data[0].keys())
        writer.writeheader()
        writer.writerows(out_data)

    return outfile


def _validate_migration(data: list[dict[str, str]], migrate_file: Path, subscription: str = None) -> Path | None:
    serials = [d["serial"] for d in data]
    inv_resp = asyncio.run(common.cache.refresh_inv_db(serial_numbers=serials))
    if not inv_resp.ok:
        render.econsole.print(f"Post migration validation skipped due to error fetching inventory {inv_resp.error}.  See logs.")
        return

    desired_by_serial = {d["serial"]: d for d in data}
    inv_resp_by_serial = {d["serial"]: d for d in inv_resp.output}
    retry_data = []
    for serial, _data in desired_by_serial.items():
        retry = True
        sub = subscription or _data.get("subscription")
        if serial not in inv_resp_by_serial:
            render.econsole.print(f"{emoji.warn} Inventory add appears to have failed for {serial}.  Not found in inventory response.")
        elif not inv_resp_by_serial[serial]["assigned"]:
            render.econsole.print(f"{emoji.warn} Assignment to Aruba Central appears to have failed for {serial}.  Inventory Resoinse does not reflect assignment to Aruba Central.")
        elif sub and not inv_resp_by_serial[serial]["services"] == sub.replace("_", "-"):
            render.econsole.print(f"{emoji.warn} Subscription assignment appears to have failed for {serial}.  Sub from inventory response: {inv_resp_by_serial[serial]['services']}")
        else:
            retry = False

        if retry:
            retry_data += [_data]

    retry_file = None
    if retry_data:
        retry_file = migrate_file if len(retry_data) == len(data) else _create_migrate_file(retry_data, retry=True)
        render.econsole.print(f"{emoji.warn}  Failures appear to have occured with {len(retry_data)} of the {len(data)} devices.")

    return retry_file


@app.command()
def devices(
    to_workspace: str = common.arguments.dest_workspace,
    import_file: Path = common.arguments.get("import_file", help="A file containing devices to migrate"),
    import_sites: bool = typer.Option(False, "-S", "--import-sites", help=f"indicates import file contains sites.  Devices associated with those sites will be migrated. {render.help_block('import is expected to contain devices')}"),
    site: str = common.options.get("site", "-s", "--site", help="Migrate all devices associated with a given site"),
    group: str = common.options.get("group", "-g", "--group", help="Migrate all devices associated with a given group"),
    to_group: str = common.options.get("group", help="Override the existing group, assign all devices to this group in dest workspace"),
    not_group: str = typer.Option(None, "--not-group", help="Exclude devices belonging to a specific group [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]"),
    dev_type: AllDevTypes = typer.Option(None, "--dev-type", help="Only migrate devices of a given type. [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]", show_default=False,),
    not_type: AllDevTypes = typer.Option(None, "--not-type", help="Exclude a specific device type [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]"),
    no_cx_retain: bool = typer.Option(False, "--no-cx-retain", help="Pre-provision CX to group by same name in dest workspace.  [dim red]CX existing config will [bold]NOT[/] be retained[/]"),
    no_group: bool = typer.Option(False, "--no-group", help="Do not pre-provision any devices to groups"),
    no_refresh: bool = common.options.get("no_refresh", "--nr", "--no-refresh", help="Forgo pre-command cache refresh, [dim italic]Applies when --site, --group, or --import-sites :triangular_flag: is provided[/]"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Migrate devices to a different [green]GreenLake[/] WorkSpace.

    This command should be ran in the Workspace you are migrating devices from.

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
        render.console.print(render.render_title("device import"))
        render.console.print(examples.migrate_devices)
        render.console.print(render.render_title("site import [dim italic]Devices associated with the provided sites in the 'from workspace' will be migrated to the 'to workspace'[/]"))
        render.console.print(examples.migrate_devs_by_site)
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
    if config.workspace == to_workspace:
        common.exit(f"Migrating from [cyan]{config.workspace}[/] to [cyan]{to_workspace}[/] does not make any sense.  Did you forget [cyan]--ws <workspace>[/] [dim italic](This would be the 'from' WorkSpace)[/]")

    dest_workspace = config.workspaces.get(to_workspace)
    if not dest_workspace:
        common.exit(f"Destination Workspace [magenta]{to_workspace}[/] not found in the config")

    cache_site = None if not site else common.cache.get_site_identifier(site)
    cache_group = None if not group else common.cache.get_group_identifier(group)
    _not_group  = None if not not_group else common.cache.get_group_identifier(not_group)
    warnings = [""]

    if cache_site or cache_group or (import_file and import_sites):
        data = common.get_filtered_devices_w_inventory(refresh=not no_refresh, site=cache_site, group=cache_group, not_group=_not_group, dev_type=dev_type, not_dev_type=not_type, site_import=None if not import_file and import_sites else import_file)
        has_cx = "cx" in [d["type"] for d in data if "type" in d]
        if no_group:
            warnings += [f"{emoji.info} [cyan] Devices will not be pre-provisioned to associated group in [cyan]{to_workspace}[/] workspace."]
        elif no_cx_retain and has_cx and any([d.get("group_name") for d in data]):
            warnings += [f"{emoji.warn} [cyan]--no-cx-retain[/] :triangular_flag: used.  Any existing configuration on CX devices will be lost."]
        elif has_cx:
            warnings += [f"{emoji.info} configuration for CX switches will be retained.  They will not be pre-provisioned to matching group in [cyan]{to_workspace}[/] workspace."]
    elif import_file:
        data = common._get_import_file(import_file, import_type="devices")
        all_keys = utils.all_keys(data)
        if "group" in all_keys and "retain_config" not in all_keys:
            warnings += [
                f"{emoji.warn} Migration data provided by import.  You are responsible for ensuring retain_config = True for CX devices. [dim](It should be null/empty-string/unset for other device types)[/]",
                f"{emoji.warn} Any existing configuration for CX switches will be overwritten if they are pre-assigned to a group in [cyan]{to_workspace}[/] workspace, unless retain_config = True."
            ]
    else:
        common.exit(render._batch_invalid_msg("cencli migrate devices [OPTIONS] [IMPORT_FILE]"))

    if not data:
        common.exit("No devices found to migrate given the provided filters / import file.")

    migrate_file = import_file if (import_file and not import_sites) else _create_migrate_file(data, no_cx_retain=no_cx_retain, no_group=no_group, to_group=to_group)
    conf_caption = [
        f"\n{emoji.warn}  If pre-assigning groups, The groups, and configurations should already be in place in [cyan]{to_workspace}[/] workspace.  Configurations will be lost otherwise.",
        f"[italic]Devices will remain in UI in [cyan]{config.workspace}[/] Workspace.[/]",
        f"[italic]Use [cyan]cencli batch delete devices {migrate_file} --ui-only[/] to delete from ui after the devices have gone offline.[/]"
    ]

    devs = utils.format_table(common._get_import_file(migrate_file, "devices"), key_order = ["name", "serial", "mac", "status", "type", "model", "group", "site", "services"])
    render.console.print(f"Migrat{'ing' if yes else 'e'} the following {len(devs)} device{'s' if len(devs) > 1 else ''} from [cyan]{config.workspace}[/] workspace to [bright_green]{to_workspace}[/] workspace")
    render.console.print(f"  {utils.summarize_data(devs).lstrip()}", emoji=False)
    render.console.print(*conf_caption, *warnings, sep="\n")
    yes = render.confirm(yes)

    resp = common.batch_delete_devices(data, yes=yes, migrate=True)
    render.display_results(
        resp,
        title=f"Delete devices from [cyan]{config.workspace}[/] workspace [dim italic]([green]GreenLake[/green] Inventory Only)[/]",
        tablefmt="action",
        exit_on_fail=False,
        caption=f"Devices will remain in UI use [cyan]cencli batch delete devices {migrate_file} --ui-only[/] to delete from ui after the devices have gone offline."
    )
    # update status in monitoring cache so --ui-only delete is possible without cache update
    real_responses = [r for r in resp if r.status != 299 and "greenlake" in r.url.host]  # 299 is returned (no call performed) when the devices are not found in migrate from workspace, this only happens when retrying w/ a previously used migrate file
    if real_responses:
        with render.Spinner(f"Updating device status ([red]Down[/]) in monitoring Cache in [cyan]{config.workspace}[/] workspace."):
            try:
                deleted = [d["id"] for r in real_responses if r.ok and r.output.get("async operation response") for d in r.output["async operation response"].get("result", {}).get("succeededDevices", [{}]) if "id" in d]
                update_data = [{**common.cache.devices_by_serial.get(common.cache.inventory_by_id[_id].serial, {}), "status": "Down"} for _id in deleted]
                update_data = [d for d in update_data if len(d) > 1]  # inner dict will just be {"status": "Down"} if the dev is not found in dev cache
                if update_data:
                    _ = asyncio.run(common.cache.update_dev_db(update_data))
            except Exception as e:
                log.exception(f"{repr(e)} during attempt to update device cache with down status after glp device unassignment.")
                render.econsole.print(
                    f"{emoji.warn} {repr(e)} occured when updating monitoring cache to reflect [red]Down[/] status after GLP removal in anticipation they will eventually go down.\n"
                    f"You will have to run [cyan]cencli show all --ws {config.workspace}[/] to refresh the cache, prior to running the [cyan]--ui-only[/] delete command."
                )

    with render.Spinner(f"Allowing time for {cli_strings.glp} to free up devices for addition to {to_workspace}"):
        sleep(3)
    with render.Spinner(f"Adding devices to {to_workspace} Workspace"):
        sleep(3)

    # need to set up here as we flip the config object to the destination workspace below meaning config.workspace and to_workspace are the same thing after that point.
    caption = [
        f"Run [cyan]cencli batch delete devices {migrate_file} --ui-only --ws {config.workspace}[/] to remove devices from UI monitoring views in [cyan]{config.workspace}[/] WorkSpace [italic](Once they've gone offline)[/].",
        f"Run [cyan]cencli batch move devices {migrate_file} --ws {to_workspace}[/] to move devices to site and move any cx switches to the final group [dim](with retain configuration option)[/] in the [cyan]{to_workspace}[/] workspace.",
        f"[cyan]cencli batch verify {migrate_file} --ws {to_workspace}[/] can be used to verify {utils.color(['[green]GreenLake[/] Inventory', 'Group', 'Site', '[green]Up[/]/[red]Down[/] status'], sep='|')}"
    ]
    title = f"Add Devices to {cli_strings.glp} inventory in [cyan]{to_workspace}[/] workspace. Assign Subscriptions.  Pre-provision to groups (CX depends on retain-config options)"

    # flip environment to destination workspace
    config.workspace = to_workspace
    common.cache = Cache(config=config)

    add_resp = common.batch_add_devices(migrate_file, yes=True, migrate=True)  # they already confirmed when delete was performed

    retry_file = _validate_migration(data, migrate_file)
    retry_resp = []
    if retry_file:
        render.econsole.print(
            "[bright_green]Attempting to retry [red]failed[/] devices.[/]",
            f"Subsequent retry can be performed using: [cyan]cencli batch add devices {retry_file} --ws {to_workspace}",
            sep="\n"
        )
        retry_resp = common.batch_add_devices(retry_file, yes=True, migrate=True)  # they already confirmed when delete was performed
    else:
        caption += [f":white_check_mark:  Inventory Validation completed successfully. [green]All devices appear as expected[/] in [cyan]{to_workspace}[/] workspace inventory."]

    render.display_results([*add_resp, *retry_resp], title=title, tablefmt="action", caption=caption)



@app.callback()
def callback():
    """
    Migrate items from one [green]GreenLake[/] Workspace to another.
    """
    pass


if __name__ == "__main__":
    app()
