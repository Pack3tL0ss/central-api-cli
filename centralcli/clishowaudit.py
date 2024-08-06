#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
import time
import pendulum
from pathlib import Path
from rich import print
from datetime import datetime


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

def _verify_time_range(start: datetime | pendulum.DateTime | None, end: datetime | pendulum.DateTime = None, past: str = None, show_all: bool = False, max_days: int = 90) -> pendulum.DateTime | None:
    if show_all:
        if any([start, end, past]):
            cli.exit("Invalid combination of arguments. [cyan]--start[/], [cyan]--end[/], and [cyan]--past[/] are invalid when [cyan]--all[/] is used.")

    if end and past:
        log.warning("[cyan]--end[/] flag ignored, providing [cyan]--past[/] implies end is now.", caption=True,)
        end = None

    if start and past:
        log.warning(f"[cyan]--start[/] flag ignored, providing [cyan]--past[/] implies end is now - {past}", caption=True,)

    if past:
        start = cli.past_to_start(past=past)

    if start is None:
        return start, end

    if not hasattr(start, "timezone"):
        start = pendulum.from_timestamp(start.timestamp(), tz="UTC")
    if end is None:
        _end = pendulum.now(tz=start.timezone)
    else:
        _end = end if hasattr(end, "timezone") else pendulum.from_timestamp(end.timestamp(), tz="UTC")

    delta = _end - start

    if delta.days > max_days:
        if end:
            cli.exit(f"[cyan]--start[/] and [cyan]--end[/] provided span {delta.days} days.  Max allowed is 90 days.")
        else:
            log.info(f"[cyan]--past[/] option spans {delta.days} days.  Max allowed is 90 days.  Output constrained to 90 days.", caption=True)
            return cli.past_to_start("2_159h"), end  # 89 days and 23 hours to avoid issue with API endpoint

    return start, _end


