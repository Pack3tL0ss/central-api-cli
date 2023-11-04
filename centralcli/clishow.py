#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import typer
import time
import pendulum
import asyncio
import sys
from typing import List, Iterable, Literal
from pathlib import Path
from rich import print

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response, cleaner, clishowfirmware, clishowwids, clishowbranch, clishowospf, clishowtshoot, clishowoverlay, BatchRequest, caas, cli, utils, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response, cleaner, clishowfirmware, clishowwids, clishowbranch, clishowospf, clishowtshoot, clishowoverlay, BatchRequest, caas, cli, utils, config
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    ClientArgs, SortInventoryOptions, ShowInventoryArgs, StatusOptions, SortWlanOptions, IdenMetaVars, CacheArgs, LogAppArgs, LogSortBy, SortSiteOptions,
    DevTypes, SortDevOptions, SortTemplateOptions, SortClientOptions, SortCertOptions, SortVlanOptions, SortSubscriptionOptions, SortRouteOptions, DhcpArgs,
    EventDevTypeArgs, ShowHookProxyArgs, SubscriptionArgs, AlertTypes, SortAlertOptions, AlertSeverity, SortWebHookOptions, TunnelTimeRange, lib_to_api, what_to_pretty  # noqa
)

app = typer.Typer()
app.add_typer(clishowfirmware.app, name="firmware")
app.add_typer(clishowwids.app, name="wids")
app.add_typer(clishowbranch.app, name="branch")
app.add_typer(clishowospf.app, name="ospf")
app.add_typer(clishowtshoot.app, name="tshoot")
app.add_typer(clishowoverlay.app, name="overlay")

tty = utils.tty
iden_meta = IdenMetaVars()

def _build_caption(resp: Response, *, inventory: bool = False) -> str:
    dev_types = set([t.get("type", "NOTYPE") for t in resp.output])
    devs_by_type = {_type: [t for t in resp.output if t.get("type", "ERR") == _type] for _type in dev_types}
    status_by_type = {_type: {"total": len(devs_by_type[_type]), "up": len([t for t in devs_by_type[_type] if t.get("status", "") == "Up"]), "down": len([t for t in devs_by_type[_type] if t.get("status", "") == "Down"])} for _type in devs_by_type}
    _cnt_str = ", ".join([f'[{"bright_green" if not status_by_type[t]["down"] else "red"}]{t}[/]: [cyan]{status_by_type[t]["total"]}[/] ([bright_green]{status_by_type[t]["up"]}[/]:[red]{status_by_type[t]["down"]}[/])' for t in status_by_type])
    caption = "  [cyan]Show all[/cyan] displays fields common to all device types. "
    caption = f"[reset]Counts: {_cnt_str}\n{caption}To see all columns for a given device use [cyan]show <DEVICE TYPE>[/cyan]"
    if "gw" in dev_types:
        caption = f"{caption}\n  [magenta]Note[/]: GW firmware version has been simplified, the actual gw version is [cyan]aa.bb.cc.dd-aa.bb.cc.dd[-beta]_build[/]"
        caption = f"{caption}\n  [italic]given the version is repeated it has been simplified.  You need to use the full version string when upgrading."
    if inventory:
        caption = f"{caption}\n  [italic green3]verbose listing, devices lacking name/ip are in the inventory, but have not connected to central.[/]"
    return caption

