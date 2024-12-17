#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import typer
from rich import print
from rich.markup import escape
from rich.console import Console
from typing import List, TYPE_CHECKING

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, log, BatchRequest, caas, config, render
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log, BatchRequest, caas, config, render
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import iden_meta
from .cache import CacheDevice

if TYPE_CHECKING:
    from .cache import CacheGroup, CacheSite

app = typer.Typer()
console = Console(emoji=False)

def _config_header(header_text: str, console: Console = None) -> None:
    console = console or Console()
    console.rule()
    console.print(header_text)
    console.rule()

@app.command()
def configs(
    group: str = typer.Option(
        None,
        metavar=f"{iden_meta.group}",
        autocompletion=cli.cache.group_completion,
        help = "Export device level configs for a specific Group",
        show_default=False,
    ),
    site: str = typer.Option(
        None,
        metavar=f"{iden_meta.site}",
        autocompletion=cli.cache.site_completion,
        help = "Export device level configs for a specific Site",
        show_default=False,
    ),
    do_gw: bool = typer.Option(None, "--gw", help="Export gateway configs."),
    do_ap: bool = typer.Option(None, "--ap", help="Export AP configs."),
    ap_env: bool = typer.Option(False, "-e", "--env", help="Export AP environment settings.  All ap-env settings are exported to a single file. [italic grey62]Valid for APs only[/]", show_default=False,),
    show: bool = typer.Option(False, "-s", "--show", help=f"Display configs to terminal along with exporting to filesystem.  [grey62]{escape('[default: Display only export progress]')}[/]"),
    yes: bool = cli.options.yes,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Export configs in mass.

    Collect Group and device level configs for APs, and gateways.

    Can filter by group and/or site along with device type [cyan]--ap[/] [cyan]--gw[/]
    Use [cyan]-e[/]|[cyan]--env[/] to also export per-ap-settings/ap-env for all APs

    [italic]With no filters all device and group level configs will be exported (supported on APs and Gateways)[/]

    Configs will be exported to [cyan]cencli-config-export[/] with subfolders for each group, then device type.

    [red]:warning:[/]  Can result in a lot of API calls.
    """
    if not do_ap and not do_gw:
        do_ap = do_gw = True  # Fetch configs for both
    group: CacheGroup = None if not group else cli.cache.get_group_identifier(group)
    site: CacheSite = None if not site else cli.cache.get_site_identifier(site)

    # if they are already in export dir navigate back to top for output
    outdir: Path = config.outdir / "cencli-config-export"
    if "cencli-config-export" in outdir.parent.parts[1:]:
        outdir = outdir.parent
        while outdir.name != "cencli-config-export":
            outdir = outdir.parent

    br = BatchRequest
    console = Console(emoji=False)
    caasapi = caas.CaasAPI(central=cli.central)
    gw_reqs, ap_reqs, ap_env_reqs, gw_grp_reqs, ap_grp_reqs = [], [], [], [], []

    if do_gw:
        gws: List[CacheDevice] = [CacheDevice(d) for d in cli.cache.devices if d["type"] == "gw" and (not group or d["group"] == group.name) and (not site or d["site"] == site.name)]

        if gws:
            gw_reqs = [br(caasapi.show_config, d.group, d.mac) for d in gws]

    if do_ap:
        aps: List[CacheDevice] = [CacheDevice(d) for d in cli.cache.devices if d["type"] == "ap" and (not group or d["group"] == group.name) and (not site or d["site"] == site.name)]

        if aps:
            ap_reqs = [br(cli.central.get_ap_config, d.swack_id) for d in aps]

            if ap_env:
                ap_env_reqs = [br(cli.central.get_per_ap_config, d.serial) for d in aps]

    gw_groups = [] if not gws else list(set([d.group for d in gws]))
    ap_groups = [] if not aps else list(set([d.group for d in aps]))

    if gw_groups:
        gw_grp_reqs = [br(caasapi.show_config, group) for group in gw_groups]

    if ap_groups:
        ap_grp_reqs = [br(cli.central.get_ap_config, group) for group in ap_groups]

    req_cnt = len(gw_reqs) + len(ap_reqs) + len(ap_env_reqs) + len(gw_grp_reqs) + len(ap_grp_reqs)
    print(f"{req_cnt} API calls will be performed to fetch requested configs.")
    print(f"Files will be exported to {outdir}")
    print("[red]:warning:[/]  Any existing configs for the same device will be overwritten")
    if cli.confirm(yes):
        ...  # aborted above if they don't confirm

    if gw_grp_reqs:
        gw_grp_res = cli.central.batch_request(gw_grp_reqs)

        for g, r in zip(gw_groups, gw_grp_res):
            if not r.ok:
                error = f"Failed to retrieve Group level gateway configuration for group [cyan]{g}[/]... {r.error}"
                log.error(error, caption=True)
                continue
            if isinstance(r.output, dict) and "config" in r.output:
                r.output = r.output["config"]

            _outdir: Path = outdir / g / "gateways"
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / "group.cfg"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]Gateway group level config for [cyan]{g}[/] group[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if ap_grp_reqs:
        ap_grp_res = cli.central.batch_request(ap_grp_reqs)

        for g, r in zip(ap_groups, ap_grp_res):
            if not r.ok:
                log.error(f"Failed to retrieve Group level AP configuration for group [cyan]{g}[/]... {r.error}", caption=True)
                continue

            _outdir = outdir / g / "aps"
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / "group.cfg"

            if not show:
                outdata = render.output(r.output, tablefmt="simple")
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]AP group level config for [cyan]{g}[/] group[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if gw_reqs:
        gw_res = cli.central.batch_request(gw_reqs)

        for d, r in zip(gws, gw_res):
            if not r.ok:
                log.error(f"Failed to retrieve configuration for {d.name}... {r.error}", caption=True)
                continue
            if isinstance(r.output, dict) and "config" in r.output:
                r.output = r.output["config"]

            _outdir = outdir / d.group / "gateways"
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{d.name}_dev.cfg"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]Config for {d.rich_help_text}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if ap_reqs:
        ap_res = cli.central.batch_request(ap_reqs)

        for d, r in zip(aps, ap_res):
            if not r.ok:
                log.error(f"Failed to retrieve configuration for {d.name}... {r.error}", caption=True)
                continue

            _outdir = outdir / d.group / "aps"
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{d.name}_dev.cfg"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]Config for {d.rich_help_text}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

        if ap_env_reqs:
            ap_env_res = cli.central.batch_request(ap_env_reqs)

            console = Console(force_terminal=False, emoji=False)
            with console.capture() as cap:
                for d, r in zip(aps, ap_env_res):
                    if not r.ok:
                        log.error(f"Failed to retrieve per-ap-settings for {d.name}... {r.error}", caption=True)
                        continue
                    console.rule()
                    console.print(f"[bold]AP env for {d.rich_help_text}[reset]")
                    console.rule()
                    console.print("\n".join(r.output))

            outfile = outdir / "ap_env.txt"
            res = sorted([r for r in ap_env_res if r.ok], key=lambda r: r.rl)[0]
            res.output = cap.get()

            if not show:
                cli.write_file(outfile, res.output)
            else:
                cli.display_results(res, tablefmt=None, pager=pager, outfile=outfile)


@app.callback()
def callback():
    """
    Collect configs in mass
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
