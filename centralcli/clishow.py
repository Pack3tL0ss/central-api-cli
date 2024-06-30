#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import typer
import time
import pendulum
import asyncio
import sys
import json
import os
from typing import List, Iterable, Literal, Dict
from pathlib import Path
from rich import print
from rich.console import Console
from copy import deepcopy

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response, cleaner, clishowfirmware, clishowwids, clishowbranch, clishowospf, clitshoot, clishowtshoot, clishowoverlay, clishowaudit, clishowcloudauth, clishowmpsk, BatchRequest, caas, render, cli, utils, config, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response, cleaner, clishowfirmware, clishowwids, clishowbranch, clishowospf, clitshoot, clishowtshoot, clishowoverlay, clishowaudit, clishowcloudauth, clishowmpsk, BatchRequest, caas, render, cli, utils, config, log
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    SortInventoryOptions, ShowInventoryArgs, StatusOptions, SortWlanOptions, IdenMetaVars, CacheArgs, SortSiteOptions, SortGroupOptions, SortStackOptions, DevTypes, SortDevOptions,
    SortTemplateOptions, SortClientOptions, SortCertOptions, SortVlanOptions, SortSubscriptionOptions, SortRouteOptions, DhcpArgs, EventDevTypeArgs, ShowHookProxyArgs, SubscriptionArgs,
    AlertTypes, SortAlertOptions, AlertSeverity, SortWebHookOptions, TunnelTimeRange, GenericDevTypes, lib_to_api, what_to_pretty, LIB_DEV_TYPE  # noqa
)
from centralcli.cache import CentralObject

app = typer.Typer()
app.add_typer(clishowfirmware.app, name="firmware")
app.add_typer(clishowwids.app, name="wids")
app.add_typer(clishowbranch.app, name="branch")
app.add_typer(clishowospf.app, name="ospf")
app.add_typer(clishowtshoot.app, name="tshoot")
app.add_typer(clishowoverlay.app, name="overlay")
app.add_typer(clishowaudit.app, name="audit")
app.add_typer(clishowcloudauth.app, name="cloud-auth")
app.add_typer(clishowmpsk.app, name="mpsk")

tty = utils.tty
iden_meta = IdenMetaVars()

class Counts:
    def __init__(self, total: int, up: int, not_checked_in: int, down: int = None ):
        self.total = total
        self.up = up
        self.inventory = not_checked_in
        self.down = down or total - not_checked_in - up

def _build_caption(resp: Response, *, inventory: bool = False, dev_type: GenericDevTypes = None, status: Literal["Up", "Down"] = None) -> str:
    inventory_only = False  # toggled while building cnt_str if no devices have status (meaning called from show inventory)
    def get_switch_counts(data) -> dict:
        dev_types = set([t.get("switch_type", "ERR") for t in data])
        # return {LIB_DEV_TYPE.get(_type, _type): [t for t in data if t.get("switch_type", "ERR") == _type] for _type in dev_types}
        return {
            LIB_DEV_TYPE.get(_type, _type): {
                "total": len(list(filter(lambda x: x["switch_type"] == _type, data))),
                "up": len(list(filter(lambda x: x["switch_type"] == _type and x["status"] == "Up", data)))
            }
            for _type in dev_types
        }

    def get_counts(data: List[Dict], dev_type: Literal["cx", "sw", "ap", "gw"]) -> Counts:
        _match_type = [d for d in data if d["type"] == dev_type]
        _tot = len(_match_type)
        _up = len([d for d in _match_type if d.get("status") and d["status"] == "Up"])
        _inv = len([d for d in _match_type if not d.get("status")])
        return Counts(_tot, _up, _inv)


    if not dev_type:
        if inventory:  # cencli show inventory -v or cencli show all --inv
            status_by_type = {}
            _types = set(d["type"] for d in resp.output)
            for t in _types:
                counts = get_counts(resp.output, t)
                status_by_type[t] = {"total": counts.total, "up": counts.up, "down": counts.down, "inventory_only": counts.inventory}

        else:  # show all [--inv], or show ivnentory -v
            counts_by_type = {**{k: {"total": resp.raw[k][0]["total"], "up": len(list(filter(lambda x: x["status"] == "Up", resp.raw[k][0][k if k != "gateways" or not config.is_cop else "mcs"])))} for k in resp.raw.keys() if k != "switches"}, **get_switch_counts(resp.raw["switches"][0]["switches"])}
            status_by_type = {LIB_DEV_TYPE.get(_type, _type): {"total": counts_by_type[_type]["total"], "up": counts_by_type[_type]["up"], "down": counts_by_type[_type]["total"] - counts_by_type[_type]["up"]} for _type in counts_by_type}
    elif dev_type == "switch":
        counts_by_type = get_switch_counts(resp.raw["switches"])
        status_by_type = {LIB_DEV_TYPE.get(_type, _type): {"total": counts_by_type[_type]["total"], "up": counts_by_type[_type]["up"], "down": counts_by_type[_type]["total"] - counts_by_type[_type]["up"]} for _type in counts_by_type}
    else:
        _tot = len(resp)
        _up = len(list(filter(lambda a: a["status"] == "Up", resp.output)))
        _down = _tot - _up
        status_by_type = {dev_type: {"total": _tot, "up": _up, "down": _down}}

    # Put together counts caption string
    if status:
        _cnt_str = ", ".join([f'[{"bright_green" if status.lower() == "up" else "red"}]{t}[/]: [cyan]{status_by_type[t]["total"]}[/]' for t in status_by_type])
    elif inventory:
        def _get_inv_msg(data: Dict, dev_type: DevTypes) -> str:
            inv_str = '' if not data["inventory_only"] else f" Not checked in: [cyan]{data['inventory_only']}[/]"
            up_down_str = '' if data["up"] + data["down"] == 0 else f'([bright_green]{data["up"]}[/]:[red]{data["down"]}[/])'
            return f'[{"bright_green" if not data["down"] else "red"}]{dev_type}[/]: [cyan]{data["total"]}[/] {up_down_str}{inv_str if up_down_str else ""}'

        _cnt_str = f"Total in inventory: [cyan]{len(resp.output)}[/], "
        _cnt_str = _cnt_str + ", ".join(
            [f'{_get_inv_msg(status_by_type[t], t)}' for t in status_by_type]
        )
        if "(" not in _cnt_str:
            inventory_only = True
    else:
        _cnt_str = ", ".join([f'[{"bright_green" if not status_by_type[t]["down"] else "red"}]{t}[/]: [cyan]{status_by_type[t]["total"]}[/] ([bright_green]{status_by_type[t]["up"]}[/]:[red]{status_by_type[t]["down"]}[/])' for t in status_by_type])

    if status is None or status.lower() != "down":
        try:
            clients = sum([t.get("client_count", 0) for t in resp.output if t.get("client_count") != "-"])
            if clients:
                _cnt_str = f"{_cnt_str}, [bright_green]clients[/]: [cyan]{clients}[/]"
        except Exception as e:
            log.exception(f"Exception occured in _build_caption\n{e}")

    if not inventory_only:
        caption = "  [cyan]cencli show all[/cyan]|[cyan]cencli show inventory -v[/cyan] displays fields common to all device types. "
        caption = f"[reset]{'Counts' if not status else f'{status} Devices'}: {_cnt_str}\n{caption}"
        if not dev_type:
            caption = f"{caption} To see all columns for a given device use [cyan]cencli show <DEVICE TYPE>[/cyan]"
        else:
            caption = f"[reset]Counts: {_cnt_str}"
    else:
        caption = f"[reset]Counts: {_cnt_str}"

    if inventory and not inventory_only:
        caption = f"{caption}\n  [italic green3]Devices lacking name/ip are in the inventory, but have not connected to central.[/]"
    return caption

def show_devices(
    devices: str | Iterable[str] = None, dev_type: Literal["all", "ap", "gw", "cx", "sw", "switch"] = None, include_inventory: bool = False, verbosity: int = 0, outfile: Path = None,
    update_cache: bool = False, group: str = None, site: str = None, label: str = None, status: str = None, state: str = None, pub_ip: str = None,
    do_clients: bool = True, do_stats: bool = False, do_ssids: bool = False, sort_by: str = None, reverse: bool = False, pager: bool = False, do_json: bool = False, do_csv: bool = False,
    do_yaml: bool = False, do_table: bool = False
) -> None:
    caption = None
    central = cli.central
    if update_cache:
        cli.central.request(cli.cache.update_dev_db)

    if group:
        group: CentralObject = cli.cache.get_group_identifier(group)
    if site:
        site: CentralObject = cli.cache.get_site_identifier(site)
    if label:
        label: CentralObject = cli.cache.get_label_identifier(label)

    resp = None
    status = status or state
    params = {
        "group": None if not group else group.name,
        "site": None if not site else site.name,
        "status": None if not status else status.title(),
        "label": None if not label else label.name,
        "public_ip_address": pub_ip,
        "calculate_client_count": do_clients,
        "show_resource_details": do_stats,
        "calculate_ssid_count": do_ssids,
    }

    # if any of these values are set it's a filtered result so we don't update cache
    filtering_params = [
        "group",
        "site",
        "label",
        "public_ip_address"
    ]

    cache_generic_types = {
        "aps": "ap",
        "gateways": "gw",
        "mobility_controllers": "gw",
        "switches": "switch"
    }

    params = {k: v for k, v in params.items() if v is not None}
    if not devices and dev_type is None:
        dev_type = "all"

    default_tablefmt = "rich" if not verbosity and not devices else "yaml"

    if devices:  # cencli show devices <device iden>
        # Asking for details of a specific device implies verbose
        if not verbosity:
            verbosity = 99
        if dev_type:
            dev_type = cache_generic_types.get(dev_type)

        br = cli.central.BatchRequest
        devs = [cli.cache.get_dev_identifier(d, dev_type=dev_type, include_inventory=include_inventory) for d in devices]
        _types = [dev.type for dev in devs]
        reqs = [br(central.get_dev_details, (lib_to_api("monitoring", _type), dev.serial,)) for _type, dev in zip(_types, devs)]
        batch_res = cli.central.batch_request(reqs)

        if do_table and len(_types) > 1:
            _output = [r.output for r in batch_res]
            common_keys = set.intersection(*map(set, _output))
            _output = [{k: d[k] for k in common_keys} for d in _output]
            resp = batch_res[-1]
            resp.output = _output
            caption = f'{caption or ""}\n  Displaying fields common to all specified devices.  Request devices individually to see all fields.'
        else:
            resp = batch_res

        if "cx" in _types:
            caption = f'{caption or ""}\n  mem_total for cx devices is the % of memory currently in use.'
    elif dev_type == "all":  # cencli show all | cencli show devices
        if include_inventory:
            resp = cli.cache.get_devices_with_inventory()
            caption = _build_caption(resp, inventory=True)
            if params.get("show_resource_details", False) is True or params.get("calculate_ssid_count", False) is True:
                caption = f'{caption or ""}\n  [bright_red]WARNING[/]: Filtering options ignored, not valid w/ [cyan]-v[/] (include inventory devices)'
        elif [p for p in params if p in filtering_params]:  # We clean here and pass the data back to the cache update, this allows an update with the filtered data without trucating the db
            resp = central.request(central.get_all_devicesv2, cache=True, **params)  # TODO send get_all_devices kwargs to update_dev_db and evaluate params there to determine if upsert or truncate is appropriate
            if resp.ok and resp.output:
                cache_output = cleaner.get_devices(deepcopy(resp.output), cache=True)
                _ = central.request(cli.cache.update_dev_db, cache_output)
            caption = None if not resp.ok else _build_caption(resp)
        else:  # No filtering params, get update from cache
            if central.get_all_devicesv2 not in cli.cache.updated:
                resp = central.request(cli.cache.update_dev_db, **params)
                caption = _build_caption(resp, status=status)
            else:
                # get_all_devicesv2 already called (to populate/update cache) grab response from cache.  This really only happens if hidden -U option is used
                resp = cli.cache.responses.dev  # TODO should update_client_db return responses.client if get_clients already in cache.updated?
    else:  # cencli show switches | cencli show aps | cencli show gateways (with any params)  No cahce update here
        resp = central.request(central.get_devices, dev_type, **params)
        caption = _build_caption(resp, dev_type=cache_generic_types.get(dev_type), status=status)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default=default_tablefmt)
    title_sfx = [
        f"{k}: {v}" for k, v in params.items() if k not in ["calculate_client_count", "show_resource_details", "calculate_ssid_count"] and v
    ] if not include_inventory else ["including Devices from Inventory"]
    title = "Device Details" if not dev_type else f"{what_to_pretty(dev_type)} {', '.join(title_sfx)}".rstrip()

    # With inventory needs to be serial because inv only devs don't have a name yet.  Switches need serial appended so stack members are unique.
    if include_inventory:
        output_key = "serial"
    elif dev_type and dev_type == "switches":
        output_key = "name+serial"
    else:
        output_key = "name"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        output_by_key=output_key,
        cleaner=cleaner.get_devices,
        verbosity=verbosity,
    )

