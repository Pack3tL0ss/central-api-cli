#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import typer
from rich import print
from rich.console import Console
from rich.markup import escape

from centralcli import api_clients, cache, cleaner, common, config, log, render, utils
from centralcli.client import BatchRequest
from centralcli.constants import BatchRenameArgs, GroupDevTypes, iden_meta, possible_sub_keys
from centralcli.environment import env_var
from centralcli.response import Response
from rich.text import Text

from . import add, delete, examples, update

try:
    import readline  # noqa imported for backspace support during prompts.
except Exception:  # pragma: no cover
    pass

app = typer.Typer()
app.add_typer(delete.app, name="delete",)
app.add_typer(add.app, name="add",)
app.add_typer(update.app, name="update",)
api = api_clients.classic


class FstrInt:  # pragma: no cover requires tty
    def __init__(self, val: int) -> None:
        self.i = val
        self.o = val + 1

    def __len__(self):
        return len(str(self.i))


def _get_full_int(val: list[str]) -> FstrInt:  # pragma: no cover requires tty
    rv = []
    while True:
        for i in val:
            if i.isdigit():
                rv += [i]
            else:
                return FstrInt(int("".join(rv)) - 1)


def _lldp_rename_get_fstr():  # pragma: no cover requires tty
    rtxt = "[bright_blue]RESULT: [/bright_blue]"
    point_txt = "[bright_blue]-->[/bright_blue]"
    lldp_rename_text = f"""
[bright_green]Auto rename APs based on LLDP:[/]

[bold cyan]This function will automatically rename APs based on a combination of
information from the upstream switch (via LLDP) and from the AP itself.[/]

[cyan]Use the following field indicators:[reset]
    %h: switch hostname
    %m: AP MAC
    %p: switch port
    %M: AP model
    %S: site
    %s: AP serial

[cyan]Values used in the examples below:[/]
    switch hostname (%h): 'SNAN-IDF3-sw1'
    switch port (%p): 7
    AP mac (%m): aa:bb:cc:dd:ee:ff
    AP model (%M): 655
    site (%S): WadeLab
    [italic]Note: serial (%s) not shown as examples but follow same format.[/]

[bold bright_green]Format String Syntax:[/]
    '%h[1:2]'  will use the first 2 characters of the switches hostname.
    {rtxt} 'SN'
    '%h[2:4]'  will use characters 2 through 4 of the switches hostname.
    {rtxt} 'NAN'
    '%h-1'  will split the upstream switches hostname into parts separating on '-' and use
            the firt segment.
    {rtxt} 'SNAN
    '%p'  represents the interface.
    {rtxt} '7'
    '%p/3'  seperates the port string on / and uses the 3rd segment.
    {rtxt} (given port 1/1/7): '7'
    '%M'  represents the the AP model.
    {rtxt} '655'
    '%m[-4]'  The last 4 digits of the AP MAC
    [italic]NOTE: delimiters ':' are stripped from MAC[/]
    {rtxt} 'eeff'

[bold bright_green]Examples:[/]
    %h-1-AP%M-%m[-4]           {point_txt} [cyan]SNAN-AP535-eeff[/]
    %h[1-4]-%h-2%h-3.p%p.%M-ap {point_txt} [cyan]SNAN-IDF3sw1.p7.535-ap[/]
    %S-%h-1-%M-%m[-4]-ap       {point_txt} [cyan]WadeLab-SNAN-655-eeff-ap[/]
    %h-1-%M.%m[-4]-ap          {point_txt} [cyan]SNAN-535.eeff-ap[/]

[italic bright_red]Note:[/][italic] Automation will only apply to APs that are [bright_green]Up[/].
[italic]Use[/] [cyan]'cencli show aps --down'[/] to see APs that were excluded.
    """
    while True:
        print(lldp_rename_text)
        fstr = render.ask("Enter Desired format string",)
        if "%%" in fstr:
            typer.clear()
            print(f"\n[cyan]{fstr}[/] appears to be invalid.  Should never be 2 consecutive '%'.")
        else:
            return fstr


# TODO use get_topo_for_site similar to show aps -n  single call can get neigbor detail for all aps
def _get_lldp_dict(ap_dict: dict[str, dict[str, Any]]) -> dict:  # pragma: no cover requires tty
    """Updates provided dict of APs keyed by AP serial number with lldp neighbor info
    """
    br = BatchRequest
    out = {}

    sites = list(set([ap["site"] for ap in ap_dict.values() if ap.get("site")]))
    cache_sites = [common.cache.get_site_identifier(s) for s in sites]
    topo_reqs = [br(api.topo.get_topo_for_site, s.id) for s in cache_sites]
    if topo_reqs:
        topo_resp = api.session.batch_request(topo_reqs)

        if not all(r.ok for r in topo_resp):
            log.error("Error occured while gathering site topo info", show=True)
            render.display_results(topo_resp, exit_on_fail=True)

        topo_aps = {dev["serial"]: dev for r in topo_resp if r.ok for dev in r.output["devices"] if dev["role"] == "IAP"}
        ap_connections = {edge["toIf"]["serial"]: edge for r in topo_resp if r.ok for edge in r.output["edges"] if edge["toIf"]["serial"] in topo_aps}
        out = {serial: {**ap_data, "neighborHostName": ap_connections[serial]["fromIf"]["deviceName"], "remotePort": ap_connections[serial]["fromIf"]["name"]} for serial, ap_data in ap_dict.items() if serial in ap_connections}

    # Any APs that lack a site or lack upstream device info from topo API ... need to fetch neighbor per AP
    lldp_reqs = [br(api.topo.get_ap_lldp_neighbor, serial) for serial in ap_dict if serial not in out]
    if lldp_reqs:
        lldp_resp = api.session.batch_request(lldp_reqs)

        if not all(r.ok for r in lldp_resp):
            log.error("Error occured while gathering lldp neighbor info", show=True)
            render.display_results(lldp_resp, exit_on_fail=True)

        _unlistified_output: list[dict[str, Any]] = [d for r in lldp_resp for d in r.output]
        lldp_dict = {d["serial"]: {k: v for k, v in d.items()} for d in _unlistified_output}
        by_ap_dict = {
            serial: {
                **ap_data,
                "neighborHostName": lldp_dict[serial]["neighborHostName"],
                "remotePort": lldp_dict[serial]["remotePort"],
            }
            for serial, ap_data in ap_dict.items() if serial in lldp_dict
        }
        out = {**out, **by_ap_dict}

    return out


