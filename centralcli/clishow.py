# -*- coding: utf-8 -*-
#!/usr/bin/env python3

from __future__ import annotations
import typer
import pendulum
import sys
import json
import os
from datetime import datetime
from typing import List, Iterable, Literal, Dict, Any, Tuple, TYPE_CHECKING
from pathlib import Path
import getpass
from jinja2 import Template
from rich import print
from rich.console import Console
from rich.markup import escape



try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import (
        Response, cleaner, clishowfirmware, clishowwids, clishowbranch, clishowospf, clitshoot, clishowtshoot, clishowoverlay, clishowaudit, clishowcloudauth, clishowmpsk, clishowbandwidth,
        BatchRequest, caas, render, cli, utils, config, log
    )
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import (
            Response, cleaner, clishowfirmware, clishowwids, clishowbranch, clishowospf, clitshoot, clishowtshoot, clishowoverlay, clishowaudit, clishowcloudauth, clishowmpsk, clishowbandwidth,
            BatchRequest, caas, render, cli, utils, config, log
        )
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    SortInventoryOptions, ShowInventoryArgs, StatusOptions, SortWlanOptions, IdenMetaVars, CacheArgs, SortSiteOptions, SortGroupOptions, SortStackOptions, DevTypes, SortDevOptions, SortLabelOptions,
    SortTemplateOptions, SortClientOptions, SortCertOptions, SortVlanOptions, SortSubscriptionOptions, SortRouteOptions, DhcpArgs, EventDevTypeArgs, ShowHookProxyArgs, SubscriptionArgs, AlertTypes,
    SortAlertOptions, AlertSeverity, SortWebHookOptions, GenericDevTypes, TimeRange, RadioBandOptions, SortDhcpOptions, SortArchivedOptions, LicenseTypes, LogLevel, SortPortalOptions, DeviceStatus,
    DeviceTypes, GenericDeviceTypes, lib_to_api, what_to_pretty, lib_to_gen_plural, LIB_DEV_TYPE  # noqa
)
from centralcli.cache import CentralObject
from .objects import DateTime, ShowInterfaceFilters
from .strings import cron_weekly
from .cache import CacheDevice
from .response import CombinedResponse
from .models import Device

if TYPE_CHECKING:
    from .cache import CacheSite, CacheGroup, CacheLabel, CachePortal
    from tinydb.table import Document


app = typer.Typer()
app.add_typer(clishowfirmware.app, name="firmware")
app.add_typer(clishowwids.app, name="wids")
app.add_typer(clishowbranch.app, name="branch")
app.add_typer(clishowospf.app, name="ospf")
app.add_typer(clishowtshoot.app, name="ts")
app.add_typer(clishowoverlay.app, name="overlay")
app.add_typer(clishowaudit.app, name="audit")
app.add_typer(clishowcloudauth.app, name="cloud-auth")
app.add_typer(clishowmpsk.app, name="mpsk")
app.add_typer(clishowbandwidth.app, name="bandwidth")

tty = utils.tty
iden_meta = IdenMetaVars()

class Counts:
    def __init__(self, total: int, up: int, not_checked_in: int, down: int = None ):
        self.total = total
        self.up = up
        self.inventory = not_checked_in
        self.down = down or total - not_checked_in - up

def _get_switch_counts(data: List[Dict[str, Any]] | None) -> List[Dict[str: Dict[str: int]]] | None:
    """parse response data to determine switch counts by switch type

    Args:
        data (List[Dict[str, Any]]): Combined resp.output data from API, with data for any or all device types.

    Returns:
        List[Dict[str: Dict[str: int]]] | None: Returns a dict with total and up keys available for each switch type.
            i.e. {"cx": {"total": 10, "up": 9}, "sw": {"total": 3, "up": 3}}
            Returns None, if data was None
    """
    if data is None:
        return {}
    dev_types = set([t.get("switch_type", "ERR") for t in data])

    return {
        LIB_DEV_TYPE.get(_type, _type): {
            "total": len(list(filter(lambda x: x["switch_type"] == _type, data))),
            "up": len(list(filter(lambda x: x["switch_type"] == _type and x["status"] == "Up", data)))
        }
        for _type in dev_types
    }

def _get_counts(data: List[dict], dev_type: DeviceTypes) -> Counts:
    _match_type = [d for d in data if d["type"] == dev_type]
    _tot = len(_match_type)
    _up = len([d for d in _match_type if d.get("status") == "Up"])
    _inv = len([d for d in _match_type if not d.get("status")])
    return Counts(_tot, _up, _inv)

def _get_counts_with_inv(data: List[dict]) -> dict:
    """parse combined output attr of inventory and monitoring responses to determine counts by device type.

    Args:
        data (List[dict]): Combined resp.output for monitoring and inventory response.

    Returns:
        dict: dictionary with counts keyed by type.  i.e.: {"cx": {"total": 12, "up": 10, "down": 1, "inventory_only": 1}}
    """
    status_by_type = {}
    _types = set(d["type"] for d in data)
    for t in _types:
        counts = _get_counts(data, t)
        status_by_type[t] = {"total": counts.total, "up": counts.up, "down": counts.down, "inventory_only": counts.inventory}

    return status_by_type

def _get_inv_msg(data: Dict[str, Any], dev_type: DeviceTypes) -> str:
    inv_str = '' if not data["inventory_only"] else f" Not checked in: [cyan]{data['inventory_only']}[/]"
    up_down_str = '' if data["up"] + data["down"] == 0 else f'([bright_green]{data["up"]}[/]:[red]{data["down"]}[/])'
    return f'[{"bright_green" if not data["down"] else "red"}]{dev_type}[/]: [cyan]{data["total"]}[/] {up_down_str}{inv_str if up_down_str else ""}'

def _build_device_caption(resp: Response, *, inventory: bool = False, dev_type: GenericDevTypes = None, status: DeviceStatus = None, verbosity: int = 0) -> str:
    inventory_only = False  # toggled while building cnt_str if no devices have status (meaning called from show inventory)
    if not dev_type:
        if inventory:  # cencli show inventory -v or cencli show all --inv
            status_by_type = _get_counts_with_inv(resp.output)
        else:
            def url_to_key(url) -> str:
                path_end = url.split("/")[-1]
                return path_end if path_end != "mobility_controllers" else "mcs"

            counts_by_type = {
                **{
                    url_to_key(path): {
                        "total": resp.raw[path].get("total", 0),
                        "up": len(list(filter(lambda x: x["status"] == "Up", resp.raw[path].get(url_to_key(path), []))))
                    } for path in resp.raw.keys() if not path.endswith("switches")
                },
                **_get_switch_counts(resp.raw.get("/monitoring/v1/switches", {}).get("switches"))
            }
            status_by_type = {LIB_DEV_TYPE.get(_type, _type): {"total": counts_by_type[_type]["total"], "up": counts_by_type[_type]["up"], "down": counts_by_type[_type]["total"] - counts_by_type[_type]["up"]} for _type in counts_by_type}
    elif dev_type == "switch":
        if inventory:
            status_by_type = _get_counts_with_inv(resp.output)
        else:
            counts_by_type = _get_switch_counts(resp.raw["/monitoring/v1/switches"]["switches"])
            status_by_type = {LIB_DEV_TYPE.get(_type, _type): {"total": counts_by_type[_type]["total"], "up": counts_by_type[_type]["up"], "down": counts_by_type[_type]["total"] - counts_by_type[_type]["up"]} for _type in counts_by_type}
    else:
        counts = _get_counts(resp.output, dev_type=dev_type)
        status_by_type = {dev_type: {"total": counts.total, "up": counts.up, "down": counts.down}}
        if inventory:
            status_by_type[dev_type]["inventory_only"] = counts.inventory

    # Put together counts caption string
    if status:
        _cnt_str = ", ".join([f'[{"bright_green" if status.lower() == "up" else "red"}]{status.capitalize()} {t if t != "ap" else "APs"}[/]: [cyan]{status_by_type[t]["total"]}[/]' for t in status_by_type])
    elif inventory:
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
        caption = "  [cyan]cencli show all[/cyan]|[cyan]cencli show inventory -v[/cyan] displays fields common to all device types. " if not verbosity else " "
        caption = f"[reset]{'Counts' if not status else f'{status} Devices'}: {_cnt_str}\n{caption}"
        if not dev_type:
            caption = f"{caption} To see all columns for a given device use [cyan]cencli show <DEVICE TYPE>[/cyan]"
        else:
            caption = f"[reset]Counts: {_cnt_str}"
    else:
        caption = f"[reset]Counts: {_cnt_str}"

    if inventory and not inventory_only:
        caption = f"{caption}\n  [italic green3]Devices lacking name/status are in the inventory, but have not connected to central.[/]"
    return caption


def _build_client_caption(resp: Response, wired: bool = None, wireless: bool = None, band: bool = None, device: CentralObject = None, verbose: bool = False,):
    def _update_counts_by_band(caption: str, wlan_clients: List[Dict[str, Any]], end: str = "\n") -> str:
        two_four_clients = len([c for c in wlan_clients if c.get("band", 0) == 2.4])
        five_clients = len([c for c in wlan_clients if c.get("band", 0) == 5])
        six_clients = len([c for c in wlan_clients if c.get("band", 0) == 6])

        return f"{caption} ([bright_green]2.4Ghz[/]: [bright_red]{two_four_clients}[/], [bright_green]5Ghz[/]: [cyan]{five_clients}[/], [bright_green]6Ghz[/]: [cyan]{six_clients}[/]){end}"

    if wired:
        count_text = f"[cyan]{len(resp)}[/] Wired Clients."
    elif wireless or band:
        count_text = f"[cyan]{len(resp)}[/] Wireless Clients."
        wlan_clients = resp.raw.get("clients", [])
        count_text = _update_counts_by_band(count_text, wlan_clients=wlan_clients, end=",")
    else:
        _tot = len(resp)
        wlan_raw = list(filter(lambda d: "raw_wireless_response" in d, resp.raw))
        wired_raw = list(filter(lambda d: "raw_wired_response" in d, resp.raw))
        caption_data = {}
        if device is None:
            for _type, data in zip(["wireless", "wired"], [wlan_raw, wired_raw]):
                caption_data[_type] = {
                    "count": "" if not data or "total" not in data[0][f"raw_{_type}_response"] else data[0][f"raw_{_type}_response"]["total"],
                }
            count_text = f"Counts: [bright_green]Total[/]: [cyan]{_tot}[/], [bright_green]Wired[/]: [cyan]{caption_data['wired']['count']}[/],"
            count_text = f"{count_text} [bright_green]Wireless[/]: [cyan]{caption_data['wireless']['count']}[/]"

            # Add counts by band
            wlan_clients = wlan_raw[0]["raw_wireless_response"]["clients"]  # TODO use CombinedResponse
            count_text = _update_counts_by_band(count_text, wlan_clients=wlan_clients)
        else:
            count_text = f"[bright_green]Client Count[/]: [cyan]{_tot}[/],"
            if device.type == "ap":
                wlan_clients = resp.raw.get("clients", [])
                count_text = _update_counts_by_band(count_text.rstrip(","), wlan_clients=wlan_clients, end=",")

    return f"[reset]{count_text} Use {'[cyan]-v[/] for more details, ' if not verbose else ''}[cyan]--raw[/] for unformatted response."