def download_logo(resp: Response, path: Path, portal: CentralObject) -> None:
    if not resp.output.get("logo"):
        cli.exit(f"Unable to download logo image.  A logo has not been applied to the {resp.output['name']} portal")

    import base64
    file = path / resp.output["logo_name"] if path.is_dir() else path
    if not os.access(file.parent, os.W_OK):
        cli.exit(f"{file.parent} is not writable")

    img_data = base64.b64decode(resp.output["logo"].split(",")[1])
    if file.write_bytes(img_data):
        cli.exit(f"Logo saved to {file}", code=0)
    else:
        cli.exit(
            f"Check {file}, write operation indicated no bytes were written.  Use [cyan]cencli show portals {portal.name} --raw[/] to see raw response including logo data."
        )

@app.command("all")
def all_(
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    # do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics", hidden=False,),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    verbose: int = typer.Option(
        0,
        "-v",
        count=True,
        help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
        show_default=False,
    ),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include devices in Inventory that have yet to connect", show_default=False,),
    sort_by: SortDevOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", rich_help_panel="Common Options", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show details for All devices
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"
    show_devices(
        dev_type='all', outfile=outfile, include_inventory=with_inv, verbosity=verbose, update_cache=update_cache, group=group, site=site, status=status,
        state=state, label=label, pub_ip=pub_ip, do_stats=bool(verbose), do_clients=True, sort_by=sort_by, reverse=reverse,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command()
def devices(
    devices: List[str] = typer.Argument(
        None,
        metavar=iden_meta.dev_many.replace("]", "|'all']"),
        hidden=False,
        # HACK added ctx param to dev_completion
        autocompletion=lambda incomplete: [
            m for m in [("all", "Show all devices"), *[m for m in cli.cache.dev_completion(incomplete=incomplete)]]
            if m[0].lower().startswith(incomplete.lower())
        ],
        help="Show details for a specific device [grey42]\[default: show details for all devices][/]",
        # show_default=False,
    ),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    verbose: int = typer.Option(
        0,
        "-v",
        count=True,
        help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
        show_default=False,
    ),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include devices in Inventory that have yet to connect", show_default=False,),
    sort_by: SortDevOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", rich_help_panel="Common Options", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show details for devices
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    devices = devices if devices is not None else ["all"]

    if "all" in devices:
        dev_type = "all"
        devices = None
    else:
        dev_type = None

    show_devices(
        devices, dev_type=dev_type, include_inventory=with_inv, verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site,
        label=label, status=status, state=state, pub_ip=pub_ip, do_stats=do_stats, do_clients=True,
        sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table
    )


@app.command()
def aps(
    aps: List[str] = typer.Argument(None, metavar=iden_meta.dev_many, hidden=False, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    # do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per AP)"),
    # do_ssids: bool = typer.Option(True, "--ssids", is_flag=True, help="Calculate SSID count (per AP)"),
    neighbors: bool = typer.Option(False, "-n", "--neighbors", help="Show all AP LLDP neighbors for a site \[requires --site]", show_default=False,),
    verbose: int = typer.Option(
        0,
        "-v",
        count=True,
        help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
        show_default=False,
    ),
    sort_by: SortDevOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show details for APs
    """
    if neighbors:
        if site is None:
            print(":x: [bright_red]Error:[/] [cyan]--site <site name>[/] is required for neighbors output.")
            raise typer.Exit(1)

        site = cli.cache.get_site_identifier(site)
        resp = cli.central.request(cli.central.get_topo_for_site, site.id, )
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
        cli.display_results(resp, tablefmt=tablefmt, title="AP Neighbors", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.show_all_ap_lldp_neighbors_for_site)
    else:
        if down:
            status = "Down"
        elif up:
            status = "Up"
        show_devices(
            aps, dev_type="aps", verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label, status=status,
            state=state, pub_ip=pub_ip, do_clients=True, do_stats=True, do_ssids=True,
            sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
            do_table=do_table)

@app.command("switches")
def switches_(
    switches: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    # do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per switch)"),
    verbose: int = typer.Option(
        0,
        "-v",
        count=True,
        help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
        show_default=False,
    ),
    sort_by: SortDevOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show details for switches
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        switches, dev_type='switches', verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=True, do_stats=True,
        sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(name="gateways")
def gateways_(
    gateways: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    # do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per gateway)"),
    verbose: int = typer.Option(
        0,
        "-v",
        count=True,
        help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
        show_default=False,
    ),
    sort_by: SortDevOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show details for gateways
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        gateways, dev_type='gateways', verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=True, do_stats=True,
        sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command("controllers", hidden=True)
def controllers_(
    controllers: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    # do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per switch)"),
    verbose: int = typer.Option(
        0,
        "-v",
        count=True,
        help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
        show_default=False,
    ),
    sort_by: SortDevOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show details for controllers

    Hidden as it is the same as show gateways
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        controllers, dev_type='mobility_controllers', verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=True, do_stats=True, sort_by=sort_by, reverse=reverse,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table)



@app.command()
def stacks(
    switches: List[str] = typer.Argument(None, help="List of specific switches to pull stack details for", metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    sort_by: SortStackOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show details for switch stacks
    """
    if down:
        status = StatusOptions("Down")
    elif up:
        status = StatusOptions("Up")

    if group:
        group: CentralObject = cli.cache.get_group_identifier(group)

    cleaner_kwargs = {"status": status}
    args = ()
    kwargs = {}
    func = cli.central.get_switch_stacks
    if switches:
        devs: List[CentralObject] = [cli.cache.get_dev_identifier(d, dev_type="switch", swack=True,) for d in switches]
        if len(devs) == 1:  # if the specify a we use the details call
            func = cli.central.get_switch_stack_details
            args = (devs[0].swack_id,)
        else: # if the specify multiple hosts we grab info for all stacks and filter in the cleaner
            cleaner_kwargs["stack_ids"] = set([d.swack_id for d in devs])
            if group:
                kwargs = {"group": group.name}

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    resp = cli.central.request(func, *args, **kwargs)

    title = "Switch stack details"
    caption = ""
    if resp:
        if "count" in resp.raw:
            caption = f"Total # of Stacks Returned: [cyan]{resp.raw['count']}[/]"

    cli.display_results(resp, tablefmt=tablefmt, title=title, caption=caption, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_switch_stacks, **cleaner_kwargs)


@app.command(short_help="Show device inventory", help="Show device inventory / all devices that have been added to Aruba Central.")
def inventory(
    dev_type: ShowInventoryArgs = typer.Argument("all"),
    sub: bool = typer.Option(
        None,
        help="Show devices with applied subscription/license, or devices with no subscription/license applied."
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        help="include additional details for devices that have connected to Aruba Central",
        show_default=False,
    ),
    sort_by: SortInventoryOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    if hasattr(dev_type, "value"):
        dev_type = dev_type.value
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    if dev_type == "all":
        title = "Devices in Inventory"
    elif dev_type in ["cx", "sw", "switch"]:
        title = "Switches in Inventory"
    elif dev_type == "gw":
        title = "Gateways in Inventory"
    elif dev_type == "ap":
        title = "APs in Inventory"
    elif dev_type == "vgw":
        title = "Virtual Gateways in Inventory"
    else:
        title = "Inventory"

    if verbose:
        show_devices(
            dev_type='all', outfile=outfile, include_inventory=verbose, do_clients=True, sort_by=sort_by, reverse=reverse,
            pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table
        )
        cli.exit("", code=0)

    resp = cli.central.request(cli.cache.update_inv_db, dev_type=lib_to_api("inventory", dev_type), sub=sub)

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        sort_by=sort_by,
        reverse=reverse,
        caption=_build_caption(resp, inventory=True),
        pager=pager,
        outfile=outfile,
        cleaner=None,  # Cleaner is applied in cache update
    )


# TODO --sort option for date fields sorts converted value, needs to be sorted by epoch before conversion
# TODO break into seperate command group if we can still all show subscription without an arg to default to details
@app.command()
def subscription(
    what: SubscriptionArgs = typer.Argument("details"),
    service: str = typer.Option(None, hidden=True),  # TODO this is for show subscription stats also a couple more options we could allow
    sort_by: SortSubscriptionOptions = typer.Option(None, "--sort", show_default=False,),  # Need to adapt a bit for stats or make sub-command
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting) (vertically)",
        show_default=False,
    ),
) -> None:
    """Show subscription/license details or stats
    """
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich" if what != "stats" else "yaml")
    if what is None or what == "details":
        resp = cli.central.request(cli.central.get_subscriptions)  # TODO might be useful to restore passing license type to subscriptions (filter option)
        title = "Subscription Details"
        _cleaner = cleaner.get_subscriptions
        set_width_cols = {"name": 40}
    elif what == "auto":
        resp = cli.central.request(cli.central.get_auto_subscribe)
        if resp and "services" in resp.output:
            resp.output = resp.output["services"]
        title = "Services with auto-subscribe enabled"
        _cleaner = None
        set_width_cols = None
    elif what == "stats":
        resp = cli.central.request(cli.central.get_subscription_stats)
        title = "Subscription Stats"
        _cleaner = None
        set_width_cols = None
    elif what == "names":
        resp = cli.central.request(cli.cache.update_license_db)
        title = "Valid Subscription/License Names"
        _cleaner = None
        set_width_cols = {"name": 31}
    else:
        raise ValueError("Error in logic evaluating what")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=_cleaner,
        set_width_cols=set_width_cols
    )


# TODO need sort_by enum
@app.command(short_help="Show Swarms (IAP Clusters)")
def swarms(
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by swarm status", show_default=False,),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    up: bool = typer.Option(False, "--up", help="Filter by swarms that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by swarms that are Down", show_default=False),
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by swarm Public IP", show_default=False,),
    name: str = typer.Option(None, "--name", help="Filter by swarm/cluster name", show_default=False,),
    # do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True, rich_help_panel="Common Options"),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """
    [cyan]Show Swarms (IAP Clusters)[/]
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"
    else:
        status = status or state

    resp = cli.central.request(cli.central.get_swarms, group=group, status=status, public_ip_address=pub_ip, swarm_name=name)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.simple_kv_formatter)


# TODO define sort_by fields
@app.command()
def interfaces(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_gw_completion, show_default=False,),
    slot: str = typer.Argument(None, help="Slot name of the ports to query [italic grey42](chassis only)[/]", show_default=False,),
    # stack: bool = typer.Option(False, "-s", "--stack", help="Get intrfaces for entire stack [grey42]\[default: Show interfaces for specified stack member only][/]",),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    verbose: int = typer.Option(0, "-v", count=True, help="Verbose: Show all interface details vertically", show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True, rich_help_panel="Common Options"),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options"),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    """Show interfaces/details

    Command is valid for switches and gateways
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=["gw", "switch"], conductor_only=True,)
    if dev.generic_type == "gw":
        resp = cli.central.request(cli.central.get_gateway_ports, dev.serial)
    else:
        iden = dev.swack_id or dev.serial
        resp = cli.central.request(cli.central.get_switch_ports, iden, slot=slot, stack=dev.swack_id is not None, aos_sw=dev.type == "sw")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich" if not verbose else "yaml")
    title = f"{dev.name} Interfaces"

    caption = []
    if dev.type == "sw":
        caption = [render.rich_capture(":information:  Native VLAN for trunk ports not shown as not provided by API for aos-sw", emoji=True)]

    if resp:
        try:
            up = len([i for i in resp.output if i.get("status").lower() == "up"])
            down = len(resp.output) - up
            caption += [f"  Counts: Total: [cyan]{len(resp.output)}[/], Up: [bright_green]{up}[/], Down: [bright_red]{down}[/]"]
        except Exception as e:
            log.error(f"{e.__class__.__name__} while trying to get counts from {dev.name} interface output")

    # TODO cleaner returns a Dict[dict] assuming "vsx enabled" is the same bool for all ports put it in caption and remove from each item
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption="\n".join(caption),
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.show_interfaces,
        verbosity=verbose,
        dev_type=dev.type
    )