def get_lldp_names(fstr: str, default_only: bool = False, lower: bool = False, space: str = None, **kwargs) -> list[dict[str, str]]:  # pragma: no cover requires tty
    need_lldp = False if "%h" not in fstr and "%p" not in fstr else True
    space = "_" if space is None else space
    # TODO get all APs then filter down after, stash down aps for easy subsequent call
    resp = api.session.request(api.monitoring.get_devices, "aps", status="Up", **kwargs)

    if not resp:
        render.display_results(resp, exit_on_fail=True)
    elif not resp.output:
        filters = ", ".join([f"{k}: {v}" for k, v in kwargs.items()])
        render.display_results(resp)
        common.exit(f"No Up APs found matching provided filters ({filters}).")

    _all_aps = utils.listify(resp.output)
    _keys = ["name", "macaddr", "model", "site", "serial"]
    if not default_only:
        ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps}
    else:
        ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps if d["name"] == d["macaddr"]}
        if not ap_dict:
            common.exit("No Up APs found with default name.  Nothing to rename.")

    fstr_to_key = {
        "h": "neighborHostName",
        "m": "mac",
        "p": "remotePort",
        "M": "model",
        "S": "site",
        "s": "serial"
    }

    data, shown_prompt = [], False
    if not ap_dict:
        common.exit("Something went wrong, no ap_dict provided or empty")

    num_calls = len(ap_dict) * 2
    if need_lldp:
        topo_calls = len(set([ap["site"] for ap in ap_dict.values() if ap.get("site")]))
        per_ap_calls = len([ap for ap in ap_dict.values() if not ap.get("site")])
        lldp_calls = topo_calls + per_ap_calls
        num_calls += lldp_calls

    if len(ap_dict) > 5:
        _warn = "\n\n[dark_orange3]:warning:[/]  [blink bright_red blink]WARNING[reset]"
        if need_lldp:
            _warn = f"{_warn} Format provided requires details about the upstream switch.\n"
            _warn = f"{_warn} Best case... This automation will result in [cyan]{num_calls}[/] API calls.\n\n"
            _warn = f"{_warn} Minimum [cyan]{lldp_calls}[/] to gather details about the upstream switches.\n"
            _warn = f"{_warn} [dim italic]Could be more. If topo API doesn't have data for an AP (fallback is to make call per AP when topo API lack upstream details)[/]\n\n"
            _warn = f"{_warn} The remaining operations require 2 calls per AP:\n"
        else:
            _warn = f"{_warn} This automation will result in [cyan]{num_calls}[/] API calls, 2 for each AP.\n"
        _warn = f"{_warn} 1 to get the aps current settings (all settings need to be provided during the update, only the name changes).\n"
        _warn = f"{_warn} 1 to Update the settings / rename the AP.\n"
        _warn = f"{_warn}\n Current daily quota: [bright_green]{resp.rl.remain_day}[/] calls remaining\n"

        print(_warn)
        if resp.rl.remain_day < num_calls:
            print(f"  {resp.rl}")
            print(f"  More calls required {num_calls} than what's remaining in daily quota {resp.rl.remain_day}.")

        render.confirm()

    if need_lldp:
        ap_dict = _get_lldp_dict(ap_dict)

    # TODO refactor and use a template string or j2 something should already exist for this stuff.
    for ap in ap_dict:
        ap_dict[ap]["mac"] = utils.Mac(ap_dict[ap]["mac"]).clean
        while True:
            st = 0
            x = ''
            try:
                for idx, c in enumerate(fstr):
                    if not idx >= st:
                        continue
                    if c == '%':
                        if fstr[idx + 1] not in fstr_to_key.keys():
                            _e1 = typer.style(
                                    f"Invalid source specifier ({fstr[idx + 1]}) in format string {fstr}: ",
                                    fg="red"
                            )
                            _e2 = "Valid values:\n{}".format(
                                ", ".join(fstr_to_key.keys())
                            )
                            typer.echo(f"{_e1}\n{_e2}")
                            raise KeyError(f"{fstr[idx + 1]} is not valid")

                        _src = ap_dict[ap][fstr_to_key[fstr[idx + 1]]]
                        if fstr[idx + 2] != "[":
                            if fstr[idx + 2] == "%" or fstr[idx + 3] == "%":
                                x = f'{x}{_src}'
                                st = idx + 2
                            elif fstr[idx + 2:idx + 4] == "((":
                                # +3 should also be (
                                _from = fstr[idx + 4]
                                _to = fstr[idx + 6]

                                if not fstr[idx + 5] == ",":
                                    typer.secho(
                                        f"expected a comma at character {idx + 1 + 5} but found {fstr[idx + 5]}\n"
                                        "will try to proceed.", fg="bright_red"
                                    )

                                if not fstr[idx + 7:idx + 9] == "))":
                                    typer.secho(
                                        f"expected a )) at characters {idx + 1 + 7}-{idx + 1 + 8} "
                                        f"but found {fstr[idx + 7]}{fstr[idx + 8]}\n"
                                        "will try to proceed.", fg="bright_red"
                                    )

                                x = f'{x}{_src.replace(_from, _to)}'
                                st = idx + 9
                            else:
                                try:
                                    fi = _get_full_int(fstr[idx + 3:])
                                    x = f'{x}{_src.split(fstr[idx + 2])[fi.i]}'
                                    st = idx + 3 + len(fi)
                                except IndexError:
                                    _e1 = ", ".join(_src.split(fstr[idx + 2]))
                                    _e2 = len(_src.split(fstr[idx + 2]))
                                    typer.secho(
                                        f"\nCan't use segment {fi.o} of '{_e1}'\n"
                                        f"  It only has {_e2} segments.\n",
                                        fg="red"
                                    )
                                    raise
                        else:  # +2 is '['
                            if fstr[idx + 3] == "-":
                                try:
                                    fi = _get_full_int(fstr[idx + 4:])
                                    x = f'{x}{"".join(_src[-fi.o:])}'
                                    st = idx + 4 + len(fi) + 1  # +1 for closing ']'
                                except IndexError:
                                    typer.secho(
                                        f"Can't extract the final {fi.o} characters from {_src}"
                                        f"It's only {len(_src)} characters."
                                    )
                                    raise
                            else:  # +2 is '[' +3: should be int [1:4]
                                fi = _get_full_int(fstr[idx + 3:])
                                fi2 = _get_full_int(fstr[idx + 3 + len(fi) + 1:])  # +1 for expected ':'
                                if len(_src[slice(fi.i, fi2.o)]) <= fi2.o - fi.i:
                                    _e1 = typer.style(
                                        f"\n{fstr} wants to take characters "
                                        f"\n{fi.o} through {fi2.o}"
                                        f"\n\"from {_src}\" (slice ends at character {len(_src[slice(fi.i, fi2.o)])}).",
                                        fg="red"
                                    )
                                    if shown_prompt or typer.confirm(
                                        f"{_e1}"
                                        f"\n\nResult will be \""
                                        f"{typer.style(''.join(_src[slice(fi.i, fi2.o)]), fg='bright_green')}\""
                                        " for this segment."
                                        "\nOK to continue?",
                                        abort=True
                                    ):
                                        shown_prompt = True
                                        x = f'{x}{"".join(_src[slice(fi.i, fi2.o)])}'
                                        st = idx + 3 + len(fi) + len(fi2) + 2  # +2 for : and ]
                    else:
                        x = f'{x}{c}'
                x = x if not lower else x.lower()
                x = x.replace(" ", space)
                data += [{"serial": ap, "hostname": x}]
                break
            except typer.Abort:
                fstr = _lldp_rename_get_fstr()
            except Exception as e:
                log.exception(f"Auto/LLDP rename exception while parsing {fstr}\n{e}", show=log.DEBUG)
                print(f"\nThere Appears to be a problem with [red]{fstr}[/]: {e.__class__.__name__}")
                if typer.confirm("Do you want to edit the format string and try again?", abort=True):
                    fstr = _lldp_rename_get_fstr()

    return data


