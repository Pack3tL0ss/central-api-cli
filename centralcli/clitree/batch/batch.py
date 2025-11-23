#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import typer
from rich import print
from rich.console import Console
from rich.markup import escape

from centralcli import cleaner, common, log, render, utils
from centralcli.cache import CentralObject, api
from centralcli.client import BatchRequest
from centralcli.constants import BatchRenameArgs, iden_meta
from centralcli.response import Response

from . import add, assign, delete, examples, update

try:
    import readline  # noqa imported for backspace support during prompts.
except Exception:  # pragma: no cover
    pass

app = typer.Typer()
app.add_typer(assign.app, name="assign",)
app.add_typer(delete.app, name="delete",)
app.add_typer(add.app, name="add",)
app.add_typer(update.app, name="update",)


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
    '%h-1'  will split the hostname into parts separating on '-' and use
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
        fstr = typer.prompt("Enter Desired format string",)
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
    lldp_reqs = [br(api.topo.get_ap_lldp_neighbor, ap) for ap in ap_dict]
    lldp_resp = api.session.batch_request(lldp_reqs)

    if not all(r.ok for r in lldp_resp):
        log.error("Error occured while gathering lldp neighbor info", show=True)
        render.display_results(lldp_resp, exit_on_fail=True)

    _unlistified_output: list[dict[str, Any]] = [d for r in lldp_resp for d in r.output]  # type: ignore
    lldp_dict = {d["serial"]: {k: v for k, v in d.items()} for d in _unlistified_output}
    ap_dict = {
        ser: {
            **val,
            "neighborHostName": lldp_dict[ser]["neighborHostName"],
            "remotePort": lldp_dict[ser]["remotePort"],
        }
        for ser, val in ap_dict.items()
    }

    return ap_dict

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
        ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps}  # type: ignore
    else:
        ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps if d["name"] == d["macaddr"]}  # type: ignore
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

    num_calls = len(ap_dict) * 3 if need_lldp else len(ap_dict) * 2

    if len(ap_dict) > 5:
        _warn = "\n\n[dark_orange3]:warning:[/]  [blink bright_red blink]WARNING[reset]"
        if need_lldp:
            _warn = f"{_warn} Format provided requires details about the upstream switch.\n"
            _warn = f"{_warn} This automation will result in [cyan]{num_calls}[/] API calls. 3 per AP.\n"
            _warn = f"{_warn} 1 to gather details about the upstream switch\n"
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
    _start=None
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



