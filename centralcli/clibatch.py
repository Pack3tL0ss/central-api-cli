#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from time import sleep
from typing import Dict, List, Tuple, Union

import typer
from pydantic import BaseModel, Extra, Field, ValidationError, validator
from rich import print
from rich.console import Console
from rich.progress import track
from tinydb.table import Document

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import BatchRequest, Response, caas, cleaner, cli, config, log, models, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import BatchRequest, Response, caas, cleaner, cli, config, log, models, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import (
    AllDevTypes,
    BatchAddArgs,
    BatchDelArgs,
    BatchRenameArgs,
    CloudAuthUploadType,
    GatewayRole,
    IdenMetaVars,
    SendConfigDevIdens,
    SiteStates,
    state_abbrev_to_pretty,
)
from centralcli.exceptions import DevException, ImportException, MissingFieldException
from centralcli.strings import ImportExamples, LongHelp

# from centralcli.models import GroupImport
examples = ImportExamples()
help_text = LongHelp()
from centralcli.cache import CentralObject  # NoQA

iden = IdenMetaVars()
tty = utils.tty
app = typer.Typer()


# TODO template upload based on j2 support
class GroupImport(BaseModel):
    group: str
    allowed_types: List[AllDevTypes] = Field(["ap", "gw", "cx", "sw"], alias="types")
    gw_role: GatewayRole = Field("branch",)  # alias="gw-role")
    aos10: bool = False
    microbranch: bool = False
    wlan_tg: bool = Field(False,)  # alias="wlan-tg")
    wired_tg: bool = Field(False,)  # alias="wired-tg")
    monitor_only_sw: bool = Field(False,)  # alias="monitor-only-sw")
    monitor_only_cx: bool = Field(False,)  # alias="monitor-only-cx")
    gw_config: Path = Field(None,)  # alias="gw-config")
    ap_config: Path = Field(None,)  # alias="ap-config")
    gw_vars: Path = Field(None,)  # alias="gw-vars")
    ap_vars: Path = Field(None,)  # alias="ap-vars")

    class Config:
        use_enum_values = True

# TODO move to models.py
class SiteImport(BaseModel):
    site_name: str
    address: str = None
    city: str = None
    state: str = None
    country: str = Field(None, min_length=3)
    zipcode: str = Field(None, min_length=5, alias="zip")
    latitude: str = Field(None, min_length=5, alias="lat")
    longitude: str = Field(None, min_length=5, alias="lon")

    class Config:
        extra = Extra.allow
        use_enum_values = True
        allow_population_by_alias = True

    @validator("state")
    def short_to_long(cls, v: str) -> str:
        try:
            return SiteStates(state_abbrev_to_pretty.get(v.upper(), v.title())).value
        except ValueError:
            return SiteStates(v).value


class FstrInt:
    def __init__(self, val: int) -> None:
        self.i = val
        self.o = val + 1

    def __len__(self):
        return len(str(self.i))


def _get_full_int(val: List[str]) -> FstrInt:
    rv = []
    while True:
        for i in val:
            if i.isdigit():
                rv += [i]
            else:
                return FstrInt(int("".join(rv)) - 1)


def _lldp_rename_get_fstr():
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
        if "%%" in fstr:
            typer.clear()
            print(f"\n[cyan]{fstr}[/] appears to be invalid.  Should never be 2 consecutive '%'.")
        else:
            return fstr

# TODO use get_topo_for_site similar to show aps -n  single call can get neigbor detail for all aps
def _get_lldp_dict(ap_dict: dict) -> dict:
    """Updates provided dict of APs keyed by AP serial number with lldp neighbor info
    """
    br = cli.central.BatchRequest
    lldp_reqs = [br(cli.central.get_ap_lldp_neighbor, ap) for ap in ap_dict]
    lldp_resp = cli.central.batch_request(lldp_reqs)

    if not all(r.ok for r in lldp_resp):
        log.error("Error occured while gathering lldp neighbor info", show=True)
        cli.display_results(lldp_resp, exit_on_fail=True)

    lldp_dict = {d.output[-1]["serial"]: {k: v for k, v in d.output[-1].items()} for d in lldp_resp}
    ap_dict = {
        ser: {
            **val,
            "neighborHostName": lldp_dict[ser]["neighborHostName"],
            "remotePort": lldp_dict[ser]["remotePort"],
        }
        for ser, val in ap_dict.items()
    }

    return ap_dict

def do_lldp_rename(fstr: str, default_only: bool = False, **kwargs) -> Response:
    need_lldp = False if "%h" not in fstr and "%p" not in fstr else True
    # TODO get all APs then filter down after, stash down aps for easy subsequent call
    resp = cli.central.request(cli.central.get_devices, "aps", status="Up", **kwargs)

    if not resp:
        cli.display_results(resp, exit_on_fail=True)
    elif not resp.output:
        filters = ", ".join([f"{k}: {v}" for k, v in kwargs.items()])
        resp.output = {
            "description": "API called was successful but returned no results.",
            "error": f"No Up APs found matching provided filters ({filters})."
        }
        resp.ok = False
        cli.display_results(resp, exit_on_fail=True)

    _all_aps = utils.listify(resp.output)
    _keys = ["name", "macaddr", "model", "site", "serial"]
    if not default_only:
        ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps}
    else:
        ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps if d["name"] == d["macaddr"]}
        if not ap_dict:
            print(":warning:  No Up APs found with default name.  Nothing to rename.")
            raise typer.Exit(1)

    fstr_to_key = {
        "h": "neighborHostName",
        "m": "mac",
        "p": "remotePort",
        "M": "model",
        "S": "site",
        "s": "serial"
    }

    req_list, name_list, shown_prompt = [], [], False
    if not ap_dict:
        log.error("Something went wrong, no ap_dict provided or empty", show=True)
        raise typer.Exit(1)

    num_calls = len(ap_dict) * 3 if need_lldp else len(ap_dict) * 2

    if len(ap_dict) > 5:
        _warn = "\n\n[blink bright_red blink]WARNING[reset]"
        if need_lldp:
            _warn = f"{_warn} Format provided requires details about the upstream switch.\n"
            _warn = f"{_warn} This automation will result in [cyan]{num_calls}[/] API calls. 3 per AP.\n"
            _warn = f"{_warn} 1 to gather details about the upstream switch\n"
        else:
            _warn = f"{_warn} This automation will result in [cyan]{num_calls}[/] API calls, 1 for each AP.\n"
        _warn = f"{_warn} 1 to get the aps current settings (all settings need to be provided during the update, only the name changes).\n"
        _warn = f"{_warn} 1 to Update the settings / rename the AP.\n"
        _warn = f"{_warn}\n Current daily quota: [bright_green]{resp.rl.remain_day}[/] calls remaining\n"


        print(_warn)
        if resp.rl.remain_day < num_calls:
            print(f"  {resp.rl}")
            print(f"  More calls required {num_calls} than what's remaining in daily quota {resp.rl.remain_day}.")

        typer.confirm("Proceed:", abort=True)

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
                                if len(_src[slice(fi.i, fi2.o)]) < fi2.o - fi.i:
                                    _e1 = typer.style(
                                        f"\n{fstr} wants to take characters "
                                        f"\n{fi.o} through {fi2.o}"
                                        f"\n\"from {_src}\" (slice ends at character {len(_src[slice(fi.i, fi2.o)])}).",
                                        fg="red"
                                    )
                                    if not shown_prompt and typer.confirm(
                                        f"{_e1}"
                                        f"\n\nResult will be \""
                                        f"{typer.style(''.join(_src[slice(fi.i, fi2.o)]), fg='bright_green')}\""
                                        " for this segment."
                                        "\nOK to continue?"
                                    ):
                                        shown_prompt = True
                                        x = f'{x}{"".join(_src[slice(fi.i, fi2.o)])}'
                                        st = idx + 3 + len(fi) + len(fi2) + 2  # +2 for : and ]
                                    else:
                                        raise typer.Abort()
                    else:
                        x = f'{x}{c}'
                req_list += [cli.central.BatchRequest(cli.central.update_ap_settings, (ap, x))]
                name_list += [f"  {x}"]
                break
            except typer.Abort:
                fstr = _lldp_rename_get_fstr()
            except Exception as e:
                log.exception(f"LLDP rename exception while parsing {fstr}\n{e}", show=log.DEBUG)
                print(f"\nThere Appears to be a problem with [red]{fstr}[/]: {e.__class__.__name__}")
                if typer.confirm("Do you want to edit the format string and try again?", abort=True):
                    fstr = _lldp_rename_get_fstr()

    print(f"[bright_green]Resulting AP names based on '{fstr}':")
    if len(name_list) <= 6:
        typer.echo("\n".join(name_list))
    else:
        typer.echo("\n".join(
                [
                    *name_list[0:3],
                    "  ...",
                    *name_list[-3:]
                ]
            )
        )

    if typer.confirm("Proceed with AP Rename?", abort=True):
        return cli.central.batch_request(req_list)


def _convert_site_key(_data: dict) -> dict:
    _site_aliases = {
        "site-name": "site_name",
        "site": "site_name",
        "name": "site_name",
        "latitude": "lat",
        "longitude": "lon",
        "zipcode": "zip",
    }

    _data = {
        **_data.get("site_address", {}),
        **_data.get("geolocation", {}),
        **{k: v for k, v in _data.items() if k not in ["site_address", "geolocation"]}
    }
    _data = {_site_aliases.get(k, k): v for k, v in _data.items()}
    return _data