# TODO finish extraction of uplink commands from commands sent to gw
# so they can be sent in 2nd request as gw always errors interface doesn't
# exist yet.
def _extract_uplink_commands(commands: list[str]) -> tuple[list[str], list[str]]:  # pragma: no cover
    _start = None
    uplk_cmds = []
    for idx, c in enumerate(commands):
        if c.lower().startswith("uplink wired"):
            _start = idx
        elif _start and c.lstrip().startswith("!"):
            uplk_cmds += [slice(_start, idx + 1)]
            _start = None
    uplk_lines = [line for x in [commands[s] for s in uplk_cmds] for line in x]
    idx_list = [x for idx in [list(range(s.start, s.stop)) for s in uplk_cmds] for x in idx]
    non_uplk_lines = [cmd for idx, cmd in enumerate(commands) if idx not in idx_list]
    return uplk_lines, non_uplk_lines


def batch_deploy(import_file: Path, yes: bool = False) -> list[Response]:
    data = common._get_import_file(import_file)
    if "groups" in data:
        resp = common.batch_add_groups(import_file, yes=bool(yes))
        yes = yes if not yes else yes - 1
        render.display_results(resp, tablefmt="action", exit_on_fail=True)
    if "sites" in data:
        resp = common.batch_add_sites(import_file, yes=bool(yes))
        render.display_results(resp)
        yes = yes if not yes else yes - 1
    if "labels" in data:
        resp = common.batch_add_labels(import_file, yes=bool(yes))
        render.display_results(resp, tablefmt="action")
        yes = yes if not yes else yes - 1
    if "devices" in data:
        resp = common.batch_add_devices(import_file, yes=bool(yes))
        render.display_results(resp, tablefmt="action")


def _get_migrate_down_devs(import_file: Path) -> dict[str, dict[str, Any]]:
    if "migrate" not in import_file.stem:
        return {}

    down_file1 = import_file.parent / f'down{import_file.stem.removeprefix("migrate")}.json'
    # down_file2 = import_file.parent / f'down{import_file.stem.removeprefix("migrate")}.csv'
    for down_file in [down_file1]:
        if down_file.exists():
            try:
                if down_file.suffix == ".json":
                    return json.loads(down_file.read_text())
                else:
                    with render.Spinner(f"Fetching data from [dark_violet]{down_file.name}[/]", spinner="arrow3"):
                        return common._get_import_file(down_file, "devices", required_fields=["serial"])
            except Exception as e:
                log.exception(f"{repr(e)} during attempt to read in {down_file}", show=True)
    return {}