# TODO expand params into available kwargs
def _get_details_for_all_devices(params: dict, include_inventory: bool = False, status: DeviceStatus = None, verbosity: int = 0,):
    if include_inventory:
        resp = cli.cache.get_devices_with_inventory(status=status)
        caption = _build_device_caption(resp, inventory=True, verbosity=verbosity)
    elif not cli.cache.responses.dev:
        resp = cli.central.request(cli.cache.refresh_dev_db, **params)
        caption = None if not hasattr(resp, "ok") or not resp.ok else _build_device_caption(resp, status=status)
    else:
        # get_all_devices already called (to populate/update cache) grab response from cache.  This really only happens if hidden -U option is used
        resp, caption = cli.cache.responses.dev, None  # TODO should update_client_db return responses.client if get_clients already in cache.updated?

    return resp, caption

def _update_cache_for_specific_devices(batch_res: List[Response], devs: List[CacheDevice]):
    try:
        data = [{**r.output, "type": d.type, "switch_role": r.output.get("switch_role", d.switch_role), "swack_id": r.output.get("swarm_id", r.output.get("stack_id")) or (d.serial if d.is_aos10 else None)} for r, d in zip(batch_res, devs) if r.ok]
        model_data: List[dict] = [Device(**dev).model_dump() for dev in data]
        cli.central.request(cli.cache.update_dev_db, model_data)
    except Exception as e:
        log.exception(f"Cache Update Failure from _update_cache_for_specific_devices \n{e}")
        log.error(f"Cache update failed {e.__class__.__name__}.", caption=True)


def _get_details_for_specific_devices(
        devices: List[CentralObject],
        dev_type: Literal["ap", "gw", "cx", "sw"] | None = None,
        include_inventory: bool = False,
        do_table: bool = False
    ) -> Tuple[Response | List[Response], str]:
        caption = None

        # Build requests
        br = cli.central.BatchRequest
        devs = [cli.cache.get_dev_identifier(d, dev_type=dev_type, include_inventory=include_inventory) for d in devices]
        dev_types = [dev.type for dev in devs]
        reqs = [br(cli.central.get_dev_details, dev.type, dev.serial) for dev in devs]

        # Fetch results from API
        batch_res = cli.central.batch_request(reqs)
        if include_inventory:  # Combine results with inventory results
            _ = cli.central.request(cli.cache.refresh_inv_db, device_type=dev_type)
            for r, dev in zip(batch_res, devs):
                r.output = {**r.output, **cli.cache.inventory_by_serial.get(dev.serial, {})}

        _update_cache_for_specific_devices(batch_res, devs)

        if do_table and len(dev_types) > 1:
            _output = [r.output for r in batch_res]
            resp = batch_res[-1]
            resp.output = _output
            resp.output = resp.table
            caption = f'{caption or ""}\n  Displaying fields common to all specified devices.  Request devices individually to see all fields.'
        else:
            resp = batch_res

        if "cx" in dev_types:
            caption = f'{caption or ""}\n  mem_total for cx devices is the % of memory currently in use.'.lstrip("\n")

        return resp, caption

# TODO break this into multiple functions
def show_devices(
    devices: str | Iterable[str] = None,
    dev_type: Literal["all", "ap", "gw", "cx", "sw", "switch"] = None,
    include_inventory: bool = False,
    verbosity: int = 0,
    outfile: Path = None,
    update_cache: bool = False,
    group: str = None,
    site: str = None,
    label: str = None,
    status: DeviceStatus = None,
    state: str = None,
    pub_ip: str = None,
    do_clients: bool = True,
    do_stats: bool = False,
    do_ssids: bool = False,
    sort_by: str = None,
    reverse: bool = False,
    pager: bool = False,
    do_json: bool = False,
    do_csv: bool = False,
    do_yaml: bool = False,
    do_table: bool = False
) -> None:
    # include subscription implies include_inventory
    if update_cache:
        cli.central.request(cli.cache.refresh_dev_db)

    if group:
        group: CacheGroup = cli.cache.get_group_identifier(group)
    if site:
        site: CacheSite = cli.cache.get_site_identifier(site)
    if label:
        label: CacheLabel = cli.cache.get_label_identifier(label)

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

    params = {k: v for k, v in params.items() if v is not None}
    if dev_type is None:
        dev_type = None if devices else "all"
    elif dev_type != "all":
        dev_type = lib_to_api(dev_type)

    # verbosity = verbosity if not any([devices, include_inventory, include_subscription]) else verbosity or 99
    default_tablefmt = "rich" if not verbosity else "yaml"

    if devices:  # cencli show devices <device iden>
        verbosity = verbosity or 99  # specific device implies verbose output vertically
        default_tablefmt = "yaml"
        resp, caption = _get_details_for_specific_devices(devices, dev_type=dev_type, include_inventory=include_inventory, do_table=do_table)
    elif dev_type == "all":  # cencli show all | cencli show devices
        resp, caption = _get_details_for_all_devices(params=params, include_inventory=include_inventory, status=status, verbosity=verbosity)
    else:  # cencli show switches | cencli show aps | cencli show gateways | cencli show inventory [cx|sw|ap|gw] ... (with any params, but no specific devices)
        resp = cli.central.request(cli.cache.refresh_dev_db, dev_type=dev_type, **params)
        if include_inventory:
            _ = cli.central.request(cli.cache.refresh_inv_db, device_type=dev_type)
            resp = cli.cache.get_devices_with_inventory(no_refresh=True, dev_type=dev_type, status=status)

        caption = None if not resp.ok or not resp.output else _build_device_caption(resp, inventory=include_inventory, dev_type=dev_type, status=status, verbosity=verbosity)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default=default_tablefmt)
    title_sfx = [
        f"{k}: {v}" for k, v in params.items() if k not in ["calculate_client_count", "show_resource_details", "calculate_ssid_count"] and v
    ] if not include_inventory else ["including Devices from Inventory"]
    title = "Device Details" if not dev_type else f"{what_to_pretty(dev_type)} {', '.join(title_sfx)}".rstrip()

    # With inventory needs to be serial because inv only devs don't have a name yet.  Switches need serial appended so stack members are unique.
    if include_inventory:
        output_key = "serial"
    elif dev_type and dev_type == "switch":
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
        output_format=tablefmt,
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
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include devices in Inventory that have yet to connect", show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortDevOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
):
    """Show details for All devices
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        dev_type='all', include_inventory=with_inv, verbosity=verbose, outfile=outfile, update_cache=update_cache,
        group=group, site=site, status=status, state=state, label=label, pub_ip=pub_ip, do_stats=True, do_clients=True, sort_by=sort_by, reverse=reverse,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table)


@app.command()
def devices(
    devices: List[str] = typer.Argument(
        None,
        metavar=iden_meta.dev_many.replace("]", "|'all']"),
        hidden=False,
        autocompletion=lambda incomplete: [
            m for m in [("all", "Show all devices"), *[m for m in cli.cache.dev_completion(incomplete=incomplete)]]
            if m[0].lower().startswith(incomplete.lower())
        ],
        help=f"Show details for a specific device [grey42]{escape('[default: show details for all devices]')}[/]",
        show_default=False,
    ),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include devices in Inventory that have yet to connect", show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortDevOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
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
        devices, dev_type=dev_type, include_inventory=with_inv, verbosity=verbose if not with_inv else verbose + 1, outfile=outfile, update_cache=update_cache,
        group=group, site=site, status=status, state=state, label=label, pub_ip=pub_ip, do_stats=True, do_clients=True, sort_by=sort_by, reverse=reverse,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table)


@app.command()
def aps(
    aps: List[str] = typer.Argument(None, metavar=iden_meta.dev_many, hidden=False, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    dirty: bool = typer.Option(False, "--dirty", "-D", help=f"Get Dirty diff [grey42 italic](config items not pushed) {escape('[requires --group]')}[/]"),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    neighbors: bool = typer.Option(False, "-n", "--neighbors", help=f"Show all AP LLDP neighbors for a site [grey42 italic]{escape('[requires --site]')}[/]", show_default=False,),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include aps in Inventory that have yet to connect", show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortDevOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
) -> None:
    """Show details for APs

    Use [cyan]cencli show aps -n --site <SITE>[/] to see lldp neighbors for all APs in a site.
    """
    if dirty:
        if not group:
            cli.exit("[cyan]--group[/] must be provided with [cyan]--dirty[/] option.")

        group = cli.cache.get_group_identifier(group)
        resp = cli.central.request(cli.central.get_dirty_diff, group.name)
        tablefmt: str = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
        cli.display_results(resp, tablefmt=tablefmt, title=f"AP config items that have not pushed for group {group.name}", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse)
    elif neighbors:
        if site is None:
            cli.exit("[cyan]--site <site name>[/] is required for neighbors output.")

        site: CentralObject = cli.cache.get_site_identifier(site)
        resp: Response = cli.central.request(cli.central.get_topo_for_site, site.id, )
        tablefmt: str = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

        cleaner_kwargs = {}
        if up and down:
            ...  # They used both flags.  ignore
        elif up or down:
            cleaner_kwargs["filter"] = "down" if down else "up"
        cli.display_results(resp, tablefmt=tablefmt, title=f"AP Neighbors for site {site.name}", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.show_all_ap_lldp_neighbors_for_sitev2, **cleaner_kwargs)
    else:
        if up and down:
            ...  # They used both flags.  ignore
        elif up or down:
            status = "down" if down else "up"

        show_devices(
            aps, dev_type="ap", include_inventory=with_inv, verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label, status=status,
            state=state, pub_ip=pub_ip, do_clients=True, do_stats=True, do_ssids=True,
            sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
            do_table=do_table)

@app.command("switches")
def switches_(
    switches: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include switches in Inventory that have yet to connect", show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortDevOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
) -> None:
    """Show details for switches
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        switches, dev_type='switch', include_inventory=with_inv, verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=True, do_stats=True,
        sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(name="gateways")
