#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pragma: exclude file
from __future__ import annotations

import asyncio
import csv
from dataclasses import dataclass
import itertools
import json
import time
from pathlib import Path
from typing import Any

import pendulum
import typer

from centralcli import common, config, log, render, utils
from centralcli.cache import Cache, DBAction
from centralcli.classic.api import ClassicAPI
from centralcli.client import BatchRequest
from centralcli.constants import AllDevTypes
from centralcli.response import Response
from centralcli.strings import cli_strings, emoji
from centralcli.environment import env_var

from .batch import examples

app = typer.Typer()


def _create_migrate_file(data: list[dict[str, str]], no_cx_retain: bool = False, no_group: bool = False, to_group: str = None, retry: bool = False, no_sub: bool = False, file: Path = None) -> Path:
    migrate_keys = ["name", "status", "type", "model", "ip", "mac", "serial", "site"]
    if not no_sub:
        migrate_keys += ["subscription"]
    if not no_group:
        data = [{k if k != "group_name" else "group": v for k, v in dev.items()} for dev in data]
        migrate_keys.insert(7, "group")

    out_data = [{key: dev.get(key) for key in migrate_keys} for dev in data]
    _has_cx = bool([d for d in data if d["type"] == "cx"])
    if _has_cx and not no_cx_retain:
        out_data = [{**dev, "retain_config": None if dev["type"] != "cx" else True} for dev in out_data]
    if to_group:
        out_data = [{**dev, "group": to_group} for dev in out_data]

    timestamp = pendulum.now().format("MMDDYY-HHmmss")
    outfile = file or (config.outdir / f"{'migrate' if not retry else 'retry'}-{timestamp}.csv")

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
            render.econsole.print(f"{emoji.warn} Assignment to Aruba Central appears to have failed for {serial}.  Inventory response does not reflect assignment to Aruba Central.")
        elif sub and not inv_resp_by_serial[serial].get("subscription", inv_resp_by_serial[serial].get("services")) == sub.replace("_", "-"):
            render.econsole.print(f'{emoji.warn} Subscription assignment appears to have failed for {serial}.  Sub from inventory response: {inv_resp_by_serial[serial].get("subscription", inv_resp_by_serial[serial].get("services"))}')
        else:
            retry = False

        if retry:
            retry_data += [_data]

    retry_file = None
    if retry_data:
        retry_file = migrate_file.parent / f'retry{migrate_file.name.removeprefix("migrate")}'
        retry_file = migrate_file if len(retry_data) == len(data) else _create_migrate_file(retry_data, retry=True, file=retry_file)
        render.econsole.print(f"{emoji.warn}  Failures appear to have occured with {len(retry_data)} of the {len(data)} devices.")

    return retry_file


def _update_dev_db_status(responses: list[Response]) -> None:
    start = time.perf_counter()
    real_responses = [r for r in responses if r.status != 299 and "greenlake" in r.url.host]  # 299 is returned (no call performed) when the devices are not found in migrate from workspace, this only happens when retrying w/ a previously used migrate file
    deleted = []
    update_data = []
    if real_responses:
        with render.Spinner(f"Updating device status ([red]Down[/]) in monitoring Cache in [cyan]{config.workspace}[/] workspace."):
            try:
                deleted = itertools.chain.from_iterable([r.async_success_devices for r in responses if r.ok])
                update_data = [{"serial": common.cache.get_inv_identifier(_id).serial, "status": "Down"} for _id in deleted]
                if update_data:
                    _ = asyncio.run(common.cache.update_dev_db(update_data, action=DBAction.UPDATE))
            except Exception as e:
                log.exception(f"{repr(e)} during attempt to update device cache with down status after glp device unassignment.")
                render.econsole.print(
                    f"{emoji.warn} {repr(e)} occured when updating monitoring cache to reflect [red]Down[/] status after GLP removal in anticipation they will eventually go down.\n"
                    f"   You will have to run [cyan]cencli show all --ws {config.workspace}[/] to refresh the cache, prior to running the [cyan]--ui-only[/] delete command."
                )
        log.debug(f"_update_dev_db_status, updated {len(update_data)} devices in {round(time.perf_counter() - start, 3)}s")