@app.command(help="Show (switch) poe details for an interface")
def poe(
    device: str = typer.Argument(..., metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    port: str = typer.Argument(None, show_default=False, help="Show PoE details for a specific interface",),
    _port: str = typer.Option(None, "--port", show_default=False, hidden=True,),
    powered: bool = typer.Option(False, "-p", "--powered", help="Show only interfaces currently delivering power", show_default=False,),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", hidden=False, rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", hidden=False, rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", rich_help_panel="Formatting",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    verbose: int = typer.Option(0, "-v", count=True, help="Verbose: Show all interface details vertically", show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    port = _port if _port else port
    dev = cli.cache.get_dev_identifier(device, dev_type="switch")
    resp = cli.central.request(cli.central.get_switch_poe_details, dev.serial, port=port, aos_sw=dev.type == "sw")
    resp.output = utils.unlistify(resp.output)
    caption = "  Power values are in watts."
    if resp:
        resp.output = utils.listify(resp.output)  # if they specify an interface output will be a single dict.
        _delivering_count = len(list(filter(lambda i: i.get("poe_detection_status", 99) == 3, resp.output)))
        caption = f"{caption}  Interfaces delivering power: [bright_green]{_delivering_count}[/]"
        if "poe_slots" in resp.output[0] and resp.output[0]["poe_slots"]:  # CX has the key but it appears to always be an empty dict
            caption = f"{caption}\n  Switch Poe Capabilities (watts): Max: [cyan]{resp.output[0]['poe_slots'].get('maximum_power_in_watts', '?')}[/]"
            caption = f"{caption}, Draw: [cyan]{resp.output[0]['poe_slots'].get('power_drawn_in_watts', '?')}[/]"
            caption = f"{caption}, In use: [cyan]{resp.output[0]['poe_slots'].get('power_in_use_in_watts', '?')}[/]"

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml" if verbose else "rich")
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"Poe details for {dev.name}",
        caption=caption,
        sort_by=sort_by,
        reverse=reverse,
        pager=pager,
        outfile=outfile,
        output_by_key="port",
        cleaner=cleaner.get_switch_poe_details,
        verbosity=verbose,
        powered=powered,
        aos_sw=dev.type == "sw"
    )
    # TODO output cleaner / sort & reverse options


@app.command()
def vlans(
    dev_site: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.dev} (vlans for a device) OR {iden_meta.site} (vlans for a site)",
        autocompletion=cli.cache.dev_gw_switch_site_completion,
        show_default=False,
    ),
    # stack: bool = typer.Option(False, "-s", "--stack", help="Get VLANs for entire stack [grey42]\[default: Get VLANs for the individual member switch specified][/]"),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by VLAN status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    sort_by: SortVlanOptions = typer.Option(None, "--sort", help="Field to sort by", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order", rich_help_panel="Formatting"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format", rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", rich_help_panel="Common Options", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show VLANs for device or site

    Command applies to sites, gateways, or switches
    """
    # TODO cli command lacks the filtering options available from method currently.
    central = cli.central
    obj: CentralObject = cli.cache.get_identifier(dev_site, qry_funcs=("dev", "site"), conductor_only=True)

    if up:
        status = "Up"
    elif down:
        status = "Down"
    else:
        if state and not status:
            status = state

    if obj.is_site:
        resp = central.request(central.get_site_vlans, obj.id)
    elif obj.is_dev:
        if obj.generic_type == "switch":
            if obj.swack_id:
                iden = obj.swack_id
                stack = True
            else:
                iden = obj.serial
                stack = False

            resp = central.request(central.get_switch_vlans, iden, stack=stack, aos_sw=obj.type == "sw")
        elif obj.type.lower() == 'gw':
            resp = central.request(central.get_gateway_vlans, obj.serial)
        else:
            print("Command is only valid on gateways and switches")
            raise typer.Exit(1)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{obj.name} Vlans",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_vlans
    )


@app.command()
def dhcp(
    what: DhcpArgs = typer.Argument(..., show_default=False,),
    dev: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.dev} (Valid for Gateways Only) ",
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    no_res: bool = typer.Option(False, "--no-res", is_flag=True, help="Filter out reservations"),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", show_default=False),
    reverse: bool = typer.Option(False, "-r", help="Reverse sort order", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", show_default=False, writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting) (vertically)",
        show_default=False,
    ),
) -> None:
    """Show DHCP pool or lease details (gateways only)
    """
    central = cli.central
    dev: CentralObject = cli.cache.get_dev_identifier(dev, dev_type="gw")

    if what == "server":
        resp = central.request(central.get_dhcp_server, dev.serial)
    else:
        resp = central.request(central.get_dhcp_clients, dev.serial, reservation=not no_res)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    if verbose2:
        print(resp.raw)
    else:
        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=f"{dev.name} DHCP {what.rstrip('s')} details",
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=reverse,
            cleaner=cleaner.get_dhcp,  # TODO CHANGE.. placeholder
        )


@app.command(short_help="Show firmware upgrade status")
def upgrade(
    device: List[str] = typer.Argument(..., metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_completion),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
):
    central = cli.central
    # Allow unnecessary keyword status `cencli show upgrade status <dev>`
    device = [d for d in device if d != "status"]

    if not device:
        cli.exit("Missing required parameter [cyan]<device>[/]")
    elif len(device) > 1:
        cli.exit("Specify only one device.")

    params, dev = {}, None
    dev: CentralObject = cli.cache.get_dev_identifier(device[-1], conductor_only=True)
    if dev.type == "ap":
        params["swarm_id"] = dev.swack_id
    else:
        params["serial"] = dev.serial

    resp = central.request(central.get_upgrade_status, **params)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Upgrade Status" if not dev else f"{dev.name} Upgrade Status",
        pager=pager,
        outfile=outfile
    )


@app.command("cache", help="Show contents of Identifier Cache.", hidden=True)
def cache_(
    args: List[CacheArgs] = typer.Argument(None, show_default=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options"),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", show_default=False, rich_help_panel="Common Options"),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Common Options"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True,),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options"),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    args = ('all',) if not args else args
    for arg in args:
        cache_out = getattr(cli.cache, arg)

        # sort devices so output matches cencli show all
        if isinstance(arg, str) and arg == "all":
            if "devices" in cache_out:
                cache_out["devices"] = sorted(cache_out["devices"], key=lambda i: (i.get("site") or "", i.get("type") or "", i.get("name") or ""))
        elif arg.value == "devices":
            cache_out = sorted(cache_out, key=lambda i: (i.get("site") or "", i.get("type") or "", i.get("name") or ""))

        tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table, default="rich" if "all" not in args else "yaml")
        cli.display_results(
            data=cache_out,
            tablefmt=tablefmt,
            title=f'Cache {arg.title().replace("_", " ")}',
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=reverse,
            output_by_key=None,
            stash=False,
        )


@app.command(short_help="Show groups/details")
def groups(
    sort_by: SortGroupOptions = typer.Option("name", "--sort",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting", hidden=True,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    central = cli.central
    if central.get_all_groups not in cli.cache.updated:
        resp = asyncio.run(cli.cache.update_group_db())
    else:
        resp = cli.cache.responses.group

    caption = f'Total Groups: [cyan]{len(resp.output)}[/], Template Groups: [cyan]{len(list(filter(lambda g: any(g.get("template group", {}).values()), resp.output)))}[/]'

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)
    cli.display_results(resp, tablefmt=tablefmt, title="Groups", caption=caption, pager=pager, sort_by=sort_by, reverse=reverse, outfile=outfile, cleaner=cleaner.show_groups)


@app.command(short_help="Show labels/details")
def labels(
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    central = cli.central
    if central.get_labels not in cli.cache.updated:
        resp = asyncio.run(cli.cache.update_label_db())
    else:
        resp = cli.cache.responses.labels

    tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_yaml=do_yaml)
    cli.display_results(resp, tablefmt=tablefmt, title="labels", pager=pager, outfile=outfile)


@app.command(short_help="Show sites/details")
def sites(
    site: str = typer.Argument(None, metavar=iden_meta.site, autocompletion=cli.cache.site_completion, show_default=False),
    count_state: bool = typer.Option(False, "-s", show_default=False, help="Calculate # of sites per state"),
    count_country: bool = typer.Option(False, "-c", show_default=False, help="Calculate # of sites per country"),
    sort_by: SortSiteOptions = typer.Option("name", "--sort",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options"),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
):
    central = cli.central
    sort_by = None if sort_by == "name" else sort_by  # Default sort from endpoint is by name

    site = None if site and site.lower() == "all" else site
    if not site:
        if central.get_all_sites not in cli.cache.updated:
            resp = asyncio.run(cli.cache.update_site_db())
        else:
            resp = cli.cache.responses.site
    else:
        site = cli.cache.get_site_identifier(site)
        resp = central.request(central.get_site_details, site.id)

    caption = "" if not resp.ok else f'Total Sites: [green3]{resp.raw.get("total", len(resp.output))}[/]'
    counts, count_caption = {}, None
    if resp.ok:
        for do, field in zip([count_state, count_country], ["state", "country"]):
            if do:
                _cnt_list = [site[field] for site in resp.output if site[field]]
                _cnt_dict = {
                    item: _cnt_list.count(item) for item in set(_cnt_list)
                }
                counts = {**counts, **_cnt_dict}

            if counts:
                count_caption = ", ".join([f'{k}: [cyan]{v}[/]' for k, v in counts.items()])
    if count_caption:
        caption = f'[reset]{caption}, {count_caption}[reset][/]'

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Sites" if not site else f"{site.name} site details",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        caption=caption,
    )

    if counts and tablefmt != "rich":
        print(caption)


@app.command(short_help="Show templates/details")
def templates(
    name: str = typer.Argument(
        None,
        help=f"Template: [name] or Device: {iden_meta.dev}",
        autocompletion=cli.cache.dev_template_completion,
        show_default=False,
    ),
    group: List[str] = typer.Argument(None, help="Get Templates for Group", autocompletion=cli.cache.group_completion, show_default=False),
    _group: str = typer.Option(
        None, "--group",
        help="Get Templates for Group",
        hidden=False,
        autocompletion=cli.cache.group_completion,
        show_default=False,
    ),
    device_type: DevTypes = typer.Option(
        None, "--dev-type",
        help="Filter by Device Type",
        show_default=False,
    ),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by dev version Template is assigned to", show_default=False,),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model", show_default=False,),
    #  variablised: str = typer.Option(False, "--with-vars",
    #                                  help="[Templates] Show Template with variable place-holders and vars."),
    sort_by: SortTemplateOptions = typer.Option(None, "--sort", show_default=False, rich_help_panel="Formatting",),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    if _group:
        group = _group
    elif group:
        group = group[-1]

    if group:
        group = cli.cache.get_group_identifier(group).name

    # Allows show templates group WadeLab
    if name and name.lower() == "group":
        name = None

    central = cli.central

    params = {
        # "name": name,
        "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
        "version": version,
        "model": model
    }

    params = {k: v for k, v in params.items() if v is not None}

    if name:
        log_name = name
        name = cli.cache.get_identifier(name, ("dev", "template"), device_type=device_type, group=group)
        if not name:
            typer.secho(f"Unable to find a match for {log_name}.  Listing all templates.", fg="red")

    if not name:
        if not group:
            if not params:  # show templates - Just update and show data from cache
                if central.get_all_templates not in cli.cache.updated:
                    resp = asyncio.run(cli.cache.update_template_db())
                else:
                    # cache updated this session use response from cache update
                    resp = cli.cache.responses.template
            else:
                # Can't use cache due to filtering options
                resp = central.request(central.get_all_templates, **params)
        else:  # show templates --group <group name>
            resp = central.request(central.get_all_templates_in_group, group, **params)
            # TODO update cache on individual grabs
    else:
        if name.is_dev:  # They provided a dev identifier
            resp = central.request(central.get_variablised_template, name.serial)
        elif name.is_template:
            group = group or name.group  # if they provided group via --group we use it
            resp = central.request(central.get_template, group, name.name)
        else:
            print(f"Something went wrong [bright_red blink]{name}[reset]")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    title = "All Templates" if not name else f"{name.name.title()} Template"
    cli.display_results(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, sort_by=sort_by)


@app.command(short_help="Show Variables for all or specific device")
def variables(
    # FIXME completion ... should include "all"
    args: str = typer.Argument(
        None,
        metavar=f"{iden_meta.dev.rstrip(']')}|all]",
        help="Default: 'all'",
        autocompletion=lambda incomplete: [
            m for m in [d for d in [("all", "Show Variables for all templates"), *cli.cache.dev_completion(incomplete=incomplete)]]
            if m[0].lower().startswith(incomplete.lower())
        ] or [],
        show_default=False,
    ),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
):
    central = cli.central

    if args and args != "all":
        args = cli.cache.get_dev_identifier(args)
    else:
        args = ""

    resp = central.request(central.get_variables, () if not args else args.serial)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="json")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Variables" if not args else f"{args.name} Variables",
        pager=pager,
        outfile=outfile,
    )


@app.command()
def lldp(
    device: List[str] = typer.Argument(
        ...,
        metavar=iden_meta.dev_many,
        autocompletion=cli.cache.dev_switch_ap_completion,
        show_default=False,
    ),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
    ),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show AP lldp neighbor

    Valid on APs and CX switches

    Use [cyan]cencli show aps -n --site <SITE>[/] to see lldp neighbors for all APs in a site.
    NOTE: AOS-SW will return LLDP neighbors, but only it reports neighbors for connected Aruba devices managed in Central
    """
    central = cli.central

    devs: List[CentralObject] = [cli.cache.get_dev_identifier(_dev, dev_type=("ap", "switch"), conductor_only=True,) for _dev in device if not _dev.lower().startswith("neighbor")]
    batch_reqs = [BatchRequest(central.get_ap_lldp_neighbor, (dev.serial,)) for dev in devs if dev.type == "ap"]
    batch_reqs += [BatchRequest(central.get_cx_switch_neighbors, (dev.serial,)) for dev in devs if dev.generic_type == "switch" and not dev.swack_id]
    unique_stack_ids = set([dev.swack_id for dev in devs if dev.generic_type == "switch" and dev.swack_id])
    batch_reqs += [BatchRequest(central.get_cx_switch_stack_neighbors, (swack_id,)) for swack_id in unique_stack_ids]
    batch_resp = central.batch_request(batch_reqs)
    # if all([res.ok for res in batch_resp]):
    #     concat_resp = batch_resp[-1]
    #     concat_resp.output = [{"name": f'{dev.name} {neighbor.get("localPort", "")}'.rstrip(), **neighbor} for res, dev in zip(batch_resp, devs) for neighbor in res.output]
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml")

    console = Console()
    for dev, r in zip(devs, batch_resp):
        title = f"{dev.name} LLDP Neighbor information"
        if tablefmt not in ["table", "rich"]:
            console.print(f'[green]{"-" * 5}[/] [cyan bold]{title}[/] [green]{"-" * 5}[/]')
        cli.display_results(
            r,
            tablefmt=tablefmt,
            title=title,
            caption = "  :warning:  [italic dark_olive_green2]AOS-SW only reflects LLDP neighbors that are managed by Aruba Central[/]" if dev.type == "sw" else None,
            pager=pager,
            outfile=outfile,
            output_by_key=["port", "localPort"],
            cleaner=cleaner.get_lldp_neighbor,
        )

