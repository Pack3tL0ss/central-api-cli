#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
from pathlib import Path
from rich import print
from datetime import datetime
from rich.markup import escape
from typing import Literal, TYPE_CHECKING

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, log, utils, cleaner, render, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log, utils, cleaner, render, Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, BandwidthInterval, UplinkNames, RadioBandOptions  # noqa

if TYPE_CHECKING:
    from .cache import CacheClient, CacheLabel, CacheGroup, CacheDevice

iden_meta = IdenMetaVars()
app = typer.Typer()
tty = utils.tty


def _render(resp: Response, *, tablefmt: Literal["rich", "yaml", "csv", "json", "graph"], title: str, pager: bool = False, outfile: Path = None, cleaner: callable = cleaner.get_gw_uplinks_bandwidth,) -> None:
    if resp:
        resp.output = sorted(resp.output, key=lambda x: x["timestamp"])

    # We don't graph if there is only a single sample
    if not tablefmt == "graph" or not resp or not resp.output or cli.raw_out or len(resp.output) < 2:
        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=title,
            caption=None if not resp.ok else f'[cyan]Samples[/]: [bright_green]{resp.raw.get("count", "err")}[/] [cyan]Interval[/]: [bright_green]{resp.raw.get("interval", "err")}[/]',
            exit_on_fail=True,
            pager=pager,
            outfile=outfile,
            cleaner=cleaner
        )
    else:
        render.bandwidth_graph(resp, title=title)


