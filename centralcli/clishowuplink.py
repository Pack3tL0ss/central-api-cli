#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import typer
import pendulum
import sys
from pathlib import Path
from rich import print
from datetime import datetime
import plotext as plt


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, log, utils, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log, utils, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, BandwidthInterval  # noqa

iden_meta = IdenMetaVars()
app = typer.Typer()


@app.command()
def bandwidth(
    gateway: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_gw_completion, case_sensitive=False, show_default=False,),
    uplink_name: str = typer.Argument(..., help="Name of the uplink.  Use [cyan]cencli show uplinks <GATEWAY>[/] to get uplink names.", show_default=False,),
    start: datetime = typer.Option(
        None,
        "-s", "--start",
        help="Start time of bandwidth details [grey42]\[default: 3 hours ago][/]",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"],
        show_default=False,
    ),
    end: datetime = typer.Option(
        None,
        "-e", "--end",
        help="End time of bandwidth details [grey42]\[default: Now][/]",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"],
        show_default=False,
    ),
    past: str = typer.Option(None, "-p", "--past", help="Collect bandwidth details for last <past>, d=days, h=hours, m=mins i.e.: 3h [grey42]\[default: 3h][/]", show_default=False,),
    interval: BandwidthInterval = typer.Option(BandwidthInterval._5m, "-i", "--interval", case_sensitive=False, help="One of 5m, 1h, 1d, 1w, where m=minutes, h=hours, d=days, w=weeks M=Months"),
    do_bar: bool = typer.Option(False, "-b", "--bar", help="Output bar graph [grey42]\[default: Line Graph][/]", rich_help_panel="Formatting",),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", rich_help_panel="Formatting",),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", rich_help_panel="Formatting", hidden=True),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", rich_help_panel="Formatting",),
    do_table: bool = typer.Option(False, "--table", help="Output in table format", rich_help_panel="Formatting",),
    # sort_by: str = typer.Option(None, "--sort", show_default=False, rich_help_panel="Formatting",),
    # reverse: bool = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, rich_help_panel="Common Options", show_default=False,),
    raw: bool = typer.Option(
        False,
        "--raw",
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
    """Show bandwidth usage graph for a gateway uplink

    Default output is horizontal bar graph.  Use formatting flags for alternative output.
    The larger the time-frame the more unreadable the graph will be.

    Use [cyan]cencli show uplinks <GATEWAY>[/] to get uplink names
    """
    # start and end datetime opjects are in UTC
    dev = cli.cache.get_dev_identifier(gateway, dev_type="gw")

    if end and past:
        log.warning("[cyan]--end[/] flag ignored, providing [cyan]--past[/] implies end is now.", caption=True)
        end = None

    if start and past:
        log.warning(f"[cyan]--start[/] flag ignored, providing [cyan]--past[/] implies end is now - {past}", caption=True)

    if past:
        start = cli.past_to_start(past=past)

    interval = interval.replace("m", "minutes").replace("h", "hours").replace("d", "days").replace("w", "weeks")
    resp = cli.central.request(cli.central.get_gw_uplinks_bandwidth_usage, dev.serial, uplink_name, interval=interval, from_time=start, to_time=end)

    if resp.ok and "samples" in resp.output:
        resp.output = sorted(resp.output["samples"], key=lambda x: x["timestamp"])

    # We don't graph if there is only a single sample
    if not resp or not resp.output or len(resp.output) < 2 or any([do_csv, do_json, do_yaml, do_table]):
        tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not do_table else "yaml")
        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=f'Bandwidth Usage for {dev.name} uplink {uplink_name}',
            caption=f'[cyan]Samples[/]: [bright_green]{resp.raw.get("count", "err")}[/] [cyan]Interval[/]: [bright_green]{resp.raw.get("interval", "err")}[/]',
            exit_on_fail=True,
            pager=pager,
            outfile=outfile,
            cleaner = cleaner.get_gw_uplinks_bandwidth
        )
        cli.exit(code=0)

    plt.date_form('Y-m-d H:M:S')
    start = plt.string_to_datetime(
        pendulum.from_timestamp(resp.output[0]["timestamp"]).to_datetime_string()
    )
    end = plt.string_to_datetime(
        pendulum.from_timestamp(resp.output[-1]["timestamp"]).to_datetime_string()
    )

    dates = plt.datetimes_to_string([datetime.fromtimestamp(bw_data["timestamp"]) for bw_data in resp.output])
    tx_data = [x["tx_data_bytes"] for x in resp.output]
    rx_data = [x["rx_data_bytes"] for x in resp.output]

    lowest = utils.convert_bytes_to_human(min([min(tx_data), min(rx_data)]), speed=True)
    return_size = "B" if lowest.split()[-1] == "bps" else "".join(list(lowest.split()[-1])[0:2]).upper()

    tx_data = [float(utils.convert_bytes_to_human(x, speed=True, return_size=return_size).split()[0]) for x in tx_data]
    rx_data = [float(utils.convert_bytes_to_human(x, speed=True, return_size=return_size).split()[0]) for x in rx_data]

    plt.title(f'Bandwidth Usage for {dev.name} uplink {uplink_name}')
    plt.theme("dark")

    if do_bar:
        plt.ylabel("time")
        plt.xlabel(f"{return_size}ps".capitalize())

        plt.multiple_bar(dates, [rx_data, tx_data], label=["rx", "tx"], orientation="horizontal")
    else:
        plt.xlabel("time")
        plt.ylabel(f"{return_size}ps".capitalize())

        plt.plot(dates, rx_data, label="rx",)
        plt.plot(dates, tx_data, label="tx",)

    plt.show()


@app.callback()
def callback():
    """
    Show Gateway Uplink bandwidth usage
    """
    pass


if __name__ == "__main__":
    app()