def gateways_(
    gateways: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False,),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by gateways that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by gateways that are Down", show_default=False),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include gateways in Inventory that have yet to connect", show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: SortDevOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
):
    """Show details for gateways
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        gateways, dev_type='gw', include_inventory=with_inv, verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=True, do_stats=True,
        sort_by=sort_by, reverse=reverse, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command("controllers", hidden=True)
def controllers_(
    controllers: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False,),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    with_inv: bool = typer.Option(False, "-I", "--inv", help="Include gateways in Inventory that have yet to connect", show_default=False, hidden=True,),  # hidden as not tested with this type
    verbose: int = cli.options.verbose,
    sort_by: SortDevOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
):
    """Show details for controllers

    Hidden as it is the same as show gateways
    """
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        controllers, dev_type='gw', include_inventory=with_inv, verbosity=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=True, do_stats=True, sort_by=sort_by, reverse=reverse,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table)



@app.command()
def stacks(
    switches: List[str] = typer.Argument(None, help="List of specific switches to pull stack details for", metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    group: str = cli.options.group,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status, both hidden to simplify as they can use --up or --down
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    verbose: int = cli.options.verbose,
    sort_by: SortStackOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
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
    dev_type: ShowInventoryArgs = typer.Argument("all",),
    sub: bool = typer.Option(
        None,
        help=f"Show devices with applied subscription/license, or devices with no subscription/license applied. [grey42]{escape('[default: show all]')}[/]",
        show_default=False,
    ),
    verbose: int = cli.options.verbose,
    sort_by: SortInventoryOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    if hasattr(dev_type, "value"):
        dev_type = dev_type.value


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

    include_inventory = False
    if verbose:
        include_inventory = True
        verbose -= 1

    if verbose or include_inventory:
        show_devices(
            dev_type=dev_type, outfile=outfile, include_inventory=include_inventory, verbosity=verbose, do_clients=True, sort_by=sort_by, reverse=reverse,
            pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table
        )
        cli.exit(code=0)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    resp = cli.central.request(cli.cache.refresh_inv_db, device_type=dev_type)

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=_build_device_caption(resp, inventory=True),
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        set_width_cols={"services": {"min": 31}},
        cleaner=cleaner.get_device_inventory,
        sub=sub
    )


# TODO break into seperate command group if we can still all show subscription without an arg to default to details
@app.command()
def subscriptions(
    what: SubscriptionArgs = typer.Argument("details"),
    dev_type: GenericDevTypes = typer.Option(None, help="Filter by device type", show_default=False,),
    service: LicenseTypes = typer.Option(None, "--type", help="Filter by subscription/license type", show_default=False),
    sort_by: SortSubscriptionOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show subscription/license details or stats
    """
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich" if what != "stats" else "yaml")
    if what is None or what == "details":
        resp = cli.central.request(cli.central.get_subscriptions, license_type=service, device_type=dev_type)
        title = "Subscription Details"
        _cleaner = cleaner.get_subscriptions
        set_width_cols = {"name": {"min": 39}}
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
        resp = cli.central.request(cli.cache.refresh_license_db)
        title = "Valid Subscription/License Names"
        _cleaner = None
        set_width_cols = {"name": {"min": 39}}
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
@app.command()
def swarms(
    group: str = cli.options.group,
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by swarm status", show_default=False, hidden=True,),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    up: bool = typer.Option(False, "--up", help="Filter by swarms that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by swarms that are Down", show_default=False),
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by swarm Public IP", show_default=False,),
    name: str = typer.Option(None, "--name", help="Filter by swarm/cluster name", show_default=False,),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show Swarms (IAP Clusters)
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

class ParsedCombinedResp:
    def __init__(self, dev_type: GenericDeviceTypes, passed: List[Response], failed: List[Response], output: List[Dict[str, Any]], raw: Dict[str, Any], elapsed: float, verbosity: int = 0):
        self.dev_type = dev_type
        self.passed = passed
        self.failed = failed
        self.output = output
        self.raw = raw
        self.elapsed = elapsed
        self.verbosity = verbosity

    @property
    def to_dict(self) -> dict:
        return {"response": self.response._response, "output": self.clean, "raw": self.raw, "elapsed": self.elapsed}

    @property
    def clean(self):
        _clean = sorted(
            [inner for r in self.output for inner in cleaner.show_interfaces(r, dev_type=self.dev_type, verbosity=self.verbosity, by_interface=False)],
            key=lambda d: d["device"]
        )
        return cleaner.ensure_common_keys(_clean)

    @property
    def response(self):
        return sorted(self.passed or self.failed, key=lambda r: r.rl)[0]

def parse_interface_responses(dev_type: GenericDeviceTypes, responses: List[Response], verbosity: int = 0) -> ParsedCombinedResp:
    _failed = [r for r in responses if not r.ok]
    _passed = responses if not _failed else [r for r in responses if r.ok]

    if _failed:
        try:
            log.warning(f"Incomplete output!! {len(_failed)} calls failed.  Devices: {utils.color([r.url.path.split('/')[-2:][0] for r in _failed])}. [cyan]cencli show logs --cencli[/] for details.", caption=True)
        except Exception:
            log.warning("Incomplete output, failures occured, see log")


    # output = [i for r in _passed for i in utils.listify(r.output)]
    output = [r.output for r in _passed]
    raw = {r.url.path: r.raw for r in [*_passed, *_failed]}
    elapsed = sum(r.elapsed for r in _passed)

    parsed = ParsedCombinedResp(dev_type, passed=_passed, failed=_failed, output=output, raw=raw, elapsed=elapsed, verbosity=verbosity)
    return {**parsed.to_dict}

def do_interface_filters(data: List[dict] | dict, filters: ShowInterfaceFilters, caption: List[str]) -> Tuple[List[dict] | dict, List[str]]:
    if isinstance(data, dict) and "ethernets" in data:  # single AP output
        data = data["ethernets"]

    try:
        filtered = data
        filter_caption = None
        if filters.slow:
            filtered = [d for d in data if d.get("status", "") == "Up" and int(d.get("speed", d.get("link_speed"))) < 1000]
            filter_caption = f"Slow Interfaces (link speed < 1Gbps): [bright_magenta]{len(filtered)}[/]"
        elif filters.fast:
            filtered = [d for d in data if d.get("status", "") == "Up" and int(d.get("speed", d.get("link_speed"))) >= 2500]
            filter_caption = f"Fast Interfaces (link speed >= 2.5Gbps/SmartRate): [bright_magenta]{len(filtered)}[/]"
        elif filters.up:
            filtered = [d for d in data if d.get("status", "") == "Up"]
        elif filters.down:
            filtered = [d for d in data if d.get("status", "") == "Down"]

        if not filtered:
            log.warning("Filters resulted in no results. Showing unfiltered output", caption=True)
        else:
            data = filtered
        if filter_caption:
            caption = [c if not c.lstrip().startswith("Counts:") else f"{c} {filter_caption}" for c in caption]

    except Exception as e:
        log.exception(f"{e.__class__.__name__} in do_interface_filters\n{e}")
        log.warning(f"{e.__class__.__name__} while attempting to filter output.  Please report issue on GitHub", caption=True)

    return data, caption


# TODO define sort_by fields
@app.command()
def interfaces(
    device: str = typer.Argument(
        "all",
        metavar=f"{iden_meta.dev.replace(']', '|all]')}",
        autocompletion=lambda incomplete: [item for item in [*cli.cache.dev_completion(incomplete), ("all", "Return interface details for all devices of a given type, requires --ap, --gw, or --switch",)] if item[0].startswith(incomplete)],
        help=f"Device to fetch interfaces from {cli.help_default('ALL (must provide one of --ap, --gw, or --switch)')}",
        show_default=False,
    ),
    slot: str = typer.Argument(None, help="Slot name of the ports to query [italic grey46](chassis only)[/]", show_default=False,),
    group: str = cli.options.group,
    site: str = cli.options.site,
    do_gw: bool = typer.Option(False, "--gw", help="Show interfaces for all gateways, [italic grey46](Only applies with device 'all' or when no device is provided)[/]"),
    do_ap: bool = typer.Option(False, "--ap", help="Show interfaces for all APs [italic grey46](Only applies with device 'all' or when no device is provided)[/]"),
    do_switch: bool = typer.Option(False, "--switch", help="Show interfaces for all switches [italic grey46](Only applies with device 'all' or when no device is provided)[/]"),
    _do_switch: bool = typer.Option(False, "--cx", "--sw", hidden=True,),  # hidden support common alternative switch flags
    # stack: bool = typer.Option(False, "-s", "--stack", help="Get intrfaces for entire stack [grey42]\[default: Show interfaces for specified stack member only][/]",),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    up: bool = typer.Option(False, "--up", help="Filter by interfaces that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by interfaces that are Down", show_default=False),
    slow: bool = typer.Option(False, "-s", "--slow", help="Filter by Up interfaces that have negotiated a speed below 1Gbps", show_default=False),
    fast: bool = typer.Option(False, "-f", "--fast", help="Filter by Up interfaces that have negotiated a speed at or above 2.5Gbps (Smart Rate)", show_default=False),
    verbose: int = cli.options.verbose,
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    yes: bool = cli.options.yes,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
):
    """Show interfaces/details

    Show interfaces for a device, or show interfaces for all devices (default if no device is specified) of a provided device type.
    --site & --group filters only apply when listing all interfaces of a given device type.
    """
    do_switch = do_switch or _do_switch
    title_sfx = ""
    context_filters = {
        "group": group,
        "site": site
    }

    filters = ShowInterfaceFilters(up=up, down=down, slow=slow, fast=fast)
    if not filters.ok:
        log.warning(f"Contradictory flags! {filters.error} together don't make sense.  Ignoring.", caption=True)

    if device != "all":
        if any([site, group]):
            warn_msg = ",".join([f'[cyan]--{k} {v}[/]' for k, v in context_filters.items() if v])
            log.warning(f"{warn_msg} ignored as the option does not apply when a specific device is provided.", caption=True)
        dev: CacheDevice = cli.cache.get_dev_identifier(device, conductor_only=True,)
        dev_type = dev.generic_type
        devs = [dev]
    else:
        if [do_ap, do_gw, do_switch].count(True) > 1:
            cli.exit("Only one of --ap, --gw, --switch :triangular_flag: can be provided.")

        if do_ap:
            dev_type = "ap"
        elif do_gw:
            dev_type = "gw"
        elif do_switch:
            dev_type = "switch"
        else:
            cli.exit("One of --ap, --gw, --switch :triangular_flag: is required when no device is specified")

        # Update cache basesd on provided filters
        kwargs = {"site": site} if site else {"group": group}  # monitoring API only allows 1 filter
        dev_resp = cli.central.request(cli.cache.refresh_dev_db, dev_type=dev_type, **kwargs)
        if not dev_resp:
            cli.display_results(dev_resp, tablefmt="action", exit_on_fail=True)

        site: CacheSite = site if not site else cli.cache.get_site_identifier(site)
        group: CacheGroup = group if not group else cli.cache.get_group_identifier(group)

        devs: List[CacheDevice] = [cd for cd in [CacheDevice(d) for d in cli.cache.devices] if cd.generic_type == dev_type]
        if site:
            devs = [d for d in devs if d.site == site.name]
            title_sfx = f" in site {site.name}"
        if group:
            devs = [d for d in devs if d.group == group.name]
            title_sfx = f" and group {group.name}" if site else f" in group {group.name}"

        if not devs:
            cli.exit(f"Combination of filters resulted in no {lib_to_gen_plural(dev_type)} to process")

    if dev_type == "gw":
        batch_reqs = [BatchRequest(cli.central.get_gateway_ports, d.serial) for d in devs]
    elif dev_type == "ap":
        batch_reqs = [BatchRequest(cli.central.get_dev_details, "ap", d.serial) for d in devs]
    else:
        batch_reqs = [
                BatchRequest(
                    cli.central.get_switch_ports,
                    d.swack_id or d.serial,
                    slot=slot,
                    stack=d.swack_id is not None,
                    aos_sw=d.type == "sw"
                ) for d in devs
            ]

    if len(batch_reqs) > 15:
        cli.econsole.print(f"[dark_orange3]:warning:[/]  This operation will result in {len(batch_reqs)} additional API calls")
        cli.confirm(yes)

    batch_resp = cli.central.batch_request(batch_reqs)

    # We need to include name and dev_type from cache for multi-device listings (not included in payload of all the interface endpoints)
    if len(batch_resp) > 1:
            for d, r in zip(devs, batch_resp):
                if r.ok:
                    r.output = [{"device": d.name, "_dev_type": d.type, **i} for i in utils.listify(r.output)]

    resp = batch_resp[0] if len(batch_resp) == 1 else CombinedResponse(batch_resp, lambda responses: parse_interface_responses(dev_type, responses=responses, verbosity=verbose,))

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich" if not verbose else "yaml")
    title = f"{filters.title_sfx}Interfaces for all {lib_to_gen_plural(dev_type)}{title_sfx}" if len(devs) > 1 else f"{devs[0].name} {filters.title_sfx}Interfaces"

    caption = []
    if dev_type == "switch":
        if "sw" in [d.type for d in devs] and resp.ok:
            dev_type = dev_type if len(batch_resp) > 1 else "sw"  # So single device cleaner gets specific dev_type
            caption = [render.rich_capture(":information:  Native VLAN for trunk ports not shown for aos-sw as not provided by the API", emoji=True)]
        if "cx" in [d.type for d in devs] and resp.ok:
            caption = [render.rich_capture(":information:  L3 interfaces for CX switches will show as Access/VLAN 1 as the L3 details are not provided by the API", emoji=True)]

    if resp:
        try:  # TODO can prob move the caption counts to do_interface filters (remove if filters conditional)
            ifaces = resp.output if "ethernets" not in resp.output else resp.output["ethernets"]
            up_ifaces = len([i for i in utils.listify(ifaces) if i.get("status").lower() == "up"])  # listify as individual dev response is a dict, vs List for multi-device
            down_ifaces = len(utils.listify(ifaces)) - up_ifaces
            caption += [f"Counts: Total: [cyan]{len(ifaces)}[/], Up: [bright_green]{up_ifaces}[/], Down: [bright_red]{down_ifaces}[/]"]
        except Exception as e:
            log.error(f"{e.__class__.__name__} while trying to get counts from interface output")

        if filters:
            resp.output, caption = do_interface_filters(resp.output, filters=filters, caption=caption)

    # TODO cleaner returns a Dict[dict] assuming "vsx enabled" is the same bool for all ports put it in caption and remove from each item
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        output_by_key=None,
        group_by=None if len(batch_resp) <= 1 else "device",
        cleaner=cleaner.show_interfaces if len(batch_resp) == 1 else None,  # Multi device listing is ran through cleaner already
        verbosity=verbose,
        dev_type=dev_type,
    )


