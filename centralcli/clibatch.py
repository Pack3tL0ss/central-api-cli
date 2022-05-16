#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from enum import Enum
from pathlib import Path
from typing import List, Tuple
import typer
from pydantic import BaseModel, Extra, Field, ValidationError, validator
from rich.console import Console
from rich import print

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response, BatchRequest, caas, cleaner, cli, config, log, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response, BatchRequest, caas, cleaner, cli, config, log, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import BatchAddArgs, BatchRenameArgs, GatewayRole, GenericDevIdens, IdenMetaVars, SendConfigDevIdens, SiteStates, state_abbrev_to_pretty

iden_meta_vars = IdenMetaVars()
tty = utils.tty
app = typer.Typer()

class GroupImport(BaseModel):
    group: str
    allowed_types: List[GenericDevIdens] = Field(["ap", "gw", "cx", "sw"], alias="types")
    gw_role: GatewayRole = Field("branch", alias="gw-role")
    aos10: bool = False
    microbranch: bool = False
    wlan_tg: bool = Field(False, alias="wlan-tg")
    wired_tg: bool = Field(False, alias="wired-tg")
    monitor_only_sw: bool = Field(False, alias="monitor-only-sw")
    monitor_only_cx: bool = Field(False, alias="monitor-only-cx")
    gw_config: Path = Field(None, alias="gw-config")
    ap_config: Path = Field(None, alias="ap-config")
    gw_vars: Path = Field(None, alias="gw-vars")
    ap_vars: Path = Field(None, alias="ap-vars")

    class Config:
        use_enum_values = True

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
        extra = Extra.forbid
        use_enum_values = True
        allow_population_by_alias = True

    @validator("state")
    def short_to_long(cls, v: str) -> str:
        try:
            return SiteStates(state_abbrev_to_pretty.get(v.upper(), v.title())).value
        except ValueError:
            return SiteStates(v).value


class BatchDelArgs(str, Enum):
    sites = "sites"
    # aps = "aps"


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

def do_lldp_rename(fstr: str, **kwargs) -> Response:
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
    ap_dict = {d["serial"]: {k if k != "macaddr" else "mac": d[k] for k in d if k in _keys} for d in _all_aps}
    fstr_to_key = {
        "h": "neighborHostName",
        "m": "mac",
        "p": "remotePort",
        "M": "model",
        "S": "site",
        "s": "serial"
    }

    req_list, name_list, shown_promt = [], [], False
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
                                    if not shown_promt and typer.confirm(
                                        f"{_e1}"
                                        f"\n\nResult will be \""
                                        f"{typer.style(''.join(_src[slice(fi.i, fi2.o)]), fg='bright_green')}\""
                                        " for this segment."
                                        "\nOK to continue?"
                                    ):
                                        shown_promt = True
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
                if typer.confirm("Do you want to edit the fomat string and try again?", abort=True):
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

def batch_add_sites(import_file: Path, yes: bool = False) -> Response:
    central = cli.central
    name_aliases = ["site-name", "site", "name"]
    _site_aliases = {
        "site-name": "site_name",
        "site": "site_name",
        "name": "site_name",
        "latitude": "lat",
        "longitude": "lon",
        "zipcode": "zip",
    }

    def convert_site_key(_data: dict) -> dict:
        _data = {
            **_data.get("site_address", {}),
            **_data.get("geolocation", {}),
            **{k: v for k, v in _data.items() if k not in ["site_address", "geolocation"]}
        }
        _data = {_site_aliases.get(k, k): v for k, v in _data.items()}
        return _data

    data = config.get_file_data(import_file)
    if "sites" in data:
        data = data["sites"]

    resp = None
    verified_sites: List[SiteImport] = []
    # TODO test with csv ... NOT YET TESTED
    if import_file.suffix in [".csv", ".tsv", ".dbf", ".xls", ".xlsx"]:
        verified_sites = [SiteImport(**convert_site_key(i)) for i in data.dict]
    else:
        # We allow a list of flat dicts or a list of dicts where loc info is under
        # "site_address" or "geo_location"
        # can be keyed on name or flat.
        for i in data:
            if isinstance(i, str) and isinstance(data[i], dict):
                out_dict = convert_site_key(
                    {"site_name": i, **data[i]}
                )
            else:
                out_dict = convert_site_key(i)

            verified_sites += [SiteImport(**out_dict)]

    site_names = [
        f"  [cyan]{s.site_name}[/]" for s in verified_sites
    ]
    if len(site_names) > 7:
        site_names = [*site_names[0:3], "  ...", *site_names[-3:]]

    print("[bright_green]The Following Sites will be created:[/]")
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
        return resp

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


