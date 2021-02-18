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
    from centralcli import Response, cleaner, cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response, cleaner, cli, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import ClientArgs, StatusOptions, SortOptions, IdenMetaVars, CacheArgs  # noqa

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


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
        # if not group:  # cache should handle exit now
        #     raise typer.Exit(1)

    # -- // Peform GET Call \\ --
    resp = None
    params = {
        "group": None if not group else group.name,
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
            dev = cli.cache.get_dev_identifier(args)
            resp = central.request(central.get_dev_details, dev.type, dev.serial, **params)
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
        dev = cli.cache.get_dev_identifier(args, dev_type=dev_type)
        resp = central.request(central.get_dev_details, dev_type, dev.serial)
    else:
        resp = central.request(central.get_devices, dev_type, **params)

    data = cli.eval_resp(resp)

    if data:
        # device details is a lot of data default to yaml output, default horizontal would typically overrun tty
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="yaml")
        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.sort_result_keys)


@app.command(short_help="Show APs/details")
def aps(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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
) -> None:
    show_devices(
        'aps', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show switches/details")
def switches(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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
) -> None:
    show_devices(
        'switches', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show interfaces/details")
def interfaces(
    device: str = typer.Argument(..., metavar=iden_meta.dev, hidden=False),
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
    dev_site: str = typer.Argument(..., metavar=f"{iden_meta.dev} OR {iden_meta.site}", hidden=False),
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
    # TODO cli command lacks the filtering options available from method currently.
    central = cli.central

    cli.cache(refresh=update_cache)

    obj = cli.cache.get_identifier(dev_site, qry_funcs=("dev", "site"))

    if obj:
        if obj.is_site:
            resp = central.request(central.get_site_vlans, obj.id)
        elif obj.is_dev:
            if obj.type.lower() in ['cx', 'sw']:
                resp = central.request(central.get_switch_vlans, obj.serial, cx=obj.type == "CX")
            elif obj.type.lower() == 'gateway':
                resp = central.request(central.get_gateway_vlans, obj.serial)
            elif obj.type.lower() == 'mobility_controllers':
                resp = central.request(central.get_controller_vlans, obj.serial)
        else:
            typer.secho(f"show vlans not implemented for {dev_site}", fg="red")
            typer.echo(str(obj))
            raise typer.exit(1)

    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.get_vlans)


@app.command(short_help="Show All Devices")
def all(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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
    if args and args[0] == 'all':
        dev_type = 'all'
        args = () if len(args) == 1 else args[1:]

    if args:
        dev = cli.cache.get_dev_identifier(args)
        args = utils.listify(args)
        dev_type = type_to_link.get(dev.type, dev.type)
    else:  # show devices ... equiv to show all
        dev_type = 'all'

    show_devices(
        dev_type, *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show gateways/details")
def gateways(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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


@app.command("cache", short_help="Show contents of Identifier Cache.", hidden=True)
def _cache(
    args: List[CacheArgs] = typer.Argument(None, hidden=False),
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
    args = ('all',) if not args else args
    for arg in args:
        cache_out = getattr(cli.cache, arg)
        resp = Response(output=cache_out)
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
    args: List[str] = typer.Argument(None, metavar=iden_meta.site, hidden=False),
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
    site = None
    if args:
        site = cli.cache.get_site_identifier(args)

    if not site:
        if central.get_all_sites not in cli.cache.updated:
            asyncio.run(cli.cache.update_site_db())
        resp = Response(output=cli.cache.sites)
    else:
        resp = central.request(central.get_site_details, site.id)

    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show templates/details")
def templates(
    # args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
    name: str = typer.Argument(None, hidden=False, help=f"Template: [name] or Device: {iden_meta.dev}"),
    group: List[str] = typer.Argument(None, help="Get Templates for Group"),
    _group: str = typer.Option(None, "--group", help="Get Templates for Group"),
    # _name: str = typer.Option(None, "--template", help="Get details for template by name"),
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
    # sort_by: SortOptions = typer.Option(None, "--sort"),show
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
    if _group:
        group = _group
    elif group:
        group = group[-1]

    if group:
        group = cli.cache.get_group_identifier(group)
        group = group.name

    central = cli.central
    cli.cache(refresh=update_cache)

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
            typer.secho(f"Unabled to find a match for {log_name}.  Listing all templates.", fg="red")

    if not name:
        if not group:
            if not params:  # show templates - Just update and show data from cache
                if central.get_all_templates not in cli.cache.updated:
                    asyncio.run(cli.cache.update_template_db())
                    resp = Response(output=cli.cache.templates)
                else:
                    # Can't use cache due to filtering options
                    resp = central.request(central.get_all_templates, **params)
        else:  # show templates --group <group name>
            resp = central.request(central.get_all_templates_in_group, group, **params)
    elif group:  # show template <name> --group <group_name> or show template <name> <group name>
        if name.is_template:
            resp = central.request(central.get_template, group, name.name)
        elif name.is_dev:  # They provided a dev identifier
            resp = central.request(central.get_variablised_template, name.serial)
        else:
            typer.secho(f"Something went wrong {name}", fg="red")
    else:  # provided args but no group get group from device iden
        if name.is_dev:
            resp = central.request(central.get_variablised_template, name.serial)
        elif name.is_template:
            resp = central.request(central.get_template, name.group, name.name)

    data = cli.eval_resp(resp)
    if data:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show Variables for all or specific device")
def variables(
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, hidden=False),
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

    resp = central.request(central.get_variables, args.serial)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, sort_by=sort_by)


@app.command(short_help="Show AP lldp neighbors")
def lldp(
    device: List[str] = typer.Argument(..., metavar=iden_meta.dev, hidden=False),
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

    # We take last arg [-1] from list so they can type "neighbor" if they want.
    dev = cli.cache.get_dev_identifier(device[-1])
    if dev.type == "ap":
        resp = central.request(central.get_ap_lldp_neighbor, dev.serial)
        data = cli.eval_resp(resp)
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

        cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.get_lldp_neighbor)
    else:
        typer.secho(f"This command is currently only valid for APs.  {dev.name} is type: {dev.type}", fg="red")
        raise typer.Exit(1)


@app.command(short_help="Show certificates/details")
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
) -> None:
    resp = cli.central.request(cli.central.get_certificates, name, callback=cleaner.get_certificates)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show WLAN(SSID)/details")
def wlans(
    name: str = typer.Argument(None, metavar="[WLAN NAME]", help="Get Details for a specific WLAN"),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    site: str = typer.Option(None, metavar="[site identifier]", help="Filter by device status"),
    swarm_id: str = typer.Option(None,),
    do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per SSID)"),
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
) -> None:
    cli.cache(refresh=update_cache)
    central = cli.central
    if site:
        _site = cli.cache.get_site_identifier(site, retry=False)
        site = _site.name or site

    params = {
        "name": name,
        "group": group,
        "swarm_id": swarm_id,
        "label": label,
        "site": site,
        "calculate_client_count": do_clients,
    }

    if sort_by:
        typer.secho("sort not implemented yet.", fg="red")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")
    resp = central.request(central.get_wlans, **params)
    data = cli.eval_resp(resp)
    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show clients/details")
def clients(
    filter: ClientArgs = typer.Argument('all', case_sensitive=False, ),
    args: List[str] = typer.Argument(None, metavar=iden_meta.dev, help="Show clients for a specific device"),
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


@app.command(short_help="Display Event Logs (2 days by default)")
def logs(
    # args: List[str] = typer.Argument(None, metavar=iden_meta.dev, help="Show clients for a specific device"),
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
    cli.cache(refresh=update_cache)
    # TODO start_time typer.Option pendumlum.... 3H 5h 20m etc. add other filter options
    central = cli.central
    resp = central.request(central.get_audit_logs, start_time=int(time.time() - 172800),)
    data = cli.eval_resp(resp)
    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

    cli.display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, sort_by=sort_by, reverse=reverse)


@app.callback()
def callback():
    """
    Show Details about Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
