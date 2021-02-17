#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import time
import asyncio
import sys
from typing import List, Union
from pathlib import Path


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response, cleaner, cli, log, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response, cleaner, cli, log, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import ClientArgs, StatusOptions, SortOptions  # noqa

app = typer.Typer()


tty = utils.tty
show_help = ["all (devices)", "device[s] (same as 'all' unless followed by device identifier)", "switch[es]", "ap[s]",
             "gateway[s]", "group[s]", "site[s]", "clients", "template[s]", "variables", "certs"]
args_metavar_dev = "[name|ip|mac-address|serial]"
args_metavar_site = "[name|site_id|address|city|state|zip]"
args_metavar = f"""Optional Identifying Attribute: {args_metavar_dev}"""
args_metavar_client = "[username|ip|mac]"


def show_devices(
    dev_type: str, *args, outfile: Path = None, update_cache: bool = False, group: str = None, status: str = None,
    state: str = None, label: Union[str, List[str]] = None, pub_ip: str = None, do_clients: bool = False,
    do_stats: bool = False, sort_by: str = None, no_pager: bool = False, do_json: bool = False, do_csv: bool = False,
    do_yaml: bool = False, do_rich: bool = False
) -> None:
    central = cli.central
    cli.cache(refresh=update_cache)

    if group:
        group = cli.cache.get_group_identifier(group)
        if not group:
            raise typer.Exit(1)

    # -- // Peform GET Call \\ --
    resp = None
    params = {
        "group": group,
        "status": None if not status else status.title(),
        "label": label,
        "public_ip_address": pub_ip,
        "calculate_client_count": do_clients,
        "show_resource_details": do_stats,
        "sort": None if not sort_by else sort_by._value_
    }

    # status and state keywords both allowed
    if params["status"] is None and state is not None:
        params["status"] = state.title()

    params = {k: v for k, v in params.items() if v is not None}

    if dev_type == "device":
        if args:
            dev_type, serial = cli.cache.get_dev_identifier(args, ret_field="type-serial")

            if dev_type and serial:
                resp = central.request(central.get_dev_details, dev_type, serial, **params)
        else:  # show devices ... equiv to show all
            resp = central.request(central.get_all_devicesv2, **params)

    elif dev_type == "all":
        # if no params (expected result may differ) update cli.cache if not updated this session and return results from there
        if len(params) == 2 and list(params.values()).count(False) == 2:
            if central.get_all_devicesv2 not in cli.cache.updated:
                asyncio.run(cli.cache.update_dev_db())

            resp = Response(output=cli.cache.devices)
        else:  # will only run if user specifies params (filters)
            resp = central.request(central.get_all_devicesv2, **params)

    # aps, switches, gateways, ...
    elif args:
        serial = cli.cache.get_dev_identifier(args)
        resp = central.request(central.get_dev_details, dev_type, serial)
        # device details is a lot of data default to yaml output, default horizontal would typically overrun tty
        if True not in [do_csv, do_json]:
            do_yaml = True
    else:
        resp = central.request(central.get_devices, dev_type, **params)

    data = cli.eval_resp(resp)

    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)
        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.sort_result_keys)