@app.command(help="Show (switch) poe details for an interface")
def poe(
    device: str = typer.Argument(..., metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    port: str = typer.Argument(None, show_default=False, help="Show PoE details for a specific interface",),
    _port: str = typer.Option(None, "--port", show_default=False, hidden=True,),
    powered: bool = typer.Option(False, "-p", "--powered", help="Show only interfaces currently delivering power", show_default=False,),
    verbose: int = cli.options.verbose,
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
):
    port = _port if _port else port
    dev = cli.cache.get_dev_identifier(device, dev_type="switch")
    resp = cli.central.request(cli.central.get_switch_poe_details, dev.serial, port=port, aos_sw=dev.type == "sw")
    resp.output = utils.unlistify(resp.output)
    caption = "  Power values are in watts."
    if resp:
        resp.output = utils.listify(resp.output)  # if they specify an interface output will be a single dict.
        if not port:
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
    up: bool = typer.Option(False, "--up", help="Filter by VLANs that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by VLANs that are Down", show_default=False),
    sort_by: SortVlanOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

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
    sort_by: SortDhcpOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
) -> None:
    """Show DHCP pool or lease details (gateways only)
    """
    central = cli.central
    dev: CentralObject = cli.cache.get_dev_identifier(dev, dev_type="gw")

    if what == "pools":
        resp = central.request(central.get_dhcp_pools, dev.serial)
    else:
        resp = central.request(central.get_dhcp_clients, dev.serial, reservation=not no_res)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{dev.name} DHCP {what.rstrip('s')} details",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_dhcp,
    )


@app.command()
def upgrade(
    devices: List[str] = typer.Argument(
        ...,
        metavar=iden_meta.dev_many,
        hidden=False,
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
):
    """Show firmware upgrade status (by device)
    """
    central = cli.central
    # Allow unnecessary keyword status `cencli show upgrade status <dev>` or `cencli show upgrade device <dev>`
    ignored_subcommands = ["status", "device"]
    devices = [d for d in devices if d not in ignored_subcommands]

    if not devices:
        cli.exit("Missing required parameter [cyan]<device>[/]")

    devs: List[CentralObject] = [cli.cache.get_dev_identifier(dev, conductor_only=True,) for dev in devices]
    kwargs_list = [{"swarm_id" if dev.type == "ap" else "serial": dev.swack_id if dev.type == "ap" else dev.serial} for dev in devs]
    batch_reqs: List[BatchRequest] = [BatchRequest(central.get_upgrade_status, **kwargs) for kwargs in kwargs_list]
    batch_resp: List[Response] = central.batch_request(batch_reqs, continue_on_fail=True, retry_failed=True)
    failed = [r for r in batch_resp if not r.ok]
    passed = [r for r in batch_resp if r.ok]

    if passed:
        combined_out = [{"name": dev.name, "serial": dev.serial, "site": dev.site, "group": dev.group, **r.output} for dev, r in zip(devs, passed)]
        rl = [r.rl for r in sorted(batch_resp, key=lambda x: x.rl)]
        resp = passed[-1]
        resp.rl = rl[0]
        resp.output = combined_out
        if failed:
            _ = [log.warning(f'Partial Failure {r.url.path} | {r.status} | {r.error}', caption=True) for r in failed]
    else:
        resp = batch_resp

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Upgrade Status",
        pager=pager,
        outfile=outfile,
        cleaner=cleaner.simple_kv_formatter,
    )


@app.command("cache", hidden=True)
def cache_(
    args: List[CacheArgs] = typer.Argument(None, help="[cyan]all[/] Shows data in [italic bright_green]the most pertinent[/] tables", show_default=False),
    all: bool = typer.Option(False, "--all", help="This is the Super [cyan]all[/] option, shows data in [bright_green italic]every[/] table.", show_choices=False),
    no_page: bool = typer.Option(False, "--no-page", help="For [cyan]all[/] | [cyan]--all[/] options, you hit Enter to see the next table.  This option disables that behavior.", show_default=False,),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
):
    """Show contents/size/record-count in Local Cache.

    By default (or with [cyan]all[/] as argument) the command shows the data in the most frequently used tables:
        devices, inventory, sites, groups, templates, labels, licenses, clients
        Use [cyan]--all[/] flag to see data for all tables.

    Use [cyan]tables[/] as argument to see summary and headers for all tables.
    """
    def get_fields(data: List[Dict[str, Any]], name: str = None) -> List[str]:
        data = [] if not data else data[0].keys()
        pfx = ">>" if not name else f">> {name}"
        return f"[bright_green]{pfx} fields[/]:\n{utils.color(list(data), 'cyan')}".splitlines()

    def sort_devices(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # make device order from cache match device order from other show device commands
        return sorted(data, key=lambda i: (i.get("site") or "", i.get("type") or "", i.get("name") or ""))

    args = ('all',) if not args else args
    tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table, default="rich")

    if all or "all" in args:
        tables = cli.cache.all_tables if all else cli.cache.key_tables
        length = len(cli.cache) if all else len(cli.cache._tables)
        for idx, t in enumerate(tables, start=1):
            data = t.all()
            if t.name == "devices":
                data = sort_devices(data)

            cli.display_results(data=data, tablefmt=tablefmt, title=t.name, caption=f'[cyan]{len(data)} {t.name} items in cache.', pager=pager, outfile=outfile, sort_by=sort_by, output_by_key=None)
            if not no_page and cli.econsole.is_terminal and not idx == length:
                cli.pause()

    elif "tables" in args:
        tables = cli.cache.all_tables
        data = [f"[dark_olive_green2]{t.name}[/]: records: [cyan]{len(t)}[/]\n    {' '.join(get_fields(t.all()))}" for t in tables]
        cli.display_results(data=data, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, output_by_key=None)

    else:
        for idx, arg in enumerate(args, start=1):
            cache_out: List[Document] = getattr(cli.cache, arg)
            arg = arg if not hasattr(arg, "value") else arg.value
            if arg == "devices":
                cache_out = sort_devices(cache_out)

            caption = f"{arg.title()} in cache: [cyan]{len(cache_out)}[/]"
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
                caption=caption,
            )
            if not no_page and cli.econsole.is_terminal and not idx == len(args):
                cli.pause()

    account_msg = "" if config.account in ["central_info", "default"] else f"[italic bright_green]Workspace: {config.account}[/] "
    cli.console.print(f'{account_msg}[italic dark_olive_green2]Total tables in Cache: [cyan]{len(cli.cache)}[/], Cache File Size: [cyan]{cli.cache.size}[reset]')

def _build_groups_caption(data: List[dict]) -> List[str]:
    if not data:
        return

    total = ("Total", len(data),)
    template = ("Template", len(list(filter(lambda g: any([g.get("wired_tg"), g.get("wlan_tg")]), data))),)
    mon_only = ("Monitor Only (cx or sw)", len(list(filter(lambda g: any([g.get("monitor_only_cx"), g.get("monitor_only_sw")]), data))),)
    aos10 = ("AOS10", len(list(filter(lambda g: g.get("aos10") is True, data))),)
    mb = ("MicroBranch", len(list(filter(lambda g: g.get("microbranch") is True, data))),)
    sdwan = ("EdgeConnect SD-WAN", len(list(filter(lambda g: "sdwan" in g.get("allowed_types"), data))),)
    counts = [total, template, mon_only, aos10, mb, sdwan]

    caption, _caption = [], []
    for text, count in counts:
        if count:
            _caption += [f'[bright_green]{text}[/] Groups: [cyan]{count}[/]']
    if len(_caption) > 3:
        for chunk in utils.chunker(_caption, 3):
            caption += [", ".join(chunk)]

    return caption or _caption

@app.command(help="Show groups/details")
def groups(
    sort_by: SortGroupOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    resp = cli.central.request(cli.cache.refresh_group_db)
    caption = _build_groups_caption(resp.output)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)
    cli.display_results(resp, tablefmt=tablefmt, title="Groups", caption=caption, pager=pager, sort_by=sort_by, reverse=reverse, outfile=outfile, cleaner=cleaner.show_groups, cleaner_format=tablefmt)