def batch_add_sites(import_file: Path = None, data: dict = None, yes: bool = False) -> Response:
    if all([d is None for d in [import_file, data]]):
        raise ValueError("batch_add_sites requires import_file or data arguments, neither were provided")

    central = cli.central
    if import_file is not None:
        data = config.get_file_data(import_file)

    if isinstance(data, dict) and "sites" in data:
        data = data["sites"]

    resp = None
    verified_sites: List[SiteImport] = []
    # We allow a list of flat dicts or a list of dicts where loc info is under
    # "site_address" or "geo_location"
    # can be keyed on name or flat.
    for i in data:
        if isinstance(i, str) and isinstance(data[i], dict):
            out_dict = _convert_site_key(
                {"site_name": i, **data[i]}
            )
        else:
            out_dict = _convert_site_key(i)

        verified_sites += [SiteImport(**out_dict)]

    site_names = [
        f"  [cyan]{s.site_name}[/]" for s in verified_sites
    ]
    if len(site_names) > 7:
        site_names = [*site_names[0:3], "  ...", *site_names[-3:]]

    print("\n[bright_green]The Following Sites will be created:[/]")
    _ = [print(s) for s in site_names]

    if yes or typer.confirm("Proceed?", abort=True):
        reqs = [
            BatchRequest(central.create_site, **site.dict())
            for site in verified_sites
        ]
        resp = central.batch_request(reqs)
        if all([r.ok for r in resp]):
            resp[-1].output = [r.output for r in resp]
            resp = resp[-1]
            cache_res = asyncio.run(cli.cache.update_site_db(data=resp.output))
            if len(cache_res) != len(data):
                log.warning(
                    "Attempted to add entries to Site Cache after batch import.  Cache Response "
                    f"{len(cache_res)} but we added {len(data)} sites.",
                    show=True
                )
        return resp or Response(error="No Sites were added")

# TODO REMOVE NOT USED (keeping for now in case I change my mind)
# class BatchRequest(BaseModel):
#     func: Callable
#     args: Tuple = ()
#     kwargs: Dict[str, Any] = {}

class PreConfig(BaseModel):
    name: str
    config: str
    request: BatchRequest

    class Config:
        arbitrary_types_allowed = True

# TODO finish extraction of uplink commands from commands sent to gw
# so they can be sent in 2nd request as gw always errors interface doesn't
# exist yet.
def _extract_uplink_commands(commands: List[str]) -> Tuple[List[str], List[str]]:
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

def _build_pre_config(node: str, dev_type: SendConfigDevIdens, cfg_file: Path, var_file: Path = None) -> PreConfig:
    """Build Configuration from raw config or jinja2 template/variable file.

    Args:
        node (str): The name of the central node (group name or device MAC for gw)
        dev_type (str): Type of device being pre-provisioned.  One of 'gw' or 'ap'.
        cfg_file (Path): Path of the config file.
        var_file (Path, optional): Path of the variable file. Defaults to None.

    Raises:
        typer.Exit: If config is j2 template but no variable file is found.
        typer.Exit: If result of config generation yields no commands

    Returns:
        PreConfig: PreConfig object
    """
    if not cfg_file.exists():
        print(f":warning: [cyan]{node}[/] {cfg_file} not found.  Unable to generate config.")
        raise typer.Exit(1)

    br = cli.central.BatchRequest
    caasapi = caas.CaasAPI(central=cli.central)
    config_out = utils.generate_template(cfg_file, var_file=var_file)
    commands = utils.validate_config(config_out)

    if dev_type == "gw":
        return PreConfig(name=node, config=config_out, request=br(caasapi.send_commands, node, cli_cmds=commands))
    elif dev_type == "ap":
        return PreConfig(name=node, config=config_out, request=br(cli.central.replace_ap_config, node, clis=commands))


def batch_add_groups(import_file: Path = None, data: dict = None, yes: bool = False) -> List[Response]:
    """Batch add groups to Aruba Central

    Args:
        import_file (Path, optional): import file containing group data. Defaults to None.
        data (dict, optional): data Used internally, when import_file is already parsed by batch_deploy. Defaults to None.
        yes (bool, optional): If True we bypass confirmation prompts. Defaults to False.

    Raises:
        typer.Exit: Exit if data is not in correct format.

    Returns:
        List[Response]: List[CentralApi.Response Object]
    """
    console = Console(emoji=False)
    br = cli.central.BatchRequest
    if import_file is not None:
        data = config.get_file_data(import_file)
    elif not data:
        print("[red]Error!![/] No import file provided")
        raise typer.Exit(1)

    if isinstance(data, dict) and "groups" in data:
        data = data["groups"]

    reqs, gw_reqs, ap_reqs = [], [], []
    pre_cfgs = []
    _pre_config_msg = ""
    cache_data = []
    for group in data:
        # we allow fields as wired_tg or wired-tg
        _data = {k.replace("-", "_"): v for k, v in data[group].items()}
        # if "allowed-types" in data[group]:
        #     data[group]["allowed_types"] = data[group]["allowed-types"]
        #     del data[group]["allowed-types"]

        try:
            # g = GroupImport(**{"group": group, **data[group]})
            g = GroupImport(**{"group": group, **_data})
        except ValidationError as e:
            print(e)
            raise typer.Exit(1)
        reqs += [
            br(
                cli.central.create_group,
                g.group,
                allowed_types=g.allowed_types,
                wired_tg=g.wired_tg,
                wlan_tg=g.wlan_tg,
                aos10=g.aos10,
                microbranch=g.microbranch,
                gw_role=g.gw_role,
                monitor_only_sw=g.monitor_only_sw,
                monitor_only_cx=g.monitor_only_cx,
            )
        ]
        cache_data += [
            {"name": g.group, "template group": {"Wired": g.wired_tg, "Wireless": g.wlan_tg}}
        ]
        for dev_type, cfg_file, var_file in zip(["gw", "ap"], [g.gw_config, g.ap_config], [g.gw_vars, g.ap_vars]):
            if cfg_file is not None:
                pc = _build_pre_config(g.group, dev_type=dev_type, cfg_file=cfg_file, var_file=var_file)
                pre_cfgs += [pc]
                _pre_config_msg += (
                    f"  [bright_green]{len(pre_cfgs)}[/]. [cyan]{g.group}[/] {'gateways' if dev_type == 'gw' else 'AP'} "
                    f"group level will be configured based on [cyan]{cfg_file.name}[/]\n"
                )
                if dev_type == "gw":
                    gw_reqs += [pc.request]
                else:
                    ap_reqs += [pc.request]

    if pre_cfgs:
        _pre_config_msg = (
            "\n[bright_green]Group level configurations will be sent:[/]\n"
            f"{_pre_config_msg}"
        )
    _pre_config_msg = (
        f"{_pre_config_msg}\n"
        f"[italic dark_olive_green2]{len(reqs) + len(gw_reqs) + len(ap_reqs)} API calls will be performed.[/]\n"
    )

    print("[bright_green]The following groups will be created:[/]")
    _ = [print(f"  [cyan]{g}[/]") for g in data]

    print(_pre_config_msg)

    if pre_cfgs:
        for idx in range(len(pre_cfgs) + 1):
            if idx > 0:
                print(_pre_config_msg)
            print("Select [bright_green]#[/] to display config to be sent or [bright_green]go[/] to continue.")
            ch = utils.ask(
                ">",
                console=console,
                choices=[*[str(idx) for idx in range(1, len(pre_cfgs) + 1)], "abort", "go"],
            )
            if ch.lower() == "go":
                yes = True
                break
            else:
                pc: PreConfig = pre_cfgs[int(ch) - 1]
                console.rule(f"Config to be sent to {pc.name}")
                with console.pager():
                    console.print(pc.config)
                console.rule(f" End {pc.name} config ")

    resp = None
    if reqs and yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.batch_request(reqs)
        if all(r.ok for r in resp):
            cache_resp = asyncio.run(cli.cache.update_group_db(cache_data))
            log.debug(f"batch add group cache resp: {cache_resp}")
        # cli.display_results(resp)
        config_reqs = []
        if gw_reqs:
            print("\n[bright_green]Sending Group level gateway config (CLI commands)[/]")
            print("\n  [italic]This can take some time.[/]")
            config_reqs += gw_reqs
        #     resp = cli.central.batch_request(gw_reqs)
        #     cli.display_results(resp, cleaner=cleaner.parse_caas_response)
        if ap_reqs:
            print("\n[bright_green]Sending Group level AP config (Replaces entire group level)[/]\n")
            config_reqs += ap_reqs
            # resp = cli.central.batch_request(ap_reqs)
            # cli.display_results(resp,  tablefmt="action")
        if config_reqs:
            for _ in track(range(10), description="Pausing to ensure groups are ready to accept configs."):
                sleep(1)
            resp += cli.central.batch_request(config_reqs, retry_failed=True)

    return resp or Response(error="No Groups were added")





