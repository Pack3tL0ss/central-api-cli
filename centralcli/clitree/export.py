#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import typer
import json
from rich import print
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

from centralcli import cli, log, BatchRequest, caas, config, render
from centralcli.cache import CacheDevice
from centralcli.classic.api import ClassicAPI

if TYPE_CHECKING:
    from ..cache import CacheGroup, CacheSite, CacheDevice

app = typer.Typer()
console = Console(emoji=False)

def _config_header(header_text: str, console: Console = None) -> None:
    console = console or Console()
    console.rule()
    console.print(header_text)
    console.rule()

@app.command()
def configs(
    group: str = cli.options.get("group", help="Export device level configs for a specific Group",),
    site: str = cli.options.get("site", help="Export device level configs for a specific Site",),
    do_gw: bool = typer.Option(None, "--gw", help="Export gateway configs."),
    do_ap: bool = typer.Option(None, "--ap", help="Export AP configs."),
    do_cx: bool = typer.Option(None, "--cx", help="Export CX templates. [dim italic](export not available for CX UI group config)[/]"),
    do_sw: bool = typer.Option(None, "--sw", help="Export AOS-SW templates. [dim italic](export not available for AOS-SW UI group config)[/]"),
    do_variables: bool = typer.Option(None, "-V", "--variables", help="Export variables associated with devices in Template Groups.", show_default=False,),
    do_switch: bool = typer.Option(None, "--switch", help="Export both CX and AOS-SW templates. [dim italic](export not available for switch UI group config)[/]"),
    groups_only: bool = typer.Option(None,"-G",  "--groups-only", help="Export Group level configs only, not device level configs."),
    ap_env: bool = typer.Option(False, "-e", "--env", help="Export AP environment settings.  All ap-env settings are exported to a single file. [italic dim]Valid for APs only[/]", show_default=False,),
    show: bool = typer.Option(False, "-s", "--show", help=f"Display configs to terminal along with exporting to filesystem.  {cli.help_block('Display only export progress')}"),
    outdir: Path = typer.Option(None, "-D", "--dir", help=f"Specify custom output dir.  {cli.help_block(str(config.export_dir))}", show_default=False,),
    flat: bool = typer.Option(False, "-F", "--flat", help=f"place all configs in root of output directory {cli.help_block('Configs are exported to subfolders GROUP/DEV_TYPE/')}", show_default=False,),
    group_match: str = typer.Option(None, "--match", help="Export Configs for groups and devices where the associated group contains the provided text", show_default=False,),
    refresh: bool = typer.Option(False, "-R", "--refresh", help="Only applies if device configs are being exported. By default configs are pulled for devices in the cache.  Use this option to update the device cache prior to the export.", show_default=False,),
    yes: bool = cli.options.yes,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    workspace: str = cli.options.workspace,
) -> None:
    """Export configs in mass.

    Collect Group and device level configs for APs, and gateways.

    Can filter by group and/or site along with device type [cyan]--ap[/] [cyan]--gw[/]
    Use [cyan]-e[/]|[cyan]--env[/] to also export per-ap-settings/ap-env for all APs

    [italic]With no filters all device and group level configs will be exported (APs and Gateways).
    [yellow3]:information:[/]  [yellow]Switches will export only defined templates.  UI/multi-edit is not supported.[/yellow][/italic]

    Configs will be exported to [cyan]cencli-config-export[/] with subfolders for each group, then device type.

    [red]:warning:[/]  This command can result in a lot of API calls.
    """
    br = BatchRequest
    console = Console(emoji=False)
    caasapi = caas.CaasAPI()
    api = ClassicAPI()
    gw_reqs, ap_reqs, ap_env_reqs, gw_grp_reqs, ap_grp_reqs, aps, gws, ap_groups, gw_groups, ap_template_reqs = [], [], [], [], [], [], [], [], [], []

    if do_switch:
        do_cx = True
        do_sw = True

    # Default to all device types if none are specified
    if not any([do_gw, do_ap, do_cx, do_sw]):
        do_ap, do_gw, do_cx, do_sw = True, True, True, True

    group: CacheGroup = None if not group else cli.cache.get_group_identifier(group)
    site: CacheSite = None if not site else cli.cache.get_site_identifier(site)
    outdir = outdir or config.export_dir

    template_db = True if any([do_cx, do_sw, do_switch]) else False

    if groups_only and refresh:
        log.warning("ignoring [cyan]-R[/]|[cyan]--refresh[/].  Device Cache refresh is not necessary when doing [cyan]-G[/]|[cyan]--groups-only[/] export.", show=True)

    dev_types = [] if not do_ap else ["ap"]
    if do_gw:
        dev_types += ["gw"]
    dev_types = dev_types or None
    # We don't need to update switches we only support fetching templates which does not require device cache

    _ = cli.cache.check_fresh(dev_db=refresh and not groups_only, template_db=template_db, group_db=True, dev_type=dev_types)

    if do_ap:
        ap_groups = [group["name"] for group in cli.cache.groups if "ap" in group["allowed_types"] and not group["wlan_tg"] and group.get("cnx") is not True and group["name"] != "default"]
    if do_gw:
        gw_groups = [group["name"] for group in cli.cache.groups if "gw" in group["allowed_types"] and group.get("cnx") is not True and group["name"] != "default"]

    # build device level ap/gw config requests
    if not groups_only:
        if do_gw:
            gws: List[CacheDevice] = [CacheDevice(d) for d in cli.cache.devices if d["type"] == "gw" and (not group or d["group"] == group.name) and (not site or d["site"] == site.name)]

            if gws:
                if group_match:
                    gws = [gw for gw in gws if group_match in gw.group]
                gw_reqs = [br(caasapi.show_config, d.group, d.mac) for d in gws]

        if do_ap:
            aps: List[CacheDevice] = [CacheDevice(d) for d in cli.cache.devices if d["type"] == "ap" and (not group or d["group"] == group.name) and (not site or d["site"] == site.name) and d["group"] in ap_groups]

            if aps:
                if group_match:
                    aps = [ap for ap in aps if group_match in ap.group]
                ap_reqs = [br(api.configuration.get_ap_config, d.swack_id) for d in aps]

                if ap_env:
                    ap_env_reqs = [br(api.configuration.get_per_ap_config, d.serial) for d in aps]

    # build group level ap/gw config requests
    if gw_groups:
        if group_match:
            gw_groups = [group for group in gw_groups if group_match in group]

        gw_grp_reqs = [br(caasapi.show_config, group) for group in gw_groups]

    if ap_groups:
        if group_match:
            ap_groups = [group for group in ap_groups if group_match in group]

        ap_grp_reqs = [br(api.configuration.get_ap_config, group) for group in ap_groups]

    # build template requests
    ap_template_reqs = {} if not do_ap else {
        f'{t["group"]}~|~{t["name"]}': br(api.configuration.get_template, group=t["group"], template=t["name"])
        for t in cli.cache.templates if t["device_type"] == "ap" and (not group or t["group"] == group.name) and (not site or t["site"] == site.name) and (not group_match or group_match in t["group"])
        }
    cx_template_reqs = {} if not do_cx else {
        f'{t["group"]}~|~{t["name"]}': br(api.configuration.get_template, group=t["group"], template=t["name"])
        for t in cli.cache.templates if t["device_type"] == "cx" and (not group or t["group"] == group.name) and (not site or t["site"] == site.name) and (not group_match or group_match in t["group"])
        }
    sw_template_reqs = {} if not do_sw else {
        f'{t["group"]}~|~{t["name"]}': br(api.configuration.get_template, group=t["group"], template=t["name"])
        for t in cli.cache.templates if t["device_type"] == "sw" and (not group or t["group"] == group.name) and (not site or t["site"] == site.name) and (not group_match or group_match in t["group"])
        }

    req_cnt = len(gw_reqs) + len(ap_reqs) + len(ap_env_reqs) + len(gw_grp_reqs) + len(ap_grp_reqs) + len(ap_template_reqs) + len(cx_template_reqs) + len(sw_template_reqs)
    req_cnt = req_cnt if not do_variables else req_cnt + 1
    if req_cnt == 0:
        cli.exit("No exports based on provided filtering options.  Nothing to do")

    print(f"Minimum of {req_cnt} additional API calls will be performed to fetch requested configs.")
    print(f"Files will be exported to {outdir}")
    if outdir.exists():
        print("[red]:warning:[/]  Any existing configs for the same device will be overwritten")
    cli.confirm(yes)

    if gw_grp_reqs:
        gw_grp_res = api.session.batch_request(gw_grp_reqs)

        for g, r in zip(gw_groups, gw_grp_res):
            if not r.ok:
                error = f"Failed to retrieve Group level gateway configuration for group [cyan]{g}[/]... {r.error}"
                log.error(error, show=True)
                continue
            if isinstance(r.output, dict) and "config" in r.output:
                r.output = r.output["config"]

            _outdir: Path = outdir if flat else outdir / g / "gateways"
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / "group.cfg" if not flat else _outdir / f"{g}_gw_group.cfg"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]Gateway group level config for [cyan]{g}[/] group[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if ap_grp_reqs:
        ap_grp_res = api.session.batch_request(ap_grp_reqs)

        for g, r in zip(ap_groups, ap_grp_res):
            if not r.ok:
                log.error(f"Failed to retrieve Group level AP configuration for group [cyan]{g}[/]... {r.error}", show=True)
                continue

            _outdir = outdir if flat else outdir/ g / "aps"
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / "group.cfg" if not flat else _outdir / f"{g}_ap_group.cfg"

            if not show:
                outdata = render.output(r.output, tablefmt="simple")
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]AP group level config for [cyan]{g}[/] group[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if gw_reqs:
        gw_res = api.session.batch_request(gw_reqs)

        for d, r in zip(gws, gw_res):
            if not r.ok:
                log.error(f"Failed to retrieve configuration for {d.name}... {r.error}", show=True)
                continue
            if isinstance(r.output, dict) and "config" in r.output:
                r.output = r.output["config"]

            _outdir = outdir / d.group / "gateways" if not flat else outdir
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{d.name}_dev.cfg"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]Config for {d.rich_help_text}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if ap_reqs:
        ap_res = api.session.batch_request(ap_reqs)

        for d, r in zip(aps, ap_res):
            if not r.ok:
                log.error(f"Failed to retrieve configuration for {d.name}... {r.error}", show=True)
                continue

            _outdir = outdir / d.group / "aps" if not flat else outdir
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{d.name}_dev.cfg"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]Config for {d.rich_help_text}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

        if ap_env_reqs:
            ap_env_res = api.session.batch_request(ap_env_reqs)

            console = Console(force_terminal=False, emoji=False)
            with console.capture() as cap:
                for d, r in zip(aps, ap_env_res):
                    if not r.ok:
                        log.error(f"Failed to retrieve per-ap-settings for {d.name}... {r.error}", show=True)
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

    if ap_template_reqs:
        ap_template_resp = api.session.batch_request(list(ap_template_reqs.values()))

        for (group, name), r in zip(map(lambda k: k.split("~|~"), ap_template_reqs.keys()), ap_template_resp):
            if not r.ok:
                log.error(f"Failed to retrieve template contents for AP template: {name} in group {group}... {r.error}", show=True)
                continue

            _outdir = outdir / group / "aps" if not flat else outdir
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{name}.cen" if not flat else _outdir / f"{group}_{name}_ap.cen"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]AP Template Group: {group}, Name: {name}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if cx_template_reqs:
        cx_template_resp = api.session.batch_request(list(cx_template_reqs.values()))

        for (group, name), r in zip(map(lambda k: k.split("~|~"), cx_template_reqs.keys()), cx_template_resp):
            if not r.ok:
                log.error(f"Failed to retrieve template contents for CX template: {name} in group {group}... {r.error}", show=True)
                continue

            _outdir = outdir / group / "switch" if not flat else outdir
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{name}.cen" if not flat else _outdir / f"{group}_{name}_cx.cen"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]CX Template Group: {group}, Name: {name}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if sw_template_reqs:
        sw_template_resp = api.session.batch_request(list(sw_template_reqs.values()))

        for (group, name), r in zip(map(lambda k: k.split("~|~"), sw_template_reqs.keys()), sw_template_resp):
            if not r.ok:
                log.error(f"Failed to retrieve template contents for AOS-SW template: {name} in group {group}... {r.error}", show=True)
                continue

            _outdir = outdir / group / "switch" if not flat else outdir
            _outdir.mkdir(parents=True, exist_ok=True)
            outfile = _outdir / f"{name}.cen" if not flat else _outdir / f"{group}_{name}_sw.cen"

            if not show:
                outdata = render.output(r.output)
                cli.write_file(outfile, outdata.file)
            else:
                _config_header(f"[bold]AOS-SW Template Group: {group}, Name: {name}[reset]")
                cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)

    if do_variables:  # This block will exit on failure, will need to be changed if more is added below
        variable_resp = api.session.request(api.configuration.get_variables)
        if not variable_resp.ok:
            log.error(f"Failed to retrieve variables... {variable_resp.error}", show=True)
            cli.display_results(variable_resp, tablefmt="action", exit_on_fail=True)
            cli.cache.get_dev_identifier()

        _outdir = outdir
        outfile = _outdir / "variables.json"

        if not show:
            outdata = json.dumps(variable_resp.output, indent=2)
            cli.write_file(outfile, outdata)
        else:
            _config_header("[bold]Combined Variables file[reset]")
            cli.display_results(r, tablefmt=None, pager=pager, outfile=outfile)





@app.callback()
def callback():
    """
    Collect configs in mass
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