@app.command()
def ap(
    ap: str = typer.Argument(None, help=f"Show Bandwidth details for a specific AP [grey42]{escape('[default: All APs]')}[/]", metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, case_sensitive=False, show_default=False,),
    group: str = cli.options.group,
    site: str = cli.options.site,
    label: str = cli.options.label,
    swarm: bool = typer.Option(False, "-s", "--swarm", help=f"Show Bandwidth for the swarm/cluster the provided AP belongs to [grey42]{escape('[AP argument must be provided. Valid for AOS8 IAP]')}[/]", show_default=False),
    band: RadioBandOptions = typer.Option(None, help=f"Show Bandwidth for a specific band [grey42]{escape('[ap must be provided]')}[/]", autocompletion=cli.cache.group_completion, show_default=False),
    ssid: str = typer.Option(None, help=f"Show Bandwidth for a specifc ssid [grey42]{escape('[ap must be provided]')}[/]", show_default=False),
    interval: BandwidthInterval = typer.Option(BandwidthInterval._5m, "-i", "--interval", case_sensitive=False, help="One of 5m, 1h, 1d, 1w, where m=minutes, h=hours, d=days, w=weeks M=Months"),
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show AP(s) bandwidth usage graph.

    Default output is line graph showing bandwidth usage over the last 3 hours.
    Use formatting flags for alternative output.  [cyan]--start[/], [cyan]--end[/], [cyan]--past[/] to adjust time-frame.

    The larger the time-frame the more unreadable the graph will be.
    """
    # start and end datetime opjects are in UTC
    dev = None if not ap else cli.cache.get_dev_identifier(ap, dev_type="ap")
    group = None if not group else cli.cache.get_group_identifier(group)
    site = None if not site else cli.cache.get_site_identifier(site)
    label = None if not label else cli.cache.get_label_identifier(label)
    start, end = cli.verify_time_range(start, end=end, past=past)

    interval = interval.replace("m", "minutes").replace("h", "hours").replace("d", "days").replace("w", "weeks")

    if band and not dev:
        log.warning(f"[cyan]--band[/] is only valid when gathering bandwidth for a specific AP.  [cyan]--band[/] {band} ignored.", caption=True,)
        band = None
    if ssid and not dev:
        log.warning(f"[cyan]--ssid[/] is only valid when gathering bandwidth for a specific AP.  [cyan]--ssid[/] {ssid} ignored.", caption=True,)
        ssid = None
    if any([group, site, label]) and dev:
        log.warning(f"[cyan]--group[/] [cyan]--site[/] [cyan]--label[/] flags don't apply when gathering usage for a specific AP ({dev.summary_text})", caption=True,)
        group = site = label = None
        ssid = None
    if swarm and dev and dev.is_aos10:
        cli.exit(f"[cyan]--swarm[/] is only valid for [bright_green]AOS8[/] IAP clusters [cyan]{dev.name}[/] is an [bright_red]AOS10[/] AP.")


    params = ["serial", "group", "site", "label", "swarm_id", "band", "network"]
    args = [
        dev if dev is None else dev.serial,
        group if group is None else group.name,
        site if site is None else site.name,
        label if label is None else label.name,
        None if not swarm or not dev else dev.swack_id,
        band if band is None else band.value,
        ssid
    ]
    title_sfx = [
        f"for AP [cyan]{'' if not dev else dev.name}[/]",
        f"for APs in group [cyan]{'' if not group else group.name}[/]",
        f"for APs in site [cyan]{'' if not site else site.name}[/]",
        f"for APs with label [cyan]{'' if not label else label.name}[/]",
        f"for APs in same cluster as {'' if not swarm or not dev else dev.summary_text}",
        f"{band}Ghz radio",
        f"[bright_green]SSID[/]: [cyan]{ssid}[/]",
    ]

    kwargs = {k: v for k, v in zip(params, args) if v is not None}
    if dev and swarm:
        del kwargs["serial"]  # They provided the --swarm flag so we keep the swarm_id kwargs but strip the serial.  --swarm means to return bandwidth for the swarm the AP belongs to (swarm_ids are not human friendly)

    title_parts = ["Bandwidth Usage", *[title_part for k, title_part in zip(params, title_sfx) if k in kwargs]]
    title = " ".join(title_parts)
    title = title if title != "Bandwidth Usage" else "Bandwidth Usage All APs"

    resp = cli.central.request(cli.central.get_aps_bandwidth_usage, **kwargs, interval=interval, from_time=start, to_time=end)

    tablefmt = "graph" if not any([do_csv, do_json, do_yaml, do_table]) else cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not do_table else "yaml")
    _render(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile,)


@app.command()
def switch(
    switch: str = typer.Argument(..., help="Switch to show Bandwidth details for", metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_completion, case_sensitive=False, show_default=False,),
    port: str = typer.Argument("All Ports", help="Show bandwidth for a specific port",),
    uplink: bool = typer.Option(False, "--uplink", help="Show Bandwidth usage for the uplink", show_default=False,),
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show Bandwidth usage for a switch or a specific port on a switch.

    Default output is line graph showing bandwidth usage over the last 3 hours.
    Use formatting flags for alternative output.  [cyan]--start[/], [cyan]--end[/], [cyan]--past[/] to adjust time-frame.

    The larger the time-frame the more unreadable the graph will be.
    """
    # start and end datetime opjects are in UTC
    dev = cli.cache.get_dev_identifier(switch, dev_type="switch")
    port = None if port == "All Ports" else port
    start, end = cli.verify_time_range(start, end=end, past=past)


    title = f"Bandwidth Usage [cyan]{dev.name}[/]"
    if uplink:
        title = f"{title} [bright_green]Uplink[/]"
    elif port:
        title = f"{title} port [bright_green]{port}[/]"

    resp = cli.central.request(cli.central.get_switch_ports_bandwidth_usage, dev.serial, switch_type=dev.type, from_time=start, to_time=end, port=port, show_uplink=uplink)

    _interval = resp.raw.get("interval")
    if _interval and not any([do_json, do_yaml, do_csv, do_table]):
        title = f"{title}, Sample Frequency: {_interval}"

    tablefmt = "graph" if not any([do_csv, do_json, do_yaml, do_table]) else cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not do_table else "yaml")
    _render(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile,)