def show_devices(
    devices: str | Iterable[str] = None, dev_type: Literal["all", "ap", "gw", "cx", "sw", "switch"] = None, include_inventory: bool = False, outfile: Path = None,
    update_cache: bool = False, group: str = None, site: str = None, label: str = None, status: str = None, state: str = None, pub_ip: str = None,
    do_clients: bool = False, do_stats: bool = False, do_ssids: bool = False, sort_by: str = None, reverse: bool = False, pager: bool = False, do_json: bool = False, do_csv: bool = False,
    do_yaml: bool = False, do_table: bool = False
) -> None:
    caption = None
    central = cli.central
    if update_cache:
        cli.central.request(cli.cache.update_dev_db)

    # device details is a lot of data default to yaml output, default horizontal would typically overrun tty
    _formatter = "yaml"

    if group:
        group = cli.cache.get_group_identifier(group)
    if site:
        site = cli.cache.get_site_identifier(site)

    resp = None
    params = {
        "group": None if not group else group.name,
        "site": None if not site else site.name,
        "status": None if not status else status.title(),
        "label": label,
        "public_ip_address": pub_ip,
        "calculate_client_count": do_clients,
        "show_resource_details": do_stats,
        "calculate_ssid_count": do_ssids,
    }

    # status and state keywords both allowed
    if params["status"] is None and state is not None:
        params["status"] = state.title()

    params = {k: v for k, v in params.items() if v is not None}
    if not devices and dev_type is None:
        dev_type = "all"

    if devices:
        cache_generic_types = {
            "aps": "ap",
            "gateways": "gw",
            "mobility_controllers": "gw",
            "switches": "switch"
        }
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
    elif dev_type == "all":
        # if they have a single device type in inventory, it's too many fields to display as table
        if len(cli.cache.device_types) > 1:
            _formatter = "rich"

        if include_inventory:
            resp = cli.cache.get_devices_with_inventory()
            caption = _build_caption(resp, inventory=True)
            if len(params) > 3:
                caption = f'{caption or ""}\n  [bright_red]WARNING[/]: Filtering options ignored, not valid w/ [cyan]-v[/] (include inventory devices)'
        # if no params (expected result may differ) update cli.cache if not updated this session and return results from there
        elif len(params) == 3 and list(params.values()).count(False) == 3:
            if central.get_all_devicesv2 not in cli.cache.updated:
                resp = central.request(cli.cache.update_dev_db)
                caption = _build_caption(resp)
            else:
                # get_all_devicesv2 already called (to populate/update cache) grab response from cache.
                resp = cli.cache.responses.dev
        else:  # will only run if user specifies params (filters)
            resp = central.request(central.get_all_devicesv2, **params)
            caption = _build_caption(resp)
    else:
        resp = central.request(central.get_devices, dev_type, **params)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default=_formatter)
    title_sfx = [
        f"{k}: {v}" for k, v in params.items() if k not in ["calculate_client_count", "show_resource_details", "calculate_ssid_count"] and v
    ] if not include_inventory else ["including Devices from Inventory"]
    title = "Device Details" if not dev_type else f"{what_to_pretty(dev_type)} {', '.join(title_sfx)}".rstrip()

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.get_devices
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
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    verbose: bool = typer.Option(
        False,
        "-v",
        help="additional details (include devices in Inventory that have yet to connect)",
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
        dev_type='all', outfile=outfile, include_inventory=verbose, update_cache=update_cache, group=group, site=site, status=status,
        state=state, label=label, pub_ip=pub_ip, do_stats=do_stats, do_clients=do_clients, sort_by=sort_by, reverse=reverse,
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
        show_default=False,
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
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    verbose: bool = typer.Option(
        False,
        "-v",
        help="additional details (include devices in Inventory that have yet to connect)",
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

    if "all" in devices:
        dev_type = "all"
        devices = None
    else:
        dev_type = None

    show_devices(
        devices, dev_type=dev_type, include_inventory=verbose, outfile=outfile, update_cache=update_cache, group=group, site=site,
        label=label, status=status, state=state, pub_ip=pub_ip, do_stats=do_stats, do_clients=do_clients,
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
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per AP)"),
    do_ssids: bool = typer.Option(False, "--ssids", is_flag=True, help="Calculate SSID count (per AP)"),
    neighbors: bool = typer.Option(False, "-n", "--neighbors", help="Show AP neighbors \[requires --site]", show_default=False,),
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

        # TODO check the value of tagged/untagged VLAN for AP if it has tagged mgmt VLAN
        if resp:
            aps_in_cache = [dev["serial"] for dev in cli.cache.devices if dev["type"] == "ap"]
            ap_connections = [edge for edge in resp.output["edges"] if edge["toIf"]["serial"] in aps_in_cache]
            resp.output = [
                {
                    "ap": x["toIf"].get("deviceName", "--"),
                    "ap_ip": x["toIf"].get("ipAddress", "--"),
                    "ap_serial": x["toIf"].get("serial", "--"),
                    "ap_port": x["toIf"].get("portNumber", "--"),
                    # "ap_untagged_vlan": x["toIf"].get("untaggedVlan"),
                    # "ap_tagged_vlans": x["toIf"].get("taggedVlans"),
                    "switch": x["fromIf"].get("deviceName", "--"),
                    "switch_ip": x["fromIf"].get("ipAddress", "--"),
                    "switch_serial": x["fromIf"].get("serial", "--"),
                    "switch_port": x["fromIf"].get("name", "--"),
                    "untagged_vlan": x["fromIf"].get("untaggedVlan", "--"),
                    "tagged_vlans": ",".join([str(v) for v in x["fromIf"].get("taggedVlans", []) if v != x["fromIf"].get("untaggedVlan", 9999)]),
                    "healthy": "✅" if x.get("health", "") == "good" else "❌"
                } for x in ap_connections
            ]

        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
        cli.display_results(resp, tablefmt=tablefmt, title="AP Neighbors", pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse)
    else:
        if down:
            status = "Down"
        elif up:
            status = "Up"
        show_devices(
            aps, dev_type="aps", outfile=outfile, update_cache=update_cache, group=group, site=site, label=label, status=status,
            state=state, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats, do_ssids=do_ssids,
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
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per switch)"),
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
        switches, dev_type='switches', outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
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
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per switch)"),
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
        gateways, dev_type='gateways', outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
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
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per switch)"),
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
        controllers, dev_type='mobility_controllers', outfile=outfile, update_cache=update_cache, group=group, site=site, label=label,
        status=status, state=state, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats, sort_by=sort_by, reverse=reverse,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, do_table=do_table)


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

    resp = cli.central.request(cli.cache.update_inv_db, dev_type=lib_to_api("inventory", dev_type), sub=sub)
    if verbose:  # TODO just pass this to all_() so output is consistent
        cache_devices = cli.cache.devices
        for idx, dev in enumerate(resp.output):
            from_cache = [d for d in cache_devices if d["serial"] == dev["serial"]]
            if from_cache:
                resp.output[idx] = {**dev, **from_cache[0]}

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        sort_by=sort_by,
        reverse=reverse,
        caption=None if not verbose else _build_caption(resp, inventory=True),
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
    sort_by: SortSubscriptionOptions = typer.Option(None, "--sort"),  # Need to adapt a bit for stats or make sub-command
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
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
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
    dev = cli.cache.get_dev_identifier(device,)
    if dev.generic_type == "gw":
        resp = cli.central.request(cli.central.get_gateway_ports, dev.serial)
    else:
        resp = cli.central.request(cli.central.get_switch_ports, dev.serial, slot=slot, aos_sw=dev.type == "sw")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml")

    # TODO cleaner returns a Dict[dict] assuming "vsx enabled" is the same bool for all ports put it in caption and remove from each item
    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse, cleaner=cleaner.show_interfaces)