@app.command()
def verify(
    import_file: Path = common.arguments.import_file,
    no_refresh: bool = typer.Option(False, hidden=True, help="Used for repeat testing when there is no need to update cache."),
    failed: bool = typer.Option(False, "-F", help="Output only a simple list with failed serials"),
    passed: bool = typer.Option(False, "-OK", help="Output only a simple list with serials that validate OK"),
    outfile: Path = common.options.outfile,
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
) -> None:
    """Validate batch Add operations using import data from file.

    The same import file used to add/move can be used to validate.
    """
    data = common._get_import_file(import_file, import_type="devices")

    resp: Response = common.cache.get_devices_with_inventory(no_refresh=no_refresh)
    if not resp.ok:
        render.display_results(resp, stash=False, exit_on_fail=True)
    resp.output = cleaner.simple_kv_formatter(resp.output)
    central_devs = [CentralObject("dev", data=r) for r in resp.output]

    file_by_serial = {
        d["serial"]: {
            k: v if k != "license" else v.lower().replace("-", "_").replace(" ", "_") for k, v in d.items() if k != "serial"
        } for d in data
    }
    central_by_serial = {
        d.serial: {
            k: v if k != "services" or v is None else v.lower().replace(" ", "_") for k, v in d.data.items() if k != "serial"
        }
        for d in central_devs
    }
    # TODO figure out what key we are going to require  batch add devices --example show license
    # batch add allows the same three keys
    _keys = ["license", "services", "subscription"]
    file_key = [k for k in _keys if k in file_by_serial[list(file_by_serial.keys())[0]].keys()]
    file_key = None if not file_key else file_key[0]

    validation = {}
    for s in file_by_serial:
        validation[s] = []
        if s not in central_by_serial:
            validation[s] += ["Device not in inventory"]
            continue
        _dev_type = central_by_serial[s]['type'].upper()
        _dev_type = _dev_type if _dev_type not in ["CX", "SW"] else f"{_dev_type} switch"
        _pfx = f"[magenta]{_dev_type}[/] is in inventory, "
        if file_by_serial[s].get("group"):
            if not central_by_serial[s].get("status"):
                validation[s] += [f"[cyan]Group:[/] {_pfx}but has not connected to Central.  Not able to validate pre-provisioned group via API."]
            elif not central_by_serial[s].get("group"):
                validation[s] += [f"[cyan]Group:[/] {_pfx}Group [cyan]{file_by_serial[s]['group']}[/] from import != [italic]None[/] reflected in Central."]
            elif file_by_serial[s]["group"] != central_by_serial[s]["group"]:
                validation[s] += [f"[cyan]Group:[/] {_pfx}Group [bright_red]{file_by_serial[s]['group']}[/] from import != [bright_green]{central_by_serial[s]['group']}[/] reflected in Central."]

        if file_by_serial[s].get("site"):
            if not central_by_serial[s].get("status"):
                validation[s] += [f"[cyan]Site:[/] {_pfx}Unable to assign/verify site prior to device checking in."]
            elif not central_by_serial[s].get("site"):
                validation[s] += [f"[cyan]Site:[/]{_pfx}Site: [cyan]{file_by_serial[s]['site']}[/] from import != [italic]None[/] reflected in Central."]
            elif file_by_serial[s]["site"] != central_by_serial[s]["site"]:
                validation[s] += [f"[cyan]Site:[/]{_pfx}Site: [bright_red]{file_by_serial[s]['site']}[/] from import != [bright_green]{central_by_serial[s]['site']}[/] reflected in Central."]

        if file_key:
            _pfx = "" if _pfx in str(validation[s]) else _pfx
            if file_by_serial[s][file_key].replace("_", "-") != central_by_serial[s]["services"]: # .replace("-", "_").replace(" ", "_")
                validation[s] += [f"[cyan]Subscription[/]: {_pfx}[bright_red]{file_by_serial[s][file_key]}[/] from import != [bright_green]{central_by_serial[s]['services'] or 'No Subscription Assigned'}[/] reflected in Central."]
            elif validation[s]:  # Only show positive valid results here if the device failed other items.
                validation[s] += [f"[cyan]Subscription[/]: {_pfx}[bright_green]OK[/] ({central_by_serial[s]['services']}) Assigned.  Matches import file."]


    ok_devs, not_ok_devs = [], []
    for s in file_by_serial:
        if not validation[s]:
            ok_devs += [s]
            _msg = "Added to Inventory: [bright_green]OK[/]"
            for field in ["group", "site", file_key]:
                if field is not None and field in file_by_serial[s] and file_by_serial[s][field]:
                    _msg += f", {field.title()} [bright_green]OK[/]"
            validation[s] += [_msg]
        else:
            not_ok_devs += [s]

    caption = f"Out of {len(file_by_serial)} in {import_file.name} {len(not_ok_devs)} potentially have validation issue, and {len(ok_devs)} validate OK."
    console = Console(emoji=False, record=True)
    console.begin_capture()

    if failed:
        render.econsole.print("\n".join(not_ok_devs))
    elif passed:
        render.console.print("\n".join(ok_devs))
    else:
        console.rule("Validation Results")
        for s in validation:
            if s in ok_devs:
                console.print(f"[bright_green]{s}[/]: {validation[s][0]}")
            else:
                _msg = f"\n{' ' * (len(s) + 2)}".join(validation[s])
                console.print(f"[bright_red]{s}[/]: {_msg}")
        console.rule()
        console.print(f"[italic dark_olive_green2]{caption}[/]")

    outdata = console.end_capture()
    typer.echo(outdata)

    if outfile:
        render.write_file(outfile, typer.unstyle(outdata))

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
    if "'license': " in str(devices):
        devices = [{**d, "services": d["license"]} for d in devices]
    elif "'subscription': " in str(devices):
        devices = [{**d, "services": d["subscription"]} for d in devices]

    subs = set([utils.unlistify(d["services"]) for d in devices if d.get("services")])  # TODO Inventory actually returns a list for services if the device has multiple subs this would be an issue
    ignored = [d for d in devices if not d.get("services")]
    devices = [d for d in devices if d.get("services")]  # filter any devs that currently do not have subscription

    if ignored:
        log.warning(f"Ignored {len(ignored)} devices, no desired subscription provided", caption=True)

    try:
        subs = [common.cache.LicenseTypes(s.lower().replace("_", "-").replace(" ", "-")).name for s in subs]
    except ValueError as e:
        sub_names = "\n".join(common.cache.license_names)
        common.exit(str(e).replace("ValidLicenseTypes", f'subscription name.\n[cyan]Valid subscriptions[/]: \n{sub_names}'))

    devs_by_sub = {s: [] for s in subs}
    for d in devices:
        devs_by_sub[d["services"].lower().replace("-", "_").replace(" ", "_")] += [d["serial"]]

    func = api.platform.unassign_licenses if unsub else api.platform.assign_licenses
    # Both Assign and unassign allow a max of 50 serials per call
    requests = [
        BatchRequest(func, serials=chunk, services=sub) for sub in devs_by_sub for chunk in utils.chunker(devs_by_sub[sub], 50)
    ]

    return devices, ignored, requests