# TODO update cache after succesful group add
def batch_add_groups(import_file: Path, yes: bool = False) -> List[Response]:
    console = Console(emoji=False)
    br = cli.central.BatchRequest
    data = config.get_file_data(import_file)
    # TODO handle csv
    if isinstance(data, dict) and "groups" in data:
        data = data["groups"]
    reqs, gw_reqs, ap_reqs = [], [], []
    pre_cfgs = []
    _pre_config_msg = ""
    cache_data = []
    for group in data:
        if "allowed-types" in data[group]:
            data[group]["allowed_types"] = data[group]["allowed-types"]
            del data[group]["allowed-types"]

        try:
            g = GroupImport(**{"group": group, **data[group]})
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

    print(f"[bright_green]The following groups will be created:[/]")
    _ = [print(f"  [cyan]{g}[/]") for g in data]

    _pre_config_msg = (
        "\n[bright_green]Group level configurations will be sent:[/]\n"
        f"{_pre_config_msg}"
        f"\n[italic dark_olive_green2]{len(reqs) + len(gw_reqs) + len(ap_reqs)} API calls will be performed.[/]\n"
    )
    print(_pre_config_msg)
    for idx in range(len(pre_cfgs) + 1):
        if idx > 0:
            print(_pre_config_msg)
        print(f"Select [bright_green]#[/] to display config to be sent or [bright_green]go[/] to continue.")
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

    if reqs and yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.batch_request(reqs)
        if all(r.ok for r in resp):
            cache_resp = asyncio.run(cli.cache.update_group_db(cache_data))
            log.debug(f"batch add group cache resp: {cache_resp}")
        cli.display_results(resp)
        if gw_reqs:
            print("\n[bright_green]Results from Group level gateway config push (CLI commands)[/]")
            print("\n  [italic]This can take some time.[/]")
            resp = cli.central.batch_request(gw_reqs)
            cli.display_results(resp, cleaner=cleaner.parse_caas_response)
        if ap_reqs:
            print("\n[bright_green]Results from Group level AP config push (Replaces entire group level)[/]\n")
            resp = cli.central.batch_request(ap_reqs)
            cli.display_results(resp,  tablefmt="action")



@app.command(short_help="Perform Batch Add from file")
def add(
    what: BatchAddArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(..., exists=True),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False
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
    """Perform batch Add operations using import data from file."""
    yes = yes_ if yes_ else yes
    if what == "sites":
        resp = batch_add_sites(import_file, yes)
        cli.display_results(resp)
    elif what == "groups":
        batch_add_groups(import_file, yes)


@app.command()
def delete(
    what: BatchDelArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(..., exists=True, readable=True),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
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
    """Perform batch Delete operations using import data from file."""
    yes = yes_ if yes_ else yes
    central = cli.central
    data = config.get_file_data(import_file)
    if hasattr(data, "dict"):  # csv
        data = data.dict

    resp = None
    if what == "sites":
        del_list = []
        _msg_list = []
        for i in data:
            if isinstance(i, str) and isinstance(data[i], dict):
                i = {"site_name": i, **data[i]} if "name" not in i and "site_name" not in i else data[i]

            if "site_id" not in i and "id" not in i:
                if "site_name" in i or "name" in i:
                    _name = i.get("site_name", i.get("name"))
                    _id = cli.cache.get_site_identifier(_name).id
                    found = True
                    _msg_list += [_name]
                    del_list += [_id]
            else:
                found = False
                for key in ["site_id", "id"]:
                    if key in i:
                        del_list += [i[key]]
                        _msg_list += [i.get("site_name", i.get("site", i.get("name", f"id: {i[key]}")))]
                        found = True
                        break

            if not found:
                if i.get("site_name", i.get("site", i.get("name"))):
                    site = cli.cache.get_site_identifier(i.get("site_name", i.get("site", i.get("name"))))
                    _msg_list += [site.name]
                    del_list += [site.id]
                    break
                else:
                    typer.secho("Error getting site ids from import, unable to find required key", fg="red")
                    raise typer.Exit(1)

        if len(_msg_list) > 7:
            _msg_list = [*_msg_list[0:3], "...", *_msg_list[-3:]]
        typer.secho("\nSites to delete:", fg="bright_green")
        typer.echo("\n".join([f"  {m}" for m in _msg_list]))
        if yes or typer.confirm(f"\n{typer.style('Delete', fg='red')} {len(del_list)} sites", abort=True):
            resp = central.request(central.delete_site, del_list)
            if resp:
                cache_del_res = asyncio.run(cli.cache.update_site_db(data=del_list, remove=True))
                if len(cache_del_res) != len(del_list):
                    log.warning(
                        f"Attempt to delete entries from Site Cache returned {len(cache_del_res)} "
                        f"but we tried to delete {len(del_list)} sites.",
                        show=True
                    )

    cli.display_results(resp)


@app.command(help="Batch rename APs based on import file or site/LLDP info.")
def rename(
    what: BatchRenameArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(None, metavar="['lldp'|IMPORT FILE PATH]"),  # TODO completion
    lldp: bool = typer.Option(None, help="Automatic AP rename based on lldp info from upstream switch.",),
    ap: str = typer.Option(None, metavar=iden_meta_vars.dev, help="[LLDP rename] Perform on specified AP",),
    label: str = typer.Option(None, help="[LLDP rename] Perform on APs with specified label",),
    group: str = typer.Option(None, help="[LLDP rename] Perform on APs in specified group",),
    site: str = typer.Option(None, metavar=iden_meta_vars.site, help="[LLDP rename] Perform on APs in specified site",),
    model: str = typer.Option(None, help="[LLDP rename] Perform on APs of specified model",),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
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
    yes = yes_ if yes_ else yes

    if str(import_file).lower() == "lldp":
        lldp = True
        import_file = None

    if not import_file and not lldp:
        print("[bright_red]ERROR[/]: Missing required parameter [IMPORT_FILE|'lldp']")
        raise typer.Exit(1)

    central = cli.central
    if import_file:
        data = config.get_file_data(import_file)

        if not data:
            print(f"[bright_red]ERROR[/] {import_file.name} not found or empty.")
            raise typer.Exit(1)

        resp = None
        if what == "aps":
            # transform flat csv struct to Dict[str, Dict[str, str]] {"<AP serial>": {"hostname": "<desired_name>"}}
            if import_file.suffix in [".csv", ".tsv", ".dbf", ".xls", ".xlsx"]:
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

        resp = do_lldp_rename(_lldp_rename_get_fstr(), **kwargs)

    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Perform batch operations.
    """
    pass


if __name__ == "__main__":
    app()