@app.command(help="Show (switch) poe details for an interface")
def poe(
    device: str = typer.Argument(..., metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_switch_completion, show_default=False,),
    port: str = typer.Argument(None, show_default=False,),
    _port: str = typer.Option(None, "--port", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", hidden=True),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", hidden=False),
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
    port = _port if _port else port
    dev = cli.cache.get_dev_identifier(device, dev_type="switch")
    resp = cli.central.request(cli.central.get_switch_poe_details, dev.serial, port=port, aos_sw=dev.type == "sw")
    resp.output = utils.unlistify(resp.output)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="json")
    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile)
    # TODO output cleaner / sort & reverse options


@app.command()
def vlans(
    dev_site: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.dev} (vlans for a device) OR {iden_meta.site} (vlans for a site)",
        autocompletion=cli.cache.dev_gw_switch_site_completion,
        show_default=False,
    ),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
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
    obj = cli.cache.get_identifier(dev_site, qry_funcs=("dev", "site"))

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
            resp = central.request(central.get_switch_vlans, obj.serial, aos_sw=obj.type == "sw")
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


@app.command(short_help="Show DHCP pool or lease details (gateways only)")
def dhcp(
    what: DhcpArgs = typer.Argument(..., help=["server", "clients"]),
    dev: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.dev} (Valid for Gateways Only) ",
        autocompletion=cli.cache.dev_completion,
    ),
    no_res: bool = typer.Option(False, "--no-res", is_flag=True, help="Filter out reservations"),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by"),
    reverse: bool = typer.Option(False, "-r", help="Reverse sort order", show_default=False,),
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
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting) (vertically)",
        show_default=False,
    ),
) -> None:
    central = cli.central
    dev = cli.cache.get_dev_identifier(dev, dev_type="gw")

    # if dev.generic_type != "gw":
    #     typer.secho(f"show dhcp ... only valid for gateways not {dev.generic_type}", fg="red")
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
    # TODO The API method only accepts swarm id for IAP which AOS10 does not have / serial rejected
    central = cli.central
    if len(device) > 2:
        typer.echo(f"Unexpected argument {', '.join([a for a in device[0:-1] if a != 'status'])}")

    params, dev = {}, None
    if device and device[-1] != "status":
        dev = cli.cache.get_dev_identifier(device[-1])
        params["serial"] = dev.serial
    else:
        print("Missing required parameter [cyan]<device>[/]")

    resp = central.request(central.get_upgrade_status, **params)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Upgrade Status" if not dev else f"{dev.name} Upgrade Status",
        pager=pager,
        outfile=outfile
    )