def _check_for_down_devs(data: list[dict[str, Any]], to_workspace: str, migrate_file: Path) -> list[str]:
    if "status" not in utils.all_keys(data):
        return []

    _msg = []
    stash_dict = {}
    down_devs = [d for d in data if d["status"] == "Down"]
    if down_devs:
        _msg += [
            f"\n{emoji.warn} The following {len(down_devs)} devices are currently down in [cyan]{config.workspace}[/] workspace.  They will still be migrated, but may not come Up in [bright_green]{to_workspace}[/] workspace."
        ]
        for d in down_devs:
            base_msg = f"  [dark_olive_green2]{d['name']}[/]|{utils.color([d['serial'], d['mac']], color_str=['turquoise4', 'cyan'], sep='|')}"
            stash_msg = f"|[cyan]Site[/]: [turquoise2]{d.get('site') or '[red]Not Assigned[/]'}[/]"
            stash_msg += '|[red]NO SUBSCRIPTION ASSIGNED[/]' if not d.get("subscription") else f"|[spring_green2]{d['subscription']}[/]"
            if d.get("archived") is True:
                stash_msg += "|[red]ARCHIVED[/]"
            elif d.get("assigned") is False:
                stash_msg += "|[red]NOT ASSIGNED[/]"
            _msg += [f"{base_msg}{stash_msg}"]
            stash_dict[d["serial"]] = stash_msg.lstrip(' |')

        # capture down devs to reference during verification phase
        down_file = migrate_file.parent / f'down{migrate_file.stem.removeprefix("migrate")}.json'
        down_file.write_text(json.dumps(stash_dict, indent=4, sort_keys=False))

    return _msg


def _verify_and_create_retry(migrate_data: list[dict[str, Any]], migrate_file: Path, caption: list[str], to_workspace: str):
    retry_file = _validate_migration(migrate_data, migrate_file)
    retry_resp = []
    if retry_file:
        render.econsole.print(
            "[bright_green]Attempting to retry [red]failed[/] devices.[/]",
            f"Subsequent retry can be performed using: [cyan]cencli batch add devices {retry_file} --ws {to_workspace}",
            sep="\n"
        )
        retry_resp = common.batch_add_devices(retry_file, yes=True, migrate=True)  # they already confirmed when delete was performed
    else:
        caption.insert(0, f":white_check_mark:  Inventory Validation completed successfully. [green]All devices appear as expected[/] in [cyan]{to_workspace}[/] workspace inventory.\n")
    return retry_resp, caption


