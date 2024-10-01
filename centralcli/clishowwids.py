#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

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
from centralcli.objects import DateTime
from centralcli.models import Wids

app = typer.Typer()


class WidsResponse:
    def __init__(self, wids_cat: Literal["rogue", "interfering", "suspect", "all"], response: Response, start: None | datetime = None, end: None | datetime = None,) -> None:
        self.response = response
        if response.ok:
            wids_model = Wids(response.output)
            self.response.output = wids_model.model_dump()
        if wids_cat == "all":
            self.caption = self.all_caption()
        else:
            if not end:
                caption = "in past 3 hours." if not start else f"in {DateTime(start.timestamp(), 'timediff-past')}"
            else:
                caption = f"from {DateTime(start.timestamp(), 'mdyt')} to {DateTime(end.timestamp(), 'mdyt')}"
                # TODO most other time-frame captions don't handle end (show alerts...)

            self.caption = f"[cyan]{len(response)} {wids_cat} AP{'s' if len(response) > 1 else ''} {caption}[/]"


    def all_caption(self) -> str:
        caption = None
        if self.response.raw.get("_counts"):
            caption = f'Rogue APs: [cyan]{self.response.raw["_counts"]["rogues"]}[/cyan] '
            caption += f'Suspected Rogue APs: [cyan]{self.response.raw["_counts"]["suspect"]}[/] '
            caption += f'Interfering APs: [cyan]{self.response.raw["_counts"]["interfering"]}[/] '
            caption += f'Neighbor APs: [cyan]{self.response.raw["_counts"]["neighbor"]}[/]'

        return caption

def get_wids_response(
    wids_cat: Literal["rogue", "interfering", "suspect", "all"],
    device: str = None,
    group: List[str] = None,
    site: List[str] = None,
    label: List[str] = None,
    start: datetime = None,
    end: datetime = None,
    past: str = None,
) -> WidsResponse:
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
        "from_time": start,
        "to_time": end,
        "group": group,
        "label": label,
        "site": site,
        "swarm_id": None if not device else device.swack_id
    }

    if wids_cat == "all":
        func = cli.central.wids_get_all
    else:
        func = getattr(cli.central, f"wids_get_{wids_cat}_aps")

    return WidsResponse(wids_cat, response=cli.central.request(func, **kwargs), start=start, end=end)


# Default Time-Range for all wids Endpoints is past 3 hours.
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
        resp.response,
        tablefmt=tablefmt,
        title="Rogues",
        caption=resp.caption,
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
        resp.response,
        tablefmt=tablefmt,
        title="Interfering APs",
        caption=resp.caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.wids
    )


@app.command()
def neighbors(
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
        resp.response,
        tablefmt=tablefmt,
        title="Suspected Rogues",
        caption=resp.caption,
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
        resp.response,
        tablefmt=tablefmt,
        title="Suspected Rogues",
        caption=resp.caption,
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

    tablefmt = cli.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    cli.display_results(
        resp.response,
        tablefmt=tablefmt,
        title="WIDS Report (All classification types)",
        caption=resp.caption,
        pager=pager,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.wids,
    )


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    Show Wireless Intrusion Detection data
    """
    # We run show wids all if they don't provide a subcommand.
    if not ctx.invoked_subcommand:
        ctx.invoked_subcommand = "all"
        kwargs = {
            "device": None,
            "group": None,
            "site": None,
            "label": None,
            "verbose": 0,
            "start": None,
            "end": None,
            "past": None,
            "sort_by": None,
            "reverse": None,
            "do_json": None,
            "do_yaml": None,
            "do_csv": None,
            "do_table": None,
            "raw": False,
            "outfile": None,
            "pager": False,
            "debug": False,
            "default": None,
            "account": cli.account,
        }
        ctx.invoke(all, **kwargs)


if __name__ == "__main__":
    app()