@app.command(short_help="Show certificates/details")
def certs(
    name: str = typer.Argument(None, metavar='[certificate name|certificate hash]',),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    sort_by: SortCertOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    resp = cli.central.request(cli.central.get_certificates, name, callback=cleaner.get_certificates)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp, tablefmt=tablefmt, title="Certificates", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse
    )

# TODO show task --device  look up task by device if possible
@app.command(short_help="Show Task/Command status")
def task(
    task_id: str = typer.Argument(..., show_default=False),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show status of previously issued task/command.

    Requires task_id which is provided in the response of the previously issued command.
        Example: [cyan]cencli bounce interface idf1-6300-sw 1/1/11[/] will queue the command
                and provide the task_id.
    """
    resp = cli.central.request(cli.central.get_task_status, task_id)

    cli.display_results(
        resp, tablefmt="action", title=f"Task {task_id} status")


@app.command()
def run(
    device: str = typer.Argument(..., metavar=iden_meta.dev, show_default=False, autocompletion=cli.cache.dev_completion),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Applies to AOS-SW: Output in YAML format [grey42]\[default: JSON][/]", rich_help_panel="Formatting",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", show_default=False, writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show running config for a device

    APs get the last known running config from Central
    Switches and GWs request the running config from the device
    """

    central = cli.central
    dev = cli.cache.get_dev_identifier(device)

    if dev.type == "cx":
        clitshoot.send_cmds_by_id(dev, commands=[6002], pager=pager, outfile=outfile)
        raise typer.Exit(0)
    elif dev.type == "sw":
        clitshoot.send_cmds_by_id(dev, commands=[1022], pager=pager, outfile=outfile)
        raise typer.Exit(0)
    elif dev.type == "gw":
        clitshoot.send_cmds_by_id(dev, commands=[2385], pager=pager, outfile=outfile)
        raise typer.Exit(0)
    else:
        resp = central.request(central.get_device_configuration, dev.serial)

    if isinstance(resp.output, str) and resp.output.startswith("{"):
        try:
            cli_config = json.loads(resp.output)
            cli_config = cli_config.get("_data", cli_config)
            resp.output = cli_config
        except Exception as e:
            log.exception(e)

    if isinstance(resp.output, dict):
        tablefmt = "json" if not do_yaml else "yaml"
    else:
        tablefmt = None

    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile)