@app.command()
def client(
    client: str = typer.Argument(None, help=f"Show Bandwidth details for a specific client [grey42]{escape('[default: All clients]')}[/]", metavar=iden_meta.client, autocompletion=cli.cache.client_completion, show_default=False,),
    device: str = typer.Option(None, "--dev", help="Show Bandwidth details for clients connected to a specific device", metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, case_sensitive=False, show_default=False,),
    group: str = typer.Option(None, help="Show Bandwidth for clients connected to devices in a specific group", metavar=iden_meta.group, autocompletion=cli.cache.group_completion, show_default=False),
    label: str = typer.Option(None, help="Show Bandwidth for clients connected to devices with a specific label", metavar=iden_meta.label, autocompletion=cli.cache.label_completion, show_default=False),
    swarm_or_stack: bool = typer.Option(False, "-s", "--swarm", "--stack", help="Show Bandwidth for the swarm or stack the provided device belongs to [cyan]--dev[/] argument must be provided.", show_default=False),
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show client bandwidth usage graph.

    Default output is line graph showing bandwidth usage over the last 3 hours.
    Use formatting flags for alternative output.  [cyan]--start[/], [cyan]--end[/], [cyan]--past[/] to adjust time-frame.

    The larger the time-frame the more unreadable the graph will be.
    """
    # start and end datetime opjects are in UTC
    dev: CacheDevice | None = None if not device else cli.cache.get_dev_identifier(device, conductor_only=True)
    group: CacheGroup | None = None if not group else cli.cache.get_group_identifier(group)
    label: CacheLabel | None = None if not label else cli.cache.get_label_identifier(label)
    client: CacheClient | None = None if not client else cli.cache.get_client_identifier(client, exit_on_fail=True)
    start, end = cli.verify_time_range(start, end=end, past=past)

    kwargs = {}
    title = "Bandwidth Usage"

    if client:
        kwargs["mac"] = client.mac
        title = f'{title} for Client: {client.name}|{client.ip}|{client.mac}|{client.connected_name}'
        if client.site:
            title = f'{title}|s:{client.site}'
        if swarm_or_stack:
            log.warning(f"[cyan]-s[/]|[cyan]--swarm[/]|[cyan]--stack[/] was ignored as client was specified.  Output is for client {client.summary_text}", caption=True)
        if dev:
            log.warning(f"[cyan]--dev[/] {device} was ignored as client was specified.  Output is for client {client.summary_text}", caption=True)
        if any([group, label]):
            _err = f"[cyan]--group[/] {group.name}" if group and not label else f"[cyan]--label[/] {label.name}"
            _err = _err if not label else f"[cyan]--group[/] {group.name} & [cyan]--label[/] {label.name}"
            log.warning(f"{_err} was ignored as client was specified.  Output is for client {client.summary_text}", caption=True)
    elif swarm_or_stack:
        if not dev:
            cli.exit("[cyan]--dev[/] DEVICE must be provided with [cyan]-s[/]|[cyan]--swarm[/]|[cyan]--stack[/] option.")
        else:
            if dev.type == "ap" and dev.is_aos10:
                log.warning(f"[cyan]-s[/]|[cyan]--swarm[/] is only valid for AOS8 APs {dev.name} is AOS10.", caption=True)
                log.warning(f"[cyan]-s[/]|[cyan]--swarm[/] was ignored.  Output is for clients connected to {dev.name}", caption=True)
                kwargs["serial"] = dev.serial
            elif dev.generic_type not in ["switch", "ap"]:
                log.warning(f"[cyan]swarm[/]/[cyan]stack[/] flag only applies to switches or APs not {dev.type}.", caption=True)
                log.warning(f"[cyan]-s[/]|[cyan]--swarm[/]|[cyan]--stack[/] was ignored.  Output is for clients connected to {dev.name}", caption=True)
            else:
                kwargs[f'{"swarm_id" if dev.type == "ap" else "stack_id"}'] = dev.swack_id
    elif dev:
        if any([group, label]):
            log.warning("[cyan]--group[/] & [cyan]--label[/] flags are mutually exclusive with [cyan]--dev[/] <DEVICE>.", caption=True,)
            log.info(f"Ignoring {'[cyan]--group[/]' if group else '[cyan]--label[/]'}.  Output is for clients connected to {dev.summary_text}", caption=True,)
            title = f"{title} for clients connected to {dev.name}"
            kwargs["serial"] = dev.serial
    elif any([group, label]):
        if group:
            kwargs["group"] = group.name
            title = f"{title} for clients connected to devices in [cyan]{group.name}[/] group"

        if label:
            kwargs["label"] = label.name
            title = f"{title} for clients connected to devices with label {label.name}" if not group else f"{title} with label {label.name}"
    else:
        title = f"{title} [bright_green]All[/] Clients"

    if dev and title == "Bandwidth Usage":
        title = f"{title} for Clients connected to {dev.summary_text}"


    resp = cli.central.request(cli.central.get_clients_bandwidth_usage, **kwargs, from_time=start, to_time=end)

    tablefmt = "graph" if not any([do_csv, do_json, do_yaml, do_table]) else cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not do_table else "yaml")
    _render(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile,)


@app.command()
def uplink(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_switch_gw_completion, show_default=False,),
    uplink_name: UplinkNames = typer.Argument("uplink101", help="[Applies to Gateway] Name of the uplink.  Use [cyan]cencli show uplinks <GATEWAY>[/] to get uplink names.", show_default=True,),
    interval: BandwidthInterval = typer.Option(BandwidthInterval._5m, "-i", "--interval", case_sensitive=False, help="[Applies to Gateway] One of 5m, 1h, 1d, 1w, where m=minutes, h=hours, d=days, w=weeks M=Months"),
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show bandwidth usage graph for a switch or gateway uplink

    Default output is line graph showing uplink bandwidth usage over the last 3 hours.
    Use formatting flags for alternative output.  [cyan]--start[/], [cyan]--end[/], [cyan]--past[/] to adjust time-frame.

    The larger the time-frame the more unreadable the graph will be.
    Use [cyan]cencli show uplinks <GATEWAY>[/] to get uplink names
    """
    # start and end datetime opjects are in UTC
    dev = cli.cache.get_dev_identifier(device, dev_type=["gw", "switch"])
    start, end = cli.verify_time_range(start, end=end, past=past)

    interval = interval.replace("m", "minutes").replace("h", "hours").replace("d", "days").replace("w", "weeks")

    if dev.type == "gw":
        resp = cli.central.request(cli.central.get_gw_uplinks_bandwidth_usage, dev.serial, uplink_name, interval=interval, from_time=start, to_time=end)
    else:
        resp = cli.central.request(cli.central.get_switch_ports_bandwidth_usage, dev.serial, switch_type=dev.type, from_time=start, to_time=end, show_uplink=True)

    title = f'Bandwidth Usage for [cyan]{dev.name}[/] uplink [cyan]{uplink_name}[/]'

    tablefmt = "graph" if not any([do_csv, do_json, do_yaml, do_table]) else cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not do_table else "yaml")
    _render(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile,)