# TOGLP batch assign subscription is the GLP subscribe, need to decide if makes sense to keep it there, or update this command to support GLP
@app.command()
def subscribe(
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

    devices = common._get_import_file(import_file, "devices")
    devices, ignored, sub_reqs = _build_sub_requests(devices)

    render.display_results(data=devices, tablefmt="rich", title="Devices to be subscribed", caption=f'{len(devices)} devices will have subscriptions assigned')
    # print("[bright_green]All Devices Listed will have subscriptions assigned.[/]")
    if ignored:
        render.display_results(data=ignored, tablefmt="rich", title="[bright_red]!![/] The following devices will be IGNORED [bright_red]!![/]", caption=f'{len(ignored)} devices will be ignored due to incomplete data')
    if render.confirm(yes):
        resp = api.session.batch_request(sub_reqs)
        render.display_results(resp, tablefmt="action")

@app.command()
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
        else:
            devices = [d for d in resp.output if d.get("status") is None and d["services"]]
            if dis_cen:
                resp = common.batch_delete_devices(devices, yes=yes)
            else:
                devices, ignored, unsub_reqs = _build_sub_requests(devices, unsub=True)
                if not devices:
                    common.exit("No devices with subscriptions found in inventory that have never connected.\nNoting to do.")

                render.display_results(data=devices, tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
                print("[bright_green]All Devices Listed will have subscriptions unassigned.[/]")
                if render.confirm(yes):
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
        if render.confirm(yes):
            resp = api.session.batch_request(unsub_reqs)

    render.display_results(resp, tablefmt="action")
    if not dis_cen:
        inv_devs = [{"serial": serial, "services": None, "subscription_key": None, "subscription_expires": None} for req, resp in zip(unsub_reqs, resp) if resp.ok for serial in req.kwargs["serials"]]
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
        cache_data = [{**dev, "name": data[dev["serial"]]["hostname"]}  for dev in cache_data]           # 299 is default, indicates no call was performed, this is returned when the current data matches what's already set for the dev
        api.session.request(common.cache.update_dev_db, data=cache_data)


@app.command()
def move(
    import_file: list[Path] = typer.Argument(None, autocompletion=lambda incomplete: [("devices", "batch move devices")] if incomplete and "devices".startswith(incomplete.lower()) else [], show_default=False,),
    do_group: bool = typer.Option(False, "-G", "--group", help="Only process group move from import."),
    do_site: bool = typer.Option(False, "-S", "--site", help="Only process site move from import."),
    do_label: bool = typer.Option(False, "-L", "--label", help="Only process label assignment from import."),
    cx_retain_config: bool = typer.Option(
        False,
        "-k",
        help="Keep config intact for CX switches during group move. [cyan italic]retain_config[/] [italic dark_olive_green2]in import_file takes precedence[/], this flag enables the option without it being specified in the import_file."
    ),
    cx_retain: bool = typer.Option(
        None,
        help="Keep config intact or not for CX switches during group move [italic dark_olive_green2]regardless of what is in the import_file[/].",
        show_default=False,
    ),
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
    """
    if show_example:
        print(examples.move_devices)
        return

    import_file = [f for f in import_file if not str(f).startswith("device")] # allow unnecessary 'devices' sub-command

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch move [OPTIONS] [IMPORT_FILE]"))
    elif len(import_file) > 1:
        common.exit("Too many arguments.  Use [cyan]cencli batch move --help[/] for help.")
    elif not import_file[0].exists():
        common.exit(f"Invalid value for '[IMPORT_FILE]': Path '[cyan]{str(import_file[0])}[/]' does not exist.")

    resp = common.batch_move_devices(import_file[0], yes=yes, do_group=do_group, do_site=do_site, do_label=do_label, cx_retain_config=cx_retain_config, cx_retain_force=cx_retain)
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
    """Batch archive devices based on import data from file.

    This will archive the devices in GreenLake
    """
    if show_example:
        print(examples.archive)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch archive [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, "devices", text_ok=True)
    serials = [x.get("serial") or x.get("serial_num") for x in data]

    render.econsole.print(f"[red]Archiv{'e' if not yes else 'ing'}[/] the [bright_green]{len(serials)}[/] devices found in {import_file.name}")
    render.confirm(yes)
    res = api.session.request(api.platform.archive_devices, serials)
    if res:
        caption = res.output.get("message")
        if res.get("succeeded_devices"):
            title = "Devices successfully archived."
            data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
            render.display_results(data=data, title=title, caption=caption)
        if res.get("failed_devices"):
            title = "These devices failed to archived."
            data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
            render.display_results(data=data, title=title, caption=caption)
    else:
        render.display_results(res, tablefmt="action", exit_on_fail=True)


@app.command()
def unarchive(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
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

    data = common._get_import_file(import_file, import_type="devices", text_ok=True)
    serials = [dev["serial"] for dev in data]

    res = api.session.request(api.platform.unarchive_devices, serials)
    if res:
        caption = res.output.get("message")
        if res.get("succeeded_devices"):
            title = "Devices successfully unarchived."
            data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
            render.display_results(data=data, title=title, caption=caption)
        if res.get("failed_devices"):
            title = "These devices failed to unarchived."
            data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
            render.display_results(data=data, title=title, caption=caption)
    else:
        render.display_results(res, tablefmt="action", exit_on_fail=True)


@app.callback()
def callback():
    """Perform batch operations"""
    pass


if __name__ == "__main__":
    app()
