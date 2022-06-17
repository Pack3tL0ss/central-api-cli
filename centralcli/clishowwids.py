#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
import typer
import sys
import pendulum
import time
from pathlib import Path


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars  # noqa

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()


class ShowFirmwareDevType(str, Enum):
    ap = "ap"
    # gateway = "gateway"
    gw = "gw"
    switch = "switch"


class ShowFirmwareKwags(str, Enum):
    group = "group"
    type = "type"


@app.command(short_help="Show Detected Rogue APs")
def rogues(
    start: str = typer.Option(None, help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    group: str = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    label: str = typer.Argument(None, metavar="[LABEL]",),  # autocompletion=cli.cache.group_completion),  # TODO cache labels
    site: str = typer.Argument(None, metavar="[SITE-NAME]", autocompletion=cli.cache.site_completion),
    # swarm: str = typer.Argument(None, metavar="[SWARM NAME or ID]", autocompletion=cli.cache.swarm_completion),  # TODO
    sort_by: str = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    central = cli.central
    cli.cache(refresh=update_cache)

    if group:
        group = cli.cache.get_group_identifier(group).name

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

    kwargs = {
        "from_timestamp": start,
        "to_timestamp": end,
        "group": group,
        "label": label,
        "site": site,
        # "swarm_id": swarm, TODO
    }

    resp = central.request(central.wids_get_rogue_aps, **kwargs)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Rogues",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by if not sort_by else sort_by.replace("_", " "),
        reverse=reverse,
        # cleaner=cleaner.get_audit_logs if not verbose else None,
        # cache_update_func=cli.cache.update_log_db if not verbose else None,
        # caption=f"Use {_cmd_txt} to see details for a log.  Logs lacking an id don\'t have details.",
    )


@app.command(short_help="Show interfering APs")
def interfering(
    start: str = typer.Option(None, help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    group: str = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    label: str = typer.Argument(None, metavar="[LABEL]",),  # autocompletion=cli.cache.group_completion),  # TODO cache labels
    site: str = typer.Argument(None, metavar="[SITE-NAME]", autocompletion=cli.cache.site_completion),
    # swarm: str = typer.Argument(None, metavar="[SWARM NAME or ID]", autocompletion=cli.cache.swarm_completion),  # TODO
    sort_by: str = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    central = cli.central
    cli.cache(refresh=update_cache)

    if group:
        group = cli.cache.get_group_identifier(group).name

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

    kwargs = {
        "from_timestamp": start,
        "to_timestamp": end,
        "group": group,
        "label": label,
        "site": site,
        # "swarm_id": swarm, TODO
    }

    resp = central.request(central.wids_get_interfering_aps, **kwargs)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Interfering APs",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by if not sort_by else sort_by.replace("_", " "),
        reverse=reverse,
        cleaner=cleaner.wids
        # cache_update_func=cli.cache.update_log_db if not verbose else None,
        # caption=f"Use {_cmd_txt} to see details for a log.  Logs lacking an id don\'t have details.",
    )


@app.command(short_help="Show Neighbor APs")
def neighbor(
    start: str = typer.Option(None, help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    group: str = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    label: str = typer.Argument(None, metavar="[LABEL]",),  # autocompletion=cli.cache.group_completion),  # TODO cache labels
    site: str = typer.Argument(None, metavar="[SITE-NAME]", autocompletion=cli.cache.site_completion),
    # swarm: str = typer.Argument(None, metavar="[SWARM NAME or ID]", autocompletion=cli.cache.swarm_completion),  # TODO
    sort_by: str = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    central = cli.central
    cli.cache(refresh=update_cache)

    if group:
        group = cli.cache.get_group_identifier(group).name

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

    kwargs = {
        "from_timestamp": start,
        "to_timestamp": end,
        "group": group,
        "label": label,
        "site": site,
        # "swarm_id": swarm, TODO
    }

    resp = central.request(central.wids_get_neighbor_aps, **kwargs)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Suspected Rogues",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by if not sort_by else sort_by.replace("_", " "),
        reverse=reverse,
        cleaner=cleaner.wids
        # cache_update_func=cli.cache.update_log_db if not verbose else None,
        # caption=f"Use {_cmd_txt} to see details for a log.  Logs lacking an id don\'t have details.",
    )


@app.command(short_help="Show Suspected Rogue APs")
def suspect(
    start: str = typer.Option(None, help="Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)",),
    end: str = typer.Option(None, help="End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)",),
    past: str = typer.Option(None, help="Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h"),
    group: str = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    label: str = typer.Argument(None, metavar="[LABEL]",),  # autocompletion=cli.cache.group_completion),  # TODO cache labels
    site: str = typer.Argument(None, metavar="[SITE-NAME]", autocompletion=cli.cache.site_completion),
    # swarm: str = typer.Argument(None, metavar="[SWARM NAME or ID]", autocompletion=cli.cache.swarm_completion),  # TODO
    sort_by: str = typer.Option(None, "--sort",),  # Uses post formatting field headers
    reverse: bool = typer.Option(
        True, "-r",
        help="Reverse Output order.",
        show_default=False
    ),
    verbose: bool = typer.Option(False, "-v", help="Show raw unformatted response (vertically)"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_table: bool = typer.Option(False, "--table", help="Output in table format",),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cli.cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    central = cli.central
    cli.cache(refresh=update_cache)

    if group:
        group = cli.cache.get_group_identifier(group).name

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

    kwargs = {
        "from_timestamp": start,
        "to_timestamp": end,
        "group": group,
        "label": label,
        "site": site,
        # "swarm_id": swarm, TODO
    }

    resp = central.request(central.wids_get_suspect_aps, **kwargs)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Suspected Rogues",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by if not sort_by else sort_by.replace("_", " "),
        reverse=reverse,
    )


@app.callback()
def callback():
    """
    Show Wireless Intrusion Detection data
    """
    pass


if __name__ == "__main__":
    app()