def _create_manual_add_file(migrate_data: list[dict[str, Any]]) -> Path:
    timestamp = pendulum.now().format("MMDDYY-HHmmss")
    outfile = config.outdir / f"manual-add-{timestamp}.csv"
    glp_key_map = {
        "serial": "Serial_No",
        "mac": "MAC_Address",
    }

    out_data = [{glp_key_map[k]: v for k, v in inner.items() if k in glp_key_map} for inner in migrate_data]

    with outfile.open('w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=out_data[0].keys())
        writer.writeheader()
        writer.writerows(out_data)

    return outfile


@dataclass
class SwitchInfo:
    serial: str
    port: str


@dataclass
class APInfo:
    serial: str
    site: str
    switch: SwitchInfo


@app.command()
def bounce_aps(
    max_per_site: int = typer.Argument(1, help="The maximum number of APs that will be PoE bounced per site in the event more than 1 are down."),
    ap_lldp_file: Path = typer.Option(..., "--lldp-file", help="The output of [cyan]show aps -n --site-file <site import> --csv --out ...[/].  This file contains the APs switch and port details.", envvar=env_var.migrate_lldp_file, exists=True, show_default=False),
    migrate_file: Path = typer.Option(None, "--migrate-file", help=f"The device file originally used to migrate devices.  {render.help_block('Most recent file in current directory matching patterns: final-moves.csv, migrate-*.csv, devices*')}", exists=True, show_default=False),
    refresh: bool = common.options.get("refresh", help=f"Refresh the cache if cache lookup for AP or connected switch yields no results {render.help_block('No Refresh is performed')}", show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Bounce APs that have been migrated using [cyan]cencli migrate devices[/]

    PoE bounces APs that have been migrated, but have yet to connect to the "migrate to" workspace.

    This command requires the output of [cyan]show aps -n --site-file <site import> --csv --out LLDP_FILE[/] from the migrate from environment.

    Will bounce at most 1 AP per site per run by default.
    """
    dir = Path.cwd()
    if not migrate_file:
        patterns = [dir.glob('final-moves.csv'), dir.glob('migrate-*.csv'), dir.glob('devices*')]
        try:
            migrate_file = max(
                (f for pattern in patterns for f in pattern if f.suffix != ".bak"),
                key=lambda x: x.stat().st_mtime
            )
        except ValueError:
            common.exit("No matching files found.")

    bounced_aps_file = migrate_file.parent / "bounced-aps"
    prev_bounced = []
    spin_pfx = "Fetching [medium_spring_green]device[/] data from import file"
    with render.Spinner(f"{spin_pfx} [dark_violet]{migrate_file.name}[/]", spinner="arrow3") as spinner:
        devs = common._get_import_file(migrate_file, "devices", required_fields=["serial", "type"])
        spinner.succeed()

    with render.Spinner(f"{spin_pfx.replace('device', 'lldp')} [dark_violet]{ap_lldp_file.name}[/]", spinner="arrow3") as spinner:
        required_fields = ["ap_serial", "switch_serial", "switch_port"]
        with ap_lldp_file.open('r', newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            lldp_data = {row["ap_serial"]: {"serial": row["switch_serial"], "port": row["switch_port"]} for row in reader if all([field in row for field in required_fields])}
        spinner.succeed()

    if not lldp_data:
        common.exit(f"Nothing imported from {ap_lldp_file.name}")

    if bounced_aps_file.exists():
        prev_bounced = [line for line in bounced_aps_file.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]

    devs_by_serial = {d["serial"]: d for d in devs if d["type"] in ["ap", "cx", "sw"]}
    cache_devs = common.cache.bulk_dev_cache_lookup(serial_numbers=list(devs_by_serial.keys()), dev_type=["ap", "cx", "sw"], refresh_on_fail=refresh)
    never_checked_in_serials = [serial for serial, cache_dev in zip(list(devs_by_serial.keys()), cache_devs) if cache_dev is None]
    never_checked_in_aps = {k: v for k, v in devs_by_serial.items() if k in never_checked_in_serials and v["type"] == "ap"}
    never_checked_in_switches = {k: v for k, v in devs_by_serial.items() if k in never_checked_in_serials and v["type"] in ["cx", "sw"]}
    aps_by_serial = {k: v for k, v in devs_by_serial.items() if v["type"] == "ap"}

    ap_info_by_site = {}
    no_lldp_info_cnt = 0
    switch_not_checked_in_cnt = 0
    for ap in never_checked_in_aps.values():
        if ap["serial"] not in lldp_data:
            no_lldp_info_cnt += 1
            render.econsole.print(f"[dark_orange_3]Skipping[/] [cyan]{ap['serial']}[/] [dim italic]No LLDP info[/]")
            continue
        if lldp_data[ap["serial"]]["serial"] in never_checked_in_switches:
            switch_not_checked_in_cnt += 1
            render.econsole.print(f"[dark_orange_3]Skipping[/] [cyan]{ap['serial']}[/] [dim italic]Upstream switch has not connected[/]")
            continue
        ap_info_by_site[ap.get("site", "NOSITE")] = {**ap_info_by_site.get(ap.get("site", "NOSITE"), {}), ap["serial"]: {**lldp_data[ap["serial"]]}}

    batch_reqs = []
    queued_by_site = {}
    conf_aps = []
    prev_bounced_cnt = 0
    api = ClassicAPI(config)
    for site, ap_info in ap_info_by_site.items():
        for serial, switch_info in ap_info.items():
            if serial in prev_bounced:
                prev_bounced_cnt += 1
                render.econsole.print(f"[dark_orange_3]Skipping[/] [cyan]{serial}[/] [dim italic]Previously bounced[/]")
                continue
            if queued_by_site.get(site, 0) < max_per_site:
                conf_aps += [aps_by_serial[serial]]
                batch_reqs.append(BatchRequest(api.device_management.send_bounce_command_to_device, switch_info["serial"], "bounce_poe_port", switch_info["port"]))  # TODO this does not factor in devices that have yet to check in
                queued_by_site[site] = queued_by_site.get(site, 0) + 1

    if no_lldp_info_cnt or switch_not_checked_in_cnt or prev_bounced_cnt:
        render.econsole.print()
    if no_lldp_info_cnt:
        render.econsole.print(f"{emoji.warn} {no_lldp_info_cnt} APs were [dark_orange3]skipped[/]. [dim italic]No lldp information[/]")
    if prev_bounced_cnt:
        render.econsole.print(f"{emoji.warn} {prev_bounced_cnt} APs were [dark_orange3]skipped[/]. [dim italic]Previously bounced[/]")
    if switch_not_checked_in_cnt:
        render.econsole.print(f"{emoji.warn} {switch_not_checked_in_cnt} APs were [dark_orange3]skipped[/]. [dim italic]Upstream switch has not connected[/]")

    if not batch_reqs:
        common.exit("No APs found that can be bounced.")

    render.econsole.print(f"\nPoE Bounce the following {len(batch_reqs)} APs {utils.summarize_data(conf_aps)}", emoji=False)
    render.confirm(yes)
    batch_resp = api.session.batch_request(batch_reqs, continue_on_fail=True)
    just_bounced = [ap["serial"] for ap, res in zip(conf_aps, batch_resp) if res.ok]
    bounced_aps_file.write_text("\n".join([*prev_bounced, *just_bounced, ""]))  # The empty str is so there is a \n at the EoF
    _failed_cnt = len(batch_reqs) - len(just_bounced)
    render.display_results(batch_resp, tablefmt="action", caption=f"[bright_green]Success[/]: {len(just_bounced)}{'' if not _failed_cnt else f' [red]Failed[/]: {_failed_cnt}'}")


@app.command()
def combine_files(
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Combine devices from multiple migrate files into 1 large master file.

    [cyan]cencli migrate devices[/] creates [dark_violet]migrate-<timestamp>.csv[/] and [dark_violet]down-<timestamp>.csv[/] when
    migrating by sites.

    If multiple runs are performed, this command combines the various migrate-/down- files into a large master file.
    """
    dir = Path.cwd()
    year = str(pendulum.now().year)[-2:]
    out_file = Path(f"migrate-{dir.name}{year}-999999.csv")
    down_file = Path(f"down-{dir.name}{year}-999999.json")
    down, devs = {}, []

    for file in dir.iterdir():
        if file.name in [out_file.name, down_file.name]:
            continue
        if file.name.startswith("down-"):
            down = {**down, **json.loads(file.read_text())}
        elif file.name.startswith("migrate-"):
            devs += common._get_import_file(file, "devices")

    if not down:
        down = {
            d["serial"]: f'[cyan]Site[/]: [turquoise2]{d.get("site", "?")}[/]|[{"spring_green2" if d.get("subscription") else "red"}]{d.get("subscription", "NO SUBSCRIPTION ASSIGNED")}[/]'
            for d in devs if d["status"] == "Down"
        }

    if devs:
        out_devs = utils.format_table(devs, key_order=list(devs[0].keys()))
        csv_str = render.get_csv_string(out_devs)
        out_file.write_text(csv_str)
        render.econsole.print(f"[medium_spring_green italic]Migrate files combined into[/] [dark_violet]{out_file.name}[/]")
    if down:
        down_file.write_text(json.dumps(down, indent=2, sort_keys=True))
        render.econsole.print(f"{len(down)} [medium_spring_green italic]devices were down prior to migration.[/] down file created: [dark_violet]{down_file.name}[/]")
    if not devs and not down:
        common.exit(f"No migrate files found in {dir.name}")


@app.command()
def devices(
    to_workspace: str = common.arguments.move_workspace,
    import_file: Path = common.arguments.get("import_file", help="A file containing devices to migrate"),
    import_sites: bool = typer.Option(False, "-S", "--import-sites", help=f"indicates import file contains sites.  Devices associated with those sites will be migrated. {render.help_block('import is expected to contain devices')}", envvar=env_var.import_sites),
    site: str = common.options.get("site", "-s", "--site", help="Migrate all devices associated with a given site"),
    group: str = common.options.get("group", "-g", "--group", help="Migrate all devices associated with a given group"),
    to_group: str = common.options.get("group", help="Override the existing group, assign all devices to this group in dest workspace", envvar=env_var.to_group),
    not_group: str = typer.Option(None, "--not-group", help="Exclude devices belonging to a specific group [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]"),
    dev_type: AllDevTypes = typer.Option(None, "--dev-type", help="Only migrate devices of a given type. [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]", show_default=False,),
    not_type: AllDevTypes = typer.Option(None, "--not-type", help="Exclude a specific device type [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]"),
    no_cx_retain: bool = typer.Option(False, "--no-cx-retain", help="Pre-provision CX to group by same name in dest workspace.  [dim red]CX existing config will [bold]NOT[/] be retained[/]"),
    no_group: bool = typer.Option(False, "--no-group", help="Do not pre-provision any devices to groups"),
    no_refresh: bool = common.options.get("no_refresh", "--nr", "--no-refresh", help="Forgo pre-command cache refresh, [dim italic]Applies when --site, --group, or --import-sites :triangular_flag: is provided[/]", envvar=env_var.no_refresh),
    no_sub: bool = typer.Option(False, "--no-sub", help="Ignore subscription from source workspace.  This saves API calls.  [bright_green italic]auto subscribe should be enabled in destination workspace[/]", envvar=env_var.no_sub),
    skip_del: bool = typer.Option(False, help="Skip delete (useful for retry/repeating command)"),
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
    _not_group = None if not not_group else common.cache.get_group_identifier(not_group)
    warnings = [""]

    site_names = []
    if import_file and import_sites:
        site_data = common._get_import_file(import_file, import_type="sites", text_ok=True)
        site_names += [s["name"] for s in site_data]
    if cache_site:
        site_names += [cache_site.name]
    site_names = site_names or None
    conf_caption = []

    if cache_site or cache_group or (import_file and import_sites):  # TODO there are 2 fetches 1 here, and again in batch_delete_devices_glp...
        with render.Spinner(f"Fetching devices associated with provided filters from [cyan]{config.workspace}[/] workspace..."):
            start = time.perf_counter()
            migrate_devs = common.cache.get_inv_mon_devs_from_cache(refresh_on_fail=no_refresh, sites=site_names, group=cache_group, not_group=_not_group, dev_type=dev_type, not_dev_type=not_type)
            log_append = "" if no_refresh else " (includes cache refresh time)"
            log.debug(f"Gathered data for {len(migrate_devs)} from cache in {round(time.perf_counter() - start, 3)}s{log_append}")

        has_cx = bool([d.type for d in migrate_devs if d.type == "cx"])
        if no_group:
            conf_caption += [f"{emoji.info} [cyan] Devices will not be pre-provisioned to associated group in [cyan]{to_workspace}[/] workspace."]
        elif no_cx_retain and has_cx and any([d.group for d in migrate_devs]):
            warnings += [f"{emoji.warn} [cyan]--no-cx-retain[/] :triangular_flag: used.  Any existing configuration on CX devices will be lost."]
        elif has_cx:
            conf_caption += [f"{emoji.info} configuration for CX switches will be retained.  They will not be pre-provisioned to matching group in [cyan]{to_workspace}[/] workspace."]

        data = [dict(d) for d in migrate_devs]
    elif import_file:
        data = common._get_import_file(import_file, import_type="devices")
        all_keys = utils.all_keys(data)
        if "group" in all_keys and "retain_config" not in all_keys:
            warnings += [
                f"{emoji.warn} Migration data provided by import.  You are responsible for ensuring [bright_green]retain_config = True[/] for CX devices. [dim](It should be null/empty-string/unset for other device types)[/]",
                f"   [bold red]Any existing configuration for CX switches will be overwritten[/] if they are pre-assigned to a group in [cyan]{to_workspace}[/] workspace, unless retain_config = True."
            ]
    else:
        common.exit(render._batch_invalid_msg("cencli migrate devices [OPTIONS] [IMPORT_FILE]"))
    if not data:
        common.exit("No devices found to migrate given the provided filters / import file.")

    if no_sub:
        conf_caption += [f"{emoji.info} [cyan]--no-sub[/] provided.  Subscriptions will not be assigned.  [dim italic]Auto Subscribe should be enabled in [cyan]{to_workspace}[/] workspace.[/]"]

    migrate_file = import_file if (import_file and not import_sites) else _create_migrate_file(data, no_cx_retain=no_cx_retain, no_group=no_group, to_group=to_group, no_sub=no_sub)
    warnings += _check_for_down_devs(data, to_workspace=to_workspace, migrate_file=migrate_file)
    warnings += [
        f"{emoji.warn}  If pre-assigning groups, The groups, and configurations should already be in place in [cyan]{to_workspace}[/] workspace.  Configurations will be lost otherwise.",
        f"[italic]Devices will remain in UI in [cyan]{config.workspace}[/] Workspace.[/]",
        f"[italic]Use [cyan]cencli batch delete devices {migrate_file} --ui-only[/] to delete from ui after the devices have gone offline.[/]"
    ]

    migrate_data = utils.format_table(common._get_import_file(migrate_file, "devices"), key_order=["name", "serial", "mac", "status", "type", "model", "group", "site", "subscription"])
    confirm_data = [d if d.get("type", "") != "cx" or not d.get("retain_config") else {**d, "group": "[dark_olive_green2]unprovisioned[/]"} for d in migrate_data]
    render.console.print(f"Migrat{'ing' if yes else 'e'} the following {len(migrate_data)} device{'s' if len(migrate_data) > 1 else ''} from [cyan]{config.workspace}[/] workspace to [bright_green]{to_workspace}[/] workspace")
    render.console.print(f"  {utils.summarize_data(confirm_data).lstrip()}", emoji=False)
    render.console.print(*conf_caption, *warnings, sep="\n", emoji=False)
    yes = render.confirm(yes)

    if skip_del:
        render.econsole.print(f"{emoji.info} Skipping delete calls based on [cyan]--skip-del[/] flag.")
    else:
        resp = common.batch_delete_devices(data, yes=yes, migrate=True, do_retry=True)
        render.display_results(
            resp,
            title=f"Delete devices from [cyan]{config.workspace}[/] workspace [dim italic]([green]GreenLake[/green] Inventory Only)[/]",
            tablefmt="action",
            exit_on_fail=False,
            caption=f"Devices will remain in UI use [cyan]cencli batch delete devices {migrate_file} --ui-only[/] to delete from ui after the devices have gone offline."
        )

        # update status in monitoring cache so --ui-only delete is possible without cache update
        _update_dev_db_status(resp)  # We update here so this can run while they are doing manual csv import

    manual_flow = True if len(migrate_data) > 25 else False  # DEBUG adjust device count back to 125 # DEBUG  # TODO change devices.add_devices to use v1 endpoint which allows 5 devices in each payload

    if manual_flow:  # pragma: no cover requires tty
        manual_add_file = _create_manual_add_file(migrate_data)
        render.console.print(
            "The [green]GreenLake[/] API endpoint for adding devices has a restrictive rate limit.  It's faster to import them in the UI, when adding large batches.\n"
            f"{manual_add_file} has been created.  For use as import file.  Import the devices into [green]GreenLake[/] via the UI"
        )

        render.ask(
            "Enter [bright_green]go[/] to continue [dim italic]after manual csv import[/]",
            choices=["go"]
        )  # pragma: no cover requires tty
    else:
        with render.Spinner(f"Allowing time for {cli_strings.glp} to free up devices for addition to [cyan]{to_workspace}[/] workspace"):
            time.sleep(3)
        with render.Spinner(f"Adding devices to {to_workspace} Workspace"):
            time.sleep(3)

    # need to set up here as we flip the config object to the destination workspace below meaning config.workspace and to_workspace are the same thing after that point.
    caption = [
        f"Run the following after devices show [green]Up[/] in [cyan]{to_workspace}[/] / [red]Down[/] in [cyan]{config.workspace}[/] workspace.",
        f"[cyan]cencli batch move devices {migrate_file} --ws {to_workspace}[/]",
        f"[cyan]cencli batch verify {migrate_file} --ws {to_workspace}",
        f"[cyan]cencli batch delete devices {migrate_file} --ui-only --ws {config.workspace}[/]",
    ]
    if import_file and import_sites:
        caption += [f"[cyan]cencli batch delete sites {import_file} --ws {config.workspace}"]
    title = f"Add Devices to {cli_strings.glp} inventory in [cyan]{to_workspace}[/] workspace. Assign Subscriptions.  Pre-provision to groups (CX depends on retain-config options)"

    # flip environment to destination workspace
    config.workspace = to_workspace
    common.cache = Cache(config=config)

    add_resp = common.batch_add_devices(migrate_file, yes=True, migrate=True, manual_flow=manual_flow)  # pragma: no cover

    retry_resp, caption = _verify_and_create_retry(migrate_data, migrate_file=migrate_file, caption=caption, to_workspace=to_workspace)
    # retry_file = _validate_migration(migrate_data, migrate_file)
    # retry_resp = []
    # if retry_file:
    #     render.econsole.print(
    #         "[bright_green]Attempting to retry [red]failed[/] devices.[/]",
    #         f"Subsequent retry can be performed using: [cyan]cencli batch add devices {retry_file} --ws {to_workspace}",
    #         sep="\n"
    #     )
    #     retry_resp = common.batch_add_devices(retry_file, yes=True, migrate=True)  # they already confirmed when delete was performed
    # else:
    #     caption.insert(0, f":white_check_mark:  Inventory Validation completed successfully. [green]All devices appear as expected[/] in [cyan]{to_workspace}[/] workspace inventory.\n")

    render.display_results([*add_resp, *retry_resp], title=title, tablefmt="action", caption=caption)


@app.callback()
def callback():
    """
    Migrate items from one [green]GreenLake[/] Workspace to another.
    """
    pass


if __name__ == "__main__":
    app()
