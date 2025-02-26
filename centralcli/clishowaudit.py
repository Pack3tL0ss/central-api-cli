#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
import pendulum
from pathlib import Path
from rich import print
from datetime import datetime
from typing import TYPE_CHECKING


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cleaner, cli, utils, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cleaner, cli, utils, log
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, LogAppArgs, LogSortBy

if TYPE_CHECKING:
    from .cache import CacheGroup, CacheDevice

app = typer.Typer()


tty = utils.tty
iden_meta = IdenMetaVars()

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
def acp_logs(
    log_id: str = typer.Argument(
        None,
        metavar='[LOG_ID]',
        help="Show details for a specific log_id",
        autocompletion=cli.cache.audit_log_completion,
        show_default=False,
    ),
    user: str = typer.Option(None, help="Filter logs by user", show_default=False,),
    _all: bool = typer.Option(False, "-a", "--all", help="Display all available audit logs.  Overrides default of 5 days", show_default=False,),
    device: str = cli.options.device,
    app: LogAppArgs = typer.Option(None, help="Filter logs by app_id", hidden=True),
    ip: str = typer.Option(None, help="Filter logs by device IP address", show_default=False,),
    description: str = typer.Option(None, help="Filter logs by description (fuzzy match)", show_default=False,),
    _class: str = typer.Option(None, "--class", help="Filter logs by classification (fuzzy match)", show_default=False,),
    count: int = typer.Option(None, "-n", max=10_000, help="Collect Last n logs [grey42 italic]max: 10,000[/]", show_default=False,),
    start: datetime = cli.options(timerange="5d").start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
    verbose: int = typer.Option(
            0,
            "-v",
            count=True,
            metavar="",
            help="Verbosity: -v Show periodic system default app tasks, which are filtered by default, -vv Show logs with original field names and minimal formatting (vertically)",
            rich_help_panel="Formatting",
            show_default=False,
    ),
    sort_by: LogSortBy = cli.options.sort_by,
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
    """Show ACP audit logs

    This command shows logs associated with Aruba Cloud Platform (ACP).
    i.e. [cyan]Device Onboarded[/]
         [cyan]Device checked in[/]
         [cyan]New API Gateway app added (token creation)[/]

    Use [cyan]show audit logs[/] to show audit event logs.
    or [cyan]show logs[/] to show device event logs.

    :clock5:  Displays prior 5 days if no time options are provided.
    """
    title = "ACP Audit Logs"
    if (_all or count) and [start, end, past].count(None) != 3:
        cli.exit("Invalid combination of arguments. [cyan]--start[/], [cyan]--end[/], and [cyan]--past[/] are invalid when [cyan]-a[/]|[cyan]--all[/] or [cyan]-n[/] flags are used.")

    start, end = cli.verify_time_range(start, end=end, past=past)

    dev_id = None
    if device:
        if utils.is_serial(device):
            dev_id = device
            title = f"{title} related to device with serial [cyan]{device}[/]"
        else:
            dev = cli.cache.get_dev_identifier(device)
            dev_id = dev.serial if not dev.type == "ap" else dev.swack_id  # AOS10 AP swack_id is serial
            title = f"{title} related to {dev.summary_text}"

    if _all:
        title = f"All available {title}"
    elif count:
        title = f"Last {count} {title}"
    elif [start, end].count(None) == 2:
        start = pendulum.now(tz="UTC").subtract(days=5)
        title = f"{title} for last 5 days"

    kwargs = {
        "log_id": log_id if log_id is None else cli.cache.get_audit_log_identifier(log_id),  # TODO show audit system-logs and show audit logs is using same DB
        "username": user,
        "from_time": start,
        "to_time": end,
        "description": description,
        "target": dev_id,
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
        tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if verbose <= 1 else "yaml")

        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=title,
            caption="Use [cyan]show audit acp-logs <id>[/] to see details for a log.  Logs lacking an id don't have details.",
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=not reverse,  # API returns newest is on top this makes newest on bottom unless they use -r
            cleaner=cleaner.get_audit_logs,  # if not verbose else None,
            cache_update_func=cli.cache.update_log_db,  # cache is not updated if -vv if not verbose else None,
            verbosity = verbose
        )


@app.command()
def logs(
    log_id: str = typer.Argument(
        None,
        metavar='[LOG_ID]',
        help="Show details for a specific log (log_id from previous run of the command)",
        autocompletion=cli.cache.audit_log_completion,
        show_default=False,
    ),
    group: str = cli.options(timerange="48h").group,
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
    _all: bool = typer.Option(False, "-a", "--all", help="Display all available audit logs.  Overrides default of 48h", show_default=False,),
    device: str = cli.options.device,
    _class: str = typer.Option(None, "--class", help="Filter logs by classification (fuzzy match)", show_default=False,),
    count: int = typer.Option(None, "-n", max=10_000, help="Collect Last n logs [grey42 italic]max: 10,000[/]", show_default=False,),
    sort_by: LogSortBy = cli.options.sort_by,
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
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
) -> None:
    """Show Audit Event Logs.

    Other available log commands:
      - [cyan]show audit acp-logs[/] to show audit logs related to Central itself.
      - [cyan]show logs[/] to show device event logs.

    :clock2:  Displays prior 2 days if no time options are provided.
    """
    title = "audit event logs"
    start, end = cli.verify_time_range(start, end=end, past=past)

    if all(x is None for x in [start, end]):
        start = pendulum.now(tz="UTC").subtract(days=2)
        title = f"{title} for last 2 days"
    elif _all:
        title = f"All available {title}"

    dev_id = None
    if device:
        if utils.is_serial(device):
            dev_id = device
            title = f"{title} related to device with serial [cyan]{device}[/]"
        else:
            dev: CacheDevice = cli.cache.get_dev_identifier(device)
            dev_id = dev.serial if not dev.type == "ap" else dev.swack_id  # AOS10 AP swack_id is serial
            title = f"{title} related to {dev.summary_text}"

        if group:
            log.warning(f"[cyan]--group[/] [bright_green]{group}[/] ignored as it doesn't make sense with [cyan]--device[/] [bright_green]{device}[/]", caption=True)
            group = None
    elif group:
        group: CacheGroup = cli.cache.get_group_identifier(group)
        title = f"{title} associated with group {group.name}"

    kwargs = {
        'log_id': None if not log_id else cli.cache.get_audit_log_identifier(log_id),
        'group_name': None if not group else group.name,
        'device_id': dev_id,
        'classification': _class,
        'from_time': start,
        'to_time': end,
        'count': count,
    }

    resp = cli.central.request(cli.central.get_audit_event_logs, **kwargs)

    if log_id is not None:
        if resp and "body" in resp.output:
            body = utils.unlistify(resp.output["body"]).replace("\t", "  ")
            body = f'  body:\n    {"    ".join(body.splitlines(keepends=True))}'
            other = "\n".join([f"{k}: {str(v)}" for k, v in resp.output.items() if k != "body"])
            resp.output = f"{other}\n{body}"
        cli.display_results(resp, tablefmt="action")
    else:
        tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=title,
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=not reverse,  # API returns newest on top this makes newest on bottom unless they use -r
            cleaner=cleaner.get_audit_logs if not verbose else None,
            cache_update_func=cli.cache.update_log_db if not verbose else None,
            caption="Use [cyan]show audit logs <id>[/] to see details for a log.  Logs lacking an id don't have details.",
        )

@app.callback()
def callback():
    """
    Show Aruba Central audit logs / audit event logs
    """
    pass


if __name__ == "__main__":
    app()