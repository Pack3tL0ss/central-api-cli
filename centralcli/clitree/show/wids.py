#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Literal

import pendulum
import typer

from centralcli import cleaner, common, render
from centralcli.cache import CacheDevice, api
from centralcli.models.wids import Wids
from centralcli.response import Response

app = typer.Typer()


class WidsResponse:
    def __init__(self, wids_cat: Literal["rogue", "interfering", "suspect", "all"], response: Response, start: None | datetime = None, end: None | datetime = None,) -> None:
        self.response = response
        self.exit_code = 0 if response.ok else 1

        if response.ok:
            wids_model = Wids(response.output)
            self.response.output = wids_model.model_dump()
        if wids_cat == "all":
            self.caption = self.all_caption()
            self.exit_code = response.raw.get("_exit_code") or self.exit_code
        else:
            caption = common.get_time_range_caption(start, end, default="in past 3 hours.")
            self.caption = f"[cyan]{len(response)}[/] [medium_spring_green]{wids_cat.capitalize()}[/] AP{'s' if len(response) != 1 else ''} {caption}"


    def all_caption(self) -> str:
        caption = ""
        sections = ["rogue", "suspect", "interfering", "neighbor"]
        if self.response.raw.get("_counts"):
            for section in sections:
                if section in self.response.raw["_counts"]:
                    caption += f'{section.capitalize()} APs: [cyan]{self.response.raw["_counts"][section]}[/cyan] '

        caption = caption.strip()
        return caption or None

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
        device: CacheDevice = common.cache.get_dev_identifier(device, dev_type="ap", swack_only=True)
        if device.is_aos10:
            common.exit(f"[cyan]-S[/]|[cyan]--swarm[/] option only applies to [bright_green]AOS8[/] IAP.\n{device.summary_text} is an [red1]AOS10[/] AP.")
    if group:
        group: List[str] = [common.cache.get_group_identifier(g).name for g in group]
    if site:
        site: List[str] = [common.cache.get_site_identifier(s).name for s in site]
    if label:
        label: List[str] = [common.cache.get_label_identifier(_label).name for _label in label]

    if end and not start:
        start = end - pendulum.duration(hours=48)
    start, end = common.verify_time_range(start=start, end=end, past=past)

    kwargs = {
        "from_time": start,
        "to_time": end,
        "group": group,
        "label": label,
        "site": site,
        "swarm_id": None if not device else device.swack_id
    }

    if wids_cat == "all":
        func = api.rapids.wids_get_all
    else:
        func = getattr(api.rapids, f"wids_get_{wids_cat}_aps")

    return WidsResponse(wids_cat, response=api.session.request(func, **kwargs), start=start, end=end)


# Default Time-Range for all wids Endpoints is past 3 hours.
@app.command()
def rogues(
    device: str = common.options.swarm_device,
    group: List[str] = common.options.group_many,
    site: List[str] = common.options.site_many,
    label: List[str] = common.options.label_many,
    verbose: int = common.options.verbose,
    start: datetime = common.options.start,
    end: datetime = common.options.end,
    past: str = common.options.past,
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show Detected Rogue APs"""
    resp = get_wids_response("rogue", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    render.display_results(
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
    device: str = common.options.swarm_device,
    group: List[str] = common.options.group_many,
    site: List[str] = common.options.site_many,
    label: List[str] = common.options.label_many,
    verbose: int = common.options.verbose,
    start: datetime = common.options.start,
    end: datetime = common.options.end,
    past: str = common.options.past,
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show interfering APs"""
    resp = get_wids_response("interfering", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    render.display_results(
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
    device: str = common.options.swarm_device,
    group: List[str] = common.options.group_many,
    site: List[str] = common.options.site_many,
    label: List[str] = common.options.label_many,
    verbose: int = common.options.verbose,
    start: datetime = common.options.start,
    end: datetime = common.options.end,
    past: str = common.options.past,
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show Neighbor APs"""
    resp = get_wids_response("neighbor", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    render.display_results(
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
    device: str = common.options.swarm_device,
    group: List[str] = common.options.group_many,
    site: List[str] = common.options.site_many,
    label: List[str] = common.options.label_many,
    verbose: int = common.options.verbose,
    start: datetime = common.options.start,
    end: datetime = common.options.end,
    past: str = common.options.past,
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show Suspected Rogue APs"""
    resp = get_wids_response("suspect", device=device, group=group, site=site, label=label, start=start, end=end, past=past)
    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    render.display_results(
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
    device: str = common.options.swarm_device,
    group: List[str] = common.options.group_many,
    site: List[str] = common.options.site_many,
    label: List[str] = common.options.label_many,
    verbose: int = common.options.verbose,
    start: datetime = common.options.start,
    end: datetime = common.options.end,
    past: str = common.options.past,
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show All WIDS Classifications"""
    resp = get_wids_response("all", device=device, group=group, site=site, label=label, start=start, end=end, past=past)

    tablefmt = common.get_format(do_json, do_yaml, do_csv, do_table, default="rich" if not verbose else "yaml")

    render.display_results(
        resp.response,
        tablefmt=tablefmt,
        title="WIDS Report (All classification types)",
        caption=resp.caption,
        pager=pager,
        exit_on_fail=False,
        outfile=outfile,
        sort_by=sort_by,
        reverse=reverse,
        cleaner=cleaner.wids,
    )
    common.exit(code=resp.exit_code)


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context,
    device: str = common.options.swarm_device,
    group: List[str] = common.options.group_many,
    site: List[str] = common.options.site_many,
    label: List[str] = common.options.label_many,
    verbose: int = common.options.verbose,
    start: datetime = common.options.start,
    end: datetime = common.options.end,
    past: str = common.options.past,
    sort_by: str = common.options.sort_by,
    reverse: bool = common.options.reverse,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """
    Show Wireless Intrusion Detection data
    """
    # We run show wids all if they don't provide a subcommand.
    if not ctx.invoked_subcommand:
        ctx.invoked_subcommand = "all"
        ctx.invoke(all, **ctx.params)


if __name__ == "__main__":
    app()  # pragma: no cover
