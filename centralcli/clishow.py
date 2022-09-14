#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import time
import pendulum
import asyncio
import sys
from typing import List, Union
from pathlib import Path
from rich import print
from rich.console import Console

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response, cleaner, clishowfirmware, clishowwids, clishowbranch, caas, cli, utils, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response, cleaner, clishowfirmware, clishowwids, clishowbranch, caas, cli, utils, config
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    ClientArgs, InventorySortOptions, ShowInventoryArgs, StatusOptions, SortOptions, IdenMetaVars, CacheArgs, LogAppArgs, LogSortBy, SortSiteOptions,
    DevTypes, SortDevOptions, SortTemplateOptions, SortClientOptions, SortCertOptions, SortVlanOptions,
    DhcpArgs, EventDevTypeArgs, ShowHookProxyArgs, lib_to_api, what_to_pretty  # noqa
)

app = typer.Typer()
app.add_typer(clishowfirmware.app, name="firmware")
app.add_typer(clishowwids.app, name="wids")
app.add_typer(clishowbranch.app, name="branch")

tty = utils.tty
iden_meta = IdenMetaVars()

def _build_caption(resp: Response, *, inventory: bool = False) -> str:
    dev_types = set([t.get("type", "NOTYPE") for t in resp.output])
    _cnt_str = ", ".join([f'[bright_green]{_type}[/]: [cyan]{[t.get("type", "ERR") for t in resp.output].count(_type)}[/]' for _type in dev_types])
    caption = "  [cyan]Show all[/cyan] displays fields common to all device types. "
    caption = f"[reset]Counts: {_cnt_str}\n{caption}To see all columns for a given device type use [cyan]show <DEVICE TYPE>[/cyan]\n"
    if inventory:
        caption = f"{caption}  [italic dark_olive_green2]verbose listing, devices lacking name/ip are in the inventory, but have not connected to central.[/]"
    return caption

def show_devices(
    dev_type: str, *args, include_inventory: bool = False, serial: str = None, outfile: Path = None, update_cache: bool = False, group: str = None,
    status: str = None, state: str = None, label: Union[str, List[str]] = None, pub_ip: str = None, do_clients: bool = False,
    do_stats: bool = False, sort_by: str = None, pager: bool = False, do_json: bool = False, do_csv: bool = False,
    do_yaml: bool = False, do_table: bool = False
) -> None:
    caption = None
    central = cli.central
    if update_cache:
        cli.cache.update_dev_db()

    _formatter = "yaml"

    if group:
        group = cli.cache.get_group_identifier(group)

    # -- // Perform GET Call \\ --
    resp = None
    params = {
        "group": None if not group else group.name,
        "status": None if not status else status.title(),
        "label": label,
        "public_ip_address": pub_ip,
        "calculate_client_count": do_clients,
        "show_resource_details": do_stats,
        # "sort": None if not sort_by else sort_by._value_
    }

    # status and state keywords both allowed
    if params["status"] is None and state is not None:
        params["status"] = state.title()

    params = {k: v for k, v in params.items() if v is not None}

    if dev_type == "device":
        if args:  # show devices [name|ip|mac|serial]
            dev = cli.cache.get_dev_identifier(args)
            _type = lib_to_api("monitoring", dev.type)
            resp = central.request(central.get_dev_details, _type, dev.serial)
        else:  # show devices ... equiv to show all
            _formatter = "rich"
            resp = central.request(central.get_all_devicesv2, **params)

    elif dev_type == "all":
        _formatter = "rich"
        if include_inventory:
            resp = cli.cache.get_devices_with_inventory()
            caption = _build_caption(resp, inventory=True)
            if len(params) > 2:
                caption = f"{caption}\n  [bright_red]WARNING[/]: Filtering options ignored, not valid w/ [cyan]-v[/] (include inventory devices)"
        # if no params (expected result may differ) update cli.cache if not updated this session and return results from there
        elif len(params) == 2 and list(params.values()).count(False) == 2:
            if central.get_all_devicesv2 not in cli.cache.updated:
                resp = central.request(cli.cache.update_dev_db)
                caption = _build_caption(resp)
            else:
                # get_all_devicesv2 already called (to populate/update cache) grab response from cache.
                resp = cli.cache.responses.dev
        else:  # will only run if user specifies params (filters)
            resp = central.request(central.get_all_devicesv2, **params)
    elif serial:
        api_dev_type = lib_to_api("monitoring", dev_type)
        resp = central.request(central.get_dev_details, api_dev_type, serial)

    # aps, switches, gateways, ...  # TODO shouldn't hit from show devices dev iden
    elif args:
        api_dev_type = lib_to_api("monitoring", dev_type)
        dev = cli.cache.get_dev_identifier(args, dev_type=dev_type if dev_type != "gateways" else "gw")
        resp = central.request(central.get_dev_details, api_dev_type, dev.serial)
    else:
        resp = central.request(central.get_devices, dev_type, **params)

    # device details is a lot of data default to yaml output, default horizontal would typically overrun tty
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default=_formatter)
    title_sfx = [
        f"{k}: {v}" for k, v in params.items() if k not in ["calculate_client_count", "show_resource_details"] and v
    ] if not include_inventory else ["including Devices from Inventory"]
    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{what_to_pretty(dev_type)} {', '.join(title_sfx)}",
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        cleaner=cleaner.get_devices
    )