# TODO --status does not work
# https://web.yammer.com/main/org/hpe.com/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMTQyNzU1MDg5MTQ0MjE3NiJ9
@app.command("config")
def config_(
    group_dev: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.group_dev_cencli}",
        autocompletion=cli.cache.group_dev_ap_gw_completion,
        help = "Device Identifier, Group Name along with --ap or --gw option, or 'cencli' to see cencli configuration details.",
        show_default=False,
    ),
    device: str = typer.Argument(
        None,
        autocompletion=cli.cache.dev_ap_gw_completion,
        hidden=True,
        show_default=False,
    ),
    do_gw: bool = typer.Option(None, "--gw", help="Show group level config for gateways."),
    do_ap: bool = typer.Option(None, "--ap", help="Show group level config for APs."),
    all: bool = typer.Option(
        False, "-A", "--all",
        help="collect device level configs for all devices of specified type [grey42]1st argument needs to be a group and --gw or --ap needs to be provided[/]",
        show_default=False,
    ),
    status: bool = typer.Option(
        False,
        "--status",
        help="Show config (sync) status. Applies to GWs.",
        hidden=True,
    ),
    # version: str = typer.Option(None, "--ver", help="Version of AP (only applies to APs)"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show Effective Group/Device Config (UI Group) or cencli config.

    Group level configs are available for APs or GWs.
    Device level configs are available for all device types, however
    AP and GW, show what Aruba Central has configured at the group or device level.
    Switches fetch the running config from the device.  [italic]Same as [cyan]cencli show run[/cyan][/italic].

    Examples:
    \t[cyan]cencli show config GROUPNAME --gw[/]\tCentral's Group level config for a GW
    \t[cyan]cencli show config DEVICENAME[/]\t\tCentral's device level config if device is AP or GW, or running config from device if switch
    \t[cyan]cencli show config cencli[/]\t\tcencli configuration information (from config.yaml)
    """
    if group_dev == "cencli":  # Hidden show cencli config
        return _get_cencli_config()

    group_dev: CentralObject = cli.cache.get_identifier(group_dev, ["group", "dev"], device_type=["ap", "gw"])
    if all:  # TODO move this either to cliexport or clibatch (cencli batch export configs)
        if not any([do_gw, do_ap]):
            print(":warning:  Invalid combination [cyan]--all[/] requires [cyan]--ap[/] or [cyan]--gw[/] flag.")
            raise typer.Exit(1)
        elif not group_dev.is_group:
            print(":warning:  Invalid combination [cyan]--all[/] requires first argument to be a group")
            raise typer.Exit(1)
        else:  # TODO make this a sep func  Allow site as first arg
            br = BatchRequest
            if do_gw:
                devs: List[CentralObject] = [CentralObject("dev", d) for d in cli.cache.devices if d["type"] == "gw" and d["group"] == group_dev.name]
                caasapi = caas.CaasAPI(central=cli.central)

                reqs = [br(caasapi.show_config, (group_dev.name, d.mac)) for d in devs]
                res = cli.central.batch_request(reqs)

                outdir = config.outdir / f"{group_dev.name.replace(' ', '_')}_gw_configs"
                outdir.mkdir(parents=True, exist_ok=True)
                for d, r in zip(devs, res):
                    if isinstance(r.output, dict) and "config" in r.output:
                        r.output = r.output["config"]
                    console = Console(emoji=False)
                    console.rule()
                    console.print(f"[bold]Config for {d.rich_help_text}[reset]")
                    console.rule()
                    outfile = outdir / f"{d.name}_gw_dev.cfg"
                    # cli.display_results(r, tablefmt="simple", pager=pager, outfile=outfile)
                    cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)
            if do_ap:
                devs: List[CentralObject] = [CentralObject("dev", d) for d in cli.cache.devices if d["type"] == "ap"]

                reqs = [br(cli.central.get_per_ap_config, d.serial) for d in devs]
                res = cli.central.batch_request(reqs)

                outdir = config.outdir / f"{group_dev.name.replace(' ', '_')}_ap_configs"
                outdir.mkdir(parents=True, exist_ok=True)

                for d, r in zip(devs, res):
                    console = Console(emoji=False)
                    console.rule()
                    console.print(f"[bold]Config for {d.rich_help_text}[reset]")
                    console.rule()
                    outfile = outdir / f"{d.name}_ap_dev.cfg"
                    cli.display_results(r, tablefmt="simple", pager=pager, outfile=outfile)

            raise typer.Exit(0)

    if group_dev.is_group:
        group = group_dev
        if device:
            device = cli.cache.get_dev_identifier(device)
        elif not do_ap and not do_gw:
            cli.exit("Invalid Input, --gw or --ap option must be supplied for group level config.")
    else:  # group_dev is a device iden
        group = cli.cache.get_group_identifier(group_dev.group)
        if device is not None:
            cli.exit("Invalid input enter \[[cyan]Group[/]] \[[cyan]device iden[/]] or \[[cyan]device iden[/]]")
        else:
            device = group_dev

    _data_key = None
    if do_gw or (device and device.generic_type == "gw"):
        if device and device.generic_type != "gw":
            cli.exit(f"Invalid input: --gw option conflicts with {device.name} which is an {device.generic_type}")
        caasapi = caas.CaasAPI(central=cli.central)
        if not status:
            func = caasapi.show_config
            _data_key = "config"
        else:
            func = caasapi.get_config_status
    elif do_ap or (device and device.generic_type == "ap"):
        if device:
            if device.generic_type == "ap":
                func = cli.central.get_per_ap_config
                args = [device.serial]
            else:
                cli.exit(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
        else:
            func = cli.central.get_ap_config
            args = [group.name]
    elif device and device.type == "cx":
        clitshoot.send_cmds_by_id(device, commands=[6002], pager=pager, outfile=outfile)
        cli.exit(code=0)
    elif device and device.type == "sw":
        clitshoot.send_cmds_by_id(device, commands=[1022], pager=pager, outfile=outfile)
        cli.exit(code=0)
    else:
        log.error("Command Logic Failure, Please report this on GitHub.  Failed to determine appropriate function for provided arguments/options", show=True)
        cli.exit()

    # Build arguments cli.central method associated with each device type supported.
    if device:
        if device.generic_type == "ap" or status:
            args = [device.serial]
        else:
            args = [group.name, device.mac]
    else:
        args = [group.name]

    resp = cli.central.request(func, *args)

    if resp and _data_key:
        resp.output = resp.output[_data_key]

    cli.display_results(resp, pager=pager, outfile=outfile)


@app.command( help="Show current access token from cache")
def token(
    no_refresh: bool = typer.Option(False, "--no-refresh", help="Do not refresh tokens first"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    if not no_refresh:
        cli.central.refresh_token()

    tokens = cli.central.auth.getToken()
    if tokens:
        if cli.account not in ["central_info", "default"]:
            print(f"Account: [cyan]{cli.account}")
        print(f"Access Token: [cyan]{tokens.get('access_token', 'ERROR')}")


# TODO clean up output ... single line output
@app.command(short_help="Show device routing table")
def routes(
    device: List[str] = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format [default]", rich_help_panel="Formatting",),
    sort_by: SortRouteOptions = typer.Option(None, "--sort", show_default=False, rich_help_panel="Formatting",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    device = device[-1]  # allow unnecessary keyword "device"
    central = cli.central
    device = cli.cache.get_dev_identifier(device)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    resp = central.request(central.get_device_ip_routes, device.serial)
    if "summary" in resp.output:
        s = resp.summary
        caption = (
            f'max: {s.get("maximum")} total: {s.get("total")} default: {s.get("default")} connected: {s.get("connected")} '
            f'static: {s.get("static")} dynamic: {s.get("dynamic")} overlay: {s.get("overlay")} '
        )
    else:
        caption = ""
    if "routes" in resp.output:
        resp.output = resp.output["routes"]

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{device.name} IP Routes",
        caption=caption,
        sort_by=sort_by,
        reverse=reverse,
        pager=pager,
        outfile=outfile,
        cleaner=cleaner.get_overlay_routes,
    )


@app.command()
def wlans(
    name: str = typer.Argument(None, metavar="[WLAN NAME]", help="Get Details for a specific WLAN", show_default=False,),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", autocompletion=cli.cache.label_completion, show_default=False,),
    site: str = typer.Option(
        None,
        metavar="<site identifier>",
        help="Filter by device status",
        autocompletion=cli.cache.site_completion,
        show_default=False,
    ),
    swarm_id: str = typer.Option(None, help="Filter by swarm", show_default=False,),  # TODO Can add option for --swarm where value is a dev iden
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per SSID)"),
    sort_by: SortWlanOptions = typer.Option(None, "--sort", help="Field to sort by [grey42]\[default: SSID][/]", show_default=False),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    verbose: int = typer.Option(0, "-v", count=True, help="get more details for SSIDs across all AP groups", show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show WLAN(SSID)/details
    """
    central = cli.central

    title = "WLANs (SSIDs)" if not name else f"Details for SSID {name}"
    if group:
        _group: CentralObject = cli.cache.get_group_identifier(group)
        title = f"{title} in group {_group.name}"
        group = _group.name
    if label:
        _label: CentralObject = cli.cache.get_label_identifier(label)
        title = f"{title} with label {_label.name}"
        label = _label.name
    if site:
        _site: CentralObject = cli.cache.get_site_identifier(site)
        title = f"{title} in site {_site.name}"
        site = _site.name

    params = {
        "name": name,
        "group": group,
        "swarm_id": swarm_id,
        "label": label,
        "site": site,
        "calculate_client_count": True,
    }

    # TODO only verbosity 0 currently if group is specified
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    if group:
        resp = central.request(central.get_full_wlan_list, group)
        cli.display_results(resp, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, cleaner=cleaner.get_full_wlan_list, verbosity=verbose)
    elif verbose:
        import json
        group_res = central.request(central.get_groups_properties)
        if group_res:
            ap_groups = [g['group'] for g in group_res.output if 'AccessPoints' in g['properties']['AllowedDevTypes']]
            batch_req = [BatchRequest(central.get_full_wlan_list, group) for group in ap_groups]
            batch_resp = cli.central.batch_request(batch_req)
            out, failed, passed = [], [], []
            for group, res in zip(ap_groups, batch_resp):
                if res.ok:
                    passed += [res]
                    wlan_dict = json.loads(res.output)
                    if wlan_dict.get("wlans"):
                        for wlan in wlan_dict['wlans']:
                            out += [{'group': group, **wlan}]
                else:
                    failed += [res]

            if passed:
                resp = passed[-1]
                resp.output = out
            else:
                resp = failed
        else:
            resp = group_res

        cli.display_results(resp, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, cleaner=cleaner.get_full_wlan_list, verbosity=0)
    else:
        resp = central.request(central.get_wlans, **params)
        cli.display_results(resp, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, cleaner=cleaner.get_wlans)