@app.command()
def labels(
    sort_by: SortLabelOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show labels/details"""
    resp = cli.central.request(cli.cache.refresh_label_db)
    tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table)
    cli.display_results(resp, tablefmt=tablefmt, title="labels", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, set_width_cols={"name": {"min": 30}}, cleaner=cleaner.get_labels)


def _build_site_caption(resp: Response, count_state: bool = False, count_country: bool = False):
    if not resp.ok:
        return

    caption = f'Total Sites: [green3]{resp.raw.get("total", len(resp.output))}[/]'
    counts, count_caption = {}, None
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

    return caption


@app.command(short_help="Show sites/details")
def sites(
    site: str = typer.Argument(None, metavar=iden_meta.site, autocompletion=cli.cache.site_completion, show_default=False),
    count_state: bool = typer.Option(False, "-s", show_default=False, help="Calculate # of sites per state"),
    count_country: bool = typer.Option(False, "-c", show_default=False, help="Calculate # of sites per country"),
    sort_by: SortSiteOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
):
    central = cli.central
    sort_by = None if sort_by == "name" else sort_by  # Default sort from endpoint is by name

    site = None if site and site.lower() == "all" else site
    if not site:
        resp = cli.central.request(cli.cache.refresh_site_db)
        cleaner_func = None  # No need to clean cache sends through model/cleans
    else:
        site: CacheSite = cli.cache.get_site_identifier(site)
        resp = central.request(central.get_site_details, site.id)
        cleaner_func = cleaner.sites

    # TODO find public API to determine country/state based on get coordinates if that's all that is set for site.
    # Country is blank when added via API and not provided.  Find public API to lookup country during add
    caption = _build_site_caption(resp, count_state=count_state, count_country=count_country)
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
        cleaner=cleaner_func,
    )


@app.command()
def templates(
    name: str = typer.Argument(
        None,
        help=f"Template: [name] or Device: {iden_meta.dev}",
        autocompletion=cli.cache.dev_template_completion,
        show_default=False,
    ),
    group: str = typer.Argument(None, help="Get Templates for Group", autocompletion=cli.cache.group_completion, show_default=False),
    _group: str = typer.Option(
        None, "--group",
        help="Get Templates for Group",
        hidden=False,
        autocompletion=cli.cache.group_completion,  # TODO add group completion specific to template_groups only
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

    sort_by: SortTemplateOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show templates/details"""
    central = cli.central

    # Allows unnecessary keyword group "cencli show templates group WadeLab"
    if name and name.lower() == "group":
        name = None

    group = group or _group
    if group:
        group: CentralObject = cli.cache.get_group_identifier(group)

    obj = None if not name else cli.cache.get_identifier(name, ("dev", "template"), device_type=device_type, group=None if not group else group.name)

    params = {
        # "name": name,
        "device_type": device_type,  # valid to API = IAP, ArubaSwitch, MobilityController, CX converted in api module
        "version": version,
        "model": model
    }
    params = {k: v for k, v in params.items() if v is not None}

    if obj:
        title = f"{obj.name.title()} Template"
        if obj.is_dev:  # They provided a dev identifier
            resp = central.request(central.get_variablised_template, obj.serial)
        else:  #  obj.is_template
            resp = central.request(central.get_template, group=obj.group, template=obj.name)
    elif group:
        title = "Templates in Group {} {}".format(group.name, ', '.join([f"[bright_green]{k.replace('_', ' ')}[/]: [cyan]{v}[/]" for k, v in params.items()]))
        resp = central.request(central.get_all_templates_in_group, group.name, **params) # TODO update cache on individual grabs
    elif params:  # show templates - Full update and show data from cache
        title = "All Templates {}".format(', '.join([f"[bright_green]{k.replace('_', ' ')}[/]: [cyan]{v}[/]" for k, v in params.items()]))
        resp = central.request(central.get_all_templates, **params)  # Can't use cache due to filtering options
    else:
        title = "All Templates"
        if central.get_all_templates not in cli.cache.updated:
            resp = cli.central.request(cli.cache.refresh_template_db)
        else:
            resp = cli.cache.responses.template  # cache updated this session use response from cache update (Only occures if hidden -U flag is used.)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)
    cli.display_results(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse)


@app.command(short_help="Show Variables for all or specific device")
def variables(
    device: str = typer.Argument(
        None,
        metavar=f"{iden_meta.dev.rstrip(']')}|all]",
        help=f"[grey42]{escape('[default: all]')}[/]",
        autocompletion=lambda incomplete: [
            m for m in [d for d in [("all", "Show Variables for all templates"), *cli.cache.dev_completion(incomplete=incomplete)]]
            if m[0].lower().startswith(incomplete.lower())
        ] or [],
        show_default=False,
    ),
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
):
    central = cli.central

    if device and device != "all":
        device = cli.cache.get_dev_identifier(device, conductor_only=True)
    else:
        device = ""

    resp = central.request(central.get_variables, () if not device else device.serial)
    if device:
        resp.output = resp.output.get("variables", resp.output)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="json")
    if not device and tablefmt in ["csv", "rich", "tabulate"] and len(resp.output) > 1:
        all_keys = [sorted(resp.output[dev].keys()) for dev in resp.output]
        if not all([all_keys[0] == key_list for key_list in all_keys[1:]]):
            tablefmt = "json"
            log.warning("Format changed to [cyan]JSON[/].  All variable names need to be identical for all devices for csv and table output.", caption=True)

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Variables" if not device else f"{device.name} Variables",
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
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,

) -> None:
    """Show lldp neighbor information

    Valid on APs and CX switches

    NOTE: AOS-SW will return LLDP neighbors, but only reports neighbors for connected Aruba devices managed in Central
    """
    central = cli.central

    devs: List[CentralObject] = [cli.cache.get_dev_identifier(_dev, dev_type=("ap", "switch"), conductor_only=True,) for _dev in device if not _dev.lower().startswith("neighbor")]
    batch_reqs = [BatchRequest(central.get_ap_lldp_neighbor, dev.serial) for dev in devs if dev.type == "ap"]
    batch_reqs += [BatchRequest(central.get_cx_switch_neighbors, dev.serial) for dev in devs if dev.generic_type == "switch" and not dev.swack_id]
    unique_stack_ids = set([dev.swack_id for dev in devs if dev.generic_type == "switch" and dev.swack_id])
    batch_reqs += [BatchRequest(central.get_cx_switch_stack_neighbors, swack_id) for swack_id in unique_stack_ids]
    batch_resp = central.batch_request(batch_reqs)
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
    sort_by: SortCertOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    resp = cli.central.request(cli.central.get_certificates, name, callback=cleaner.get_certificates)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp, tablefmt=tablefmt, title="Certificates", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse
    )