@app.command("cache", short_help="Show contents of Identifier Cache.", hidden=True)
def cache_(
    args: List[CacheArgs] = typer.Argument(None, show_default=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False,),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False,),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by", show_default=False,),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True,),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
):
    args = ('all',) if not args else args
    for arg in args:
        cache_out = getattr(cli.cache, arg)
        tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_yaml=do_yaml, default="rich" if "all" not in args else "yaml")
        cli.display_results(
            data=cache_out,
            tablefmt=tablefmt,
            title=f'Cache {arg.title().replace("_", " ")}',
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=reverse,
            stash=False,
        )


@app.command(short_help="Show groups/details")
def groups(
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    verbose: bool = typer.Option(False, "-v", help="Verbose: include additional group properties", show_default=False,),
    verbose2: bool = typer.Option(
        False,
        "-vv",
        help="Show raw response (no formatting but still honors --yaml, --csv ... if provided)",
        show_default=False,
    ),
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
    if central.get_all_groups not in cli.cache.updated:
        resp = asyncio.run(cli.cache.update_group_db())
    else:
        resp = cli.cache.responses.group

    if resp and verbose:
        groups = [g["name"] for g in resp.output]
        verbose_resp = central.request(central.get_groups_properties, groups=groups)
        if not verbose_resp:
            print("Error: Additional API call to gather group properties for verbose output failed.")
            cli.display_results(verbose_resp, tablefmt="action")
        else:
            for idx, g in enumerate(verbose_resp.output):
                g["properties"]["ApNetworkRole"] = g["properties"].get("ApNetworkRole", "NA")
                g["properties"]["GwNetworkRole"] = g["properties"].get("GwNetworkRole", "NA")
                g["properties"] = {k: g["properties"][k] for k in sorted(g["properties"].keys())}
                for grp in resp.output:
                    if g["group"] == grp["name"]:
                        verbose_resp.output[idx] = {**grp, **g["properties"]}
                        continue
            verbose_resp.output = cleaner.strip_no_value(verbose_resp.output)
            resp = verbose_resp

    tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_yaml=do_yaml)
    cli.display_results(resp, tablefmt=tablefmt, title="Groups", pager=pager, outfile=outfile, cleaner=cleaner.show_groups)


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