@app.command()
def wlan(
    network: str = typer.Argument(..., metavar="[WLAN SSID]", help="Use [cyan]cencli show wlans[/] for a list of networks", show_default=False,),
    group: str = typer.Option(None, help="Show Bandwidth for APs in a specific group", metavar=iden_meta.group, autocompletion=cli.cache.group_completion, show_default=False),
    site: str = typer.Option(None, help="Show Bandwidth for APs in a specific site", metavar=iden_meta.site, autocompletion=cli.cache.site_completion, show_default=False),
    label: str = typer.Option(None, help="Show Bandwidth for APs with a specific label", metavar=iden_meta.label, autocompletion=cli.cache.label_completion, show_default=False),
    device: str = typer.Option(
        None,
        "-s", "--swarm",
        metavar=iden_meta.dev,
        autocompletion=cli.cache.dev_switch_ap_completion,
        help=f"Show bandwidth for the swarm associated with provided AP [grey42]{escape('[Valid for AOS8 IAP]')}[/]",
        show_default=False,
    ),
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show bandwidth usage graph for a network/SSID

    Default output is line graph showing network bandwidth usage over the last 3 hours.
    Use formatting flags for alternative output.  [cyan]--start[/], [cyan]--end[/], [cyan]--past[/] to adjust time-frame.

    The larger the time-frame the more unreadable the graph will be.
    Use [cyan]cencli show wlans <GATEWAY>[/] to get list of available networks.
    """
    # start and end datetime opjects are in UTC
    title = f'Bandwidth Usage for [cyan]{network}[/]'
    if device:
        dev = cli.cache.get_dev_identifier(device, dev_type="ap", swack=True)
        title = f"{title} on swarm containing {dev.name}"

    kwargs = {
        "group": None if not group else cli.cache.get_group_identifier(group).name,
        "site": None if not site else cli.cache.get_group_identifier(site).name,
        "label": None if not label else cli.cache.get_group_identifier(label).name,
        "swarm_id": None if not device else dev.swack_id
    }
    if len([v for v in kwargs.values() if v is not None]) > 1:
        cli.exit("You can only specify one of [cyan]--group[/], [cyan]--swarm[/], [cyan]--label[/], [cyan]--site[/] parameters")

    start, end = cli.verify_time_range(start, end=end, past=past)

    resp = cli.central.request(cli.central.get_networks_bandwidth_usage, network, **kwargs)

    tablefmt = "graph" if not any([do_csv, do_json, do_yaml, do_table]) else cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not do_table else "yaml")
    _render(resp, tablefmt=tablefmt, title=title, pager=pager, outfile=outfile,)


@app.callback()
def callback():
    """
    Show bandwidth usage
    """
    pass


if __name__ == "__main__":
    app()