def batch_add_devices(import_file: Path = None, data: dict = None, yes: bool = False) -> List[Response]:
    # TODO build messaging similar to batch move.  build common func to build calls/msgs for these similar funcs
    if import_file is not None:
        data = config.get_file_data(import_file)
    elif not data:
        print("[red]Error!![/] No import file provided")
        raise typer.Exit(1)

    if "devices" in data:
        data = data["devices"]

    # accept yaml/json keyed by serial #
    if data and isinstance(data, dict):
        if utils.isserial(list(data.keys())[0]):
            data = [{"serial": k, **v} for k, v in data.items()]

    warn = False
    _reqd_cols = ["serial", "mac"]
    if not all([len(_reqd_cols) == len([k for k in d.keys() if k in _reqd_cols]) for d in data]):
        print("[reset]:warning: [bright_red] !![/]Missing Required [cyan]serial[/] or [cyan]mac[/] for at least 1 entry")
        print("\nImport file must have the following keys for each device:")
        print("[cyan]serial[/], [cyan]mac[/]")
        print("\nThe following headers/columns are optional:")
        print("[cyan]group[/], [cyan]license[reset]")
        print("Use [cyan]cencli batch add devices --show-example[/] to see valid import file formats.")
        # TODO finish full deploy workflow with config per-ap-settings variables etc allowed
        raise typer.Exit(1)

    if isinstance(data, dict) and "devices" in data:
        data = data["devices"]

    sub_key = list(set([k for d in data for k in d.keys() if k in ["license", "services", "subscription"]]))
    sub_key = None if not sub_key else sub_key[0]
    if sub_key:
        # Validate license types
        for d in data:
            if d[sub_key]:
                for idx in range(2):
                    try:
                        d["license"] = cli.cache.LicenseTypes(d[sub_key].lower().replace("_", "-")).name
                        if sub_key != "license":
                            del d[sub_key]
                        break
                    except ValueError:
                        if idx == 0:
                            print(f'[bright_red]!![/] [cyan]{d["license"]}[/] not found in list of valid licenses.  Refreshing list/updating license cache.')
                            resp = cli.central.request(cli.cache.update_license_db)
                            if not resp:
                                cli.display_results(resp, exit_on_fail=True)
                        else:
                            print(f"[bright_red]!![/] [cyan]{d['license']}[/] does not appear to be a valid license type")
                            warn = True

    msg_pfx = "" if not warn else "Warning exist "
    word = "Adding" if not warn and yes else "Add"
    confirm_devices = ['|'.join([f'{k}:{v}' for k, v in d.items()]) for d in data]
    if len(confirm_devices) > 6:
        confirm_str = '\n'.join([*confirm_devices[0:3], "...", *confirm_devices[-3:]])
    else:
        confirm_str = '\n'.join(confirm_devices)

    console = Console(emoji=False, no_color=True)
    print(f'{len(data)} [cyan]Devices found in {"import file" if not import_file else import_file.name}[/]')
    console.print(confirm_str)
    print(f'\n{word} {len(data)} devices found in {"import file" if not import_file else import_file.name}')
    resp = None
    if (not warn and yes) or typer.confirm(f"{msg_pfx}Proceed?", abort=True):
        resp = cli.central.request(cli.central.add_devices, device_list=data)
        # if any failures occured don't pass data into update_inv_db.  Results in API call to get inv from Central
        _data = None if not all([r.ok for r in resp]) else data
        if _data:
            try:
                _data = [models.Inventory(**d).dict() for d in _data]
            except ValidationError as e:
                log.info(f"Performing full cache update after batch add devices as import_file data validation failed. {e}")
                _data = None

        # always perform full dev_db update as we don't know the other fields.
        console = Console()
        with console.status(f'Performing{" full" if _data else ""} inventory cache update after device edition.'):
            cache_res = [cli.central.request(cli.cache.update_inv_db, data=_data)]
        with console.status("Allowing time for devices to populate before updating dev cache."):
            sleep(5)
        with console.status('Performing full device cache update after device edition.'):
            cache_res += [cli.central.request(cli.cache.update_dev_db)]

    return resp or Response(error="No Devices were added")


# TODO this has not been tested validated at all
# TODO adapt to add or delete based on param centralcli.delete_label needs the label_id from the cache.
def batch_add_labels(import_file: Path = None, *, data: bool = None, yes: bool = False) -> List[Response]:
    if import_file is not None:
        data = config.get_file_data(import_file)
    elif not data:
        print("[red]Error!![/] No import file provided")
        raise typer.Exit(1)

    if isinstance(data, dict) and "labels" in data:
        data = data["labels"]

    # TODO common func for this type of multi-element confirmation, we do this a lot.
    _msg = "\n".join([f"  [cyan]{name}[/]" for name in data])
    _msg = _msg.lstrip() if len(data) == 1 else f"\n{_msg}"
    _msg = f"[bright_green]Create[/] {'label ' if len(data) == 1 else f'{len(data)} labels:'}{_msg}"
    print(_msg)

    resp = None
    if yes or typer.confirm("\nProceed?", abort=True):
        reqs = [BatchRequest(cli.central.create_label, label_name=label_name) for label_name in data]
        resp = cli.central.batch_request(reqs)
        # if any failures occured don't pass data into update_label_db.  Results in API call to get inv from Central
        try:
            _data = None if not all([r.ok for r in resp]) else cleaner.get_labels([r.output for r in resp])
            asyncio.run(cli.cache.update_label_db(data=_data))
        except Exception as e:
            log.exception(f'Exception during label cache update in batch_add_labels]n{e}')
            print(f'[bright_red]Cache Update Error[/]: {e.__class__.__name__}.  See logs.\nUse [cyan]cencli show labels[/] to refresh label cache.')

    return resp or Response(error="No labels were added")


def batch_add_cloudauth(upload_type: CloudAuthUploadType = "mac", import_file: Path = None, *, ssid: str = None, data: bool = None, yes: bool = False) -> Response:
    if import_file is not None:
        data = config.get_file_data(import_file)
    elif not data:
        cli.exit("[red]Error!![/] No import file provided")

    print(f"Upload{'' if not yes else 'ing'} [cyan]{upload_type.upper()}s[/] defined in [cyan]{import_file.name}[/] to Cloud-Auth{f' for SSID: [cyan]{ssid}[/]' if upload_type == 'mpsk' else ''}")

    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.cloudauth_upload, upload_type=upload_type, file=import_file, ssid=ssid)

    return resp


# TODO TEST and complete.
def batch_deploy(import_file: Path, yes: bool = False) -> List[Response]:
    print("Batch Deploy is new, and has not been completely tested yet.")
    if typer.confirm("Proceed?"):
        data = config.get_file_data(import_file)
        if "groups" in data:
            resp = batch_add_groups(data=data["groups"], yes=yes)
            cli.display_results(resp)
        if "sites" in data:
            resp = batch_add_sites(data=data["sites"], yes=yes)
            cli.display_results(resp)
        if "labels" in data:
            print("[bright_red]WARNING!![/]: batch add labels not tested yet.  Still here as there is no real risk if it fails.")
            resp = batch_add_labels(data=data["labels"], yes=yes)
            cli.display_results(resp, tablefmt="action")
        if "devices" in data:
            resp = batch_add_devices(data=data["devices"], yes=yes)
            cli.display_results(resp, tablefmt="action")