@app.command()
def cluster(
    group: str = typer.Argument(..., autocompletion=cli.cache.group_completion, show_default=False,),
    ssid: str = typer.Argument(..., autocompletion=cli.cache.label_completion, show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show Cluster mapped to a given group/SSID
    """
    group = cli.cache.get_group_identifier(group)
    resp = cli.central.request(cli.central.get_wlan_cluster_by_group, group.name, ssid)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    if tablefmt == "rich":
        resp.output = [{"SSID": resp.output.get("profile", ""), **d} for d in resp.output.get("gw_cluster_list", resp.output)]
    cli.display_results(resp, tablefmt=tablefmt, title=f"Cluster details for [green]{ssid}[/] in group [green]{group.name}[/]", pager=pager, outfile=outfile, cleaner=cleaner.simple_kv_formatter)


@app.command()
def vsx(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format [default]", rich_help_panel="Formatting",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show VSX details for a CX switch
    """
    central = cli.central
    device: CentralObject = cli.cache.get_dev_identifier(device, dev_type="switch")  # update to cx once get_dev_iden... refactored to support type vs generic_type
    if device.type == "sw":
        cli.exit("This command is only valid for [cyan]CX[/] switches, not [cyan]AOS-SW[/]")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml")
    resp = central.request(central.get_switch_vsx_detail, device.serial)
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"VSX details for {device.name}",
        pager=pager,
        outfile=outfile,
    )


# FIXME show clients wireless <tab completion> does not filter based on type of device
# FIXME show clients wireless AP-NAME does not filter only devices on that AP
# Same applies for wired
@app.command(help="Show clients/details")
def clients(
    client: str = typer.Argument(
        None,
        metavar=iden_meta.client,
        help="Show details for a specific client. [grey42 italic]verbose assumed.[/]",
        autocompletion=cli.cache.client_completion,
        show_default=False,
    ),
    group: str = typer.Option(None, metavar="<Group>", help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, metavar="<Site>", help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, metavar="<Label>", help="Filter by Label", show_default=False,),
    wireless: bool = typer.Option(False, "-w", "--wireless", help="Show only wireless clients", show_default=False,),
    wired: bool = typer.Option(False, "-W", "--wired", help="Show only wired clients", show_default=False,),
    denylisted: bool = typer.Option(False, "-D", "--denylisted", help="Show denylisted clients [grey42 italic](--dev must also be supplied)[/]",),
    device: str = typer.Option(None, "--dev", metavar=iden_meta.dev, help="Filter by Device", autocompletion=cli.cache.dev_client_completion, show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",),
    update_cache: bool = typer.Option(False, "-U", hidden=True,),  # Force Update of cli.cache for testing
    sort_by: SortClientOptions = typer.Option(None, "--sort", show_default=False, rich_help_panel="Formatting",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",),
    verbose: bool = typer.Option(False, "-v", help="additional details (vertically)", show_default=False, rich_help_panel="Formatting",),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
    ),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output",),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    central = cli.central
    # device = utils.listify(device) if device else []
    # device = device if not _dev else [*device, *_dev]
    # TODO test --device and potentially restore multi-dev support
    device = device or []

    kwargs = {}
    dev = None
    title = "All Clients"
    args = tuple()
    if client:
        _client = cli.cache.get_client_identifier(client, exit_on_fail=True)
        kwargs["mac"] = _client.mac
        title = f"Details for client [cyan]{_client.name}[/]|[cyan]{_client.mac}[/]|[cyan]{_client.ip}[/]"
        verbose = True
    elif device:
        dev = cli.cache.get_dev_identifier(device)
        kwargs["serial"] = dev.serial
        title = f"{dev.name} Clients"

    if denylisted:
        if not dev:
            print(":warning:  [cyan]--device[/] is required when [cyan]-D|--denylisted[/] flag is set.")
            raise typer.Exit(1)
        else:
            args = (dev.serial,)
            title = f"{dev.name} Denylisted Clients"
            if any([group, site, label]):
                print(":warning:  [cyan]--group[/], [cyan]--site[/], [cyan]--label[/] options not valid with [cyan]-D|--denylisted[/].  [italic bold]Ignoring[/].")

    if not client:
        if wired:
            args = ("wired", *args)
            title = "All Wired Clients" if not dev else f"{dev.name} Wired Clients"
        elif wireless:
            args = ("wireless", *args)
            title = f"{'All' if not dev else dev.name} Wireless Clients"

    if not denylisted:
        if group:
            kwargs["group"] = cli.cache.get_group_identifier(group).name
            title = f"{title} in group {group}"

        if site:
            kwargs["site"] = cli.cache.get_site_identifier(site).name
            title = f"{title} in site {site}"

        if label:
            kwargs["label"] = cli.cache.get_label_identifier(label).name
            title = f"{title} on devices with label {label}"

    if not denylisted:
        resp = central.request(cli.cache.update_client_db, *args, **kwargs)
    else:
        resp = central.request(cli.central.get_denylist_clients, *args)

    if not resp:
        cli.display_results(resp, exit_on_fail=True)

    # Build Caption Text # TODO move to caption builder
    _count_text = ""
    _last_mac_text = ""
    if not client and not denylisted:
        if wired:
            _count_text = f"{len(resp)} Wired Clients."
            if resp.raw.get("last_client_mac"):
                _count_text = f'{_count_text} [bright_green]Last Wired Mac[/]: [cyan]{resp.raw["last_client_mac"]}[/]'
        elif wireless:
            _count_text = f"{len(resp)} Wireless Clients."
            if resp.raw.get("last_client_mac"):
                _count_text = f'{_count_text} [bright_green]Last Wireless Mac[/]: [cyan]{resp.raw["last_client_mac"]}[/]'
        else:
            _tot = len(resp)
            wlan_raw = list(filter(lambda d: "raw_wireless_response" in d, resp.raw))
            wired_raw = list(filter(lambda d: "raw_wired_response" in d, resp.raw))
            caption_data = {}
            for _type, data in zip(["wireless", "wired"], [wlan_raw, wired_raw]):
                caption_data[_type] = {
                    "count": "" if not data or "total" not in data[0][f"raw_{_type}_response"] else data[0][f"raw_{_type}_response"]["total"],
                    "last_client_mac": "" if not data or "last_client_mac" not in data[0][f"raw_{_type}_response"] else data[0][f"raw_{_type}_response"]["last_client_mac"]
                }
            _count_text = f"[reset]Counts: [bright_green]Total[/]: [cyan]{_tot}[/], [bright_green]Wired[/]: [cyan]{caption_data['wired']['count']}[/], [bright_green]Wireless[/]: [cyan]{caption_data['wireless']['count']}[/]"
            _last_mac_text = f"[bright_green]Last Wired Mac[/]: [cyan]{caption_data['wired']['last_client_mac']}[/], [bright_green]Last Wireless Mac[/]: [cyan]{caption_data['wireless']['last_client_mac']}[/]"


    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    verbose_kwargs = {}
    if not verbose2 and not denylisted:
        verbose_kwargs["cleaner"] = cleaner.get_clients
        verbose_kwargs["cache"] = cli.cache
        verbose_kwargs["verbose"] = verbose

        # filter output on multiple devices
        # TODO maybe restore multi-device looks like was handled in filter
        if dev and isinstance(dev, list):
            verbose_kwargs["filters"] = [d.serial for d in dev]

    if sort_by:
        sort_by = "802.11" if sort_by == "dot11" else sort_by.value.replace("_", " ")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=f"{_count_text} Use -v for more details, -vv for unformatted response.\n  {_last_mac_text}".rstrip() if not verbose and not denylisted else None,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        **verbose_kwargs
    )

# TODO Sortby Enum
@app.command()
def tunnels(
    gateway: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, case_sensitive=False, show_default=False,),
    time_range: TunnelTimeRange = typer.Argument("3H"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting", hidden=True),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format [default]", rich_help_panel="Formatting",),
    sort_by: str = typer.Option(None, "--sort", show_default=False, rich_help_panel="Formatting",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show Branch Gateway/VPNC Tunnel details"""
    dev = cli.cache.get_dev_identifier(gateway, dev_type="gw")
    resp = cli.central.request(cli.central.get_gw_tunnels, dev.serial, timerange=time_range.value)
    caption = None
    if resp:
        if resp.output.get("total"):
            caption = f'Tunnel Count: {resp.output["total"]}'
        if resp.output.get("tunnels"):
            resp.output = resp.output["tunnels"]

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")

    cli.display_results(resp, title=f'{dev.rich_help_text} Tunnels', caption=caption, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=None)



@app.command(short_help="Show client roaming history")
def roaming(
    client: str = typer.Argument(..., metavar=iden_meta.client, autocompletion=cli.cache.client_completion, case_sensitive=False, help="Client username, ip, or mac", show_default=False,),
    start: str = typer.Option(
        None,
        help="Start time of range to collect roaming history, format: yyyy-mm-ddThh:mm (24 hour notation), default past 3 hours.",
    ),
    end: str = typer.Option(None, help="End time of range to collect roaming history, formnat: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    past: str = typer.Option(None, help="Collect roaming history for last <past>, d=days, h=hours, m=mins i.e.: 3h", show_default=False,),
    refresh: bool = typer.Option(False, "--refresh", "-R", help="Cache is used to determine mac if username or ip are provided. This forces a cache update prior to lookup."),
    drop: bool = typer.Option(False, "--drop", "-D", help="(implies -R): Drop all users from existing cache, then refresh.  By default any user that has ever connected is retained in the cache."),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format [default]", rich_help_panel="Formatting",),
    sort_by: SortClientOptions = typer.Option(None, "--sort", show_default=False, rich_help_panel="Formatting",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Show wireless client roaming history.

    If ip or username are provided the client cache is used to lookup the clients mac address.
    The cache is updated anytime a show clients ... is ran, or automatically if the client
    is not found in the cache.

    The -R flag can be used to force a cache refresh prior to performing the disconnect.
    """
    central = cli.central
    # TODO common time function this is re-used code from another func
    time_words = ""
    if start:
        try:
            dt = pendulum.from_format(start, 'YYYY-MM-DDTHH:mm', tz="local")
            start = (dt.int_timestamp)
            if not end:
                time_words = pendulum.from_timestamp(start, tz="local").diff_for_humans()
            else:
                time_words = f'Roaming history from {pendulum.from_timestamp(dt.int_timestamp, tz="local").format("MMM DD h:mm:ss A")}'
        except Exception:
            print("[bright_red]Error:[/bright_red] Value for --start should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
            print(f"  Value: {start} appears to be invalid.")
            raise typer.Exit(1)
    if end:
        try:
            dt = pendulum.from_format(end, 'YYYY-MM-DDTHH:mm', tz="local")
            end = (dt.int_timestamp)
            time_words = f'{time_words} to {pendulum.from_timestamp(dt.int_timestamp, tz="local").format("MMM DD h:mm:ss A")}'
        except Exception:
            print("[bright_red]Error:[/bright_red] Value for --end should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
            print(f"  Value: {end} appears to be invalid.")
            raise typer.Exit(1)
    if past:
        now = int(time.time())
        past = past.lower().replace(" ", "")
        if past.endswith("d"):
            start = now - (int(past.rstrip("d")) * 86400)
        if past.endswith("h"):
            start = now - (int(past.rstrip("h")) * 3600)
        if past.endswith("m"):
            start = now - (int(past.rstrip("m")) * 60)
        time_words = f'Roaming history from [cyan]{pendulum.from_timestamp(start, tz="local").diff_for_humans()}[/cyan] till [cyan]now[/cyan].'

    time_words = f"[cyan]{time_words}[reset]\n" if time_words else "[cyan]roaming history for past 24 hours.\n[reset]"

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose2 else "json")

    if refresh or drop:
        resp = cli.central.request(cli.cache.update_client_db, "wireless", truncate=drop)
        if not resp:
            cli.display_results(resp, exit_on_fail=True)

    mac = utils.Mac(client)
    if not mac.ok:
        client = cli.cache.get_client_identifier(client, exit_on_fail=True)
        mac = utils.Mac(client.mac)

    resp = central.request(central.get_client_roaming_history, mac.cols, from_timestamp=start, to_timestamp=end)
    cli.display_results(resp, title=f"Roaming history for {mac.cols}", tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_client_roaming_history)


def show_logs_cencli_callback(ctx: typer.Context, cencli: bool):
    if ctx.resilient_parsing:  # tab completion, return without validating
        return cencli

    if ctx.params.get("tail", False):
        if ctx.args and "cencli" not in ctx.args:
            raise typer.BadParameter(
                f"{ctx.args[-1]} invalid with -f option.  Use -f --cencli or just -f to follow tail on cencli log file"
            )
        return True

    return cencli


@app.command()
def logs(
    event_id: str = typer.Argument(
        None,
        metavar='[LOG_ID|cencli]',
        help="Show details for a specific log_id or [cyan]cencli[/] to show cencli logs",
        autocompletion=cli.cache.event_completion,
        show_default=False,
    ),
    cencli: bool = typer.Option(False, "--cencli", help="Show cencli logs", callback=show_logs_cencli_callback),
    tail: bool = typer.Option(False, "-f", help="follow tail on log file (implies show logs cencli)", is_eager=True),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", autocompletion=cli.cache.label_completion, show_default=False,),
    site: str = typer.Option(None, metavar=iden_meta.site, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    start: str = typer.Option(None, "-s", "--start", help="Start time of range to collect events, format: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    end: str = typer.Option(None, "-e", "--end", help="End time of range to collect events, formnat: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    past: str = typer.Option("30m", "-p", "--past", help="Collect events for last <past>, d=days, h=hours, m=mins i.e.: 3h",),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter events by device",
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    client_mac: str = typer.Option(None, "--client-mac", help="Filter events by client MAC address", show_default=False,),
    bssid: str = typer.Option(None, help="Filter events by bssid", show_default=False,),
    hostname: str = typer.Option(None, "-H", "--hostname", help="Filter events by hostname (fuzzy match)", show_default=False,),
    dev_type: EventDevTypeArgs = typer.Option(
        None,
        "--dev-type",
        metavar="[ap|switch|gw|client]",
        help="Filter events by device type",
        show_default=False,
    ),
    description: str = typer.Option(None, help="Filter events by description (fuzzy match)", show_default=False,),
    event_type: str = typer.Option(None, "--event-type", help="Filter events by type (fuzzy match)", show_default=False,),  # TODO completion enum
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: str = typer.Option(None, "--sort", show_default=False,),  # TODO create enum in constants.. Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False,
    ),
    # count: int = typer.Option(None, "-n", help="Collect Last n logs",),
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
    verbose2: bool = typer.Option(False, "-vv", help="Show raw unformatted response from Central API Gateway"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show device event logs (last 30m by default) or show cencli logs.

    [italic]Audit logs have moved to [cyan]cencli show audit logs[/cyan][/italic]
    """
    if cencli or (event_id and event_id == "cencli"):
        from centralcli import log
        log.print_file() if not tail else log.follow()
        raise typer.Exit(0)

    # TODO move to common func for use be show logs and show audit logs
    if event_id:
        event_details = cli.cache.get_event_identifier(event_id)
        cli.display_results(
            Response(output=event_details),
            tablefmt="action",
        )
        raise typer.Exit(0)
    else:
        if device:
            device = cli.cache.get_dev_identifier(device)

        if start:
            try:
                dt = pendulum.from_format(start, 'YYYY-MM-DDTHH:mm')
                start = (dt.int_timestamp)
            except Exception:
                typer.secho(f"start appears to be invalid {start}", fg="red")
                raise typer.Exit(1)
        if end:
            try:
                dt = pendulum.from_format(end, 'YYYY-MM-DDTHH:mm')
                end = (dt.int_timestamp)
            except Exception:
                typer.secho(f"end appears to be invalid {start}", fg="red")
                raise typer.Exit(1)
        if past:
            now = int(time.time())
            past = past.lower().replace(" ", "")
            if past.endswith("d"):
                start = now - (int(past.rstrip("d")) * 86400)
            if past.endswith("h"):
                start = now - (int(past.rstrip("h")) * 3600)
            if past.endswith("m"):
                start = now - (int(past.rstrip("m")) * 60)

    api_dev_types = {
        "ap": "ACCESS POINT",
        "switch": "SWITCH",
        "gw": "GATEWAY",
        "client": "CLIENT"
    }

    kwargs = {
        "group": group,
        # "swarm_id": swarm_id,
        "label": label,
        "from_ts": start or int(time.time() - 1800),
        "to_ts": end,
        "macaddr": client_mac,
        "bssid": bssid,
        # "device_mac": None if not device else device.mac,
        "hostname": hostname,
        "device_type": None if not dev_type else api_dev_types[dev_type],
        "site": site,
        "serial": None if not device else device.serial,
        # "level": level,
        "event_description": description,
        "event_type": event_type,
        # "fields": fields,
        # "calculate_total": True,  # Total defaults to True in get_events for benefit of async multi-call
    }

    central = cli.central
    resp = central.request(central.get_events, **kwargs)

    if verbose2:
        tablefmt = "raw"
    else:
        tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    _cmd_txt = "[bright_green] show logs <id>[reset]"
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Device event Logs",
        pager=pager,
        outfile=outfile,
        # TODO move sort_by underscore removal to display_results
        sort_by=sort_by if not sort_by else sort_by.replace("_", " "),  # has_details -> 'has details'
        reverse=reverse,
        set_width_cols={"event type": {"min": 5, "max": 12}},
        cleaner=cleaner.get_event_logs if not verbose else None,
        cache_update_func=cli.cache.update_event_db if not verbose else None,
        caption=f"[reset]Use {_cmd_txt} to see details for an event.  Events lacking an id don\'t have details.",
    )


@app.command(short_help="Show Alerts/Notifications. (last 24h default)", help="Show Alerts/Notifications (for past 24 hours by default).  Notification must be Configured.")
def alerts(
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", autocompletion=cli.cache.null_completion, show_default=False,),
    site: str = typer.Option(None, metavar=iden_meta.site, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    start: str = typer.Option(None, help="Start time of range to collect alerts, format: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    end: str = typer.Option(None, help="End time of range to collect alerts, formnat: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    past: str = typer.Option(None, help="Collect alerts for last <past>, d=days, h=hours, m=mins i.e.: 3h Default: 24 hours", show_default=False,),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter alerts by device",
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    severity: AlertSeverity = typer.Option(None, help="Filter by alerts by severity.", show_default=False,),
    search: str = typer.Option(None, help="Filter by alerts with search term in name/description/category.", show_default=False,),
    ack: bool = typer.Option(None, help="Show only acknowledged (--ack) or unacknowledged (--no-ack) alerts", show_default=False,),
    alert_type: AlertTypes = typer.Option(None, "--type", help="Filter by alert type", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", rich_help_panel="Formatting",),
    sort_by: SortAlertOptions = typer.Option("time", "--sort", rich_help_panel="Formatting",),
    reverse: bool = typer.Option(
        False, "-r",
        help="Reverse Output order",
        show_default=False,
        rich_help_panel="Formatting",
    ),
    verbose: bool = typer.Option(False, "-v", help="Show alerts with original field names and minimal formatting (vertically)"),
    verbose2: bool = typer.Option(False, "-vv", help="Show raw unformatted response from Central API Gateway"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
        rich_help_panel="Common Options",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        rich_help_panel="Common Options",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    if device:
        device = cli.cache.get_dev_identifier(device)

    if alert_type:
        alert_type = "user_management" if alert_type == "user" else alert_type
        alert_type = "ids_events" if alert_type == "ids" else alert_type

    if severity:
        severity = severity.title() if severity != "info" else severity.upper()

    time_words = ""
    if start:
        try:
            dt = pendulum.from_format(start, 'YYYY-MM-DDTHH:mm', tz="local")
            start = (dt.int_timestamp)
            if not end:
                time_words = pendulum.from_timestamp(start, tz="local").diff_for_humans()
            else:
                time_words = f'Alerts from {pendulum.from_timestamp(dt.int_timestamp, tz="local").format("MMM DD h:mm:ss A")}'
        except Exception:
            print("[bright_red]Error:[/bright_red] Value for --start should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
            print(f"  Value: {start} appears to be invalid.")
            raise typer.Exit(1)
    if end:
        try:
            dt = pendulum.from_format(end, 'YYYY-MM-DDTHH:mm', tz="local")
            end = (dt.int_timestamp)
            time_words = f'{time_words} to {pendulum.from_timestamp(dt.int_timestamp, tz="local").format("MMM DD h:mm:ss A")}'
        except Exception:
            print("[bright_red]Error:[/bright_red] Value for --end should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
            print(f"  Value: {end} appears to be invalid.")
            raise typer.Exit(1)
    if past:
        now = int(time.time())
        past = past.lower().replace(" ", "")
        if past.endswith("d"):
            start = now - (int(past.rstrip("d")) * 86400)
        if past.endswith("h"):
            start = now - (int(past.rstrip("h")) * 3600)
        if past.endswith("m"):
            start = now - (int(past.rstrip("m")) * 60)
        time_words = f'Alerts from [cyan]{pendulum.from_timestamp(start, tz="local").diff_for_humans()}[/cyan] till [cyan]now[/cyan].'

    time_words = f"[cyan]{time_words}[reset]\n" if time_words else "[cyan]Alerts in past 24 hours.\n[reset]"

    kwargs = {
        "group": group,
        "label": label,
        "from_ts": start,
        "to_ts": end,
        "serial": None if not device else device.serial,
        "site": site,
        'severity': severity,
        "search": search,
        "type": alert_type,
        'ack': ack,
    }

    central = cli.central
    resp = central.request(central.get_alerts, **kwargs)

    if resp.ok:
        if len(resp) == 0:
            resp.output = "No Alerts"
        else:
            time_words = f"[reset][cyan]{len(resp)}{' active' if not ack else ' '}[reset] {time_words}"

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
    title = "Alerts/Notifications (Configured Notification Rules)"
    if device:
        title = f"{title} [reset]for[cyan] {device.generic_type.upper()} {device.name}|{device.serial}[reset]"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_alerts if not verbose else None,
        caption=time_words,
    )


@app.command(short_help="Show alert/notification configuration.")
def notifications(
    search: str = typer.Option(None, help="Filter by alerts with search term in name/description/category."),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: str = typer.Option("category", "--sort",),
    reverse: bool = typer.Option(
        False, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False
    ),
    # verbose: bool = typer.Option(False, "-v", help="Show alerts with original field names and minimal formatting (vertically)"),
    verbose2: bool = typer.Option(False, "-vv", help="Show unformatted response from Central API Gateway"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show alert/notification configuration.

    Display alerty types, notification targets, and rules.
    """
    central = cli.central
    resp = central.request(central.central_get_notification_config, search=search)

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    title = "Alerts/Notifications Configuration (Configured Notification Targets/Rules)"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        # TODO lacks cleaner cleaner=
    )


@app.command(short_help="Re-display output from Last command.", help="Re-display output from Last command.  (No API Calls)")
def last(
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: str = typer.Option(None, "--sort",),
    reverse: bool = typer.Option(
        False, "-r",
        help="Reverse Output order",
        show_default=False
    ),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    if not config.last_command_file.exists():
        print("[red]Unable to find cache for last command.")
        raise typer.Exit(1)

    kwargs = config.last_command_file.read_text()
    import json
    kwargs = json.loads(kwargs)

    last_format = kwargs.get("tablefmt", "rich")
    kwargs["tablefmt"] = cli.get_format(do_json, do_yaml, do_csv, do_table, default=last_format)
    if not kwargs.get("title") or "Previous Output" not in kwargs["title"]:
        kwargs["title"] = f"{kwargs.get('title') or ''} Previous Output " \
                        f"{cleaner._convert_epoch(int(config.last_command_file.stat().st_mtime))}"
    data = kwargs["outdata"]
    del kwargs["outdata"]

    cli.display_results(
        data=data, outfile=outfile, sort_by=sort_by, reverse=reverse, pager=pager, stash=False, **kwargs
    )


@app.command(help="Show configured webhooks")
def webhooks(
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting",),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", rich_help_panel="Formatting",),
    sort_by: SortWebHookOptions = typer.Option(None, "--sort", rich_help_panel="Formatting", show_default=False,),
    reverse: bool = typer.Option(
        False, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        rich_help_panel="Formatting",
        show_default=False
    ),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        rich_help_panel="Common Options",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        rich_help_panel="Common Options",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    if sort_by is not None:
        sort_by = sort_by.name
    ...
    resp = cli.central.request(cli.central.get_all_webhooks)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="WebHooks",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        fold_cols=["urls", "wid"],
        cleaner=cleaner.get_all_webhooks
    )


# TODO callbacks.py send all validation to callbacks
def hook_proxy_what_callback(ctx: typer.Context, what: ShowHookProxyArgs):
    if ctx.resilient_parsing:  # tab completion, return without validating
        return what

    if ctx.params.get("tail", False):
        if what is None:
            what = ShowHookProxyArgs("logs")
        elif what != "logs":
            raise typer.BadParameter(f"-f (follow tail) is only valid with 'logs' command not '{what}'")

    return "pid" if what is None else what.value


@app.command(short_help="Show WebHook Proxy details/logs", hidden=not hook_enabled)
def hook_proxy(
    what: ShowHookProxyArgs = typer.Argument(None, callback=hook_proxy_what_callback),
    tail: bool = typer.Option(False, "-f", help="follow tail on log file (implies show hook-proxy logs)", is_eager=True),
    brief: bool = typer.Option(False, "-b", help="Brief output for 'pid' and 'port'"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    def _get_process_details() -> tuple:
        for p in psutil.process_iter(attrs=["name", "cmdline"]):
            if p.info["cmdline"] and True in ["wh_proxy" in x for x in p.info["cmdline"][1:]]:
                for flag in p.cmdline()[::-1]:
                    if flag.startswith("-"):
                        continue
                    elif flag.isdigit():
                        port = flag
                        break
                return p.pid, port

    if what == "logs":
        from centralcli import log
        log.print_file() if not tail else log.follow()
    else:
        proc = _get_process_details()
        if not proc:
            print("WebHook Proxy is not running.")
            raise typer.Exit(1)

        br = proc[1] if what == "port" else proc[0]
        _out = f"[{proc[0]}] WebHook Proxy is listening on port: {proc[1]}" if not brief else br
        print(_out)
        raise typer.Exit(0)


@app.command()
def archived(
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show archived devices"""
    resp = cli.central.request(cli.central.get_archived_devices)
    cli.display_results(resp, tablefmt="yaml")


# TODO sort_by / reverse tablefmt options add verbosity 1 to cleaner
@app.command()
def portals(
    portal: List[str] = typer.Argument(
        None,
        metavar="[name|id]",
        help="show details for a specific portal profile [grey42]\[default: show summary for all portals][/]",
        autocompletion=cli.cache.portal_completion,
        show_default=False,),
    logo: bool = typer.Option(
        False,
        "-L", "--logo",
        metavar="PATH",
        help=f"Download logo for specified portal to specified path. [cyan]Portal argument is requrired[/] [grey42]\[default: {Path.cwd()}/<original_logo_filename>[/]]",
        show_default = False,
        writable=True,
    ),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", show_default=False,),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", hidden=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", hidden=True),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show Configured Guest Portals, details for a specific portal, or download logo for a specified portal"""
    path = Path.cwd()
    if portal and len(portal) > 2:
        cli.exit("Too many Arguments")
    elif len(portal) > 1:
        if not logo:
            cli.exit("Too many Arguments")
        path = Path(portal[-1])
        if not path.is_dir() and not path.parent.is_dir():
            cli.exit(f"[cyan]{path.parent}[/] directory not found, provide full path with filename, or an existing directory to use original filename")

    portal = portal[0] if portal else portal

    if portal is None:
        resp: Response = cli.central.request(cli.cache.update_portal_db)
        _cleaner = cleaner.get_portals
    else:
        p: CentralObject = cli.cache.get_name_id_identifier("portal", portal)
        resp: Response = cli.central.request(cli.central.get_portal_profile, p.id)
        _cleaner = cleaner.get_portal_profile
        if logo and resp.ok:
            download_logo(resp, path, p)  # this will exit CLI after writing to file

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml" if portal else "rich")
    cli.display_results(resp, tablefmt=tablefmt, title="Portals", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=_cleaner, fold_cols=["url"],)


# TODO add sort_by completion
@app.command()
def guests(
    portal_id: str = typer.Argument(..., ),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by"),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", hidden=True),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", hidden=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Show Guests configured for a Portal

    You need to use `cencli show portals` to get the portal id
    friendly name and completion for portals coming soon
    """
    resp = cli.central.request(cli.central.get_visitors, portal_id, )
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse)


@app.command()
def version(
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
) -> None:
    """Show current cencli version, and latest available version.
    """
    cli.version_callback()


def _get_cencli_config(
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:

    try:
        from centralcli import config
    except (ImportError, ModuleNotFoundError):
        pkg_dir = Path(__file__).absolute().parent
        if pkg_dir.name == "centralcli":
            sys.path.insert(0, str(pkg_dir.parent))
            from centralcli import config

    omit = ["deprecation_warning", "webhook", "snow"]
    out = {k: str(v) if isinstance(v, Path) else v for k, v in config.__dict__.items() if k not in omit}
    out["webhook"] = None if not config.webhook else config.webhook.dict()
    out["snow"] = None if not config.snow else config.snow.dict()

    resp = Response(output=out)

    cli.display_results(resp, stash=False, tablefmt="yaml")


@app.callback()
def callback():
    """
    Show Details about Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