# TODO show task --device  look up task by device if possible
@app.command()
def task(
    task_id: str = typer.Argument(..., show_default=False),
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show status of previously issued task/command

    Requires task_id which is provided in the response of the previously issued command.
        Example: [cyan]cencli bounce interface idf1-6300-sw 1/1/11[/] will queue the command
                and provide the task_id.
    """
    resp = cli.central.request(cli.central.get_task_status, task_id)
    if "reason" in resp.output and "expired" in resp.output:
        resp.output["reason"] = resp.output["reason"].replace("expired", "invalid/expired")

    cli.display_results(
        resp, tablefmt="action", title=f"Task {task_id} status", outfile=outfile)


@app.command()
def run(
    device: str = cli.arguments.device,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show running config for a device

    APs get the last known running config from Central
    Switches and GWs request the running config from the device
    """
    central = cli.central
    dev = cli.cache.get_dev_identifier(device)

    if dev.type == "cx":
        clitshoot.send_cmds_by_id(dev, commands=[6002], pager=pager, outfile=outfile, exit=True)
    elif dev.type == "sw":
        clitshoot.send_cmds_by_id(dev, commands=[1022], pager=pager, outfile=outfile, exit=True)
    elif dev.type == "gw":
        clitshoot.send_cmds_by_id(dev, commands=[2385], pager=pager, outfile=outfile, exit=True)
    # Above device types will exit above

    # APs
    resp = central.request(central.get_device_configuration, dev.serial)
    if isinstance(resp.output, str) and resp.output.startswith("{"):
        try:
            cli_config = json.loads(resp.output)
            cli_config = cli_config.get("_data", cli_config)
            resp.output = cli_config
        except Exception as e:
            log.exception(e)

    cli.display_results(resp, pager=pager, outfile=outfile)


# TODO --status does not work
# https://web.yammer.com/main/org/hpe.com/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMTQyNzU1MDg5MTQ0MjE3NiJ9
@app.command("config")
def config_(
    group_dev: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.group_dev_cencli}",
        autocompletion=cli.cache.group_dev_completion,
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
    ap_env: bool = typer.Option(False, "-e", "--env", help="Show AP environment settings.  [italic grey62]Valid for APs only[/]", show_default=False,),
    status: bool = typer.Option(
        False,
        "--status",
        help="Show config (sync) status. Applies to GWs.",
        hidden=True,
    ),
    # version: str = typer.Option(None, "--ver", help="Version of AP (only applies to APs)"),
    file: bool = typer.Option(False, "-f", help="Applies to [cyan]cencli show config cencli[/].  Display raw file contents (i.e. cat the file)"),
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show Effective Group/Device Config (UI Group) or cencli config.

    Group level configs are available for APs or GWs.
    Device level configs are available for all device types, however
    AP and GW, show what Aruba Central has configured at the group or device level.
    Switches fetch the running config from the device ([italic]Same as [cyan]cencli show run[/cyan][/italic]).
    \tor the template if it's in a template group ([italic]Same as [cyan]cencli show template <SWITCH>[/cyan][/italic])).

    Examples:
    \t[cyan]cencli show config GROUPNAME --gw[/]\tCentral's Group level config for a GW
    \t[cyan]cencli show config DEVICENAME[/]\t\tCentral's device level config if GW, per AP settings if AP, template or
    \t\trunning config if switch.
    \t[cyan]cencli show config cencli[/]\t\tcencli configuration information (from config.yaml)
    """
    if group_dev == "cencli":  # Hidden show cencli config
        if file:
            cli.display_results(data=config.file.read_text())
            cli.exit(code=0)
        return _get_cencli_config()

    group_dev: CacheGroup | CacheDevice = cli.cache.get_identifier(group_dev, ["group", "dev"],)
    if group_dev.is_dev and group_dev.type not in ["ap", "gw"]:
        _group: CacheGroup = cli.cache.get_group_identifier(group_dev.group)
        if device:
            log.warning(f"ignoring extra argument {device}.  As {group_dev.name} is a device.", caption=True)
        if _group.wired_tg:
            return templates(group_dev.serial, group=group_dev.group, device_type=group_dev.type, outfile=outfile, pager=pager)
        else:
            return run(group_dev.serial, outfile=outfile, pager=pager)

    if group_dev.is_group:
        group = group_dev
        if device:
            device = cli.cache.get_dev_identifier(device)
        elif not do_ap and not do_gw:
            cli.exit("Invalid Input, --gw or --ap option must be supplied for group level config.")
    else:  # group_dev is a device iden
        group = cli.cache.get_group_identifier(group_dev.group)
        if device is not None:
            lbrkt, rbrkt = escape("["), escape("]")
            cli.exit(f"Invalid input provide {lbrkt}[cyan]GROUP NAME[/]{rbrkt} {lbrkt}[cyan]device iden[/]{rbrkt} or {lbrkt}[cyan]device iden[/]{rbrkt} [red]NOT[/] 2 devices.")
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
        func = cli.central.get_ap_config
        if device:
            if device.generic_type == "ap":
                args = [device.serial]
                if ap_env:
                    func = cli.central.get_per_ap_config
            else:
                cli.exit(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
        else:
            args = [group.name]
    else:
        cli.exit("Command Logic Failure, Please report this on GitHub.  Failed to determine appropriate function for provided arguments/options", show=True)
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
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    if not no_refresh:
        cli.central.refresh_token()

    tokens = cli.central.auth.getToken()
    if tokens:
        if cli.account not in ["central_info", "default"]:
            print(f"Account: [cyan]{cli.account}")
        print(f"Access Token: [cyan]{tokens.get('access_token', 'ERROR')}")


# TODO clean up output ... single line output
@app.command()
def routes(
    device: List[str] = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False,),
    sort_by: SortRouteOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show gateway routing table

    :information:  This command is only valid on Gateways
    """
    device = device[-1]  # allow unnecessary keyword "device"
    central = cli.central
    device = cli.cache.get_dev_identifier(device, dev_type="gw")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    resp = central.request(central.get_device_ip_routes, device.serial)
    caption = ""
    if "summary" in resp.raw:
        s = resp.raw["summary"]
        caption = (
            f'max: {s.get("maximum")}, total: {s.get("total")}, default: {s.get("default")}, connected: {s.get("connected")}, '
            f'static: {s.get("static")}, dynamic: {s.get("dynamic")}, overlay: {s.get("overlay")} '
        )


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


def _combine_wlan_properties_responses(groups: List[str], responses: List[Response]):
    out, failed, passed = [], [], []
    for group, res in zip(groups, responses):
        if res.ok:
            passed += [res]
            for wlan in res.output:
                out += [{'group': group, **wlan}]
        else:
            failed += [res]
    if passed:
        resp: Response = sorted(passed, key=lambda r: r.rl)[0]
        resp.output = out
    else:
        resp: List[Response] = failed

    if failed and passed:
        _ = [log.warning(f'Partial Failure [cyan]{f.url.name}[/] [red]{f.error}[/]: {f.output.get("description", f.output)}', caption=True) for f in failed]

    return resp


@app.command()
def wlans(
    name: str = typer.Argument(None, metavar="[WLAN NAME]", help="Get Details for a specific WLAN", show_default=False,),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    swarm: str = cli.options.swarm_device,
    verbose: int = typer.Option(0, "-v", count=True, help="get more details for SSIDs across all AP groups", show_default=False,),
    sort_by: SortWlanOptions = typer.Option(None, "--sort", help=f"Field to sort by [grey42]{escape('[default: SSID]')}[/]", show_default=False),
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache: bool = cli.options.update_cache,
) -> None:
    """Show WLAN(SSID)/details

    Shows summary of all WLANs in Central by default.  Each SSID is only listed once.
    Use -v (fetch details for wlans in each group) or specify [cyan]--group[/] for more details.
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
    if swarm:
        _dev: CentralObject = cli.cache.get_dev_identifier(swarm, dev_type="ap")
        title = f"{title} in swarm associated with {_dev.name}"
        swarm = _dev.swack_id


    params = {
        "name": name,
        "group": group,
        "swarm_id": swarm,
        "label": label,
        "site": site,
        "calculate_client_count": True,
    }

    # TODO specifying WLAN name ... is ignored if verbose
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    if group:  # Specifying the group implies verbose (same # of API calls either way.)
        resp = central.request(central.get_full_wlan_list, group)
        caption = None  if not resp else f"[green]{len(resp.output)}[/] SSIDs configured in group [cyan]{group}[/]"
        cli.display_results(resp, title=title, caption=caption, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, cleaner=cleaner.get_full_wlan_list, verbosity=verbose, format=tablefmt)
    elif swarm:
        resp = central.request(central.get_full_wlan_list, swarm)
        caption = None  if not resp else f"[green]{len(resp.output)}[/] SSIDs configured in swarm associated with [cyan]{_dev.name}[/]"
        cli.display_results(resp, title=title, caption=caption, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, cleaner=cleaner.get_full_wlan_list, verbosity=verbose, format=tablefmt)
    elif verbose:
        group_res = central.request(central.get_groups_properties)
        if group_res:
            ap_groups = [g['group'] for g in group_res.output if 'AccessPoints' in g['properties']['AllowedDevTypes']]
            batch_req = [BatchRequest(central.get_full_wlan_list, group) for group in ap_groups]
            batch_resp = cli.central.batch_request(batch_req)
            resp = _combine_wlan_properties_responses(ap_groups, batch_resp)
        else:
            resp = group_res

        cli.display_results(resp, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile, cleaner=cleaner.get_full_wlan_list, verbosity=verbose, format=tablefmt)
    else:
        resp = central.request(central.get_wlans, **params)
        caption = None
        if resp and not name:
            caption = [f'[green]{len(resp.output)}[/] SSIDs,  [green]{sum([wlan.get("client_count", 0) for wlan in resp.output])}[/] Wireless Clients.']
            caption += ["Summary Output, Specify the group ([cyan]--group GROUP[/])",  "or use the verbose flag ([cyan]`-v`[/]) for additional details"]
        cli.display_results(resp, tablefmt=tablefmt, title=title, caption=caption, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_wlans)


@app.command()
def cluster(
    group: str = typer.Argument(..., autocompletion=cli.cache.group_completion, show_default=False,),
    ssid: str = typer.Argument(..., help="SSIDs are not cached.  Ensure text/case is accurate.", show_default=False,),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
) -> None:
    """Show Cluster mapped to a given group/SSID
    """
    caption = None
    group: CacheGroup = cli.cache.get_group_identifier(group)
    resp = cli.central.request(cli.central.get_wlan_cluster_by_group, group.name, ssid)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    if resp and not resp.output:
        caption = [
            ":information:  This API will return 200 if the SSID does not exist in the group / or the SSID is bridge mode.",
            f"Ensure {ssid} is accurate, as WLANs/SSIDs are not cached.",
            f"Use 'show wlans -v' to see details for all SSIDs or 'show wlans --group {group.name}' to see details for SSIDs in group {group.name}",
        ]
    elif tablefmt == "rich":
        resp.output = [{"SSID": resp.output.get("profile", ""), **d} for d in resp.output.get("gw_cluster_list", resp.output)]
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"Cluster details for [green]{ssid}[/] in group [green]{group.name}[/]",
        pager=pager,
        caption=caption,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.simple_kv_formatter
    )


@app.command()
def vsx(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
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
        sort_by=sort_by,
        reverse=reverse
    )


# FIXME show clients wireless <tab completion> does not filter based on type of device
# FIXME show clients wireless AP-NAME does not filter only devices on that AP
# Same applies for wired
@app.command()
def clients(
    client: str = typer.Argument(
        None,
        metavar=iden_meta.client,
        help="Show details for a specific client. [grey42 italic]verbose assumed.[/]",
        autocompletion=cli.cache.client_completion,
        show_default=False,
    ),
    past: TimeRange = cli.options("3h", include_mins=False).past,
    group: str = typer.Option(None, metavar="<Group>", help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, metavar="<Site>", help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, metavar="<Label>", help="Filter by Label", show_default=False,),
    wireless: bool = typer.Option(False, "-w", "--wireless", help="Show only wireless clients", show_default=False,),
    wired: bool = typer.Option(False, "-W", "--wired", help="Show only wired clients", show_default=False,),
    ssid: str = typer.Option(None, help="Filter by SSID [grey42 italic](Applies only to wireless clients)[/]", show_default=False,),
    band: RadioBandOptions = typer.Option(None, help="Filter by Band [grey42 italic](Applies only to wireless clients)[/]", show_default=False,),
    denylisted: bool = typer.Option(False, "-D", "--denylisted", help="Show denylisted clients [grey42 italic](--dev (AP only) must also be supplied)[/]",),
    failed: bool = typer.Option(False, "-F", "--failed", help="Show clients that have failed to connect", show_choices=False,),
    device: str = cli.options.device,
    verbose: int = cli.options.verbose,
    sort_by: SortClientOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
) -> None:
    """Show clients/details

    Shows clients that have connected within the last 3 hours by default.
    """
    central = cli.central
    if [site, group, label].count(None) < 2:
        cli.exit("You can only specify one of [cyan]--group[/], [cyan]--label[/], [cyan]--site[/] filters")

    kwargs = {}
    dev = None
    title = "All Clients"
    if band:
        kwargs["band"] = band.value
    if client:
        _client = cli.cache.get_client_identifier(client, exit_on_fail=True)
        kwargs["mac"] = _client.mac
        title = f"Details for client [cyan]{_client.name}[/]|[cyan]{_client.mac}[/]|[cyan]{_client.ip}[/]"
        verbose = verbose or 1
    elif device:
        dev: CentralObject = cli.cache.get_dev_identifier(device)
        kwargs["client_type"] = "wireless" if dev.type == "ap" else "wired"
        if dev.generic_type == "switch" and dev.swack_id:
            kwargs["stack_id"] = dev.swack_id
        else:
            kwargs["serial"] = dev.serial
        title = f'{dev.name} Clients'
        ignored = {
            "group": group,
            "site": site,
            "label": label
        }
        if any([ignored.values()]):
            for k, v in ignored.items():
                if v:
                    log.warning(f"[cyan]--{k}[/] [green]{v}[/] ignored.  Doesn't make sense with [cyan]--dev[/] [green]{dev.name}[/] specified.", log=False, caption=True)
            group = site = label = None

    if denylisted:
        if not dev:
            cli.exit("[cyan]--dev[/] :triangular_flag: is required when [cyan]-D|--denylisted[/] :triangular_flag: is set.", emoji=True)
        elif dev.type != "ap":
            cli.exit(f"[cyan]-D|--denylisted[/]  :triangular_flag: is only valid for APs not {lib_to_gen_plural(dev.type)}.", emoji=True)
        else:
            if len(kwargs) > 2:  # client_type and serial
                log.warning(f"Only [cyan]--dev[/] is appropriate with [cyan]-D|--denylisted[/] flag is used.  {len(kwargs) - 1} invalid flags were ignored.", caption=True)
            kwargs = {"serial": dev.serial}
            title = f"{dev.name} Denylisted Clients"

    if not client:
        if wired:
            title = "All Wired Clients" if not dev else f"{dev.name} Wired Clients"
            kwargs["client_type"] = "wired"
        elif wireless:
            title = f"{'All' if not dev else dev.name} Wireless Clients"
            kwargs["client_type"] = "wireless"
            if band:
                title = f"{title} associated with {band}Ghz radios"
        elif band:
            title = f"{'All' if not dev else dev.name} Wireless Clients associated with {band}Ghz radios"
            kwargs["client_type"] = "wireless"

    if not denylisted:
        if group:
            _group = cli.cache.get_group_identifier(group)
            kwargs["group"] = _group.name
            title = f"{title} in group {_group.name}"

        if site:
            _site = cli.cache.get_site_identifier(site)
            kwargs["site"] = _site.name
            title = f"{title} in site {_site.name}"

        if label:
            _label = cli.cache.get_label_identifier(label)
            kwargs["label"] = _label.name
            title = f"{title} on devices with label {_label.name}"

        if ssid:
            kwargs["network"] = ssid
            if "Wired Clients" in title:
                log.info(f"[cyan]--ssid[/] [bright_green]{ssid}[/] flag ignored for wired clients", caption=True, log=False)
            else:
                title = f"{title} (WLAN client filtered by those connected to [cyan]{ssid}[/])" if title.lower() == "all clients" else f"{title} connected to [cyan]{ssid}[/]"

        if failed:
            kwargs["client_status"] = "FAILED_TO_CONNECT"
            title = title.replace("Clients", "Failed Clients")

        if past:
            kwargs["past"] = past.upper()
            title = f'{title} (past {past.replace("h", " hours").replace("d", " days").replace("w", " weeks").replace("m", " months")})'

    if not denylisted:
        resp = central.request(cli.cache.refresh_client_db, **kwargs)
    else:
        resp = central.request(cli.central.get_denylist_clients, **kwargs)

    if not resp:
        cli.display_results(resp, exit_on_fail=True)

    caption = None if any([client, denylisted, failed]) else _build_client_caption(resp, wired=wired, wireless=wireless, band=band, device=dev, verbose=verbose)

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    verbose_kwargs = {}
    if not denylisted:
        verbose_kwargs["cleaner"] = cleaner.get_clients
        verbose_kwargs["cache"] = cli.cache
        verbose_kwargs["verbosity"] = verbose
        verbose_kwargs["format"] = tablefmt

    if sort_by:
        sort_by = sort_by if sort_by != "dot11" else "802.11"
        if sort_by.value == "last-connected":  # We invert so the most recent client is on top
            reverse = not reverse

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        **verbose_kwargs
    )


@app.command()
def tunnels(
    gateway: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, case_sensitive=False, show_default=False,),
    time_range: TimeRange = typer.Option(TimeRange._1d, "--past", case_sensitive=False, help="Time Range for usage/trhoughput details where 3h = 3 Hours, 1d = 1 Day, 1w = 1 Week, 1m = 1Month, 3m = 3Months."),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
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

    cli.display_results(resp, title=f'{dev.rich_help_text} Tunnels', caption=caption, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_gw_tunnels)


@app.command(hidden=config.is_cop)
def uplinks(
    gateway: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, case_sensitive=False, show_default=False,),
    time_range: TimeRange = typer.Option(TimeRange._1d, "--past", case_sensitive=False, help="Time Range for usage/trhoughput details where 3h = 3 Hours, 1d = 1 Day, 1w = 1 Week, 1m = 1Month, 3m = 3Months."),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show Branch Gateway/VPNC Uplink details"""
    dev = cli.cache.get_dev_identifier(gateway, dev_type="gw")
    resp = cli.central.request(cli.central.get_gw_uplinks_details, dev.serial, timerange=time_range.value)

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")

    cli.display_results(resp, title=f'{dev.rich_help_text} Tunnels', tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_gw_tunnels)


# TODO use common time parser see clishowbandwidth
@app.command()
def roaming(
    client: str = typer.Argument(..., metavar=iden_meta.client, autocompletion=cli.cache.client_completion, case_sensitive=False, help="Client username, ip, or mac", show_default=False,),
    start: datetime = cli.options(timerange="3h").start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
    refresh: bool = typer.Option(False, "--refresh", "-R", help="Cache is used to determine mac if username or ip are provided. This forces a cache update prior to lookup."),
    drop: bool = typer.Option(False, "--drop", "-D", help="(implies -R): Drop all users from existing cache, then refresh.  By default any user that has ever connected is retained in the cache.",),
    sort_by: SortClientOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
) -> None:
    """Show wireless client roaming history.

    If ip or username are provided the client cache is used to lookup the clients mac address.
    The cache is updated anytime a show clients ... is ran, or automatically if the client
    is not found in the cache.

    The -R flag can be used to force a cache refresh prior to looking up roaming history.
    """
    start, end = cli.verify_time_range(start, end=end, past=past)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table)
    title = "Roaming history"

    if refresh or drop:
        resp = cli.central.request(cli.cache.refresh_client_db, "wireless", truncate=drop)
        if not resp:
            cli.display_results(resp, exit_on_fail=True)

    mac = utils.Mac(client)
    if not mac.ok:
        client = cli.cache.get_client_identifier(client)
        mac = utils.Mac(client.mac)
        title = f'{title} for {utils.color([client.name, mac.cols], sep="|")}'
    else:
        title = f'{title} for {mac.cols}'


    resp = cli.central.request(cli.central.get_client_roaming_history, mac.cols, from_time=start, to_time=end)
    caption = None if not resp else f"{len(resp)} roaming events"
    caption = f"{caption} in past 3 hours" if not start else f"{caption} in {DateTime(start.timestamp(), 'timediff-past')}"
    cli.display_results(resp, title=title, caption=caption, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_client_roaming_history)


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
        autocompletion=cli.cache.event_log_completion,
        show_default=False,
    ),
    cencli: bool = typer.Option(False, "--cencli", help="Show cencli logs", callback=show_logs_cencli_callback),
    tail: bool = typer.Option(False, "-f", help="follow tail on log file (implies show logs cencli)", is_eager=True),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    _all: bool = typer.Option(False, "-a", "--all", help="Display all available event logs.  Overrides default of 30m", show_default=False,),
    count: int = typer.Option(None, "-n", max=10_000, help="Collect Last n logs [grey42 italic]max: 10,000[/]", show_default=False,),
    start: datetime = cli.options(timerange="30m").start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
    device: str = cli.options.device,
    swarm: bool = typer.Option(False, "--swarm", "-s", help="Filter logs for IAP cluster associated with provided device [cyan]--device[/] required.", show_default=False,),
    level: LogLevel = typer.Option(None, "--level", help="Filter events by log level", show_default=False,),
    client: str = typer.Option(None, "--client", metavar=iden_meta.client, autocompletion=cli.cache.client_completion, show_default=False,),
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
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
    verbose: bool = typer.Option(False, "-v", help="Verbose: Show logs with original field names and minimal formatting (vertically)", rich_help_panel="Formatting",),
) -> None:
    """Show device event logs (last 30m by default) or show cencli logs.

    [italic]Audit logs have moved to [cyan]cencli show audit logs[/cyan][/italic]
    """
    title="Device event Logs"
    if cencli or (event_id and "cencli".startswith(event_id.lower())):
        from centralcli import log
        log.print_file() if not tail else log.follow()
        cli.exit(code=0)

    # TODO move to common func for use by show logs and show audit logs
    if event_id:
        event_details = cli.cache.get_event_log_identifier(event_id)
        cli.display_results(
            Response(output=event_details),
            tablefmt="action",
        )
        cli.exit(code=0)
    else:
        if (_all or count) and [start, end, past].count(None) != 3:
            cli.exit("Invalid combination of arguments. [cyan]--start[/], [cyan]--end[/], and [cyan]--past[/] are invalid when [cyan]-a[/]|[cyan]--all[/] or [cyan]-n[/] flags are used.")

        start, end = cli.verify_time_range(start, end=end, past=past)
        level = level if level is None else level.name
        dev_id = None
        swarm_id = None
        if device:
            device = cli.cache.get_dev_identifier(device)
            if swarm:
                if device.type != "ap":
                    log.warning(f"[cyan]--s[/]|[cyan]--swarm[/] option ignored, only valid on APs not {device.type}")
                else:
                    swarm_id = device.swack_id
            else:
                dev_id = device.serial

        client_mac = None
        if client:
            if utils.Mac(client).ok:
                client_mac = client
            else:
                _client = cli.cache.get_client_identifier(client)
                client_mac = _client.mac

        if _all:
            start = pendulum.now(tz="UTC").subtract(days=89)  # max 90 but will fail pagination calls as now still moves macking this value > 90 so we use 89.  get_events defaults to now - 3 hours if not specified.
            title = f"All available {title}"
            count = 10_000
        elif count:
            title = f"Last {count} {title}"
        elif [start, end].count(None) == 2:
            start = pendulum.now(tz="UTC").subtract(minutes=30)
            title = f"{title} for last 30 minutes"

    kwargs = {
        "group": group,
        "swarm_id": swarm_id,
        "label": None if not label else cli.cache.get_label_identifier(label).name,
        "from_time": start,
        "to_time": end,
        "client_mac": client_mac,
        "bssid": bssid,
        # "device_mac": None if not device else device.mac,  # no point we use serial
        "hostname": hostname,
        "device_type": dev_type,
        "site": None if not site else cli.cache.get_site_identifier(site).name,
        "serial": dev_id,
        "level": level,
        "event_description": description,
        "event_type": event_type,
        # "fields": fields,
        # "calculate_total": True,  # Total defaults to True in get_events for benefit of async multi-call
        "count": count,
    }

    central = cli.central
    resp = central.request(central.get_events, **kwargs)

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    _cmd_txt = "[bright_green] show logs <id>[reset]"
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=not reverse,
        set_width_cols={"event type": {"min": 5, "max": 12}},
        cleaner=cleaner.get_event_logs if not verbose else None,
        cache_update_func=cli.cache.update_event_db if not verbose else None,
        caption=f"[reset]Use {_cmd_txt} to see details for an event.  Events lacking an id don\'t have details.",
    )


