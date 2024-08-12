#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import typer
import sys
from pathlib import Path
from typing import Literal, List


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, cleaner, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, cleaner, Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import iden_meta  # noqa
from centralcli.cache import CentralObject

app = typer.Typer()


def get_wids_response(
    func: str = Literal["rogue", "interfering", "suspect", "all"],
    device: str = None,
    group: List[str] = None,
    site: List[str] = None,
    label: List[str] = None,
    start: datetime = None,
    end: datetime = None,
    past: str = None,
) -> Response:
    if device:
        device: CentralObject = cli.cache.get_dev_identifier(dev_type="ap", swack=True)
    if group:
        group: List[str] = [cli.cache.get_group_identifier(g).name for g in group]
    if site:
        site: List[str] = [cli.cache.get_site_identifier(s).name for s in site]
    if label:
        label: List[str] = [cli.cache.get_label_identifier(_label).name for _label in label]

    start, end = cli.verify_time_range(start=start, end=end, past=past)

    kwargs = {
        "from_timestamp": None if not start else start.int_timestamp,
        "to_timestamp": None if not end else end.int_timestamp,
        "group": group,
        "label": label,
        "site": site,
        "swarm_id": None if not device else device.swack_id
    }

    if func == "all":
        func = getattr(cli.central, f"wids_get_{func}")
    else:
        func = getattr(cli.central, f"wids_get_{func}_aps")

    return cli.central.request(func, **kwargs)




@app.command()
def rogues(
    device: str = typer.Option(None, "-S", "--swarm", help="Show firmware for the swarm the provided AP belongs to", metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: List[str] = cli.options.group_many,
    site: List[str] = cli.options.site_many,
    label: List[str] = cli.options.label_many,
    verbose: int = cli.options.verbose,
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show Detected Rogue APs"""
    resp = get_wids_response("rogue", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Rogues",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.wids
    )


@app.command()
def interfering(
    device: str = typer.Option(None, "-S", "--swarm", help="Show firmware for the swarm the provided AP belongs to", metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: List[str] = cli.options.group_many,
    site: List[str] = cli.options.site_many,
    label: List[str] = cli.options.label_many,
    verbose: int = cli.options.verbose,
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show interfering APs"""
    resp = get_wids_response("interfering", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Interfering APs",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.wids
    )


@app.command()
def neighbor(
    device: str = typer.Option(None, "-S", "--swarm", help="Show firmware for the swarm the provided AP belongs to", metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: List[str] = cli.options.group_many,
    site: List[str] = cli.options.site_many,
    label: List[str] = cli.options.label_many,
    verbose: int = cli.options.verbose,
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show Neighbor APs"""
    resp = get_wids_response("neighbor", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Suspected Rogues",
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.wids
    )


@app.command()
def suspect(
    device: str = typer.Option(None, "-S", "--swarm", help="Show firmware for the swarm the provided AP belongs to", metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: List[str] = cli.options.group_many,
    site: List[str] = cli.options.site_many,
    label: List[str] = cli.options.label_many,
    verbose: int = cli.options.verbose,
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show Suspected Rogue APs"""
    resp = get_wids_response("suspect", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
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


@app.command()
def all(
    device: str = typer.Option(None, "-S", "--swarm", help="Show firmware for the swarm the provided AP belongs to", metavar=iden_meta.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: List[str] = cli.options.group_many,
    site: List[str] = cli.options.site_many,
    label: List[str] = cli.options.label_many,
    verbose: int = cli.options.verbose,
    start: datetime = cli.options.start,
    end: datetime = cli.options.end,
    past: str = cli.options.past,
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
    """Show All WIDS Classifications"""
    resp = get_wids_response("all", device=device, group=group, site=site, label=label, start=start, end=end, past=past)

    if resp.raw.get("_counts"):
        caption = f'Rogue APs: [cyan]{resp.raw["_counts"]["rogues"]}[/cyan] '
        caption += f'Suspected Rogue APs: [cyan]{resp.raw["_counts"]["suspect"]}[/] '
        caption += f'Interfering APs: [cyan]{resp.raw["_counts"]["interfering"]}[/] '
        caption += f'Neighbor APs: [cyan]{resp.raw["_counts"]["neighbor"]}[/]'
    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="WIDS Report (All classification types)",
        caption=caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
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