@app.command()
def verify(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    no_refresh: bool = typer.Option(False, "--nr", "--no-refresh", help="Bypass cache refresh.  Used for repeat verification when the cache is known to be up to date.", envvar="CENCLI_DEV_NO_REFRESH", hidden=False),
    failed: bool = typer.Option(False, "-F", "--failed", help="Output only devices that fail validation (full output with just [red]failed[/] devices)", rich_help_panel="Filtering Options"),
    passed: bool = typer.Option(False, "-P", "--passed", help="Output only devices that pass validation (full output with just [green]passed[/] devices)", rich_help_panel="Filtering Options"),
    down: bool = typer.Option(False, "-D", "--down", help="Output only devices that have checked in, but are currently [red]Down[/]", rich_help_panel="Filtering Options"),
    down_prior: bool = typer.Option(False, "--down-prior", help="Output only devices that were down prior to migration.  [dim italic]For use with [cyan]cencli migrate devices ...[/]", rich_help_panel="Filtering Options"),
    brief: bool = typer.Option(False, "-B", "--brief", help="Applies to -F|--failed|-P|--passed flags.  Output only a simple list of serials matching the filter", rich_help_panel="Filtering Options"),
    grep: bool = typer.Option(False, "--grep", help="Implies -B.  Format brief output [italic](serial numbers)[/] in a format that can be used with grep to filter an existing csv."),
    do_retry: bool = common.options.get("do_retry", help="create retry file with just the devices from import that fail validation"),
    outfile: Path = common.options.outfile,
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
) -> None:
    """Validate batch Add/Move (devices) operations using import data from file.

    The same import file used to add/move can be used to validate.
    """
    if show_example:
        render.console.print(examples.verify)
        return
    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch verify [OPTIONS] [IMPORT_FILE]"))

    with render.Spinner(f"Fetching data from [dark_violet]{import_file.name}[/]", spinner="arrow3"):
        data = common._get_import_file(import_file, import_type="devices", required_fields=["serial"], sub_word_sep="-")
        file_all_keys = utils.all_keys(data)
        down_prior_by_serial = _get_migrate_down_devs(import_file)
        if not down_prior_by_serial:
            if "status" in utils.all_keys(data):
                down_prior_by_serial = {d["serial"]: f'{utils.summarize_list([field for field in [[dev.get("name"), dev.get("serial"), dev.get("group"), dev.get("site")] for dev in data] if field is not None])}' for d in data if d.get("status") != "Up"}

    _spin_txt = f"Fetching device details from [medium_spring_green]{'cache' if no_refresh else 'Aruba Central'}[/]"
    with render.Spinner(_spin_txt) as spinner:
        resp: Response = common.cache.get_devices_with_inventory(no_refresh=no_refresh)
        spinner.start(_spin_txt)  # if refresh spinner will be taken over in resp.py.  This ensures it is retored
        if not resp.ok:
            render.display_results(resp, stash=False, exit_on_fail=True)
        resp.output = utils.normalize_device_sub_field(cleaner.simple_kv_formatter(resp.output), word_sep="-")

    with render.Spinner("Preparing data for validation"):
        file_by_serial = {
            d["serial"]: d
            for d in sorted(data, key=lambda d: (d.get("type", ""), d.get("site", "")))
        }
        central_by_serial = {d["serial"]: d for d in resp.output}

        validation = {}
        _down_prior = {}
        not_in_inventory = not_checked_in = _up = _down = down_prior_down_now = 0

    spinner = render.Spinner(f"Validating current status against desired status from [dark_violet]{import_file}[/]", spinner="dots2")
    spinner.start()
    for s in file_by_serial:
        validation[s] = []
        if s not in central_by_serial:
            validation[s] += ["Device not in inventory"]
            not_in_inventory += 1
            continue

        if not central_by_serial[s].get("status"):
            if s in down_prior_by_serial:
                _down_prior[s] = f"Device was [red]Down[/] prior to migration.  Still [red]Down[/]: {down_prior_by_serial[s]}"
                down_prior_down_now += 1
                continue
            not_checked_in += 1

        elif central_by_serial[s]['status'].lower() == 'up':
            _up += 1
        else:
            _down += 1

        _dev_type = central_by_serial[s]['type'].upper()
        _dev_type = _dev_type if _dev_type not in ["CX", "SW"] else f"{_dev_type} switch"
        _pfx = f"[magenta]{_dev_type}[/] is in inventory, "
        _assigned = central_by_serial[s].get("assigned")
        _subscription = central_by_serial[s].get("subscription")
        _valid = central_by_serial[s].get("expires in") and not central_by_serial[s]["expires in"].is_expired
        _expires_in = central_by_serial[s].get("expires in") and central_by_serial[s]["expires in"]
        if all([_assigned, _subscription, _valid]):
            _valid_str = f"[bright_green]Iventory Status Valid[/]: (assigned/subscribed/[cyan]expires in[/]: {_expires_in})"
        else:
            _valid_str = f"[red]Inventory Status Issue[/]: [cyan]Assigned[/]: {_assigned}, [cyan]Subscription[/]: {_subscription}, [cyan]expires in[/]: {_expires_in}"
        if file_by_serial[s].get("group"):
            if not central_by_serial[s].get("status"):
                validation[s] += [f"[cyan]Group:[/] {_pfx}but has not connected to Central.  Not able to validate pre-provisioned group via API."]
            elif not central_by_serial[s].get("group"):
                validation[s] += [f"[cyan]Group:[/] {_pfx}Group [cyan]{file_by_serial[s]['group']}[/] from import != [italic]None[/] reflected in Central."]
            elif file_by_serial[s]["group"] != central_by_serial[s]["group"]:
                validation[s] += [f"[cyan]Group:[/] {_pfx}Group [bright_red]{file_by_serial[s]['group']}[/] from import != [bright_green]{central_by_serial[s]['group']}[/] reflected in Central."]

        if file_by_serial[s].get("site"):
            if not central_by_serial[s].get("status"):
                validation[s] += [f"[cyan]Site:[/] {_pfx}Unable to assign/verify site [dim italic]([green]{file_by_serial[s]['site']}[/])[/dim italic] prior to device checking in."]
            elif not central_by_serial[s].get("site"):
                validation[s] += [f"[cyan]Site:[/] {_pfx}Site: [cyan]{file_by_serial[s]['site']}[/] from import != [italic]None[/] reflected in Central."]
            elif file_by_serial[s]["site"] != central_by_serial[s]["site"]:
                validation[s] += [f"[cyan]Site:[/] {_pfx}Site: [bright_red]{file_by_serial[s]['site']}[/] from import != [bright_green]{central_by_serial[s]['site']}[/] reflected in Central."]

        if "subscription" in file_all_keys:
            _pfx = "" if _pfx in str(validation[s]) else _pfx
            if file_by_serial[s].get("subscription", "null") != (central_by_serial[s]["subscription"] or "null"):  # .replace("-", "_").replace(" ", "_")
                validation[s] += [f"[cyan]Subscription[/]: {_pfx}[bright_red]{file_by_serial[s].get('subscription', 'null')}[/] from import != [bright_green]{central_by_serial[s].get('subscription', '[red]No Sub Key in data[/]') or 'No Subscription Assigned'}[/] reflected in Central."]
            elif validation[s]:  # Only show positive valid results here if the device failed other items.
                validation[s] += [f"[cyan]Subscription[/]: {_pfx}[bright_green]OK[/] ({central_by_serial[s].get('subscription', '[red]No Sub Key in data[/]') or '[red]No Subscription[/]'}) Assigned.  Matches import file."]
        if not central_by_serial[s].get("status"):
            validation[s] += [_valid_str]

    ok_devs, not_ok_devs, prev_down_devs, retry_data = [], [], [], []
    for s in file_by_serial:
        if not validation[s] and s not in _down_prior:
            ok_devs += [s]
            _msg = "Added to Inventory: [bright_green]OK[/]"
            for field in ["group", "site", "subscription"]:
                if field is not None and field in file_by_serial[s] and file_by_serial[s][field]:
                    _msg += f", {field.title()}: [bright_green]OK[/]"
            validation[s] += [_msg]
        elif s in _down_prior:
            prev_down_devs += [s]
            validation.pop(s)
        else:
            not_ok_devs += [s]
            retry_data += [file_by_serial[s]]

    if not_ok_devs:
        caption = f"Out of {len(file_by_serial)} devices in {import_file.name} [red]{len(not_ok_devs)}[/] potentially have validation issues, and [green]{len(ok_devs)}[/] validate [green]OK[/]."
    else:
        caption = f"\u2705 All validations pass for the {len(file_by_serial)} devices in {import_file.name}"
    zip_ = zip(['Not in Inventory', 'Not Checked in', '[dim]Ignored [red]down[/] prior to migration[/]'], [not_in_inventory, not_checked_in, down_prior_down_now])
    caption = f"{caption}\n[dark_olive_green2]Counts[/]: Total: {len(file_by_serial)}, {utils.color([f'{k}: [cyan]{v}[/]' for k, v in zip_ if v])}".rstrip(", ")
    if _up:
        caption = f"{caption}, [bright_green]Up[/]: [bright_green]{_up}[/]"
    if _down:
        caption = f"{caption}, [red]Down[/]: [red]{_down}[/]"
    spinner.stop()

    console = Console(emoji=False, record=True)
    console.begin_capture()

    brief = brief or grep
    brief_sep = "\n" if not grep else r"\|"
    brief_bookends = '"' if grep else ''
    with render.Spinner("Rendering Output..."):
        if failed and brief:
            render.econsole.print(f'{brief_bookends}{brief_sep.join(not_ok_devs)}{brief_bookends}')
        elif passed and brief:
            render.econsole.print(f'{brief_bookends}{brief_sep.join(ok_devs)}{brief_bookends}')
        elif down_prior:
            console.rule("Validation Results [deep_sky_blue2 italic]Devices down prior to migration[/]")
            _ = [console.print(f"[dim]\u2753  {s}: {_down_prior.get(s, '❓')}") for s in _down_prior]
            console.rule()
            console.print(f"[italic dark_olive_green2]{caption}[/]")
        else:
            console.rule("Validation Results")
            for s in _down_prior:
                if not any([passed, failed]):
                    console.print(f"[dim]\u2753  {s}: {_down_prior.get(s, '❓')}")  # ❓
            for s in validation:
                _hostname = central_by_serial.get(s, {}).get("name") or f'[dim]{file_by_serial.get(s, {}).get("name", "")}[/]'
                _hostname = _hostname and f"|{_hostname}"
                _site = (central_by_serial.get(s, {}).get("site", ) or "") or f'[dim]{file_by_serial.get(s, {}).get("site", "")}[/]'
                _site = _site and f"|s:{_site}"
                _status = central_by_serial.get(s, {}).get("status", "")
                _status = _status and f"|{utils.color(_status)}"
                dev_summary = f"{s}{_hostname}{_site}{_status}" if s not in ok_devs else f'{f"{s}{_hostname}{_site}{_status}":>35}'
                if down and _status != "Down":
                    continue
                if s in ok_devs:
                    if not failed:
                        console.print(f"[bright_green]\u2714  {dev_summary}[/]: {validation[s][0]}")
                elif not passed:
                    pad = len(Text.from_markup(dev_summary))
                    _msg = f"\n{' ' * (pad + 6)}".join(validation[s])
                    # _msg = f"\n{' ' * (len(s) + 2)}".join(validation[s])
                    console.print(f"[bright_red]\u274c  {dev_summary}[/]: {_msg}")
            console.rule()
            console.print(f"[italic dark_olive_green2]{caption}[/]")

        outdata = console.end_capture()
    typer.echo(outdata)

    if outfile:
        render.write_file(outfile, typer.unstyle(outdata))
    if do_retry and retry_data:
        if not ok_devs:
            render.econsole.print(f"No need for retry file, [red]no devices passed validation[/].  [italic dim]Continue to use {import_file.name}[/]")
            return
        key_order = ["name", "status", "type", "model", "ip", "serial", "mac", "group", "site", "retain_config"]
        retry_data = utils.format_table(retry_data, key_order=key_order)
        csv_str = render.get_csv_string(retry_data)
        render.write_file(import_file.parent / f"{import_file.stem}-retry.csv", csv_str, is_retry_file=True)