@app.command(short_help="Show APs/details")
def aps(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cli.cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    show_devices(
        'aps', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show switches/details")
def switches(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cli.cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    show_devices(
        'switches', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show interfaces/details")
def interfaces(
    device: str = typer.Argument(..., metavar=args_metavar_dev, hidden=False),
    slot: str = typer.Argument(None, help="Slot name of the ports to query (chassis only)",),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    cli.cache(refresh=update_cache)
    dev_type, serial = cli.cache.get_dev_identifier(device, ret_field="type-serial")

    resp = cli.central.request(cli.central.get_switch_ports, serial, cx=dev_type == "CX")
    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=None, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show VLANs for device or site")
def vlans(
    dev_site: str = typer.Argument(..., metavar=f"{args_metavar_dev} OR {args_metavar_site}", hidden=False),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    sort_by: SortOptions = typer.Option(None, "--sort", hidden=True),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    """ Get VLAN Info for a device or site. """
    # TODO cli command lacks the filtering options available from method.
    central = cli.central
    dev_type = None

    cli.cache(refresh=update_cache)

    _ = cli.cache.get_dev_identifier(dev_site, ret_field='type-serial', retry=False)
    if not _:
        iden = cli.cache.get_site_identifier(dev_site)
        if iden:
            resp = central.request(central.get_site_vlans, iden)
    else:
        dev_type, iden = _[0], _[1]
        if iden and dev_type:
            if dev_type.lower() in ['cx', 'sw']:
                resp = central.request(central.get_switch_vlans, iden, cx=dev_type == "CX")
            elif dev_type.lower() == 'gateway':
                resp = central.request(central.get_gateway_vlans, iden)
            elif dev_type.lower() == 'mobility_controllers':
                resp = central.request(central.get_controller_vlans, iden)
            else:
                typer.secho(f"show vlans not implemented for {dev_type}")

    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.get_vlans)


@app.command(short_help="Show All Devices")
def all(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cli.cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    show_devices(
        'all', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show devices [identifier]")
def devices(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cli.cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    type_to_link = {
        'ap': 'aps',
        'SW': 'switches',
        'CX': 'switches',
        'gateway': 'gateways'
    }
    if args[0] == 'all':
        dev_type = 'all'
        args = () if len(args) == 1 else args[1:]

    if args:
        dev_type, args = cli.cache.get_dev_identifier(args, ret_field="type-serial")
        args = utils.listify(args)
        dev_type = type_to_link.get(dev_type, dev_type)
    else:  # show devices ... equiv to show all
        dev_type = 'all'

    show_devices(
        dev_type, *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show gateways/details")
def gateways(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cli.cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    show_devices(
        'gateways', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show controllers/details")
def controllers(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cli.cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
    do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    show_devices(
        'mobility_controllers', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command("cache", short_help="Show contents of Identifier Cache.",)
def _cache(
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    cli.cache(refresh=update_cache)
    resp = Response(output=cli.cache.all)
    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=None, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show groups/details")
def groups(
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    central = cli.central
    if central.get_all_groups not in cli.cache.updated:
        asyncio.run(cli.cache.update_group_db())

        resp = Response(output=cli.cache.groups)
        data = cli.eval_resp(resp)
        cli.display_results(data, tablefmt='rich', pager=not no_pager, outfile=outfile)


@app.command(short_help="Show sites/details")
def sites(
    args: List[str] = typer.Argument(None, metavar=args_metavar_site, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
):
    central = cli.central
    cli.cache(refresh=update_cache)
    site_id = None
    if args:
        site_id = cli.cache.get_site_identifier(args)

    if site_id is None:
        if central.get_all_sites not in cli.cache.updated:
            asyncio.run(cli.cache.update_site_db())
        resp = Response(output=cli.cache.sites)
    else:
        resp = central.request(central.get_site_details, site_id)

    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def templates(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, "--group", help="Get Templates for Group"),
    name: str = typer.Option(None, metavar="<Template Name>", help="[Templates] Filter by Template Name"),
    device_type: str = typer.Option(None, "--dev-type", metavar="[IAP|ArubaSwitch|MobilityController|CX]>",
                                    help="[Templates] Filter by Device Type"),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by dev version Template is assigned to"),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
    #  variablised: str = typer.Option(False, "--with-vars",
    #                                  help="[Templates] Show Template with variable place-holders and vars."),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    central = cli.central
    params = {
        "name": name,
        "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
        "version": version,
        "model": model
    }

    params = {k: v for k, v in params.items() if v is not None}

    if args:
        if len(args) > 1:
            log.error(f"Only expecting 1 argument for show template, ignoring {args[1:]}", show=True)
        args = args[0]

    if not args:
        if not group:  # show templates
            if central.get_all_templates not in cli.cache.updated:
                asyncio.run(cli.cache.update_template_db())

            # TODO using cli.cache breaks filtering params
            resp = Response(output=cli.cache.templates)
        else:  # show templates --group <group name>
            resp = central.request(central.get_all_templates_in_group, group, **params)
    elif group:  # show template <arg> --group <group_name>
        _args = cli.cache.get_template_identifier(args)
        if _args:  # name of template
            resp = central.request(central.get_template, group, args)
        else:
            _args = cli.cache.get_dev_identifier(args)
            if _args:
                typer.secho(f"{args} Does not match a Template name, but does match device with serial {_args}", fg="cyan")
                typer.secho(f"Fetching Variablised Template for {args}", fg="cyan")
                msg = (
                    f"{typer.style(f'--group {group} is not required for device specific template output.  ', fg='cyan')}"
                    f"{typer.style(f'ignoring --group {group}', fg='red')}"
                    )
                typer.echo(msg)
                resp = central.request(central.get_variablised_template, _args)
    else:  # provided args but no group
        _args = cli.cache.get_dev_identifier(args, retry=False)
        if _args:  # assume arg is device identifier 1st
            resp = central.request(central.get_variablised_template, _args)
        else:  # next try template names
            _args = cli.cache.get_template_identifier(args, ret_field="group-name")
            if _args:
                group, tmplt_name = _args[0], _args[1]
                resp = central.request(central.get_template, group, tmplt_name)
            else:
                # typer.secho(f"No Match Found for {args} in Cachce")
                raise typer.Exit(1)

    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def variables(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback)
):
    central = cli.central
    cli.cache(refresh=update_cache)

    if args and args != "all":
        args = cli.cache.get_dev_identifier(args)

    resp = central.request(central.get_variables, args)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def lldp(
    device: List[str] = typer.Argument(..., metavar=args_metavar_dev, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback)
) -> None:
    central = cli.central
    cli.cache(refresh=update_cache)

    device = cli.cache.get_dev_identifier(device[-1])  # take last arg from list so they can type "neighbor" if they want.
    resp = central.request(central.get_ap_lldp_neighbor, device)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.get_lldp_neighbor)


@app.command()
def certs(
    name: str = typer.Argument(None, metavar='[certificate name|certificate hash]', hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback)
):
    resp = cli.central.request(cli.central.get_certificates, name, callback=cleaner.get_certificates)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def clients(
    filter: ClientArgs = typer.Argument('all', case_sensitive=False, ),
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, help="Show clients for a specific device"),
    # os_type:
    # band:
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    sort_by: SortOptions = typer.Option(None, "--sort", hidden=True,),  # TODO Unhide after implemented
    reverse: SortOptions = typer.Option(None, "-r", hidden=True,),  # TODO Unhide after implemented
    verbose: bool = typer.Option(False, "-v", hidden=True,),  # TODO Unhide after implemented
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        callback=cli.debug_callback,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        callback=cli.account_name_callback,
    ),
) -> None:
    central = cli.central
    # TODO quick and dirty, make less dirty (the way I passed cli.cache all the way through **kwargs to cleanerq)
    resp = central.request(central.get_clients, filter, *args,)  # callback_kwargs={'cache': cli.cache})
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    cli.display_results(
        data,
        tablefmt=tablefmt,
        pager=not no_pager,
        outfile=outfile,
        cleaner=cleaner.get_clients,
        cache=cli.cache
    )


@app.command()
def logs(
    # args: List[str] = typer.Argument(None, metavar=args_metavar_dev, help="Show clients for a specific device"),
    # os_type:
    # band:
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    sort_by: SortOptions = typer.Option(None, "--sort", hidden=True,),  # TODO Unhide after implemented
    reverse: SortOptions = typer.Option(None, "-r", hidden=True,),  # TODO Unhide after implemented
    verbose: bool = typer.Option(False, "-v", hidden=True,),  # TODO Unhide after implemented
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        callback=cli.debug_callback,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        callback=cli.account_name_callback,
    ),
) -> None:
    # TODO start_time typer.Option pendumlum.... 3H 5h 20m etc. add other filter options
    central = cli.central
    resp = central.request(central.get_audit_logs, start_time=int(time.time() - 172800),)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.callback()
def callback():
    """
    Show Details about Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