# FIXME
@app.command(short_help="Validate a batch import")
def verify(
    what: BatchAddArgs = typer.Argument(..., show_default=False,),
    import_file: Path = typer.Argument(..., exists=True, show_default=False, autocompletion=lambda incomplete: [],),
    no_refresh: bool = typer.Option(False, hidden=True, help="Used for repeat testing when there is no need to update cache."),
    failed: bool = typer.Option(False, "-F", help="Output only a simple list with failed serials"),
    passed: bool = typer.Option(False, "-OK", help="Output only a simple list with serials that validate OK"),
    outfile: Path = typer.Option(None, "--out", help="Write output to a file (and display)", show_default=False,),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Validate batch Add operations using import data from file.

    The same file used to import can be used to validate.
    """
    if what != "devices":
        print("Only devices and device assignments are supported at this time.")
        raise typer.Exit(1)

    # TODO add param to get_file_data to pull devices or similar key
    # make get_file_data return consistent List of pydantic models
    data = config.get_file_data(import_file)
    data = data if not hasattr(data, "dict") else data.dict
    if isinstance(data, dict) and what in data:
        data = data[what]

    # TODO Verify yaml/json/csv should now all look the same... only tested with csv

    resp = cli.cache.get_devices_with_inventory(no_refresh=no_refresh)
    if not resp.ok:
        cli.display_results(resp, stash=False, exit_on_fail=True)
    resp.output = cleaner.simple_kv_formatter(resp.output)
    central_devs = [CentralObject("dev", data=r) for r in resp.output]

    file_by_serial = {
        d["serial"]: {
            k: v if k != "license" else v.lower().replace("-", "_").replace(" ", "_") for k, v in d.items() if k != "serial"
        } for d in data
    }
    central_by_serial = {
        d.serial: {
            k: v if k != "services" else v.lower().replace(" ", "_") for k, v in d.data.items() if k != "serial"
        }
        for d in central_devs
    }
    # TODO figure out what key we are going to require  batch add devices --example show license
    # batch add allows the same three keys
    _keys = ["license", "services", "subscription"]
    file_key = [k for k in _keys if k in file_by_serial[list(file_by_serial.keys())[0]].keys()]
    file_key = file_key[0] if file_key else file_key

    validation = {}
    for s in file_by_serial:
        validation[s] = []
        if s not in central_by_serial:
            validation[s] += ["Device not in inventory"]
            continue
        _pfx = f"[cyan]{central_by_serial[s]['type'].upper()}[/] is in inventory, "
        if file_by_serial[s].get("group"):
            if not central_by_serial[s].get("status"):
                validation[s] += [f"{_pfx}but has not connected to Central.  Not able to validate pre-provisioned group via API."]
            elif not central_by_serial[s].get("group"):
                validation[s] += [f"{_pfx}Group: [cyan]{file_by_serial[s]['group']}[/] from import != [italic]None[/] reflected in Central."]
            elif file_by_serial[s]["group"] != central_by_serial[s]["group"]:
                validation[s] += [f"{_pfx}Group: [bright_red]{file_by_serial[s]['group']}[/] from import != [bright_green]{central_by_serial[s]['group']}[/] reflected in Central."]

        if file_by_serial[s].get("site"):
            if not central_by_serial[s].get("status"):
                validation[s] += [f"{_pfx}Unable to assign/verify site prior to device checking in."]
            elif not central_by_serial[s].get("site"):
                validation[s] += [f"{_pfx}Site: [cyan]{file_by_serial[s]['site']}[/] from import != [italic]None[/] reflected in Central."]
            elif file_by_serial[s]["site"] != central_by_serial[s]["site"]:
                validation[s] += [f"{_pfx}Site: [bright_red]{file_by_serial[s]['site']}[/] from import != [bright_green]{central_by_serial[s]['site']}[/] reflected in Central."]

        if file_key:
            _pfx = "" if _pfx in str(validation[s]) else _pfx
            if file_by_serial[s][file_key] != central_by_serial[s]["services"]: # .replace("-", "_").replace(" ", "_")
                validation[s] += [f"{_pfx}Subscription: [bright_red]{file_by_serial[s][file_key]}[/] from import != [bright_green]{central_by_serial[s]['services'] or 'No Subscription Assigned'}[/] reflected in Central."]

    ok_devs, not_ok_devs = [], []
    for s in file_by_serial:
        if not validation[s]:
            ok_devs += [s]
            _msg = "Added to Inventory: [bright_green]OK[/]"
            for field in ["license", "group", "site"]:
                if field in file_by_serial[s] and file_by_serial[s][field]:
                    _msg += f", {field.title()} [bright_green]OK[/]"
            validation[s] += [_msg]
        else:
            not_ok_devs += [s]

    caption = f"Out of {len(file_by_serial)} in {import_file.name} {len(not_ok_devs)} potentially have validation issue, and {len(ok_devs)} validate OK."
    console = Console(emoji=False, record=True)
    console.begin_capture()

    if failed:
        print("\n".join(not_ok_devs))
    elif passed:
        print("\n".join(ok_devs))
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
        print(f"\n[cyan]Writing output to {outfile}... ", end="")
        outfile.write_text(typer.unstyle(outdata))  # typer.unstyle(outdata) also works
        print("[italic green]Done")


@app.command(short_help="Batch Deploy groups, sites, devices... from file", hidden=True)
def deploy(
    import_file: Path = typer.Argument(None, exists=True, show_default=False,),
    show_example: bool = typer.Option(False, "--example", help="Show Example import file format.", show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Batch Deploy from import.

    Batch Deploy can deploy the following:
        - Groups (along with group level configs for APs and/or GWs if provided)
        - Sites
        - Labels
        - Devices

    Use --example to see example import file format.
    """
    # TODO allow optional argument for --example to show example in various formats.
    if show_example:
        print(examples.deploy)
        return

    if not import_file:
        _msg = [
            "Usage: cencli batch add [OPTIONS] WHAT:[sites|groups|devices] IMPORT_FILE",
            "Try 'cencli batch add ?' for help.",
            "",
            "Error: One of 'IMPORT_FILE' or --example should be provided.",
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)

    batch_deploy(import_file, yes)
    # cli.display_results(resp, tablefmt="action")


# FIXME appears this is not current state aware, have it only do the API calls not reflected in current state
@app.command()
def add(
    what: BatchAddArgs = typer.Argument(..., help="[cyan]macs[/] and [cyan]mpsk[/] are for cloud-auth", show_default=False,),
    import_file: Path = typer.Argument(None, exists=True, show_default=False, autocompletion=lambda incomplete: [],),  # HACK completion broken when trying to complete a Path
    ssid: str = typer.Option(None, "--ssid", help="SSID to associate mpsk definitions with [grey42 italic]Required and valid only with mpsk argument[/]", show_default=False,),
    show_example: bool = typer.Option(False, "--example", help="Show Example import file format.", show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Perform batch Add operations using import data from file
    """
    if show_example:
        print(getattr(examples, f"add_{what}"))
        return

    if not import_file:
        _msg = [
            "Usage: cencli batch add [OPTIONS] WHAT:[sites|groups|devices|macs|mpsk] IMPORT_FILE",
            "Try 'cencli batch add ?' for help.",
            "",
            "Error: One of 'IMPORT_FILE' or --example should be provided.",
        ]
        cli.exit("\n".join(_msg))

    caption, cleaner, tablefmt = None, None, "action"
    if what == "sites":
        resp = batch_add_sites(import_file, yes=yes)
        tablefmt = "rich"
    elif what == "groups":
        resp = batch_add_groups(import_file, yes=yes)
        cleaner = cleaner.parse_caas_response
    elif what == "devices":
        resp = batch_add_devices(import_file, yes=yes)
        if [r for r in resp if not r.ok and r.url.path.endswith("/subscriptions/assign")]:
            log.warning("Aruba Central took issue with some of the devices when attempting to assign subscription.  It will typically stop processing when this occurs, meaning valid devices may not have their license assigned.", caption=True)
            log.info(f"Use [cyan]cencli batch verify {import_file}[/] to check status of license assignment.", caption=True, log=False)
    elif what == "labels":
        resp = batch_add_labels(import_file, yes=yes)
    elif what == "macs":
        resp = batch_add_cloudauth("mac", import_file, yes=yes)
        caption = (
            "Use [cyan]cencli show cloud-auth upload[/] to see the status of the import.\n"
            "Use [cyan]cencli show cloud-auth registered-macs[/] to see all registered macs."
        )
    elif what == "mpsk":
        if not ssid:
            cli.exit("[cyan]--ssid[/] option is required when uploading mpsk")
        resp = batch_add_cloudauth("mpsk", import_file, ssid=ssid, yes=yes)
        caption = (
            "Use [cyan]cencli show cloud-auth upload mpsk[/] to see the status of the import."
        )

    cli.display_results(resp, tablefmt=tablefmt, title=f"Batch Add {what}", caption=caption, cleaner=cleaner)


# TODO archive and unarchive have the same block this is used by batch delete
def show_archive_results(res: Response) -> None:

    caption = res.output.get("message")
    action = res.url.name
    if res.get("succeeded_devices"):
        title = f"Devices successfully {action}d."
        data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
        cli.display_results(data=data, title=title, caption=caption)
    if res.get("failed_devices"):
        title = f"Devices that [bright_red]failed[/] to {action}d."
        data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
        cli.display_results(data=data, title=title, caption=caption)


def update_dev_inv_cache(console: Console, batch_resp: List[Response], cache_devs: List[CentralObject], devs_in_monitoring: List[CentralObject], inv_del_serials: List[str], ui_only: bool = False) -> None:
    br = BatchRequest
    all_ok = True if batch_resp and all(r.ok for r in batch_resp) else False
    cache_update_reqs = []
    with console.status(f'Performing {"[bright_green]full[/] " if not all_ok else ""}device cache update...'):
        if cache_devs and all_ok:
            cache_update_reqs += [br(cli.cache.update_dev_db, ([d.data for d in devs_in_monitoring],), remove=True)]
        else:
            cache_update_reqs += [br(cli.cache.update_dev_db)]

    with console.status(f'Performing {"[bright_green]full[/] " if not all_ok else ""}inventory cache update...'):
        if cache_devs or inv_del_serials and not ui_only:
            if all_ok:
                cache_update_reqs += [
                    br(
                        cli.cache.update_inv_db,
                        (list(set([*inv_del_serials, *[d.serial for d in devs_in_monitoring]])),),
                        remove=True
                    )
                ]
            else:
                cache_update_reqs += [br(cli.cache.update_inv_db)]

    # Update cache remove deleted items
    if cache_update_reqs:
        _ = cli.central.batch_request(cache_update_reqs)


# TODO DELME temporary debug testing
def batch_delete_devices_dry_run(data: Union[list, dict], *, ui_only: bool = False, cop_inv_only: bool = False, yes: bool = False) -> List[Response]:
    console = Console(emoji=False)

    if not data:
        print("[dark_orange]:warning:[/] [bright_red]Error[/] No data resulted from parsing of import file.")
        raise typer.Exit(1)

    serials_in = [dev["serial"].upper() for dev in data]

    cache_devs: List[CentralObject | None] = [cli.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False) for d in serials_in]  # returns None if device not found in cache after update
    not_in_inventory: List[str] = [d for d, c in zip(serials_in, cache_devs) if c is None]
    cache_devs: List[CentralObject] = [c for c in cache_devs if c]
    _all_in_inventory: Dict[str, Document] = cli.cache.inventory_by_serial
    inv_del_serials: List[str] = [s for s in serials_in if s in _all_in_inventory]

    # Devices in monitoring (have a status), If only in inventory they lack status
    aps, switches, stacks, gws, _stack_ids = [], [], [], [], []
    for dev in cache_devs:
        if not dev.status:
            continue
        elif dev.generic_type == "ap":
            aps += [dev]
        elif dev.generic_type == "gw":
            gws += [dev]
        elif dev.generic_type == "switch":
            if dev.swack_id is None:
                switches += [dev]
            elif dev.swack_id in _stack_ids:
                continue
            else:
                _stack_ids += [dev.swack_id]
                stacks += [dev]
        else:
            raise DevException(f'Unexpected device type {dev.generic_type}')

    devs_in_monitoring = [*aps, *switches, *stacks, *gws]

    console.rule(f"{len(cache_devs)} cache_devs")
    console.print("\ncache_devs=")
    _ = [console.print(c.rich_help_text) for c in cache_devs]
    console.rule("")
    console.print(f"\n{not_in_inventory=}\n\n_all_in_inventory (keys)={list(_all_in_inventory.keys())}\n\n{inv_del_serials=}")
    console.rule(f"{len(devs_in_monitoring)} devs_in_monitoring")
    _ = [console.print(c.rich_help_text) for c in devs_in_monitoring]
    console.rule("")
    console.print(f"Size of Inventory DB: {len(cli.cache.inventory)}")
    console.print(f"Size of Device DB: {len(cli.cache.devices)}")
    # inspect(cli.cache, console=console)


def batch_delete_devices(data: list | dict, *, ui_only: bool = False, cop_inv_only: bool = False, yes: bool = False, force: bool = False,) -> List[Response]:
    br = cli.central.BatchRequest
    console = Console(emoji=False)

    if not data:
        cli.exit("[bright_red]Error[/]: Parsing of import file resulted in [bright_red italic bold]no[/] data.")

    serials_in = [dev["serial"].upper() for dev in data]

    # TODO Literally copy/paste from clidel.py (then modified)... maybe move some things to clishared or clicommon
    # to avoid duplication ... # FIXME update clidel with corrections made below
    cache_devs: List[CentralObject | None] = [cli.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False) for d in serials_in]  # returns None if device not found in cache after update
    if len(serials_in) != len(cache_devs):
        log.warning(f"DEV NOTE: Error len(serials_in) ({len(serials_in)}) != len(cache_devs) ({len(cache_devs)})", show=True)
    else:
        log.warning(f"DEV NOTE: Error len(serials_in) ({len(serials_in)}) != len(cache_devs) ({len(cache_devs)})", show=True)
    not_in_inventory: List[str] = [d for d, c in zip(serials_in, cache_devs) if c is None]
    cache_devs: List[CentralObject] = [c for c in cache_devs if c]
    _all_in_inventory: Dict[str, Document] = cli.cache.inventory_by_serial
    inv_del_serials: List[str] = [s for s in serials_in if s in _all_in_inventory]

    # Devices in monitoring (have a status), If only in inventory they lack status
    aps, switches, stacks, gws, _stack_ids = [], [], [], [], []
    for dev in cache_devs:
        if not dev.status:
            continue
        elif dev.generic_type == "ap":
            aps += [dev]
        elif dev.generic_type == "gw":
            gws += [dev]
        elif dev.generic_type == "switch":
            if dev.swack_id is None:
                switches += [dev]
            elif dev.swack_id in _stack_ids:
                continue
            else:
                _stack_ids += [dev.swack_id]
                stacks += [dev]
        else:
            raise DevException(f'Unexpected device type {dev.generic_type}')

    devs_in_monitoring = [*aps, *switches, *stacks, *gws]

    _serials = inv_del_serials if not force else serials_in
    # archive / unarchive removes any subscriptions (less calls than determining the subscriptions for each then unsubscribing)
    # It's OK to send both despite unarchive depending on archive completing first, as the first call is always done solo to check if tokens need refreshed.
    arch_reqs = [] if ui_only or not _serials else [
        br(cli.central.archive_devices, (_serials,)),
        br(cli.central.unarchive_devices, (_serials,)),
    ]

    # cop only delete devices from GreenLake inventory
    cop_del_reqs = [] if not _serials or not config.is_cop else [
        br(cli.central.cop_delete_device_from_inventory, (_serials,))
    ]

    # build reqs to remove devs from monit views.  Down devs now, Up devs delayed to allow time to disc.
    mon_del_reqs, delayed_mon_del_reqs = [], []
    for dev_type, _devs in zip(["ap", "switch", "stack", "gateway"], [aps, switches, stacks, gws]):
        if _devs:
            down_now =  [d.serial if dev_type != "stack" else d.swack_id for d in _devs if d.status.lower() == "down"]
            up_now =  [d.serial if dev_type != "stack" else d.swack_id for d in _devs if d.status.lower() == "up"]
            if [*down_now, *up_now]:
                func = getattr(cli.central, f"delete_{dev_type}")
                if down_now:
                    mon_del_reqs += [br(func, s) for s in down_now]
                if up_now:
                    delayed_mon_del_reqs += [br(func, s) for s in up_now]

    # warn about devices that were not found
    if not_in_inventory:
        console.print("\n[dark_orange]Warning[/]: The following provided devices were not found in the inventory.")
        _ = [console.print(f"    [cyan]{d}[/]") for d in not_in_inventory]
        print(f"{'[bright_green italic]They will be skipped[/]' if not force else '[cyan]-F[/]|[cyan]--force[/] option provided, [bright_green italic]Will send call to delete anyway[/]'}\n")

    # None of the provided devices were found in cache or inventory
    if not [*arch_reqs, *mon_del_reqs, *delayed_mon_del_reqs, *cop_del_reqs]:
        cli.exit("Everything is as it should be, nothing to do.", code=0)

    # construnct confirmation msg
    if force:
        _msg = f"[bright_red]Delete[/] [cyan]{serials_in[0]}[/]\n"
        if len(serials_in) > 1:
            _msg += "\n".join([f"       [cyan]{d}[/]" for d in serials_in[1:]])
    else:
        _msg = f"[bright_red]Delete[/] {cache_devs[0].summary_text}\n"
        if len(cache_devs) > 1:
            _msg += "\n".join([f"       {d.summary_text}" for d in cache_devs[1:]])

    if ui_only:
        _total_reqs = len(mon_del_reqs)
    elif cop_inv_only:
        _total_reqs = len(cop_del_reqs)
    else:
        _total_reqs = len([*arch_reqs, *cop_del_reqs, *mon_del_reqs, *delayed_mon_del_reqs])

    if ui_only:
        if delayed_mon_del_reqs:
            print(f"{len(delayed_mon_del_reqs)} of the {len(serials_in)} provided are currently online, devices can only be removed from UI if they are offline.")
            delayed_mon_del_reqs = []
        if not mon_del_reqs:
            cli.exit("No devices found to remove from UI... Exiting")
        else:
            _msg += "\n[italic cyan]devices will be removed from UI only, Will appear again once they connect to Central.[/]"

    _msg += f"\n\n[italic dark_olive_green2]Will result in {_total_reqs} additional API Calls."

    # Perfrom initial delete actions (Any devs in inventory and any down devs in monitoring)
    console.print(_msg)
    batch_resp = []
    if yes or typer.confirm("\nProceed?", abort=True):
        if not cop_inv_only:
            batch_resp = cli.central.batch_request([*arch_reqs, *mon_del_reqs])
            if arch_reqs and len(batch_resp) >= 2:
                # if archive requests all pass we summarize the result.
                if all([r.ok for r in batch_resp[0:2]]) and all([not r.get("failed_devices") for r in batch_resp[0:2]]):
                    batch_resp[0].output = batch_resp[0].output.get("message")
                    batch_resp[1].output = f'  {batch_resp[1].output.get("message", "")}\n  Subscriptions successfully removed for {len(batch_resp[1].output.get("succeeded_devices"))} devices.\n  [italic]archive/unarchive flushes all subscriptions for a device.'
                else:
                    show_archive_results(batch_resp[0])  # archive
                    show_archive_results(batch_resp[1])  # unarchive
                    batch_resp = batch_resp[2:]

            if not force and not all([r.ok for r in batch_resp]):  # EARLY EXIT ON FAILURE (archive failures alone will proceed as they are removed from batch_resp)
                log.warning("[bright_red]A Failure occured aborting remaining actions.[/]", caption=True)
                update_dev_inv_cache(console, batch_resp=batch_resp, cache_devs=cache_devs, devs_in_monitoring=devs_in_monitoring, inv_del_serials=inv_del_serials, ui_only=ui_only)

                cli.display_results(batch_resp, exit_on_fail=True, caption="A Failure occured, Re-run command to perform remaining actions.", tablefmt="action")

    if not delayed_mon_del_reqs and not cop_del_reqs:
        # if all reqs OK cache is updated by deleting specific items, otherwise it's a full cache refresh
        update_dev_inv_cache(console, batch_resp=batch_resp, cache_devs=cache_devs, devs_in_monitoring=devs_in_monitoring, inv_del_serials=inv_del_serials, ui_only=ui_only)

        if batch_resp:  # Can occur if archive/unarchive has failures batch_resp[2:] could be an empty list.
            cli.display_results(batch_resp, tablefmt="action")
        cli.exit("[green italic]No more calls to perform[/]", code=0)

    elif delayed_mon_del_reqs and not cop_inv_only:
        del_resp = []
        del_reqs_try = delayed_mon_del_reqs.copy()
        _delay = 10 if not switches else 30  # switches take longer to drop off
        for _try in range(4):
            _word = "more " if _try > 0 else ""
            _prefix = "" if _try == 0 else f"\[Attempt {_try + 1}] "
            _delay -= (5 * _try) # reduce delay by 5 secs for each request
            for _ in track(range(_delay), description=f"{_prefix}[green]Allowing {_word}time for devices to disconnect."):
                sleep(1)

            _del_resp = cli.central.batch_request(del_reqs_try, continue_on_fail=True)
            if _try == 3:
                if not all([r.ok for r in _del_resp]):
                    print("\n[dark_orange]:warning:[/] Retries exceeded. Devices still remain Up in central and cannot be deleted.  This command can be re-ran once they have disconnected.")
                del_resp += _del_resp
            else:
                del_resp += [r for r in _del_resp if r.ok or isinstance(r.output, dict) and r.output.get("error_code", "") != "0007"]

            del_reqs_try = [del_reqs_try[idx] for idx, r in enumerate(_del_resp) if not r.ok and isinstance(r.output, dict) and r.output.get("error_code", "") == "0007"]
            if del_reqs_try:
                print(f"{len(del_reqs_try)} out of {len([*mon_del_reqs, *delayed_mon_del_reqs])} device{'s are' if len(del_reqs_try) > 1 else ' is'} still [bright_green]Up[/] in Central")
            else:
                break

        batch_resp += del_resp or _del_resp

        if batch_resp:
            update_dev_inv_cache(console, batch_resp=batch_resp, cache_devs=cache_devs, devs_in_monitoring=devs_in_monitoring, inv_del_serials=inv_del_serials, ui_only=ui_only)

    # On COP delete devices from GreenLake inventory (only available on CoP)
    # TODO test against a cop system
    # TODO add to cencli delete device ...
    cop_del_resp = []
    if cop_del_reqs:
        cop_del_resp = cli.central.batch_request(cop_del_reqs)
        if not all(r.ok for r in cop_del_resp):
            log.error("[bright_red]Errors occured during CoP GreenLake delete", caption=True)

    if cop_del_resp:
        batch_resp += cop_del_resp
    elif cop_inv_only and cop_del_resp:
        batch_resp = cop_del_resp

    if batch_resp:
        cli.display_results(batch_resp, tablefmt="action")


def batch_delete_sites(data: Union[list, dict], *, yes: bool = False) -> List[Response]:
    central = cli.central
    del_list = []
    verified_sites: List[SiteImport] = []
    for i in data:
        if isinstance(i, str) and isinstance(data[i], dict):
            out_dict = _convert_site_key(
                {"site_name": i, **data[i]}
            )
        else:
            out_dict = _convert_site_key(i)

        verified_sites += [SiteImport(**out_dict)]

    site_names = [
        f"  [cyan]{s.site_name}[/]" for s in verified_sites
    ]
    if len(site_names) > 7:
        site_names = [*site_names[0:3], "  ...", *site_names[-3:]]

    for site in verified_sites:
        cache_site = cli.cache.get_site_identifier(site.site_name)
        del_list += [cache_site.id]

    print(f"The following {len(del_list)} sites will be [bright_red]deleted[/]:")
    _ = [print(s) for s in site_names]
    if yes or typer.confirm("Proceed?", abort=True):
        resp = central.request(central.delete_site, del_list)
        if resp:
            cache_del_res = asyncio.run(cli.cache.update_site_db(data=del_list, remove=True))
            if len(cache_del_res) != len(del_list):
                log.warning(
                    f"Attempt to delete entries from Site Cache returned {len(cache_del_res)} "
                    f"but we tried to delete {len(del_list)} sites.",
                    show=True
                )
            return resp

# TODO copy/paste logic from clidel.py groups()
def batch_delete_groups_or_labels(data: Union[list, dict], *, yes: bool = False, del_groups: bool = None, del_labels: bool = None) -> List[Response]:
    if all([not arg for arg in [del_groups, del_labels]]):
        del_groups = True  # Default to group delete
    group_name_aliases = ["name", "group_name", "group"]
    label_name_aliases = ["name", "label_name", "label"]
    name_aliases = group_name_aliases if del_groups else label_name_aliases
    cache_func = cli.cache.get_group_identifier if del_groups else cli.cache.get_label_identifier
    del_func = cli.central.delete_group if del_groups else cli.central.delete_label
    cache_del_func = cli.cache.update_group_db if del_groups else cli.cache.update_label_db
    word = "group" if del_groups else "label"

    _names = None
    if isinstance(data, list):
        if isinstance(data[0], dict):
            _names = [g.get(name_aliases[0], g.get(name_aliases[1], g.get(name_aliases[2]))) for g in data]
            # We allow simply using "labels" header for labels. With csv this is converted to List[dict] where each label has "labels" as key
            if del_labels and all([x is None for x in _names]):
                _names = [label.get("labels") for label in data]
            if None in _names:
                raise MissingFieldException("Data is missing 'name' field")
        elif all([isinstance(item, str) for item in data]):
            _names = data
    if isinstance(data, dict):
        _names = list(data.keys())

    if _names is None:
        raise ImportException(f'Unable to get {word} names from provided import data')

    cache_objs = [cache_func(g) for g in _names]
    reqs = [cli.central.BatchRequest(del_func, (g.name if del_groups else g.id, )) for g in cache_objs]

    _msg = "\n".join([f"  [cyan]{g.name}[/]" for g in cache_objs])
    _msg = _msg.lstrip() if len(cache_objs) == 1 else f"\n{_msg}"
    if del_groups:
        _msg = f"[bright_red]Delete[/] {'group ' if len(cache_objs) == 1 else f'{len(reqs)} groups:'}{_msg}"
    elif del_labels:
        _msg = f"[bright_red]Delete[/] {'label ' if len(cache_objs) == 1 else f'{len(reqs)} labels:'}{_msg}"
    print(_msg)

    if len(reqs) > 1:
        print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")
        if resp:
            upd_res = asyncio.run(cache_del_func(data=[{"name": g.name} for g in cache_objs], remove=True))
            log.debug(f"cache update to remove deleted {'groups' if del_groups else 'labels'} returns {upd_res}")


# FIXME The Loop logic keeps trying if a delete fails despite the device being offline, validate the error check logic
# TODO batch delete sites does a call for each site, not multi-site endpoint?
@app.command(short_help="Delete devices.", help=help_text.batch_delete_devices)
def delete(
    what: BatchDelArgs = typer.Argument(..., show_default=False,),
    import_file: Path = typer.Argument(None, exists=True, readable=True, show_default=False, autocompletion=lambda incomplete: [],),
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views.  Devices remains assigned and licensed.  Devices must be offline."),
    cop_inv_only: bool = typer.Option(False, "--cop-only", help="Only delete device from CoP inventory.", hidden=True),
    dry_run: bool = typer.Option(False, "--dry-run", help="Testing/Debug Option", hidden=True),
    force: bool = typer.Option(False, "-F", "--force", help="Perform API calls based on input file without validating current states (valid for devices)"),
    show_example: bool = typer.Option(
        False, "--example",
        help="Show Example import file format.",
        show_default=False,
    ),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Batch delete Aruba Central Objects [devices|sites|groups|labels] based on input from file.
    """
    if show_example:
        print(getattr(examples, f"delete_{what}"))
        return

    # TODO common string helpers... started strings.py
    elif not import_file:
        _msg = [
            "Usage: cencli batch delete [OPTIONS] ['devices'|'sites'|'groups'] IMPORT_FILE",
            "Use [cyan]cencli batch delete --help[/] for help.",
            "",
            "[bright_red]Error[/]: Invalid combination of arguments / options.",
            "Provide IMPORT_FILE or --show-example"
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)

    data = config.get_file_data(import_file, text_ok=what == "labels")

    if what == "devices":
        if isinstance(data, dict) and "devices" in data:
            data = data["devices"]
        if not dry_run:
            resp = batch_delete_devices(data, ui_only=ui_only, cop_inv_only=cop_inv_only, yes=yes, force=force)
        else:
            resp = batch_delete_devices_dry_run(data, ui_only=ui_only, cop_inv_only=cop_inv_only, yes=yes)
    elif what == "sites":
        if isinstance(data, dict) and "sites" in data:
            data = data["sites"]
        resp = batch_delete_sites(data, yes=yes)
    elif what == "groups":
        if isinstance(data, dict) and "groups" in data:
            data = data["groups"]
        resp = batch_delete_groups_or_labels(data, yes=yes, del_groups=True)
    elif what == "labels":
        if isinstance(data, dict) and "labels" in data:
            data = data["labels"]
        elif isinstance(data, list) and all([isinstance(item, str) for item in data]):
            if data[0] == "labels":
                data = data[1:]
        resp = batch_delete_groups_or_labels(data, yes=yes, del_labels=True)
    cli.display_results(resp, tablefmt="action")


# TODO if from get inventory API endpoint subscriptions are under services key, if from endpoint file currently uses license key (maybe make subscription key)
def _build_sub_requests(devices: List[dict], unsub: bool = False) -> List[BatchRequest]:
    if "'license': " in str(devices):
        devices = [{**d, "services": d["license"]} for d in devices]
    elif "'subscription': " in str(devices):
        devices = [{**d, "services": d["subscription"]} for d in devices]

    subs = set([d["services"] for d in devices if d["services"]])  # TODO Inventory actually returns a list for services if the device has multiple subs this would be an issue
    devices = [d for d in devices if d["services"]]  # filter any devs tghat currently do not have subscription

    try:
        subs = [cli.cache.LicenseTypes(s.lower().replace("_", "-").replace(" ", "-")).name for s in subs]
    except ValueError as e:
        sub_names = "\n".join(cli.cache.license_names)
        print("[bright_red]Error[/]: " + str(e).replace("ValidLicenseTypes", f'subscription name.\n[cyan]Valid subscriptions[/]: \n{sub_names}'))
        raise typer.Exit(1)

    devs_by_sub = {s: [] for s in subs}
    for d in devices:
        devs_by_sub[d["services"].lower().replace("-", "_").replace(" ", "_")] += [d["serial"]]

    func = cli.central.unassign_licenses if unsub else cli.central.assign_licenses
    return [
        BatchRequest(func, serials=serials, services=sub) for sub, serials in devs_by_sub.items()
    ]

@app.command()
def subscribe(
    import_file: Path = typer.Argument(None, help="Remove subscriptions for devices specified in import file", exists=True, readable=True, show_default=False),
    show_example: bool = typer.Option(
        False, "--example",
        help="Show Example import file format.",
        show_default=False,
    ),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Batch subscribe devices

    Assign subscription license to devices specified in import file.

    [italic]This command assumes devices have already been added to GreenLake,
    to add devices and assign subscription use [cyan]cencli batch add devices <IMPORT_FILE>[/][/]
    """
    if show_example:
        print(getattr(examples, "subscribe"))  # TODO need example should be same as add devices
        return
    elif not import_file:
        _msg = [
            "Usage: cencli batch subscribe [OPTIONS] IMPORT_FILE",
            "Use [cyan]cencli batch subscribe --help[/] for help.",
            "",
            "[bright_red]Error[/]: Invalid combination of arguments / options.",
            "Provide IMPORT_FILE argument or --show-example flag."
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)
    elif import_file:
        devices = config.get_file_data(import_file)
        if "devices" in devices:
            devices = devices["devices"]

        sub_reqs = _build_sub_requests(devices)

        cli.display_results(data=devices, tablefmt="rich", title="Devices to be subscribed", caption=f'{len(devices)} devices will have subscriptions assigned')
        print("[bright_green]All Devices Listed will have subscriptions assigned.[/]")
        if yes or typer.confirm("\nProceed?", abort=True):
            resp = cli.central.batch_request(sub_reqs)

    cli.display_results(resp, tablefmt="action")

@app.command()
def unsubscribe(
    import_file: Path = typer.Argument(None, help="Remove subscriptions for devices specified in import file", exists=True, readable=True, show_default=False),
    never_connected: bool = typer.Option(False, "-N", "--never-connected", help="Remove subscriptions from any devices in inventory that have never connected to Central", show_default=False),
    dis_cen: bool = typer.Option(False, "-D", "--dis-cen", help="Dissasociate the device from the Aruba Central App in Green Lake"),
    show_example: bool = typer.Option(
        False, "--example",
        help="Show Example import file format.",
        show_default=False,
    ),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Batch Unsubscribe devices

    Can Unsubscribe devices specified in import file or all devices in the inventory that
    have never connected to Aruba Central (-N | --never-connected)

    Use (-D | --dis-cen) flag to also dissasociate the devices from the Aruba Central app in Green Lake.
    """
    if show_example:
        print(getattr(examples, "unsubscribe"))  # TODO need example should be same as add devices
        return
    elif never_connected:
        resp = cli.cache.get_devices_with_inventory()
        if not resp:
            cli.display_results(resp, exit_on_fail=True)
        else:
            devices = [d for d in resp.output if d.get("status") is None and d["services"]]
            if dis_cen:
                resp = batch_delete_devices(devices, yes=yes)
            else:
                unsub_reqs = _build_sub_requests(devices, unsub=True)

                cli.display_results(data=devices, tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
                print("[bright_green]All Devices Listed will have subscriptions unassigned.[/]")
                if yes or typer.confirm("\nProceed?", abort=True):
                    resp = cli.central.batch_request(unsub_reqs)
    elif not import_file:
        _msg = [
            "Usage: cencli batch unsubscribe [OPTIONS] IMPORT_FILE",
            "Use [cyan]cencli batch unsubscribe --help[/] for help.",
            "",
            "[bright_red]Error[/]: Invalid combination of arguments / options.",
            "Provide IMPORT_FILE argument or at least one of: -N, --never-connected, --show-example flags."
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)
    elif import_file:
        devices = config.get_file_data(import_file)
        if "devices" in devices:
            devices = devices["devices"]

        unsub_reqs = _build_sub_requests(devices, unsub=True)

        cli.display_results(data=devices, tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
        print("[bright_green]All Devices Listed will have subscriptions unassigned.[/]")
        if yes or typer.confirm("\nProceed?", abort=True):
            resp = cli.central.batch_request(unsub_reqs)

    if not dis_cen and all([r.ok for r in resp]):
        inv_devs = [{**d, "services": None} for d in devices]
        cache_resp = cli.cache.InvDB.update_multiple([(dev, cli.cache.Q.serial == dev["serial"]) for dev in inv_devs])
        if len(inv_devs) != len(cache_resp):
            log.warning(
                f'Inventory cache update may have failed.  Expected {len(inv_devs)} records to be updated, cache update resulted in {len(cache_resp)} records being updated'
                )


    cli.display_results(resp, tablefmt="action")


@app.command()
def rename(
    what: BatchRenameArgs = typer.Argument(..., show_default=False,),
    import_file: Path = typer.Argument(None, metavar="['lldp'|IMPORT FILE PATH]", show_default=False,),  # TODO completion
    lldp: bool = typer.Option(None, "--lldp", help="Automatic AP rename based on lldp info from upstream switch.",),
    default_only: bool = typer.Option(False, "-D", "--default-only", help="[LLDP rename] Perform only on APs that still have default name.",),
    ap: str = typer.Option(None, metavar=iden.dev, help="[LLDP rename] Perform on specified AP", show_default=False,),
    label: str = typer.Option(None, help="[LLDP rename] Perform on APs with specified label", show_default=False,),
    group: str = typer.Option(None, help="[LLDP rename] Perform on APs in specified group", show_default=False,),
    site: str = typer.Option(None, metavar=iden.site, help="[LLDP rename] Perform on APs in specified site", show_default=False,),
    model: str = typer.Option(None, help="[LLDP rename] Perform on APs of specified model", show_default=False,),  # TODO model completion
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging",),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Perform AP rename in batch from import file or automatically based on LLDP"""

    if str(import_file).lower() == "lldp":
        lldp = True
        import_file = None

    if not import_file and not lldp:
        print(":warning:  [bright_red]ERROR[/]: Missing required parameter [IMPORT_FILE|'lldp']")
        raise typer.Exit(1)

    central = cli.central
    if import_file:
        data = config.get_file_data(import_file)

        if not data:
            print(f":warning:  [bright_red]ERROR[/] {import_file.name} not found or empty.")
            raise typer.Exit(1)

        resp = None
        if what == "aps":
            # transform flat csv struct to Dict[str, Dict[str, str]] {"<AP serial>": {"hostname": "<desired_name>"}}
            if import_file.suffix in [".csv", ".tsv", ".dbf"]:
                if data and len(data.headers) < 3:
                    if "name" in data.headers:
                        data = [{k if k != "name" else "hostname": d[k] for k in d} for d in data.dict]
                        data.headers["hostname"] = data.headers.pop(
                            data.headers.index(data.headers["name"])
                        )
                    data = {
                        i.get("serial", i.get("serial_number", i.get("serial_num", "ERROR"))):
                        {k: v for k, v in i.items() if not k.startswith("serial")} for i in data.dict
                    }

            calls, conf_msg = [], [typer.style("\nNames gathered from import:", fg="bright_green")]
            for ap in data:  # keyed by serial num
                conf_msg += [f"  {ap}: {data[ap]['hostname']}"]
                calls.append(central.BatchRequest(central.update_ap_settings, ap, **data[ap]))

            if len(conf_msg) > 6:
                conf_msg = [*conf_msg[0:3], "...", *conf_msg[-3:]]
            typer.echo("\n".join(conf_msg))

            if yes or typer.confirm("\nProceed with AP rename?", abort=True):
                resp = central.batch_request(calls)

    elif lldp:
        kwargs = {}
        if group:
            kwargs["group"] = cli.cache.get_group_identifier(group).name
        if ap:
            kwargs["serial"] = cli.cache.get_dev_identifier(ap, dev_type="ap").serial
        if site:
            kwargs["site"] = cli.cache.get_site_identifier(site).name
        if model:
            kwargs["model"] = model
        if label:
            kwargs["label"] = label

        resp = do_lldp_rename(_lldp_rename_get_fstr(), default_only=default_only, **kwargs)

    cli.display_results(resp, tablefmt="action")


def batch_move_devices(import_file: Path, *, yes: bool = False, do_group: bool = False, do_site: bool = False, do_label: bool = False,):
    """Batch move devices based on contents of import file

    Args:
        import_file (Path): Import file
        yes (bool, optional): Bypass confirmation prompts. Defaults to False.
        do_group (bool, optional): Process group moves based on import. Defaults to False.
        do_site (bool, optional): Process site moves based on import. Defaults to False.
        do_label (bool, optional): Process label assignment based on import. Defaults to False.

    Group/Site/Label are processed by default, unless one of more of do_group, do_site, do_label is specified.

    Raises:
        typer.Exit: Exits with error code if none of name/ip/mac are provided for each device.
    """
    # TODO improve logic.  if they are moving to a group we can use inventory as backup
    # BUT if they are moving to a site it has to be connected to central first.  So would need to be in cache
    # TODO Break this up / func for each move type...
    if all([arg is False for arg in [do_site, do_label, do_group]]):
        do_site = do_label = do_group = True
    devices = config.get_file_data(import_file)

    dev_idens = [d.get("serial", d.get("mac", d.get("name", "INVALID"))) for d in devices]
    if "INVALID" in dev_idens:
        print(f'[bright_red]Error[/]: missing required field for {dev_idens.index("INVALID") + 1} device in import file.')
        raise typer.Exit(1)

    cache_devs = [cli.cache.get_dev_identifier(d, include_inventory=True) for d in dev_idens]

    site_rm_reqs, site_rm_msgs = {}, {}
    site_mv_reqs, site_mv_msgs = {}, {}
    pregroup_mv_reqs, pregroup_mv_msgs = {}, {}
    group_mv_reqs, group_mv_msgs = {}, {}
    group_mv_cx_retain_reqs, group_mv_cx_retain_msgs = {}, {}
    label_ass_reqs, label_ass_msgs = {}, {}

    console = Console(emoji=False)
    for cd, d in zip(cache_devs, devices):
        has_connected = True if cd.get("status") else False
        if do_group:
            _skip = False
            to_group = d.get("group")
            retain_config = d.get("retain_config")
            if retain_config:
                if str(retain_config).lower() in ["false", "no", "0"]:
                    retain_config = False
                elif str(retain_config).lower() in ["true", "yes", "1"]:
                    retain_config = True
                else:
                    print(f'{cd.help_text} has an invalid value ({retain_config}) for "retain_config".  Value should be "true" or "false" (or blank which is evaluated as false).  Aborting...')
                    raise typer.Exit(1)
            if to_group:
                if to_group not in cli.cache.group_names:
                    to_group = cli.cache.get_group_identifier(to_group)
                    to_group = to_group.name

                if to_group == cd.get("group"):
                    console.print(f'{cd.rich_help_text}: is already in group [magenta]{to_group}[/]. Ignoring.')
                    _skip = True

                # Determine if device is in inventory only determines use of pre-provision group vs move to group
                if not has_connected:
                    _dict = pregroup_mv_reqs
                    msg_dict = pregroup_mv_msgs
                    if retain_config:
                        console.print(f'[bright_red]WARNING[/]: {cd.rich_help_text} Group assignment is being ignored.')
                        console.print(f'  [italic]Device has not connected to Aruba Central, it must be "pre-provisioned to group [magenta]{to_group}[/]".  [cyan]retain_config[/] is only valid on group move not group pre-provision.[/]')
                        console.print('  [italic]To onboard and keep the config, allow it to onboard to the default unprovisioned group (default behavior without pre-provision), then move it once it appears in Central.')
                        _skip = True
                else:
                    _dict = group_mv_reqs if not retain_config else group_mv_cx_retain_reqs
                    msg_dict = group_mv_msgs if not retain_config else group_mv_cx_retain_msgs

                if not _skip:
                    if to_group not in _dict:
                        _dict[to_group] = [cd.serial]
                        msg_dict[to_group] = [cd.rich_help_text]
                    else:
                        _dict[to_group] += [cd.serial]
                        msg_dict[to_group] += [cd.rich_help_text]


        if do_site:
            to_site = d.get("site")
            now_site = cd.get("site")
            if to_site:
                to_site = cli.cache.get_site_identifier(to_site)
                if now_site and now_site == to_site.name:
                    console.print(f'{cd.rich_help_text} Already in site [magenta]{to_site.name}[/].  Ignoring.')
                elif not has_connected:
                    # TODO Need cache update here.  This command doesn't preemptively update cache.  So if device has come onboard since they did a show all it will appear as if it has not checked in
                    console.print(f'{cd.rich_help_text} Has not checked in to Central.  It can not be added to site [magenta]{to_site.name}[/].  Ignoring.')
                else:
                    key = f'{to_site.id}~|~{cd.generic_type}'
                    if key not in site_mv_reqs:
                        site_mv_reqs[key] = [cd.serial]
                    else:
                        site_mv_reqs[key] += [cd.serial]

                    if to_site.name not in site_mv_msgs:
                        site_mv_msgs[to_site.name] = [cd.rich_help_text]
                    else:
                        site_mv_msgs[to_site.name] += [cd.rich_help_text]

                if now_site:
                    now_site = cli.cache.get_site_identifier(now_site)
                    if now_site.name != to_site.name:  # need to remove from current site
                        console.print(f'{cd.rich_help_text} will be removed from site [red]{now_site.name}[/] to facilitate move to site [bright_green]{to_site.name}[/]')
                        key = f'{now_site.id}~|~{cd.generic_type}'
                        if key not in site_rm_reqs:
                            site_rm_reqs[key] = [cd.serial]
                        else:
                            site_rm_reqs[key] += [cd.serial]

                        if to_site.name not in site_rm_msgs:
                            site_rm_msgs[to_site.name] = [cd.rich_help_text]
                        else:
                            site_rm_msgs[to_site.name] += [cd.rich_help_text]

        if do_label:
            to_label = d.get("label", d.get("labels"))
            if to_label:
                to_label = utils.listify(to_label)
                for label in to_label:
                    clabel = cli.cache.get_label_identifier(to_label)
                    if clabel.name in cd.get("labels"):
                        console.print(f'{cd.rich_help_text}, already assigned label [magenta]{label.name}[/]. Ingoring.')
                    else:
                        key = f'{clabel.id}~|~{cd.generic_type}'
                        if key not in label_ass_reqs:
                            label_ass_reqs[key] = [cd.serial]
                        else:
                            label_ass_reqs[key] += [cd.serial]

                        if clabel.name not in label_ass_msgs:
                            label_ass_msgs[clabel.name] = [cd.rich_help_text]
                        else:
                            label_ass_msgs[clabel.name] += [cd.rich_help_text]

    site_rm_reqs = []
    if site_rm_reqs:
        for k, v in site_rm_reqs.items():
            site_id, dev_type = k.split("~|~")
            site_rm_reqs += [cli.central.BatchRequest(cli.central.remove_devices_from_site, site_id=int(site_id), serial_nums=v, device_type=dev_type)]

    batch_reqs = []
    if site_mv_reqs:
        for k, v in site_mv_reqs.items():
            site_id, dev_type = k.split("~|~")
            batch_reqs += [cli.central.BatchRequest(cli.central.move_devices_to_site, site_id=int(site_id), serial_nums=v, device_type=dev_type)]
    if pregroup_mv_reqs:  # TODO fix inconsistency in param group_name vs group used on other similar funcs
        batch_reqs = [*batch_reqs, *[cli.central.BatchRequest(cli.central.preprovision_device_to_group, group_name=k, serial_nums=v) for k, v in pregroup_mv_reqs.items()]]
    if group_mv_reqs:
        batch_reqs = [*batch_reqs, *[cli.central.BatchRequest(cli.central.move_devices_to_group, group=k, serial_nums=v) for k, v in group_mv_reqs.items()]]
    if group_mv_cx_retain_reqs:
        batch_reqs = [*batch_reqs, *[cli.central.BatchRequest(cli.central.move_devices_to_group, group=k, serial_nums=v, cx_retain_config=True) for k, v in group_mv_reqs.items()]]
    if label_ass_reqs:
        for k, v in label_ass_reqs.items():
            label_id, dev_type = k.split("~|~")  # TODO fix inconsistency device_type serial_nums param order vs similar funcs.
            batch_reqs += [cli.central.BatchRequest(cli.central.assign_label_to_devices, label_id=int(label_id), device_type=dev_type, serial_nums=v)]

    _tot_req = len(site_rm_reqs) + len(batch_reqs)
    if not _tot_req:
        print("Nothing to do")
        raise typer.Exit(0)

    _msg = [""]
    if pregroup_mv_msgs:
        for group, devs in pregroup_mv_msgs.items():
            _msg += [f'The following {len(devs)} devices will be pre-provisioned to group [cyan]{group}[/]']
            if len(devs) > 6:
                devs = [*devs[0:3], "...", *devs[-3:]]
            _msg = [*_msg, *[f'  {dev}' for dev in devs]]
    if group_mv_msgs:
        for group, devs in group_mv_msgs.items():
            _msg += [f'The following {len(devs)} devices will be moved to group [cyan]{group}[/]']
            if len(devs) > 6:
                devs = [*devs[0:3], "...", *devs[-3:]]
            _msg = [*_msg, *[f'  {dev}' for dev in devs]]
    if group_mv_cx_retain_msgs:
        for group, devs in group_mv_cx_retain_msgs.items():
            _msg += [f'The following {len(devs)} devices will be moved to group [cyan]{group}[/].  CX config will be preserved.']
            if len(devs) > 6:
                devs = [*devs[0:3], "...", *devs[-3:]]
            _msg = [*_msg, *[f'  {dev}' for dev in devs]]
    if site_mv_msgs:
        for site, devs in site_mv_msgs.items():
            _msg += [f'The following {len(devs)} devices will be moved to site [cyan]{site}[/]']
            if len(devs) > 6:
                devs = [*devs[0:3], "...", *devs[-3:]]
            _msg = [*_msg, *[f'  {dev}' for dev in devs]]
    if site_rm_msgs:
        for site, devs in site_mv_msgs.items():
            _msg += [f'The following {len(devs)} devices will be [red]removed[/] to site [cyan]{site}[/]']
            if len(devs) > 6:
                devs = [*devs[0:3], "...", *devs[-3:]]
            _msg = [*_msg, *[f'  {dev}' for dev in devs]]
    if label_ass_msgs:
        for label, devs in label_ass_msgs.items():
            _msg += [f'The following {len(devs)} devices will be assigned [cyan]{label}[/] label']
            if len(devs) > 6:
                devs = [*devs[0:3], "...", *devs[-3:]]
            _msg = [*_msg, *[f'  {dev}' for dev in devs]]

    if _tot_req > 1:
        _msg += [f'\n{_tot_req} API calls will be performed.']

    console.print("\n".join(_msg))
    if yes or typer.confirm("\nProceed?", abort=True):
        site_rm_res = []
        if site_rm_reqs:
            site_rm_res = cli.central.batch_request(site_rm_reqs)
            if not all([r.ok for r in site_rm_res]):
                print("[bright_red]WARNING[/]: Some site remove requests failed, Aborting...")
                return site_rm_res
        batch_res = cli.central.batch_request(batch_reqs)

        # TODO need to update cache if successful
        return [*site_rm_res, *batch_res]


@app.command()
def move(
    # what: BatchAddArgs = typer.Argument("devices", show_default=False,),
    import_file: Path = typer.Argument(None, exists=True, show_default=False, autocompletion=lambda incomplete: [],),
    do_group: bool = typer.Option(False, "-G", "--group", help="process group move from import."),
    do_site: bool = typer.Option(False, "-S", "--site", help="process site move from import."),
    do_label: bool = typer.Option(False, "-L", "--label", help="process label assignment from import."),
    show_example: bool = typer.Option(False, "--example", help="Show Example import file format.", show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Perform batch Move devices to any or all of group / site / label based on import data from file.

    By default group/site/label assignment will be processed if found in the import file.
    Use -G|--group, -S|--site, -L|--label flags to only process specified moves, and ignore
    others even if found in the import.

    i.e. if import includes a definition for group, site, and label, and you only want to
    process the site move. Use the -S|--site flag, to ignore the other columns.
    """
    if show_example:
        print(examples.move_devices)
        return

    elif not import_file:
        _msg = [
            "Usage: cencli batch move [OPTIONS] WHAT:[devices] IMPORT_FILE",
            "Try 'cencli batch move ?' for help.",
            "",
            "Error: One of 'IMPORT_FILE' or --example should be provided.",
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)
    else:
        resp = batch_move_devices(import_file, yes=yes, do_group=do_group, do_site=do_site, do_label=do_label)
        cli.display_results(resp, tablefmt="action")


@app.command()
def archive(
    import_file: Path = typer.Argument(None, exists=True, show_default=False,),
    show_example: bool = typer.Option(False, "--example", help="Show Example import file format.", show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Batch archive devices based on import data from file.

    This will archive the devices in GreenLake
    """
    if show_example:
        print(examples.archive)
        return

    elif not import_file:
        _msg = [
            "Usage: cencli batch archive [OPTIONS] WHAT:[devices] IMPORT_FILE",
            "Try 'cencli batch archive ?' for help.",
            "",
            "Error: One of 'IMPORT_FILE' or --example should be provided.",
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)
    else:
        data = config.get_file_data(import_file, text_ok=True)
        if data and isinstance(data, list):
            if all([isinstance(x, dict) for x in data]):
                serials = [x.get("serial") or x.get("serial_num") for x in data]
            elif all(isinstance(x, str) for x in data):
                serials = data if not data[0].lower().startswith("serial") else data[1:]
        else:
            print(f"[bright_red]Error[/] Unexpected data structure returned from {import_file.name}")
            print("Use [cyan]cencli batch archive --example[/] to see expected format.")
            raise typer.Exit(1)

        res = cli.central.request(cli.central.archive_devices, serials)
        if res:
            caption = res.output.get("message")
            if res.get("succeeded_devices"):
                title = "Devices successfully archived."
                data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
                cli.display_results(data=data, title=title, caption=caption)
            if res.get("failed_devices"):
                title = "These devices failed to archived."
                data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
                cli.display_results(data=data, title=title, caption=caption)
        else:
            cli.display_results(res, tablefmt="action")


@app.command()
def unarchive(
    import_file: Path = typer.Argument(None, exists=True, show_default=False,),
    show_example: bool = typer.Option(False, "--example", help="Show Example import file format.", show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
        callback=cli.default_callback,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Batch unarchive devices based on import data from file.

    This will unarchive the devices (previously archived) in GreenLake
    """
    if show_example:
        print(examples.unarchive)
        return

    elif not import_file:
        _msg = [
            "Usage: cencli batch unarchive [OPTIONS] WHAT:[devices] IMPORT_FILE",
            "Try 'cencli batch unarchive ?' for help.",
            "",
            "Error: One of 'IMPORT_FILE' or --example should be provided.",
        ]
        print("\n".join(_msg))
        raise typer.Exit(1)
    else:
        data = config.get_file_data(import_file, text_ok=True)
        if data and isinstance(data, list):
            if all([isinstance(x, dict) for x in data]):
                serials = [x.get("serial") or x.get("serial_num") for x in data]
            elif all(isinstance(x, str) for x in data):
                serials = data if not data[0].lower().startswith("serial") else data[1:]
        else:
            print(f"[bright_red]Error[/] Unexpected data structure returned from {import_file.name}")
            print("Use [cyan]cencli batch unarchive --example[/] to see expected format.")
            raise typer.Exit(1)

        res = cli.central.request(cli.central.unarchive_devices, serials)
        if res:
            caption = res.output.get("message")
            if res.get("succeeded_devices"):
                title = "Devices successfully archived."
                data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
                cli.display_results(data=data, title=title, caption=caption)
            if res.get("failed_devices"):
                title = "These devices failed to archived."
                data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
                cli.display_results(data=data, title=title, caption=caption)
        else:
            cli.display_results(res, tablefmt="action")


@app.callback()
def callback():
    """
    Perform batch operations
    """
    pass


if __name__ == "__main__":
    app()