@app.command(short_help="Batch Deploy groups, sites, devices... from file", hidden=True)
def deploy(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: int = typer.Option(False, "-Y", "-y", count=True, help="Bypass confirmation prompts - Assume Yes.  Use multiples i.e. -yy -yyy to bypass each prompt in the deploy process (groups, sites, labels, devices).",),
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch Deploy from import.

    Batch Deploy can deploy the following:
        - Groups (along with group level configs for APs and/or GWs if provided)
        - Sites
        - Labels
        - Devices

    Use --example to see example import file format.
    """
    # TODO deploy example not  # FIXME
    if show_example:
        print(examples.deploy)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch deploy [OPTIONS] [IMPORT_FILE]"))

    batch_deploy(import_file, yes)


# TODO if from get inventory API endpoint subscriptions are under services key, if from endpoint file currently uses license key (maybe make subscription key)
def _build_sub_requests(devices: list[dict], unsub: bool = False) -> tuple[list[dict], list[dict], list[BatchRequest]]:  # pragma: no cover non GLP API
    devices = [{k if k not in possible_sub_keys else "subscription": v for k, v in dev.items()} for dev in devices]
    subs = set([d["subscription"] for d in devices if d.get("subscription")])  # TODO Inventory actually returns a list for services if the device has multiple subs this would be an issue
    ignored = [d for d in devices if not d.get("subscription")]
    devices = [d for d in devices if d.get("subscription")]  # filter any devs that currently do not have subscription

    if ignored:
        log.warning(f"Ignored {len(ignored)} devices, no desired subscription provided", caption=True)

    try:
        subs = [common.cache.LicenseTypes(s.lower().replace("_", "-").replace(" ", "-")).name for s in subs]  # type: ignore
    except ValueError as e:
        sub_names = "\n".join(common.cache.licenses)
        common.exit(str(e).replace("ValidLicenseTypes", f'subscription name.\n[cyan]Valid subscriptions[/]: \n{sub_names}'))

    devs_by_sub = {s: [] for s in subs}
    try:
        for d in devices:
            devs_by_sub[d["subscription"].lower().replace("-", "_").replace(" ", "_")] += [d["serial"]]
    except KeyError as e:
        common.exit(f"Malformed import data, or required field is missing. {repr(e)}")

    func = api.platform.unassign_licenses if unsub else api.platform.assign_licenses
    requests = [
        BatchRequest(func, serials=chunk, services=sub) for sub in devs_by_sub for chunk in utils.chunker(devs_by_sub[sub], 50)
    ]  # Both Assign and unassign allow a max of 50 serials per call

    return devices, ignored, requests


@app.command("_subscribe" if config.glp.ok else "subscribe", hidden=config.glp.ok)
def classic_subscribe(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover non GLP API
    """Batch subscribe devices

    Assign subscription license to devices specified in import file.

    [italic]This command assumes devices have already been added to GreenLake,
    to add devices and assign subscription use [cyan]cencli batch add devices <IMPORT_FILE>[/][/]
    """
    if show_example:
        print(getattr(examples, "subscribe"))
        return
    elif not import_file:
        common.exit(render._batch_invalid_msg("cencli batch subscribe [OPTIONS] [IMPORT_FILE]"))

    devices = common._get_import_file(import_file, "devices", subscriptions=True)
    devices, ignored, sub_reqs = _build_sub_requests(devices)

    render.display_results(data=devices, title="Devices to be subscribed", caption=f'{len(devices)} devices will have subscriptions assigned')
    if ignored:
        render.display_results(data=ignored, title="[bright_red]!![/] The following devices will be IGNORED [bright_red]!![/]", caption=f'{len(ignored)} devices will be ignored due to incomplete data')
    render.confirm(yes)
    resp = api.session.batch_request(sub_reqs)
    render.display_results(resp, tablefmt="action")
    # CACHE


@app.command("subscribe" if config.glp.ok else "_subscribe", hidden=not config.glp.ok)
def glp_subscribe(
    import_file: Path = common.arguments.import_file,
    import_sites: bool = typer.Option(False, "--import-sites", help=f"indicates import file contains sites.  Devices associated with those sites will be re-subscribed. {render.help_block('import is expected to contain devices')}"),
    _tags: list[str] = typer.Argument(None, metavar="", hidden=True),  # HACK because list[str] does not work for typer.Option
    tags: list[str] = common.options.tags,
    sub: str = common.options.get(
        "subscription",
        help="Assign this subscription to [bright_green]all[/] devices found in import [red italic](overrides subscription in import if defined)[/]",
        autocompletion=cache.sub_completion,
    ),  # TODO sub_completion ... get_sub_identifier add match capability based on subscription key, this is what is visible in GLP
    site: str = common.options.get("site", help="Update subscription for devices associated with a specific site.  [dim italic]The subscription (matching existing tier) with the most remaining time is auto-selected if --sub not provided[/]"),
    group: str = common.options.get("group", help="Update subscription for devices associated with a specific group.  [dim italic]The subscription (matching existing tier) with the most remaining time is auto-selected if --sub not provided[/]"),
    dev_type: GroupDevTypes = typer.Option(None, "--dev-type", help="Only re-subscribe devices of a given type. [dim italic]Applies/Only valid with [cyan]--site and/or --group[/]", show_default=False,),
    show_example: bool = common.options.show_example,
    no_refresh: bool = common.options.get("no_refresh", help="Forgo pre-command cache refresh, [dim italic]Applies when --site, --group, or --import-sites :triangular_flag: is provided[/]"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Assign Subscriptions to devices ([green]GreenLake[/]).

    [cyan]--sub <subscription name|key|glp_id>[/] can be used to specify the subscription.  It will be applied to [bright_green]all[/] devices found in import [red italic](even if the device has a subsciption defined in the import)[/]
    [cyan]--tags ...[/] can also be used to assign tags to all devices in import.  This in addition to any per-device tags found within the import, it's cumulative, not an override.

    [cyan]--site[/] and/or [cyan]--group[/] Can be used to re-subscribe existing devices.  The subscription of the same tier with available subs and the most time remaining will be auto selected, or specify a specific subscription w/ the
    [cyan]--sub[/] flag.


    """
    if show_example:
        render.console.print(examples.subscribe, emoji=True)
        return
    if (site or group) and import_file:
        common.exit("Invalid combination of Options/Arguments provide IMPORT_FILE (argument) or one of [cyan]--site[/], [cyan]--group[/].  Not both.")

    cache_site = None if not site else common.cache.get_site_identifier(site)
    cache_group = None if not group else common.cache.get_group_identifier(group)

    if cache_site or cache_group or (import_file and import_sites):
        data = common.get_filtered_devices_w_inventory(refresh=not no_refresh, site=cache_site, group=cache_group, dev_type=dev_type, site_import=None if not import_file and import_sites else import_file)
    elif import_file:
        data = common._get_import_file(import_file, import_type="devices", subscriptions=True, text_ok=bool(sub))
    else:
        common.exit(render._batch_invalid_msg("cencli batch assign subscriptions [OPTIONS] [IMPORT_FILE]"))

    _tags = _tags or []  # in case they use the form --tags tagname=tagvalue which would not populate _tags
    tag_dict = None if not tags else utils.parse_var_value_list([*tags, *_tags], source="tags")

    resp = common.batch_update_glp_devices(data, tags=tag_dict, subscription=sub, sub_required=True, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.command()  # TOGLP  Need GLP version
def unsubscribe(
    import_file: Path = common.arguments.import_file,
    never_connected: bool = typer.Option(False, "-N", "--never-connected", help="Remove subscriptions from any devices in inventory that have never connected to Central", show_default=False),
    dis_cen: bool = typer.Option(False, "-D", "--dis-cen", help="Disassociate the device from the Aruba Central App in Green Lake"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:  # pragma: no cover non GLP API
    """Batch Unsubscribe devices

    Unsubscribe devices specified in import file or all devices in the inventory that
    have never connected to Aruba Central ([cyan]-N[/]|[cyan]--never-connected[/])

    Use [cyan]-D[/]|[cyan]--dis-cen[/] flag to also disassociate the devices from the Aruba Central app in Green Lake.
    """
    if show_example:
        print(getattr(examples, "unsubscribe"))
        return
    elif never_connected:
        resp = common.cache.get_devices_with_inventory()
        if not resp:
            render.display_results(resp, exit_on_fail=True)

        devices = [d for d in resp.output if d.get("status") is None and d["subscription"]]
        if dis_cen:
            resp = common.batch_delete_devices(devices, yes=yes)
        else:
            devices, ignored, unsub_reqs = _build_sub_requests(devices, unsub=True)
            if not devices:
                common.exit("No devices with subscriptions found in inventory that have never connected.\nNoting to do.")

            render.display_results(data=utils.strip_no_value(devices), tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
            render.econsole.print("[bright_green]All Devices Listed will have subscriptions unassigned.[/]")
            render.confirm(yes)
            resp = api.session.batch_request(unsub_reqs)
    elif not import_file:
        common.exit(render._batch_invalid_msg("cencli batch unsubscribe [OPTIONS] [IMPORT_FILE]"))
    elif import_file:
        devices = common._get_import_file(import_file, "devices")
        devices, ignored, unsub_reqs = _build_sub_requests(devices, unsub=True)

        render.display_results(data=devices, tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
        if ignored:
            render.display_results(data=ignored, tablefmt="rich", title="[bright_red]!![/] The following devices will be IGNORED [bright_red]!![/]", caption=f'{len(ignored)} devices will be ignored due to incomplete data')

        if not unsub_reqs:
            common.exit("Nothing to do")

        render.confirm(yes)
        resp = api.session.batch_request(unsub_reqs)

    render.display_results(resp, tablefmt="action")
    if not dis_cen:
        inv_devs = [{"serial": serial, "subscription": None, "subscription_key": None, "subscription_expires": None} for req, resp in zip(unsub_reqs, resp) if resp.ok for serial in req.kwargs["serials"]]
        api.session.request(common.cache.update_inv_db, inv_devs)


@app.command()
def rename(
    what: BatchRenameArgs = common.arguments.what,
    import_file: Optional[Path] = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    lldp: bool = typer.Option(None, "-A", "--auto", "--lldp", help="Automatic AP rename using all, or portions of, info from upstream switch, site, group, ap model...",),
    lower: bool = typer.Option(False, "--lower", help="[AUTO RENAME] Convert LLDP result to all lower case.",),
    space: str = typer.Option(
        None,
        "-S",
        "--space",
        help="[AUTO RENAME] Replace spaces with provided character (best to wrap in single quotes) [grey42]{}[/]".format(escape("[default: '_']")),
        show_default=False,
    ),
    default_only: bool = typer.Option(False, "-D", "--default-only", help="[AUTO RENAME] Perform only on APs that still have default name.",),
    ap: str = typer.Option(None, metavar=iden_meta.dev, help="[AUTO RENAME] Perform on specified AP", autocompletion=common.cache.dev_ap_completion, show_default=False,),
    label: str = typer.Option(None, help="[AUTO RENAME] Perform on APs with specified label", autocompletion=common.cache.label_completion, show_default=False,),
    group: str = typer.Option(None, help="[AUTO RENAME] Perform on APs in specified group", autocompletion=common.cache.group_completion, show_default=False,),
    site: str = typer.Option(None, metavar=iden_meta.site, help="[AUTO RENAME] Perform on APs in specified site", autocompletion=common.cache.site_completion, show_default=False,),
    model: str = typer.Option(None, help="[AUTO RENAME] Perform on APs of specified model", show_default=False,),  # TODO model completion
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Perform AP rename in batch from import file or automatically based on LLDP"""
    if show_example:
        print(getattr(examples, f"rename_{what.value}"))
        return

    if str(import_file).lower() == "lldp":  # pragma: no cover Requires tty
        lldp = True
        import_file = None

    if not import_file and not lldp:
        common.exit(
            render._batch_invalid_msg(
                "cencli batch rename [OPTIONS] aps [IMPORT_FILE]",
                provide="Provide [bright_green]IMPORT_FILE[/] argument, or one of [cyan]--lldp[/] or [cyan]--example[/]"
            )
        )

    conf_msg = ""
    if import_file:
        data = common._get_import_file(import_file)
        conf_msg = f"[bright_green]Gathered [medium_spring_green]{len(data)}[/] APs/Names from import[/]:"
    elif lldp:  # pragma: no cover Requires tty
        kwargs = {}
        if group:
            kwargs["group"] = common.cache.get_group_identifier(group).name
        if ap:
            kwargs["serial"] = common.cache.get_dev_identifier(ap, dev_type="ap").serial
        if site:
            kwargs["site"] = common.cache.get_site_identifier(site).name
        if model:
            kwargs["model"] = model
        if label:
            kwargs["label"] = label

        fstr = _lldp_rename_get_fstr()
        conf_msg = f"\n[bright_green]Resulting AP names based on [/][cyan]{fstr}[/]:"
        data = get_lldp_names(fstr, default_only=default_only, lower=lower, space=space, **kwargs)

    resp = None
    # transform flat csv struct to Dict[str, Dict[str, str]] {"<AP serial>": {"hostname": "<desired_name>"}}
    data = {
        i.get("serial", i.get("serial_number", i.get("serial_num", "ERROR"))):
        {
            k if k != "name" else "hostname": v for k, v in i.items() if k in ["name", "hostname"]
        } for i in data
    }

    calls, per_ap_conf_msg = [], []
    for ap in data:  # keyed by serial num
        per_ap_conf_msg += [f"{ap}: [cyan]{data[ap]['hostname']}[/]"]
        calls.append(BatchRequest(api.configuration.update_ap_settings, ap, **data[ap]))

    render.econsole.print(f"{conf_msg}{utils.summarize_list(per_ap_conf_msg, pad=2, max=12)}", emoji=False)

    # We only spot check the last serial.  If first call in a batch_request fails the process stops.
    if ap not in common.cache.devices_by_serial:
        render.econsole.print("\n[dark_orange3]:warning:[/]  [italic]Device must be checked into Central to assign/change hostname.[/]")

    render.confirm(yes, prompt="\nProceed with AP rename?")
    resp = api.session.batch_request(calls)

    render.display_results(resp, tablefmt="action")
    # update dev cache
    if import_file:
        cache_data = [common.cache.get_dev_identifier(r.output) for r in resp if r.ok and r.status != 299]  # responds with str serial number
        cache_data = [{**dev, "name": data[dev["serial"]]["hostname"]} for dev in cache_data]           # 299 is default, indicates no call was performed, this is returned when the current data matches what's already set for the dev
        api.session.request(common.cache.update_dev_db, data=cache_data)


@app.command()
def move(
    import_file: list[Path] = typer.Argument(None, autocompletion=lambda incomplete: [("devices", "batch move devices")] if incomplete and "devices".startswith(incomplete.lower()) else [], show_default=False,),
    do_group: bool = typer.Option(False, "-G", "--group", help="Only process group move from import."),
    do_site: bool = typer.Option(False, "-S", "--site", help="Only process site move from import."),
    do_label: bool = typer.Option(False, "-L", "--label", help="Only process label assignment from import."),
    cx_retain_config: bool = common.options.get(
        "cx_retain_config",
        help="Keep config intact for CX switches during group move. [italic][cyan]retain_config[/] [dark_olive_green2]in import_file takes precedence[/][/italic], this flag enables the option without it being specified in the import_file."
    ),
    cx_retain_all: bool = typer.Option(
        None,
        help="Keep config intact or not for CX switches during group move [italic dark_olive_green2]regardless of what is in the import_file[/].",
        show_default=False,
        envvar="CENCLI_CX_RETAIN_CONFIG_ALL"
    ),
    no_pre_prov: bool = typer.Option(
        False,
        "--no-pre-group",
        "--npg",
        help=f"Only process moves for devices that have checked in.  Do not pre-provision devices to groups if they have not yet checked in {render.help_block('Devices that have not checked in are pre-provisioned to specified group (CX depends on retain option)')}",
        envvar="CENCLI_NO_PRE_PROVISION",
    ),
    no_refresh: bool = common.options.get("no_refresh", "--nr", "--no-refresh", help=f"Do not do on-demand cache refresh {render.help_block('Refresh is performed, on demand if device or site is not found in cache or already appears to be in desired group/site')}", envvar=env_var.no_refresh),
    refresh: bool = common.options.get("refresh", help=f"Refresh the cache prior to move, {render.help_block('Refresh is performed, on demand if device or site is not found in cache')}"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch move devices to any or all of group / site / label based on import data from file.

    By default group/site/label assignment will be processed if found in the import file.
    Use -G|--group, -S|--site, -L|--label flags to only process specified moves, and ignore
    others even if found in the import.

    If a device has not connected to Central, and has a group assoicated with it in the import
    data. It will be pre-provisioned to the group in Central.

    i.e. if import includes a definition for group, site, and label, and you only want to
    process the site move. Use the -S|--site flag, to ignore the other columns.

    If failures occur:
        [cyan]cencli batch verify IMPORT_FILE -FR[/] can be used to create a retry file with only with only failed moves.
    """
    if show_example:
        print(examples.move_devices)
        return

    if import_file:
        import_file = [f for f in import_file if not str(f).startswith("device")]  # allow unnecessary 'devices' sub-command

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch move [OPTIONS] [IMPORT_FILE]"))

    if len(import_file) > 1:
        common.exit("Too many arguments.  Use [cyan]cencli batch move --help[/] for help.")
    if not import_file[0].exists():
        common.exit(f"Invalid value for '[IMPORT_FILE]': Path '[cyan]{str(import_file[0])}[/]' does not exist.")

    resp = common.batch_move_devices(import_file[0], yes=yes, do_group=do_group, do_site=do_site, do_label=do_label, cx_retain_config=cx_retain_config, cx_retain_force=cx_retain_all, no_pre_prov=no_pre_prov, refresh=refresh, refresh_on_fail=not no_refresh)
    render.display_results(resp, tablefmt="action")


@app.command()
def archive(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch archive devices (in [green]GreenLake[/]) based on import data from file.

    This will archive the devices in GreenLake
    """
    if show_example:
        print(examples.archive)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch archive [OPTIONS] [IMPORT_FILE]"))

    common.batch_archive_unarchive_devices(import_file, yes=yes, operation="archive")


@app.command()
def unarchive(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = typer.Option(True, hidden=True),  # We allow -y but not necessary for unarchive
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch unarchive devices based on import data from file.

    This will unarchive the devices (previously archived) in GreenLake
    """
    if show_example:
        print(examples.unarchive)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch unarchive [OPTIONS] [IMPORT_FILE]"))

    common.batch_archive_unarchive_devices(import_file, yes=yes, operation="unarchive")


@app.callback()
def callback():
    """Perform batch operations"""
    pass


if __name__ == "__main__":
    app()