@app.command()
def alerts(
    group: str = cli.options(timerange="24h").group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    device: str = cli.options.device,
    severity: AlertSeverity = typer.Option(None, help="Filter by alerts by severity.", show_default=False,),
    search: str = typer.Option(None, help="Filter by alerts with search term in name/description/category.", show_default=False,),
    ack: bool = typer.Option(None, help="Show only acknowledged (--ack) or unacknowledged (--no-ack) alerts", show_default=False,),
    alert_type: AlertTypes = typer.Option(None, "--type", help="Filter by alert type", show_default=False,),
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
    sort_by: SortAlertOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    verbose: bool = typer.Option(False, "-v", help="Show alerts with original field names and minimal formatting (vertically)"),
) -> None:
    """Show Alerts/Notifications (for past 24 hours by default).

    :information:  Notification must be Configured.
    """
    if device:
        device: CacheDevice = cli.cache.get_dev_identifier(device)
    if group:
        group: CacheGroup = cli.cache.get_group_identifier(group)
    if site:
        site: CacheSite = cli.cache.get_site_identifier(site)
    if label:
        if group:
            log.warning(f"Provided label {label}, was ignored.  You can only specify one of [cyan]group[/], [cyan]label[/]", caption=True)
            label = None
        else:
            label: CacheLabel = cli.cache.get_label_identifier(label)

    if alert_type:
        alert_type = "user_management" if alert_type == "user" else alert_type
        alert_type = "ids_events" if alert_type == "ids" else alert_type

    if severity:
        severity = severity.title() if severity != "info" else severity.upper()

    start, end = cli.verify_time_range(start=start, end=end, past=past)

    kwargs = {
        "group": None if not group else group.name,
        "label": None if not label else label.name,
        "from_time": start,
        "to_time": end,
        "serial": None if not device else device.serial,
        "site": None if not site else site.name,
        'severity': severity,
        "search": search,
        "type": alert_type,
        'ack': ack,
    }

    central = cli.central
    resp = central.request(central.get_alerts, **kwargs)

    caption = "in past 24 hours." if not start else f"in {DateTime(start.timestamp(), 'timediff-past')}"
    caption = f"[cyan]{len(resp)}{' active' if not ack else ' '} Alerts {caption}[/]"
    cleaner_func = cleaner.get_alerts if not verbose else None
    if resp.ok and len(resp) == 0:
        resp.output = render.rich_capture(f":information:  {caption}", emoji=True)
        cleaner_func = None

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    title = "Alerts/Notifications (Configured Notification Rules)"
    if device:
        title = f"{title} [reset]for[cyan] {device.generic_type.upper()} {device.name}|{device.serial}[reset]"
    if group or site or label:
        title = f"{title} [bright_green]filtered by[/]"
        if group:
            title = f"{title} group: [cyan]{group.name}[/]"
        if site:
            title = f"{title} site: [cyan]{site.name}[/]"
        if label:
            title = f"{title} label: [cyan]{site.name}[/]"

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=not reverse,
        cleaner=cleaner_func,
        caption=caption,
    )


@app.command()
def notifications(
    search: str = typer.Option(None, help="Filter by alerts with search term in name/description/category."),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
    update_cache = cli.options.update_cache,
) -> None:
    """Show alert/notification configuration.

    Display alerty types, notification targets, and rules.
    """
    central = cli.central
    resp = central.request(central.central_get_notification_config, search=search)

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="yaml")
    title = "Alerts/Notifications Configuration (Configured Notification Targets/Rules)"

    # TODO cleaner, currently raw response in yaml
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
    )