@app.command(short_help="Show AP lldp neighbor", help="Show AP lldp neighbor.  Command only applies to APs at this time.")
def lldp(
    device: List[str] = typer.Argument(
        ...,
        metavar=iden_meta.dev_many,
        autocompletion=lambda incomplete: cli.cache.dev_completion(incomplete=incomplete, args=["ap"]),
        show_default=False,
    ),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
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
    central = cli.central

    devs = [cli.cache.get_dev_identifier(_dev, dev_type="ap") for _dev in device if not _dev.lower().startswith("neighbor")]
    batch_reqs = [BatchRequest(central.get_ap_lldp_neighbor, (dev.serial,)) for dev in devs]
    batch_resp = central.batch_request(batch_reqs)
    if all([res.ok for res in batch_resp]):
        concat_resp = batch_resp[-1]
        concat_resp.output = [{"name": f'{dev.name} {neighbor.get("localPort", "")}'.rstrip(), **neighbor} for res, dev in zip(batch_resp, devs) for neighbor in res.output]
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="yaml")

    cli.display_results(
        concat_resp,
        tablefmt=tablefmt,
        title=f"LLDP Neighbor Info",
        pager=pager,
        outfile=outfile,
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


@app.command(short_help="Show last known running config for a device")
def run(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
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
) -> None:

    central = cli.central
    dev = cli.cache.get_dev_identifier(device)

    resp = central.request(central.get_device_configuration, dev.serial)
    cli.display_results(resp, pager=pager, outfile=outfile)


# TODO --status does not work
# https://web.yammer.com/main/org/hpe.com/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMTQyNzU1MDg5MTQ0MjE3NiJ9
@app.command(
    "config",
    short_help="Show Central Group/Device or cencli Config",
    help=(
        "Show Effective Group/Device Config (UI Group) or cencli config."
        "    Examples: 'cencli show config GROUPNAME --gw', "
        "'cencli show config DEVICENAME', "
        "'cencli show config cencli'"
    ),
)
def config_(
    group_dev: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.group_dev_cencli}",
        autocompletion=cli.cache.group_dev_ap_gw_completion,
        help = "Device Identifier for (AP or GW), Group Name along with --ap or --gw option, or 'cencli' to see cencli configuration details.",
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
    if group_dev == "cencli":  # Hidden show cencli config
        return _get_cencli_config()

    group_dev = cli.cache.get_identifier(group_dev, ["group", "dev"], device_type=["ap", "gw"])
    if group_dev.is_group:
        group = group_dev
        if device:
            device = cli.cache.get_dev_identifier(device)
        elif not do_ap and not do_gw:
            print("Invalid Input, --gw or --ap option must be supplied for group level config.")
            raise typer.Exit(1)
    else:  # group_dev is a device iden
        group = cli.cache.get_group_identifier(group_dev.group)
        if device is not None:
            print("Invalid input enter [Group] [device iden] or [device iden]")
            raise typer.Exit(1)
        else:
            device = group_dev

    _data_key = None
    if do_gw or (device and device.generic_type == "gw"):
        if device and device.generic_type != "gw":
            print(f"Invalid input: --gw option conflicts with {device.name} which is an {device.generic_type}")
            raise typer.Exit(1)
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
                print(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
                raise typer.Exit(1)
        else:
            func = cli.central.get_ap_config
            args = [group.name]
    else:
        print(f"This command is currently only supported for gw and ap, not {device.generic_type}")
        raise typer.Exit(1)

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
    swarm_id: str = typer.Option(None, help="Filter by swarm", show_default=False,),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per SSID)"),
    sort_by: SortWlanOptions = typer.Option(None, "--sort", help="Field to sort by [grey42]\[default: SSID][/]", show_default=False),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
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
    """Show WLAN(SSID)/details
    """
    central = cli.central
    if sort_by and sort_by == "ssid":
        sort_by = "essid"

    title = "WLANs (SSIDs)" if not name else f"Details for SSID {name}"
    if group:
        title = f"{title} in group {group}"
    if label:
        title = f"{title} with label {label}"
    if site:
        _site = cli.cache.get_site_identifier(site)
        site = _site.name or site
        title = f"{title} in site {site}"

    params = {
        "name": name,
        "group": group,
        "swarm_id": swarm_id,
        "label": label,
        "site": site,
        "calculate_client_count": do_clients,
    }

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    resp = central.request(central.get_wlans, **params)
    cli.display_results(resp, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile)


# FIXME show clients wireless <tab completion> does not filter based on type of device
# FIXME show clients wireless AP-NAME does not filter only devices on that AP
# Same applies for wired
@app.command(help="Show clients/details")
def clients(
    filter: ClientArgs = typer.Argument('all', case_sensitive=False, ),
    device: List[str] = typer.Argument(
        None,
        metavar=iden_meta.dev,
        help="Show clients for a specific device or multiple devices.",
        autocompletion=cli.cache.dev_client_completion,
    ),
    group: str = typer.Option(None, metavar="<Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    site: str = typer.Option(None, metavar="<Site>", help="Filter by Site", autocompletion=cli.cache.site_completion),
    label: str = typer.Option(None, metavar="<Label>", help="Filter by Label", ),
    _dev: List[str] = typer.Option(None, "--dev", metavar=iden_meta.dev, help="Filter by Device", hidden=True,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False,),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False,),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False,),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False,),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True,),
    update_cache: bool = typer.Option(False, "-U", hidden=True,),  # Force Update of cli.cache for testing
    sort_by: SortClientOptions = typer.Option(None, "--sort",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
    verbose: bool = typer.Option(False, "-v", help="additional details (vertically)", show_default=False,),
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
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        show_default=False,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    central = cli.central
    device = utils.listify(device) if device else []
    device = device if not _dev else [*device, *_dev]
    kwargs = {}
    dev = []
    if filter.value == "device":
        # TODO add support for multi-device
        if len(device) == 1:
            dev = cli.cache.get_dev_identifier(device[0])
            kwargs["serial"] = dev.serial
            args = tuple()
            title = f"{dev.name} Clients"
        else:
            dev = [cli.cache.get_dev_identifier(d) for d in device]
            args = tuple()
            title = f"Clients Connected to: {', '.join([d.name for d in dev])}"
    elif filter.value == "mac":
        # TODO add support for multi-device
        if len(device) == 1:
            kwargs["mac"] = device[0]
            args = tuple()
            title = f"Details for client with MAC {device[0]}"
        else:
            print("Only 1 client MAC allowed currently")
            raise typer.Exit(1)
            # TODO allow multiple MACs get all clients then filter result
    elif filter.value == "denylisted":
        if not device:
            print("Missing argument DEVICE:\[name|ip|mac|serial]")
            raise typer.Exit(1)
        elif len(device) > 1:
            print(f"[bright_red]Warning!![/]: Support for multiple devices not implemented yet. showing denylist for {dev.name} only.")
        dev = cli.cache.get_dev_identifier(device[0])
        args = (dev.serial,)
        title = f"{dev.name} Denylisted Clients"
    elif filter.value != "all":  # wired or wireless
        args = (filter.value, device)
        title = f"All {filter.value.title()} Clients"
    else:  # all
        args = (filter.value, device)
        title = "All Clients"

    if filter.value != "denylisted":
        if group:
            kwargs["group"] = cli.cache.get_group_identifier(group).name
            title = f"{title} in group {group}"

        if site:
            kwargs["site"] = cli.cache.get_site_identifier(site).name
            title = f"{title} in site {site}"

        if label:
            kwargs["label"] = label
            title = f"{title} on devices with label {label}"

    # TODO retain but strip out time fields in epoch for purposes of sorting
    if sort_by:
        sort_by = "802.11" if sort_by == "dot11" else sort_by.value.replace("_", " ")

    # resp = central.request(central.get_clients, *args, **kwargs)
    if filter.value != "denylisted":
        resp = central.request(cli.cache.update_client_db, *args, **kwargs)
    else:
        resp = central.request(cli.central.get_denylist_clients, *args)
    if not resp:
        cli.display_results(resp, exit_on_fail=True)

    _count_text = ""
    if filter.value not in ["mac", "denylisted"]:
        if filter.value == "wired":
            _count_text = f"{len(resp)} Wired Clients."
        elif filter.value == "wireless":
            _count_text = f"{len(resp)} Wireless Clients."
        else:
            _tot = len(resp)
            _wired = len([x for x in resp.output if x["client_type"] == "WIRED"])
            _wireless = len([x for x in resp.output if x["client_type"] == "WIRELESS"])
            _count_text = f"[reset]Counts: [bright_green]Total[/]: [cyan]{_tot}[/], [bright_green]Wired[/]: [cyan]{_wired}[/], [bright_green]Wireless[/]: [cyan]{_wireless}[/]"

    if not verbose2:
        _format = "rich" if not verbose else "yaml"
    else:
        _format = "json"
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default=_format)

    verbose_kwargs = {}
    if not verbose2 and filter.value != "denylisted":
        verbose_kwargs["cleaner"] = cleaner.get_clients
        verbose_kwargs["cache"] = cli.cache
        verbose_kwargs["verbose"] = verbose
        # filter output on multiple devices
        if dev and isinstance(dev, list):
            verbose_kwargs["filters"] = [d.serial for d in dev]

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=f"{_count_text} Use -v for more details, -vv for unformatted response." if not verbose else None,
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
    """Show Tunnel details"""
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
            print(f"[bright_red]Error:[/bright_red] Value for --start should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
            print(f"  Value: {start} appears to be invalid.")
            raise typer.Exit(1)
    if end:
        try:
            dt = pendulum.from_format(end, 'YYYY-MM-DDTHH:mm', tz="local")
            end = (dt.int_timestamp)
            time_words = f'{time_words} to {pendulum.from_timestamp(dt.int_timestamp, tz="local").format("MMM DD h:mm:ss A")}'
        except Exception:
            print(f"[bright_red]Error:[/bright_red] Value for --end should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
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

# TODO add dedicated completion function and remove cencli match from get_log_identifier
@app.command(
    help="Show Audit Logs or cencli logs.  Audit Logs will displays prior 48 hours if no time options are provided.",
    short_help="Show Audit Logs (last 48h default)",
)
def logs(
    args: List[str] = typer.Argument(
        None,
        metavar='[LOG_ID]',
        help="Show details for a specific log_id",
        autocompletion=lambda incomplete: cli.cache.get_log_identifier(incomplete)
    ),
    tail: bool = typer.Option(False, "-f", help="follow tail on log file (implies show logs)", is_eager=True),
    user: str = typer.Option(None, help="Filter logs by user"),
    start: str = typer.Option(None, help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    _all: bool = typer.Option(False, "--all", help="Display all available audit logs.  Overrides default of 48h"),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter logs by device",
        autocompletion=cli.cache.dev_completion,
    ),
    app: LogAppArgs = typer.Option(None, help="Filter logs by app_id", hidden=True),
    ip: str = typer.Option(None, help="Filter logs by device IP address",),
    description: str = typer.Option(None, help="Filter logs by description (fuzzy match)",),
    _class: str = typer.Option(None, "--class", help="Filter logs by classification (fuzzy match)",),
    count: int = typer.Option(None, "-n", help="Collect Last n logs",),
    cencli: bool = typer.Option(False, "--cencli", help="Show cencli logs", callback=show_logs_cencli_callback),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: LogSortBy = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
    verbose2: bool = typer.Option(False, "-vv", help="Show raw unformatted response from Central API Gateway"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
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
    if cencli or (args and args[-1] == "cencli"):
        from centralcli import log
        log.print_file() if not tail else log.follow()
        raise typer.Exit(0)

    if args:
        log_id = cli.cache.get_log_identifier(args[-1])
    else:
        log_id = None
        if device:
            device = cli.cache.get_dev_identifier(device)

        if _all and True in list(map(bool, [start, end, past])):
            print("Invalid combination of arguments. [cyan]--start[/], [cyan]--end[/], and [cyan]--past[/]")
            print("are invalid when [cyan]--all[/] is used.")
            raise typer.Exit(1)

        if start:
            # TODO add common dt function allow HH:mm and assumer current day
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

    kwargs = {
        "log_id": log_id,
        "username": user,
        "start_time": start or int(time.time() - 172800) if not _all else None,
        "end_time": end,
        "description": description,
        "target": None if not device else device.serial,
        "classification": _class,
        "ip_address": ip,
        "app_id": app,
        "count": count
    }

    central = cli.central
    resp = central.request(central.get_audit_logs, **kwargs)

    if kwargs.get("log_id"):
        cli.display_results(resp, tablefmt="action")
    else:
        if verbose2:
            tablefmt = "raw"
        else:
            tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")
        _cmd_txt = typer.style('show logs <id>', fg='bright_green')
        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title="Audit Logs",
            pager=pager,
            outfile=outfile,
            # TODO move sort_by underscore removal to display_results
            sort_by=sort_by if not sort_by else sort_by.replace("_", " "),  # has_details -> 'has details'
            reverse=reverse,
            cleaner=cleaner.get_audit_logs if not verbose else None,
            cache_update_func=cli.cache.update_log_db if not verbose else None,
            caption=f"[reset]Use {_cmd_txt} to see details for a log.  Logs lacking an id don\'t have details.",
        )


# TODO cache and create completion for labels
@app.command(short_help="Show Event Logs", help="Show Event Logs (last 4 hours by default)")
def events(
    event_id: str = typer.Argument(
        None,
        metavar='[LOG_ID]',
        help="Show details for a specific log_id",
        autocompletion=cli.cache.event_completion
    ),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion,),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", autocompletion=cli.cache.null_completion,),
    site: str = typer.Option(None, metavar=iden_meta.site, help="Filter by Site", autocompletion=cli.cache.site_completion,),
    start: str = typer.Option(None, help="Start time of range to collect events, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect events, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect events for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter events by device",
        autocompletion=cli.cache.dev_completion,
    ),
    client_mac: str = typer.Option(None, "--client-mac", help="Filter events by client MAC address"),
    bssid: str = typer.Option(None, help="Filter events by bssid",),
    hostname: str = typer.Option(None, help="Filter events by hostname (fuzzy match)",),
    dev_type: EventDevTypeArgs = typer.Option(
        None,
        "--dev-type",
        metavar="[ap|switch|gw|client]",
        help="Filter events by device type",
    ),
    description: str = typer.Option(None, help="Filter events by description (fuzzy match)",),
    event_type: str = typer.Option(None, "--event-type", help="Filter events by type (fuzzy match)",),  # TODO completion enum
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: str = typer.Option(None, "--sort",),  # TODO create enum in constants.. Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False
    ),
    # count: int = typer.Option(None, "-n", help="Collect Last n logs",),
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
    verbose2: bool = typer.Option(False, "-vv", help="Show raw unformatted response from Central API Gateway"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
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
    # TODO move to common func for use be show logs and show events
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
            now = int(time.time())  # FIXME --past 30m is pulling too many logs, prob timezone / timestamp issue
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
        "from_ts": start or int(time.time() - 14400),
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
        # "calculate_total": None,
    }

    central = cli.central
    resp = central.request(central.get_events, **kwargs)

    if verbose2:
        tablefmt = "raw"
    else:
        tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    _cmd_txt = "[bright_green] show events <id>[reset]"
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Event Logs",
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

    # API returns alerts in reverse order newest on top we fix that unless they specify a sort field
    # if reverse is None:
    #     reverse = True if not sort_by else False

    # TODO move to common func for use be show logs and show events
    # if args:
    #     event_details = cli.cache.get_event_identifier(args[-1])
    #     cli.display_results(
    #         Response(output=event_details),
    #         tablefmt="action",
    #     )
    #     print(type(event_details))
    #     raise typer.Exit(0)
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
            print(f"[bright_red]Error:[/bright_red] Value for --start should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
            print(f"  Value: {start} appears to be invalid.")
            raise typer.Exit(1)
    if end:
        try:
            dt = pendulum.from_format(end, 'YYYY-MM-DDTHH:mm', tz="local")
            end = (dt.int_timestamp)
            time_words = f'{time_words} to {pendulum.from_timestamp(dt.int_timestamp, tz="local").format("MMM DD h:mm:ss A")}'
        except Exception:
            print(f"[bright_red]Error:[/bright_red] Value for --end should be in format YYYY-MM-DDTHH:mm (That's a literal 'T')[reset]")
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
    title = f"Alerts/Notifications (Configured Notification Rules)"
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
    title = f"Alerts/Notifications Configuration (Configured Notification Targets/Rules)"

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


# TODO cahce portal/name ids
@app.command()
def portals(
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
    """Show Configured Guest Portals"""
    resp = cli.central.request(cli.central.get_portals)
    cli.display_results(resp, cleaner=cleaner.get_portals, fold_cols=["url"],)


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