@app.command()
def system_logs(
    log_id: str = typer.Argument(
        None,
        metavar='[LOG_ID]',
        help="Show details for a specific log_id",
        autocompletion=lambda incomplete: cli.cache.get_log_identifier(incomplete, include_cencli=False),
        show_default=False,
    ),
    tail: bool = typer.Option(False, "-f", help="follow tail on log file (implies show logs)", is_eager=True),
    user: str = typer.Option(None, help="Filter logs by user", show_default=False,),
    start: str = typer.Option(None, "-s", "--start", help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    end: str = typer.Option(None, "-e", "--end", help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    past: str = typer.Option(None, "-p", "--past", help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h", show_default=False,),
    _all: bool = typer.Option(False, "-a", "--all", help="Display all available audit logs.  Overrides default of 5 days", show_default=False,),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter logs by device",
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    app: LogAppArgs = typer.Option(None, help="Filter logs by app_id", hidden=True),
    ip: str = typer.Option(None, help="Filter logs by device IP address", show_default=False,),
    description: str = typer.Option(None, help="Filter logs by description (fuzzy match)", show_default=False,),
    _class: str = typer.Option(None, "--class", help="Filter logs by classification (fuzzy match)", show_default=False,),
    count: int = typer.Option(None, "-n", help="Collect Last n logs", show_default=False,),
    cencli: bool = typer.Option(False, "--cencli", help="Show cencli logs", callback=show_logs_cencli_callback),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: LogSortBy = typer.Option(None, "--sort", show_default=False,),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
    raw: bool = typer.Option(False, "--raw", help="Show raw unformatted response from Central API Gateway"),
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
    """Show Aruba Central audit logs

    This command shows logs associated with Aruba Central itself.
    i.e. [cyan]Device Onboarded[/]
         [cyan]Device checked in[/]
         [cyan]New API Gateway app added (token creation)[/]

    Use [cyan]show audit logs[/] to show audit event logs.
    or [cyan]show logs[/] to show device event logs.

    :clock5:  Displays prior 5 days if no time options are provided.
    """
    if cencli or (log_id and log_id[-1] == "cencli"):
        from centralcli import log
        log.print_file() if not tail else log.follow()
        raise typer.Exit(0)

    if log_id:
        log_id = cli.cache.get_log_identifier(log_id)
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
        "start_time": start or int(time.time() - 432000) if not _all else None,
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
        tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title="Audit Logs",
            pager=pager,
            outfile=outfile,
            sort_by=sort_by,
            reverse=reverse,
            cleaner=cleaner.get_audit_logs if not verbose else None,
            cache_update_func=cli.cache.update_log_db if not verbose else None,
            caption="Use [cyan]show audit system-logs <id>[/] to see details for a log.  Logs lacking an id don't have details.",
        )


@app.command()
def logs(
    log_id: str = typer.Argument(
        None,
        metavar='[LOG_ID]',
        help="Show details for a specific log (log_id from previous run of the command)",
        autocompletion=lambda incomplete: cli.cache.get_log_identifier(incomplete, include_cencli=False),
        show_default=False,
    ),
    group: str = typer.Option(None, "--group", help="Filter Audit event logs by group", show_default=False,),
    # start: str = typer.Option(None, "-s", "--start", help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    # end: str = typer.Option(None, "-e", "--end", help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)", show_default=False,),
    # past: str = typer.Option(None, "-p", "--past", help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h", show_default=False,),
    start: datetime = typer.Option(
        None,
        "-s", "--start",
        help="Start time of logs [grey42]\[default: 48 hours ago][/]",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"],
        show_default=False,
    ),
    end: datetime = typer.Option(
        None,
        "-e", "--end",
        help="End time of logs [grey42]\[default: Now][/]",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"],
        show_default=False,
    ),
    past: str = typer.Option(None, "-p", "--past", help="Collect bandwidth details for last <past>, w=weeks, d=days, h=hours, m=mins i.e.: 3h [grey42]\[default: 48h][/]", show_default=False,),
    _all: bool = typer.Option(False, "-a", "--all", help="Display all available audit logs.  Overrides default of 48h", show_default=False,),
    device: str = typer.Option(
        None,
        metavar=iden_meta.dev,
        help="Filter logs by device",
        autocompletion=cli.cache.dev_completion,
        show_default=False,
    ),
    _class: str = typer.Option(None, "--class", help="Filter logs by classification (fuzzy match)", show_default=False,),
    count: int = typer.Option(None, "-n", help="Collect Last n logs", show_default=False,),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format"),
    sort_by: LogSortBy = typer.Option(None, "--sort", show_default=False,),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order Default order: newest on bottom.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show logs with original field names and minimal formatting (vertically)"),
    raw: bool = typer.Option(False, "--raw", help="Show raw unformatted response from Central API Gateway"),
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
    """Show Audit Event Logs.

    Other available log commands:
      - [cyan]show audit system-logs[/] to show audit logs related to Central itself.
      - [cyan]show logs[/] to show device event logs.

    :clock2:  Displays prior 2 days if no time options are provided.
    """
    title = "audit event logs"
    start, end = _verify_time_range(start, end, past=past, show_all=_all)

    if all(x is None for x in [start, end]):
        start = pendulum.now(tz="UTC").subtract(days=2)
        title = f"{title} for last 2 days"
    elif _all:
        title = f"All available {title}"

    dev_id = None
    if device:
        dev = cli.cache.get_dev_identifier(device)
        dev_id = dev.serial if not dev.type == "ap" else dev.swack_id  # AOS10 AP swack_id is serial
        title = f"{title} related to {dev.summary_text}"
        if group:
            log.warning(f"[cyan]--group[/] [bright_green]{group}[/] ignored as it doesn't make sense with [cyan]--device[/] [bright_green]{device}[/]", caption=True)
            group = None
    elif group:
        group = cli.cache.get_group_identifier(group)
        title = f"{title} associated with group {group.name}"

    kwargs = {
        'log_id': None if not log_id else cli.cache.get_log_identifier(log_id),
        'group_name': None if not group else group.name,
        'device_id': dev_id,
        'classification': _class,
        'start_time': None if _all else start.int_timestamp,
        'end_time': None if _all or end is None else end.int_timestamp,
        'count': count,
    }

    resp = cli.central.request(cli.central.get_audit_logs_events, **kwargs)

    if log_id is not None:
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
            reverse=reverse,
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