@app.command(short_help="Re-display output from Last command.", help="Re-display output from Last command.  (No API Calls)")
def last(
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    if not config.last_command_file.exists():
        cli.exit("Unable to find cache for last command.")

    kwargs = config.last_command_file.read_text()
    import json
    kwargs = json.loads(kwargs)

    last_format = kwargs.get("tablefmt", "rich")
    kwargs["tablefmt"] = cli.get_format(do_json, do_yaml, do_csv, do_table, default=last_format)
    if not kwargs.get("title") or "Previous Output" not in kwargs["title"]:
        kwargs["title"] = f"{kwargs.get('title') or ''} Previous Output " \
                        f"{cleaner._convert_epoch(int(config.last_command_file.stat().st_mtime))}"  # Update to use DateTime
    data = kwargs["outdata"]
    del kwargs["outdata"]

    cli.display_results(
        data=data, outfile=outfile, sort_by=sort_by, reverse=reverse, pager=pager, stash=False, **kwargs
    )


@app.command(help="Show configured webhooks")
def webhooks(
    sort_by: SortWebHookOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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


@app.command(help="Show WebHook Proxy details/logs", hidden=not hook_enabled)
def hook_proxy(
    what: ShowHookProxyArgs = typer.Argument(None, callback=hook_proxy_what_callback),
    tail: bool = typer.Option(False, "-f", help="follow tail on log file (implies show hook-proxy logs)", is_eager=True),
    brief: bool = typer.Option(False, "-b", help="Brief output for 'pid' and 'port'"),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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
            cli.exit("WebHook Proxy is not running.")

        br = proc[1] if what == "port" else proc[0]
        _out = f"[{proc[0]}] WebHook Proxy is listening on port: {proc[1]}" if not brief else br
        cli.exit(_out, code=0)


@app.command()
def archived(
    sort_by: SortArchivedOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show archived devices"""
    resp = cli.central.request(cli.central.get_archived_devices)
    if resp.raw and "devices" in resp.raw:
        plat_cust_id = list(set([inner.get("platform_customer_id", "--") for inner in resp.raw["devices"]]))
        caption = f"Platform Customer ID: {plat_cust_id[0]}" if len(plat_cust_id) == 1 else None  #  Should not happen but if it does the cleaner keeps the item in the dicts


    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)
    cli.display_results(resp, tablefmt=tablefmt, title="Archived Devices", caption=caption, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_archived_devices)


# TODO sort_by / reverse tablefmt options add verbosity 1 to cleaner
@app.command()
def portals(
    portal: List[str] = typer.Argument(
        None,
        metavar="[name|id]",
        help=f"show details for a specific portal profile [grey42]{escape('[default: show summary for all portals]')}[/]",
        autocompletion=cli.cache.portal_completion,
        show_default=False,),
    logo: bool = typer.Option(
        False,
        "-L", "--logo",
        metavar="PATH",
        help=f"Download logo for specified portal to specified path. [cyan]Portal argument is requrired[/] [grey42]{escape(f'[default: {Path.cwd()}/<original_logo_filename>]')}[/]",
        show_default = False,
        writable=True,
    ),
    sort_by: SortPortalOptions = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show Configured Guest Portals, details for a specific portal, or download logo for a specified portal"""
    path = Path.cwd()
    if portal:
        if len(portal) > 2:
            cli.exit("Too many Arguments")
        elif len(portal) > 1:
            if not logo:
                cli.exit("Too many Arguments")
            path = Path(portal[-1])
            if not path.is_dir() and not path.parent.is_dir():
                cli.exit(f"[cyan]{path.parent}[/] directory not found, provide full path with filename, or an existing directory to use original filename")
        portal = portal[0]

    if portal is None:
        resp: Response = cli.central.request(cli.cache.refresh_portal_db)
        _cleaner = cleaner.get_portals
    else:
        p: CentralObject = cli.cache.get_name_id_identifier("portal", portal)
        resp: Response = cli.central.request(cli.central.get_portal_profile, p.id)
        _cleaner = cleaner.get_portal_profile
        if logo and resp.ok:
            download_logo(resp, path, p)  # this will exit CLI after writing to file

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml" if portal else "rich")
    cli.display_results(resp, tablefmt=tablefmt, title="Portals", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=_cleaner, fold_cols=["url"],)


# TODO add sort_by completion, portal completion
@app.command()
def guests(
    portal: str = typer.Argument(None, help=f"portal name [grey42]{escape('[default: Guests for all defined User/Pass portals]')}[/]", autocompletion=cli.cache.portal_completion, show_default=False,),
    refresh: bool = typer.Option(False, "-R", "--refresh", help="Applies only if portal is not provided.  Refresh the portal cache prior to fetching guests for all User/Pass portals"),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show Guests configured for a Portal"""
    caption = None
    title="Guest Users"
    if portal:
        portal: CachePortal = cli.cache.get_name_id_identifier("portal", portal)
        resp = cli.central.request(cli.cache.refresh_guest_db, portal.id, )
        title = f"{title} for {portal.name} portal"

    else:
        if refresh:
            _ = cli.central.request(cli.cache.refresh_portal_db)
        portals = [portal for portal in cli.cache.portals if "Username/Password" in portal["auth_type"]]
        for idx in range(0, 2):
            portals = [portal for portal in cli.cache.portals if "Username/Password" in portal["auth_type"]]
            if not portals:
                if idx == 0 and not refresh:
                    _ = cli.central.request(cli.cache.refresh_portal_db)
                else:
                    cli.exit(":information:  No portals configured with Username/Password auth type", code=0)

        batch_resp = cli.central.batch_request([BatchRequest(cli.cache.refresh_guest_db, portal["id"]) for portal in portals])
        resp_by_name = {resp: portal for portal, resp in zip(portals, batch_resp)}
        passed = [r for r in batch_resp if r.ok]
        failed = [] if len(passed) == len(batch_resp) else [r for r in batch_resp if not r.ok]
        if passed:
            passed = sorted(passed, key=lambda r: r.rl)
            resp = passed[-1]
            resp.output = [{"portal": resp_by_name[r]["name"], **item} for r in passed for item in r.output]
            resp.raw = {r.url.path: r.raw for r in batch_resp}
            portal_ids = [f"[cyan]{p['name']}[/]: {p['id']}" for p in portals]
            caption = f"[italic cornflower_blue]Portal IDs[/]: {', '.join(portal_ids)}"
            if failed:
                log.error(f"Partial call failure.  {len(failed)} API requests failed.  Refer to logs [cyan]cencli show logs cencli[/].", caption=True)
        else:
            resp = failed

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    cli.display_results(resp, tablefmt=tablefmt, title=title, caption=caption, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.get_guests, output_format=tablefmt)

def _build_radio_caption(data: List[Dict[str, str | int]]) -> str |  None:
    try:
        two_four_cnt, five_cnt, six_cnt, ap_names = 0, 0, 0, []
        two_four_up_cnt, five_up_cnt, six_up_cnt = 0, 0, 0
        for ap in data:
            ap_names += [ap["name"]]
            if "2.4" in ap["radio_name"]:
                two_four_cnt += 1
                if ap["status"] == "Up":
                    two_four_up_cnt += 1
            elif "5 GHz" in ap["radio_name"]:
                five_cnt += 1
                if ap["status"] == "Up":
                    five_up_cnt += 1
            elif "6 GHz" in ap["radio_name"]:
                six_cnt += 1
                if ap["status"] == "Up":
                    six_up_cnt += 1
        radio_cnt = len(ap_names)
        ap_cnt = len(list(set(ap_names)))
        caption = ''.join(
            [
                f"Counts [grey42 italic](in this output)[/]: Total APs [cyan]{ap_cnt}[/], Total Radios: [cyan]{radio_cnt}[/], ",
                f"2.4Ghz: [cyan]{two_four_cnt}[/] ([bright_green]{two_four_up_cnt}[/], [red]{two_four_cnt - two_four_up_cnt}[/]) ",
                f"5Ghz: [cyan]{five_cnt}[/] ([bright_green]{five_up_cnt}[/], [red]{five_cnt - five_up_cnt}[/]) ",
                f"6Ghz: [cyan]{six_cnt}[/] ([bright_green]{six_cnt}[/], [red]{six_cnt - six_up_cnt}[/])",
            ]
        )
    except Exception as e:
        log.error(f"Unable to build caption for show radios due to {e.__class__.__name__}")
        return

    return caption


@app.command()
def radios(
    aps: List[str] = typer.Argument(None, metavar=iden_meta.dev_many, hidden=False, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: str = typer.Option(None, help="Filter by Group", autocompletion=cli.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, help="Filter by Site", autocompletion=cli.cache.site_completion, show_default=False,),
    label: str = typer.Option(None, help="Filter by Label", autocompletion=cli.cache.label_completion,show_default=False,),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP", show_default=False,),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    sort_by: str = cli.options.sort_by,
    reverse: bool = cli.options.reverse,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show details for Radios
    """
    if up and down:
        ...  # They used both flags.  ignore
    elif up or down:
        status = "Down" if down else "Up"

    status = None if not status else status.title()
    group: CacheGroup = None if not group else cli.cache.get_group_identifier(group)
    site: CacheSite = None if not site else cli.cache.get_site_identifier(site)
    label: CacheLabel = None if not label else cli.cache.get_label_identifier(label)

    params = {
        "group": None if not group else group.name,
        "site": None if not site else site.name,
        "status": status,
        "label": None if not label else label.name,
        "public_ip_address": pub_ip
    }
    default_params = {
        "calculate_client_count": True,
        "show_resource_details": True,
        "calculate_ssid_count": True,
    }

    params = {k: v for k, v in params.items() if v is not None}
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    if aps:
        aps: List[CacheDevice] = [cli.cache.get_dev_identifier(ap, dev_type="ap") for ap in aps]
        resp = cli.central.batch_request([BatchRequest(cli.central.get_devices, "ap", serial=ap.serial, **default_params) for ap in aps])
        passed = [r for r in resp if r.ok]
        failed = [r for r in resp if not r.ok]
        if passed:
            combined = [ap for r in passed for ap in r.output]
            resp = sorted(passed, key=lambda ap: ap.rl)[0]
            resp.output = [{"name": ap["name"], **rdict} for ap in combined for rdict in ap["radios"]]
        if failed:
            cli.display_results(failed, tablefmt="action")
    else:
        resp = cli.central.request(cli.cache.refresh_dev_db, dev_type="ap", **{**params, **default_params})
        if resp.ok:
            resp.output = [{"name": ap["name"], **rdict} for ap in resp.output for rdict in ap["radios"]]

    if resp.ok:
        # We sort before sending data to renderer to keep groupings by AP name
        if sort_by and resp.output and sort_by in resp.output[0].keys():
            resp.output = list(sorted(resp.output, key=lambda ap: (ap["name"], ap[sort_by])))
        else:
            resp.output = list(sorted(resp.output, key=lambda ap: (ap["name"], ap["radio_name"])))

        caption = _build_radio_caption(resp.output)
        if status:
            resp.output = list(filter(lambda radio: radio["status"] == status, resp.output))

    cli.display_results(resp, tablefmt=tablefmt, title="Radio Details", reverse=reverse, outfile=outfile, pager=pager, caption=caption, group_by="name", cleaner=cleaner.show_radios)


@app.command()
def version(
    debug: bool = cli.options.debug,
) -> None:
    """Show current cencli version, and latest available version.
    """
    cli.version_callback()

@app.command(hidden=os.name != "posix")
def cron(
    accounts: List[str] = typer.Argument(None,),
) -> None:
    """Show contents of cron file that can be used to automate token refresh weekly.

    This will keep the tokens valid, even if cencli is not used.
    """
    if os.name != "posix":
        cli.econsole.print("This command is currently only supported on Linux using cron.  It is possible to do the same via Windows Task Scheduler.  Showing Linux cron.weekly output for reference.")

    user = getpass.getuser()
    exec_path = sys.argv[0]
    py_path = sys.executable

    config_data = {
        "user": user,
        "py_path": py_path,
        "exec_path": exec_path,
        "accounts": "" if not accounts else " ".join(accounts)
    }

    template = Template(cron_weekly)
    config_out = template.render(config_data)

    cli.econsole.rule("/etc/cron.weekly/cencli file contents")
    cli.console.print(config_out)
    cli.econsole.rule()

    cli.econsole.print(
        "Place the above contents into a file: /etc/cron.weekly/cencli [grey42 italic](requires sudo)[/]\n"
        f"Alternatively you can pipe the output directly [cyan]cencli show cron {'' if not accounts else ' '.join(accounts)} | sudo tee /etc/cron.weekly/cencli[/]"
        "\nThen make it executable: [cyan]sudo chmod +x /etc/cron.weekly/cencli[/]"
        "\n\n[cyan]cencli refresh token[/] [dark_olive_green2 italic]command will always update the tokens for the default workspace (that's the -d flag)[/]"
    )


def _get_cencli_config() -> None:
    try:
        from centralcli import config
    except (ImportError, ModuleNotFoundError):
        pkg_dir = Path(__file__).absolute().parent
        if pkg_dir.name == "centralcli":
            sys.path.insert(0, str(pkg_dir.parent))
            from centralcli import config

    omit = ["deprecation_warning", "webhook", "snow", "valid_suffix", "is_completion", "forget", "default_scache_file"]
    out = {k: str(v) if isinstance(v, Path) else v for k, v in config.__dict__.items() if k not in omit}
    out["webhook"] = None if not config.webhook else config.webhook.model_dump()
    out["snow"] = None if not config.snow else config.snow.model_dump()

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