@app.command(short_help="Show device inventory", help="Show device inventory / all devices that have been added to Aruba Central.")
def inventory(
    _type: ShowInventoryArgs = typer.Argument("all", metavar="[all|ap|gw|vgw|switch|others]"),
    sub: bool = typer.Option(
        None,
        help="Show devices with applied subscription/license, or devices with no subscription/license applied."
    ),
    sort_by: InventorySortOptions = typer.Option(None, "--sort"),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order"),
    verbose: bool = typer.Option(False, "-v", help="Gather additional details about device from cache.", show_default=False,),
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
) -> None:
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")
    resp = cli.central.request(cli.central.get_device_inventory, _type)
    if verbose:
        cache_devices = cli.cache.devices
        for idx, dev in enumerate(resp.output):
            from_cache = [d for d in cache_devices if d["serial"] == dev["serial"]]
            if from_cache:
                resp.output[idx] = {**dev, **from_cache[0]}

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Devices in Inventory",
        sort_by=sort_by,
        reverse=reverse,
        caption="Inventory includes devices that have yet to connect to Central",
        cleaner=cleaner.get_device_inventory,
        sub=sub
    )

@app.command(short_help="Show All Devices")
def all(
    # args: str = typer.Argument(None, metavar=iden_meta.dev, hidden=True, autocompletion=cli.cache.null_completion),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortDevOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    verbose: bool = typer.Option(
        False,
        "-v",
        help="additional details (include devices in Inventory that have yet to connect)",
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
):
    if down:
        status = "Down"
    elif up:
        status = "Up"
    show_devices(
        'all', outfile=outfile, include_inventory=verbose, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_stats=do_stats, do_clients=do_clients, sort_by=sort_by,
        pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(short_help="Show devices [identifier]")
def devices(
    device: List[str] = typer.Argument(
        None,
        metavar=iden_meta.dev_many.replace("]", "|'all']"),
        hidden=False,
        autocompletion=lambda incomplete: [
            m for m in [("all", "Show all devices"), *[m for m in cli.cache.dev_completion(incomplete)]]
            if m[0].lower().startswith(incomplete.lower())
        ],
        help="Show details for a specific device [Default: show summary for all devices]"
    ),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortDevOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    verbose: bool = typer.Option(
        False,
        "-v",
        help="additional details (include devices in Inventory that have yet to connect)",
        show_default=False,
        hidden=True,  # TODO show inventory devices
    ),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
):
    if down:
        status = "Down"
    elif up:
        status = "Up"

    serial = None
    if not device or device == 'all':
        dev_type = 'all'
    else:
        devs = [cli.cache.get_dev_identifier(d) for d in device]
        if len(devs) > 1:
            print(f"Multiple devices for this command is coming... Not implemented yet. Ignoring all but {devs[0].name}")
        # dev = cli.cache.get_dev_identifier(device)
        dev = devs[0] #  if len(devs) == 1 else devs  # TODO make multi device possible
        device = dev.name
        serial = dev.serial
        dev_type = lib_to_api("monitoring", dev.type)  # TODO I think this can be removed done in show_devices

    # TODO refactor show_devices to just send it the CentralObject(s)
    show_devices(
        dev_type, device, include_inventory=verbose, serial=serial, outfile=outfile, update_cache=update_cache,
        group=group, status=status, state=state, label=label, pub_ip=pub_ip,
        do_stats=do_stats, sort_by=sort_by, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table
    )


@app.command(short_help="Show APs/details")
def aps(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_completion),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    # do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in table format"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        'aps', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_stats=do_stats,
        sort_by=sort_by, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(short_help="Show switches/details")
def switches(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
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
) -> None:

    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        'switches', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(short_help="Show gateways/details")
def gateways(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_completion),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    # sort_by: SortOptions = typer.Option(None, "--sort"),
    sort_by: SortDevOptions = typer.Option(None, "--sort"),
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
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        'gateways', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(short_help="Show controllers/details", hidden=True)
def controllers(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_completion),
    group: str = typer.Option(
        None,
        metavar="<Device Group>",
        help="Filter by Group",
        autocompletion=cli.cache.group_completion,
    ),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    up: bool = typer.Option(False, "--up", help="Filter by devices that are Up", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter by devices that are Down", show_default=False),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortDevOptions = typer.Option(None, "--sort"),
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
    if down:
        status = "Down"
    elif up:
        status = "Up"

    show_devices(
        'mobility_controllers', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, pager=pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_table=do_table)


@app.command(short_help="Show interfaces/details")
def interfaces(
    device: str = typer.Argument(..., metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_switch_gw_completion),
    slot: str = typer.Argument(None, help="Slot name of the ports to query (chassis only)",),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    sort_by: str = typer.Option(None, "--sort", help="Field to sort by"),
    reverse: bool = typer.Option(False, "-r", is_flag=True, help="Sort in descending order"),
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

    dev = cli.cache.get_dev_identifier(device,)
    if dev.generic_type == "gw":
        resp = cli.central.request(cli.central.get_gateway_ports, dev.serial)
    else:
        resp = cli.central.request(cli.central.get_switch_ports, dev.serial, slot=slot, cx=dev.type == "CX")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="json")
    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile, sort_by=sort_by, reverse=reverse)


@app.command(help="Show (switch) poe details for an interface")
def poe(
    device: str = typer.Argument(..., metavar=iden_meta.dev, hidden=False, autocompletion=cli.cache.dev_switch_completion),
    port: str = typer.Argument(None,),
    _port: str = typer.Option(None, "--port"),
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
    resp = cli.central.request(cli.central.get_switch_poe_details, dev.serial, port=port)
    resp.output = utils.unlistify(resp.output)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="json")
    cli.display_results(resp, tablefmt=tablefmt, pager=pager, outfile=outfile)
    # TODO output cleaner / sort & reverse options


@app.command(short_help="Show VLANs for device or site")
def vlans(
    dev_site: str = typer.Argument(
        ...,
        metavar=f"{iden_meta.dev} (vlans for a device) OR {iden_meta.site} (vlans for a site)",
        autocompletion=cli.cache.dev_site_completion,
    ),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", hidden=True, help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    up: bool = typer.Option(False, "--up", help="Filter: Up VLANs", show_default=False),
    down: bool = typer.Option(False, "--down", help="Filter: Down VLANs", show_default=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortVlanOptions = typer.Option(None, "--sort"),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
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

    resp = None
    if obj:
        if obj.is_site:
            resp = central.request(central.get_site_vlans, obj.id)
        elif obj.is_dev:
            # if obj.type.lower() in ['cx', 'sw']:
            if obj.generic_type == "switch":
                resp = central.request(central.get_switch_vlans, obj.serial, cx=obj.type == "CX")
            elif obj.type.lower() == 'gw':
                resp = central.request(central.get_gateway_vlans, obj.serial)
            elif obj.type.lower() == 'mobility_controllers':
                # TODO double check should never hit this the 2 API methods should be same
                resp = central.request(central.get_controller_vlans, obj.serial)
        else:
            typer.secho(f"show vlans not implemented for {dev_site}", fg="red")
            typer.echo(str(obj))
            raise typer.exit(1)

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
    args: List[CacheArgs] = typer.Argument(None, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),
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
        tablefmt = cli.get_format(do_json=do_json, do_csv=do_csv, do_table=do_table, default="yaml")
        cli.display_results(data=cache_out, tablefmt=tablefmt, tile=f"Cache {', '.join(args)}", pager=pager, outfile=outfile)


@app.command(short_help="Show groups/details")
def groups(
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    verbose: bool = typer.Option(False, "-v", help="Verbose: adds AoS10 / Monitor only switch attributes", show_default=False,),
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
    cli.display_results(resp, tablefmt=tablefmt, title="Groups", pager=pager, outfile=outfile)


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
    site: str = typer.Argument(None, metavar=iden_meta.site, autocompletion=cli.cache.site_completion),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortSiteOptions = typer.Option(None, "--sort"),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
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

    site = None if site and site.lower() == "all" else site
    if not site:
        if central.get_all_sites not in cli.cache.updated:
            resp = asyncio.run(cli.cache.update_site_db())
        else:
            resp = cli.cache.responses.site
    else:
        site = cli.cache.get_site_identifier(site)
        resp = central.request(central.get_site_details, site.id)

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Sites" if not site else f"{site.name} site details",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
    )


@app.command(short_help="Show templates/details")
def templates(
    name: str = typer.Argument(
        None,
        help=f"Template: [name] or Device: {iden_meta.dev}",
        autocompletion=cli.cache.dev_template_completion
    ),
    group: List[str] = typer.Argument(None, help="Get Templates for Group", autocompletion=cli.cache.group_completion),
    _group: str = typer.Option(
        None, "--group",
        help="Get Templates for Group",
        hidden=False,
        autocompletion=cli.cache.group_completion,
    ),
    device_type: DevTypes = typer.Option(
        None, "--dev-type",
        help="Filter by Device Type",
    ),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by dev version Template is assigned to"),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
    #  variablised: str = typer.Option(False, "--with-vars",
    #                                  help="[Templates] Show Template with variable place-holders and vars."),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", show_default=False),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortTemplateOptions = typer.Option(None, "--sort"),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
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
            m for m in [d for d in [("all", "Show Variables for all templates"), *cli.cache.dev_completion(incomplete)]]
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
        metavar=iden_meta.dev,
        autocompletion=lambda incomplete: cli.cache.dev_completion(incomplete, args=["ap"])
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

    # We take last arg [-1] from list so they can type "neighbor" if they want.
    dev = cli.cache.get_dev_identifier(device[-1], dev_type="ap")

    if dev.type != "ap":
        typer.secho(f"This command is currently only valid for APs.  {dev.name} is type: {dev.type}", fg="red")
        raise typer.Exit(1)

    resp = central.request(central.get_ap_lldp_neighbor, dev.serial)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table, default="rich")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{dev.name} lldp neighbor",
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
    ),
    device: str = typer.Argument(
        None,
        autocompletion=cli.cache.dev_completion,
        hidden=True,
        # TODO dev type gw or ap only
        # autocompletion=lambda incomplete: [
        #    c for c in cli.cache.dev_completion(incomplete, dev_type="gw") if c.lower().startswith(incomplete.lower())
        # ]
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
    device: List[str] = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
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

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{device.name} IP Routes",
        caption=caption,
        reverse=reverse,
        pager=pager,
        outfile=outfile,
        cleaner=cleaner.routes,
    )


@app.command(short_help="Show WLAN(SSID)/details", help="Show WLAN(SSID)/details")
def wlans(
    name: str = typer.Argument(None, metavar="[WLAN NAME]", help="Get Details for a specific WLAN"),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    site: str = typer.Option(
        None,
        metavar="[site identifier]",
        help="Filter by device status",
        autocompletion=cli.cache.site_completion
    ),
    swarm_id: str = typer.Option(None,),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per SSID)"),
    sort_by: SortOptions = typer.Option(None, "--sort", hidden=True),  # TODO Unhide once implemented for show wlans
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
) -> None:
    central = cli.central


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
    cli.display_results(resp, sort_by=sort_by, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile)


# FIXME show clients wireless <tab completion> does not filter based on type of device
# FIXME show clients wireless AP-NAME does not filter only devices on that AP
# Same applies for wired
@app.command(short_help="Show clients/details")
def clients(
    filter: ClientArgs = typer.Argument('all', case_sensitive=False, ),
    device: List[str] = typer.Argument(
        None,
        metavar=iden_meta.dev,
        help="Show clients for a specific device or multiple devices.",
        autocompletion=cli.cache.dev_client_completion,
    ),
    # os_type:
    # band:
    # _: str = typer.Argument(None, hidden=True, autocompletion=cli.cache.null_completion),
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
    elif filter.value != "all":  # wired or wireless
        args = (filter.value, device)
        title = f"All {filter.value.title()} Clients"
    else:  # all
        args = (filter.value, device)
        title = "All Clients"

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

    resp = central.request(central.get_clients, *args, **kwargs)
    if not resp:
        cli.display_results(resp)
        raise typer.Exit(1)

    _count_text = ""
    if filter.value != "mac":
        if filter.value == "wired":
            _count_text = f"{len(resp)} Wired Clients."
        elif filter.value == "wireless":
            _count_text = f"{len(resp)} Wireless Clients."
        else:
            _tot = len(resp)
            _wired = len([x for x in resp.output if x["client_type"] == "WIRED"])
            _wireless = len([x for x in resp.output if x["client_type"] == "WIRELESS"])
            _count_text = f"{_tot} Clients, (Wired: {_wired}, Wireless: {_wireless})."

    if not verbose2:
        _format = "rich" if not verbose else "yaml"
    else:
        _format = "json"
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default=_format)

    verbose_kwargs = {}
    if not verbose2:
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

@app.command(short_help="Show client roaming history")
def roaming(
    client_mac: str = typer.Argument(..., case_sensitive=False, help="Client Mac Address",),
    start: str = typer.Option(
        None,
        help="Start time of range to collect roaming history, format: yyyy-mm-ddThh:mm (24 hour notation), default past 3 hours.",
    ),
    end: str = typer.Option(None, help="End time of range to collect roaming history, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect roaming history for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    sort_by: SortClientOptions = typer.Option(None, "--sort",),
    reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False,),
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
    """Show wireless client roaming history.

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
    mac = utils.Mac(client_mac)
    if not mac.ok:
        print(f"Mac Address {client_mac} appears to be invalid.")
        raise typer.Exit(1)
    resp = central.request(central.get_client_roaming_history, mac.cols, from_timestamp=start, to_timestamp=end)
    cli.display_results(resp, title=f"Roaming history for {mac.cols}", tablefmt="rich", cleaner=cleaner.get_client_roaming_history)


@app.command(short_help="Show Troubleshooting output")
def tshoot(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        help="Aruba Central Device",
        autocompletion=cli.cache.dev_completion,
    ),
    session_id: str = typer.Argument(
        None,
        help="The troubleshooting session id.",
    ),
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
    """Show Troubleshooting results from an existing session.

    Use cencli tshoot ... to start a troubleshooting session.

    """
    central = cli.central
    con = Console(emoji=False)
    dev = cli.cache.get_dev_identifier(device)

    # Fetch session ID if not provided
    if not session_id:
        resp = central.request(central.get_ts_session_id, dev.serial)
        if resp.ok and "session_id" in resp.output:
            session_id = resp.output["session_id"]
        else:
            print(f"No session id provided, unable to find active session id for {dev.name}")
            cli.display_results(resp)
            raise typer.Exit(1)

    title = f"Troubleshooting output for {dev.name} session {session_id}"
    resp = central.request(central.get_ts_output, dev.serial, session_id=session_id)
    if not resp or resp.output.get("status", "") != "COMPLETED":
        cli.display_results(resp, title=title, tablefmt="rich",)
    else:
        con.print(resp)
        con.print(f"\n   {resp.rl}")



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
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", autocompletion=cli.cache.group_completion,),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", autocompletion=cli.cache.null_completion,),
    site: str = typer.Option(None, metavar=iden_meta.site, help="Filter by Site", autocompletion=cli.cache.site_completion,),
    start: str = typer.Option(None, help="Start time of range to collect alerts, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect alerts, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect alerts for last <past>, d=days, h=hours, m=mins i.e.: 3h Default: 24 hours"),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter alerts by device",
        autocompletion=cli.cache.dev_completion,
    ),
    severity: str = typer.Option(None, help="Filter by alerts by severity."),  # TODO completion
    search: str = typer.Option(None, help="Filter by alerts with search term in name/description/category."),
    ack: bool = typer.Option(None, help="Show only acknowledged (--ack) or unacknowledged (--no-ack) alerts",),
    alert_type: str = typer.Option(None, "--type", help="Filter by alert type",),  # TODO enum with alert types
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
    verbose: bool = typer.Option(False, "-v", help="Show alerts with original field names and minimal formatting (vertically)"),
    verbose2: bool = typer.Option(False, "-vv", help="Show alerts unformatted response from Central API Gateway"),
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
    if device:
        device = cli.cache.get_dev_identifier(device)

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
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    sort_by: str = typer.Option(None, "--sort",),  # TODO create enum in constants.. Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order Default order: newest on bottom.",
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
    ...
    resp = cli.central.request(cli.central.get_all_webhooks)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv)
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
                return p.pid, p.info["cmdline"][-1]

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

# @app.command(short_help="Show config", hidden=True)
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

    out = {k: str(v) if isinstance(v, Path) else v for k, v in config.__dict__.items()}
    resp = Response(output=out)

    cli.display_results(resp, tablefmt="yaml")


@app.callback()
def callback():
    """
    Show Details about Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
