#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Dict, List, Tuple, Literal, Any

import typer
from pydantic import BaseModel, ValidationError, ConfigDict
from rich import print
from rich.console import Console
from rich.progress import track
from rich.markup import escape

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
    BatchAddArgs,
    BatchDelArgs,
    BatchRenameArgs,
    IdenMetaVars,
    SendConfigTypes,
    CloudAuthUploadTypes,
)

from centralcli.strings import ImportExamples
from centralcli.models import Groups, ImportSites, Labels
from centralcli.cache import CentralObject

# from centralcli.models import GroupImport
examples = ImportExamples()

if TYPE_CHECKING:
    from .cache import CacheSite

iden = IdenMetaVars()
tty = utils.tty
app = typer.Typer()


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

def get_lldp_names(fstr: str, default_only: bool = False, lower: bool = False, space: str = None, **kwargs) -> List[dict]:
    need_lldp = False if "%h" not in fstr and "%p" not in fstr else True
    space = "_" if space is None else space
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
            cli.exit("No Up APs found with default name.  Nothing to rename.")

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
        cli.exit("Something went wrong, no ap_dict provided or empty")

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
                log.exception(f"LLDP rename exception while parsing {fstr}\n{e}", show=log.DEBUG)
                print(f"\nThere Appears to be a problem with [red]{fstr}[/]: {e.__class__.__name__}")
                if typer.confirm("Do you want to edit the format string and try again?", abort=True):
                    fstr = _lldp_rename_get_fstr()

    return data


def _invalid_msg(usage: str, provide: str = None) -> str:
        usage = escape(usage)
        provide = provide or "Provide [bright_green]IMPORT_FILE[/] or [cyan]--example[/]"
        _msg = [
            "Invalid combination of arguments / options.",
            provide,
            "",
            f"[yellow]Usage[/]: {usage}",
            f"Use [cyan]{usage.split(' [')[0]} --help[/] for help.",
        ]
        return "\n".join(_msg)

def batch_add_sites(import_file: Path = None, data: dict = None, yes: bool = False) -> Response:
    if all([d is None for d in [import_file, data]]):
        raise ValueError("batch_add_sites requires import_file or data arguments, neither were provided")

    central = cli.central
    # We allow a list of flat dicts or a list of dicts where loc info is under
    # "site_address" or "geo_location"
    # can be keyed by name or flat.
    if import_file is not None:
        data = cli._get_import_file(import_file, "sites")
    elif isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):  # Data keyed by site name
        data = [{"site_name": k, **data[k]} for k in data]  # deploy is the only one that passed raw data in.

    try:
        verified_sites = ImportSites(data)
    except Exception as e:
        cli.exit(f"Import data failed validation, refer to [cyan]cencli batch add sites --example[/] for example formats.\n{repr(e)}")

    for idx in range(2):
        already_exists = [(s.site_name, idx) for idx, s in enumerate(verified_sites) if s.site_name in [s["name"] for s in cli.cache.sites]]
        if already_exists:
            if idx == 0:
                cli.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{len(already_exists)}[/] sites from import already exist according to the cache, ensuring cache is current.")
                _ = cli.central.request(cli.cache.refresh_site_db)
            else:
                cache_exists = [cli.cache.get_site_identifier(s[0]) for s in already_exists]
                skip_txt = utils.summarize_list([s.summary_text for s in cache_exists], color=None)
                cli.econsole.print(f"[dark_orange3]:warning:[/]  The Following Sites will be [red]skipped[/] as they already exist in Central.\n{skip_txt}\n")
                verified_sites = [site for idx, site in enumerate(verified_sites) if idx not in [s[1] for s in already_exists]]

    if not verified_sites:
        cli.exit("[italic dark_olive_green2]No Sites remain after validation[/].")

    resp = None
    address_fields = {"site_name": "bright_green", "name": "bright_green", "address": "bright_cyan", "city": "turquoise4", "state": "dark_olive_green3", "country": "magenta", "zipcode": "blue", "zip": "blue"}
    confirm_msg = utils.summarize_list(
        [
            "|".join([f'[{address_fields[k]}]{v}[/]' for k, v in site.model_dump().items() if v and k in address_fields]) for site in list(verified_sites)
        ],
        max=7
    )
    cli.console.print(f"\n[bright_green]The Following [cyan]{len(verified_sites)}[/] Sites will be created:[/]")
    cli.console.print(confirm_msg, emoji=False)
    if cli.confirm(yes):
        reqs = [
            BatchRequest(central.create_site, **site.model_dump())
            for site in verified_sites
        ]
        resp = central.batch_request(reqs)
        passed = list(sorted([r for r in resp if r.ok], key=lambda r: r.rl))
        failed = [r for r in resp if not r.ok]
        if passed:
            cache_data = [r.output for r in passed]
            cli.central.request(cli.cache.update_site_db, data=cache_data)  # TODO need an add function, this update combines old with new then truncates and re-writes all sites.
            # we combine the passing responses into 1.
            passed[0].output = cache_data
            resp = passed[0] if not failed else [passed[0], *failed]

        return resp

class PreConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    dev_type: Literal["ap", "gw"]
    config: str
    request: BatchRequest


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

def _build_pre_config(node: str, dev_type: SendConfigTypes, cfg_file: Path, var_file: Path = None) -> PreConfig:
    """Build Configuration from raw config or jinja2 template/variable file.

    Args:
        node (str): The name of the central node (group name or device MAC for gw)
        dev_type (Literal["gw", "ap"]): Type of device being pre-provisioned.  One of 'gw' or 'ap'.
        cfg_file (Path): Path of the config file.
        var_file (Path, optional): Path of the variable file. Defaults to None.

    Raises:
        typer.Exit: If config is j2 template but no variable file is found.
        typer.Exit: If result of config generation yields no commands

    Returns:
        PreConfig: PreConfig object
    """
    if not cfg_file.exists():
        cli.exit(f"[cyan]{node}[/] specified config: {cfg_file} [red]not found[/].  [red italic]Unable to generate config[/].")

    br = cli.central.BatchRequest
    caasapi = caas.CaasAPI(central=cli.central)
    config_out = utils.generate_template(cfg_file, var_file=var_file)
    commands = utils.validate_config(config_out)

    this_req = br(caasapi.send_commands, node, cli_cmds=commands) if dev_type == "gw" else br(cli.central.replace_ap_config, node, clis=commands)
    return PreConfig(name=node, config=config_out, dev_type=dev_type, request=this_req)


def _build_group_add_reqs():
    ...


def batch_add_groups(import_file: Path = None, data: dict = None, yes: bool = False) -> List[Response]:
    """Batch add groups to Aruba Central

    Args:
        import_file (Path, optional): import file containing group data. Defaults to None.
        data (dict, optional): data Used internally, when import_file is already parsed by batch_deploy. Defaults to None.
        yes (bool, optional): If True we bypass confirmation prompts. Defaults to False.

    Raises:
        typer.Exit: Exit if data is not in correct format.

    Returns:
        List[Response]: List of Response objects.
    """
    # TODO if multiple groups are being added and the first one fails, the remaining groups do not get added (due to logic in _batch_request)
    # either need to set continue_on_fail or strip any group actions for groups that fail (i.e. upload group config.)
    # TODO convert yes to int with count, allow -yy to skip config confirmation and main confirmation
    console = Console(emoji=False)
    br = cli.central.BatchRequest
    if import_file is not None:
        data = cli._get_import_file(import_file, import_type="groups")
    elif not data:
        cli.exit("No import file provided")

    reqs, gw_reqs, ap_reqs = [], [], []
    pre_cfgs = []
    confirm_msg = ""
    cache_data = []

    try:
        groups = Groups(data)
    except (ValidationError, KeyError) as e:
        cli.exit(repr(e))

    names_from_import = [g.name for g in groups]
    if any([name in cli.cache.groups_by_name for name in names_from_import]):
        cli.econsole.print("[dark_orange3]:warning:[/]  Import includes groups that already exist according to local cache.  Updating local group cache.")
        _ = cli.central.request(cli.cache.refresh_group_db)  # This updates cli.cache.groups_by_name
        # TODO maybe split batch_verify into the command and the function that does the validation, then send the data from import for groups that already exist to the validation func.

    skip = []
    for g in groups:
        for dev_type, cfg_file, var_file in zip(["gw", "ap"], [g.gw_config, g.ap_config], [g.gw_vars, g.ap_vars]):
            if cfg_file is not None:
                pc = _build_pre_config(g.name, dev_type=dev_type, cfg_file=cfg_file, var_file=var_file)
                pre_cfgs += [pc]
                confirm_msg += (
                    f"  [bright_green]{len(pre_cfgs)}[/]. [cyan]{g.name}[/] {'Gateway' if dev_type == 'gw' else 'AP'} "
                    f"group level will be configured based on [cyan]{cfg_file.name}[/]\n"
                )
                if dev_type == "gw":
                    gw_reqs += [pc.request]
                else:
                    ap_reqs += [pc.request]

        if g.name in cli.cache.groups_by_name:
            cli.econsole.print(f"[dark_orange3]:warning:[/]  Group [cyan]{g.name}[/] already exists. [red]Skipping Group Add...[/]")
            skip += [g.name]
            continue

        reqs += [
            br(
                cli.central.create_group,
                g.name,
                allowed_types=g.allowed_types,
                wired_tg=g.wired_tg,
                wlan_tg=g.wlan_tg,
                aos10=g.aos10,
                microbranch=g.microbranch,
                gw_role=g.gw_role,
                monitor_only_sw=g.monitor_only_sw,
                monitor_only_cx=g.monitor_only_cx,
                cnx=g.cnx,
            )
        ]
        cache_data += [g.model_dump()]

    groups_cnt = len(groups) - len(skip)
    reqs_cnt = len(reqs) + len(gw_reqs) + len(ap_reqs)

    if pre_cfgs:
        confirm_msg = (
            "\n[bright_green]Group level configurations will be sent:[/]\n"
            f"{confirm_msg}"
        )

    if cache_data:
        _groups_text = utils.color([g.name for g in groups if g.name not in skip], "cyan", pad_len=4, sep="\n")
        confirm_msg = (
            f"[bright_green]The following {f'[cyan]{groups_cnt}[/] groups' if groups_cnt > 1 else 'group'} will be created[/]:\n{_groups_text}\n"
            f"{confirm_msg}"
        )

    if len(reqs) + len(gw_reqs) + len(ap_reqs) > 1:
        confirm_msg = f"{confirm_msg}\n[italic dark_olive_green2]{reqs_cnt} API calls will be performed.[/]\n"

    if not reqs_cnt:
        cli.exit("No Updates to perform...", code=0)

    console.print(confirm_msg)
    if pre_cfgs:
        idx = 0
        while True:
            if idx > 0:
                console.print(confirm_msg)
            console.print("Select [bright_green]#[/] to display config to be sent, [bright_green]go[/] to continue or [red]abort[/] to abort.")
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
                pretty_type = 'Gateway' if pc.dev_type == 'gw' else pc.dev_type.upper()
                console.rule(f"{pc.name} {pretty_type} config")
                with console.pager():
                    console.print(pc.config)
                console.rule(f"End {pc.name} {pretty_type} config")
            idx += 1

    resp = []
    if reqs and cli.confirm(yes):
        resp = cli.central.batch_request(reqs)

        # -- Update group cache --
        cache_update_data = [group_data for res, group_data in zip(resp, cache_data) if res.ok]
        cli.central.request(cli.cache.update_group_db, data=cache_update_data)

    if [*ap_reqs, *gw_reqs]:
        if not reqs:
            cli.econsole.print("[dark_orange3]:warning:[/]  Updating Group level config for group(s) that [dark_olive_green2]already exists[/][red]![/]  [dark_orange3]:warning:[/]")
            if not cli.confirm():
                ...  # cli.confirm aborts

        config_reqs = []
        if gw_reqs:
            print("\n[bright_green]About to send group level gateway config (CLI commands)[/]")
            print("  [italic blink]This can take some time.[/]")
            config_reqs += gw_reqs
        if ap_reqs:
            print("\n[bright_green]About to send group level AP config (Replaces entire group level)[/]\n")
            config_reqs += ap_reqs
        if config_reqs:
            for _ in track(range(10), description="Delay to ensure groups are ready to accept configs."):
                sleep(1)
            resp += cli.central.batch_request(config_reqs, retry_failed=True)

    return resp or Response(error="No Groups were added")

def verify_required_fields(data: List[Dict[str, Any]], required: List[str], optional: List[str] | None = None, example_text: str | None = None, exit_on_fail: bool = True):
    ok = True
    if not all([len(required) == len([k for k in d.keys() if k in required]) for d in data]):
        ok = False
        print("[bright_red]:warning:  !![/] Missing at least 1 required field")
        print("\nThe following fields are [bold]required[/]:")
        print(utils.color(required, pad_len=4, sep="\n"))
        if optional:
            print("\nThe following fields are optional:")
            print(utils.color(optional, color_str="cyan", pad_len=4, sep="\n"))
        if example_text:
            print(f"\nUse [cyan]{example_text}[/] to see valid import file formats.")
        # TODO finish full deploy workflow with config per-ap-settings variables etc allowed
        if exit_on_fail:
            raise typer.Exit(1)
    return ok


def validate_license_type(data: List[Dict[str, Any]]):
    """validate device add import data for valid subscription name.

    Args:
        data (List[Dict[str, Any]]): The data from the import

    Returns:
        Tuple[List[Dict[str, Any]], bool]: Tuple with the data, and a bool indicating if a warning should occur indicating the license doesn't appear to be valid
            The data is the same as what was provided, with the key changed to 'license' if they used 'services' or 'subscription'
    """
    sub_key = list(set([k for d in data for k in d.keys() if k in ["license", "services", "subscription"]]))
    sub_key = None if not sub_key else sub_key[0]
    warn = False
    if not sub_key:
        return data, warn

    already_warned = []
    for d in data:
        if d.get(sub_key):
            for idx in range(2):
                try:
                    d["license"] = cli.cache.LicenseTypes(d[sub_key].lower().replace("_", "-")).name
                    if sub_key != "license":
                        del d[sub_key]
                    break
                except ValueError:
                    if idx == 0 and cli.cache.responses.license is None:
                        cli.econsole.print(f'[dark_orange3]:warning:[/]  [cyan]{d["license"]}[/] [red]not found[/] in list of valid licenses.\n:arrows_clockwise: Refreshing subscription/license name cache.')
                        resp = cli.central.request(cli.cache.refresh_license_db)
                        if not resp:
                            cli.display_results(resp, exit_on_fail=True)
                    else:
                        warn = True
                        if d['license'] not in already_warned:
                            already_warned += [d['license']]
                            cli.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{d['license']}[/] does not appear to be a valid license type.")
    return data, warn


def batch_add_devices(import_file: Path = None, data: dict = None, yes: bool = False) -> List[Response]:
    # TODO build messaging similar to batch move.  build common func to build calls/msgs for these similar funcs
    data: List[Dict[str, Any]] = data or cli._get_import_file(import_file, import_type="devices")
    if not data:
        cli.exit("No data/import file")

    _reqd_cols = ["serial", "mac"]
    verify_required_fields(
        data, required=_reqd_cols, optional=['group', 'license'], example_text='cencli batch add devices --show-example'
    )
    data, warn = validate_license_type(data)
    word = "Adding" if not warn and yes else "Add"

    confirm_devices = ['|'.join([f'[bright_green]{k}[/]:[cyan]{v}[/]' for k, v in d.items() if v or isinstance(v, bool)]) for d in data]
    confirm_str = utils.summarize_list(confirm_devices, pad=2, color=None,)
    file_str = "import file" if not import_file else f"[cyan]{import_file.name}[/]"
    print(f'{len(data)} Devices found in {file_str}')
    cli.console.print(confirm_str, emoji=False)
    print(f'\n{word} {len(data)} devices found in {file_str}')
    if warn:
        msg = ":warning:  Warnings exist"
        msg = msg if not yes else f"{msg} [cyan]-y[/] flag ignored."
        cli.econsole.print(msg)

    resp = None
    if cli.confirm(yes=not warn and yes):
        resp = cli.central.request(cli.central.add_devices, device_list=data)
        # if any failures occured don't pass data into update_inv_db.  Results in API call to get inv from Central
        _data = None if not all([r.ok for r in resp]) else data
        update_func = cli.cache.refresh_inv_db
        kwargs = {}
        if _data:
            try:
                _data = models.Inventory(_data).model_dump()
                update_func = cli.cache.update_inv_db
                kwargs = {"data": _data}
            except ValidationError as e:
                log.info(f"Performing full cache update after batch add devices as import_file data validation failed. {e}")
                _data = None

        console = Console()
        cache_res = [cli.central.request(update_func, **kwargs)]  # This starts it's own spinner
        with console.status("Allowing time for devices to populate before updating dev cache.") as spin:
            sleep(3)
            spin.update('Performing full device cache update after device edition.')
            sleep(2)
        # always perform full dev_db update as we don't know the other fields.
        cache_res += [cli.central.request(cli.cache.refresh_dev_db)]  # This starts it's own spinner

    return resp or Response(error="No Devices were added")


# TODO this has not been tested validated at all
# TODO adapt to add or delete based on param centralcli.delete_label needs the label_id from the cache.
def batch_add_labels(import_file: Path = None, *, data: bool = None, yes: bool = False) -> List[Response]:
    if import_file is not None:
        data = cli._get_import_file(import_file, "labels", text_ok=True)
    elif not data:
        cli.exit("No import file provided")

    for idx in range(2):
        already_exists = [d["name"] for d in data if d["name"] in cli.cache.label_names]
        if already_exists:
            if idx == 0:
                cli.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{len(already_exists)}[/] labels from import already exist according to the cache, ensuring cache is current.")
                _ = cli.central.request(cli.cache.refresh_label_db)
            else:
                skip_txt = utils.summarize_list(already_exists)
                cli.econsole.print(f"[dark_orange3]:warning:[/]  The Following Labels will be [red]skipped[/] as they already exist in Central.\n{skip_txt}\n")
                data = [label for label in data if label["name"] not in cli.cache.label_names]

    if not data:
        cli.exit("[italic dark_olive_green2]No Labels remain after validation[/].")

    # TODO common func for this type of multi-element confirmation, we do this a lot.
    _msg = "\n".join([f"  [cyan]{inner['name']}[/]" for inner in data])
    _msg = _msg.lstrip() if len(data) == 1 else f"\n{_msg}"
    _msg = f"[bright_green]Create[/] {'label ' if len(data) == 1 else f'{len(data)} labels:'}{_msg}"
    cli.console.print(_msg, emoji=False)

    if cli.confirm(yes):
        reqs = [BatchRequest(cli.central.create_label, label_name=inner['name']) for inner in data]
        resp = cli.central.batch_request(reqs)
        try:
            cache_data = Labels([r.output for r in resp if r.ok])
            _  = cli.central.request(cli.cache.update_label_db, data=cache_data.model_dump())
        except Exception as e:
            log.exception(f'Exception during label cache update in batch_add_labels]n{e}')
            cli.econsole.print(f'[dark_orange3]:warning:[/]  [bright_red]Cache Update Error[/]: {e.__class__.__name__}.  See logs.\nUse [cyan]cencli show labels[/] to refresh label cache.')

        return resp


def batch_add_cloudauth(upload_type: CloudAuthUploadTypes = "mac", import_file: Path = None, *, ssid: str = None, data: bool = None, yes: bool = False) -> Response:
    if import_file is not None:
        data = cli._get_import_file(import_file, "macs")
    elif not data:
        cli.exit("[red]Error!![/] No import file provided")

    print(f"Upload{'' if not yes else 'ing'} [bright_green]{len(data)}[/] [cyan]{upload_type.upper()}s[/] defined in [cyan]{import_file.name}[/] to Cloud-Auth{f' for SSID: [cyan]{ssid}[/]' if upload_type == 'mpsk' else ''}")

    if cli.confirm(yes):
        resp = cli.central.request(cli.central.cloudauth_upload, upload_type=upload_type, file=import_file, ssid=ssid)

    return resp


def batch_deploy(import_file: Path, yes: bool = False) -> List[Response]:
    data = cli._get_import_file(import_file)
    if "groups" in data:
        resp = batch_add_groups(import_file, yes=bool(yes))
        yes = yes if not yes else yes - 1
        cli.display_results(resp, tablefmt="action", exit_on_fail=True)
    if "sites" in data:
        resp = batch_add_sites(import_file, yes=bool(yes))
        cli.display_results(resp)
        yes = yes if not yes else yes - 1
    if "labels" in data:
        resp = batch_add_labels(import_file, yes=bool(yes))
        cli.display_results(resp, tablefmt="action")
        yes = yes if not yes else yes - 1
    if "devices" in data:
        resp = batch_add_devices(import_file, yes=bool(yes))
        cli.display_results(resp, tablefmt="action")



@app.command()
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

    The same import file used to add/move can be used to validate.
    """
    if what != "devices":
        cli.exit("Only devices and device assignments are supported at this time.")

    data = cli._get_import_file(import_file, import_type=what)

    resp: Response = cli.cache.get_devices_with_inventory(no_refresh=no_refresh)
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
            if file_by_serial[s][file_key].replace("-", "_") != central_by_serial[s]["services"]: # .replace("-", "_").replace(" ", "_")
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
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    yes: int = typer.Option(False, "-Y", "-y", count=True, help="Bypass confirmation prompts - Assume Yes.  Use multiples i.e. -yy -yyy to bypass each prompt in the deploy process (groups, sites, labels, devices).",),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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
        cli.exit(_invalid_msg("cencli batch deploy [OPTIONS] [IMPORT_FILE]"))

    batch_deploy(import_file, yes)


# FIXME appears this is not current state aware, have it only do the API calls not reflected in current state
@app.command()
def add(
    what: BatchAddArgs = typer.Argument(..., help="[cyan]macs[/] and [cyan]mpsk[/] are for cloud-auth", show_default=False,),
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    ssid: str = typer.Option(None, "--ssid", help="SSID to associate mpsk definitions with [grey42 italic]Required and valid only with mpsk argument[/]", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Perform batch Add operations using import data from file
    """
    if show_example:
        print(getattr(examples, f"add_{what.value}"))
        return

    if not import_file:
        cli.exit(_invalid_msg("cencli batch add [OPTIONS] WHAT:[sites|groups|devices|macs|mpsk] [IMPORT_FILE]"))

    caption, tablefmt = None, "action"
    if what == "sites":
        resp = batch_add_sites(import_file, yes=yes)
        if resp.ok:
            try:
                resp.output = cleaner.sites(resp.output)
            except Exception as e:
                log.error(f"Error cleaning output of batch site addition {repr(e)}", caption=True, log=True)
        tablefmt = "rich"
    elif what == "groups":
        resp = batch_add_groups(import_file, yes=yes)
    elif what == "devices":
        resp = batch_add_devices(import_file, yes=yes)
        if [r for r in resp if not r.ok and r.url.path.endswith("/subscriptions/assign")]:
            log.warning("Aruba Central took issue with some of the devices when attempting to assign subscription.  It will typically stop processing when this occurs, meaning valid devices may not have their license assigned.", caption=True)
            log.info(f"Use [cyan]cencli batch verify devices {import_file}[/] to check status of license assignment.", caption=True)
    elif what == "labels":
        resp = batch_add_labels(import_file, yes=yes)
    elif what == "macs":
        resp = batch_add_cloudauth("mac", import_file, yes=yes)
        caption = (
            "\nUse [cyan]cencli show cloud-auth upload[/] to see the status of the import.\n"
            "Use [cyan]cencli show cloud-auth registered-macs[/] to see all registered macs."
        )
        if resp.ok:
            try:
                resp.output = cleaner.cloudauth_upload_status(resp.output)
            except Exception as e:
                log.error(f"Error cleaning output of cloud auth mac upload {repr(e)}", caption=True, log=True)
    elif what == "mpsk":
        if not ssid:
            cli.exit("[cyan]--ssid[/] option is required when uploading mpsk")
        resp = batch_add_cloudauth("mpsk", import_file, ssid=ssid, yes=yes)
        caption = (
            "Use [cyan]cencli show cloud-auth upload mpsk[/] to see the status of the import."
        )

    cli.display_results(resp, tablefmt=tablefmt, title=f"Batch Add {what.value}", caption=caption)


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


def batch_delete_sites(data: list | dict, *, yes: bool = False) -> List[Response]:
    central = cli.central
    del_list = []
    if isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):
        data = [{"site_name": k, **data[k]} for k in data]

    try:
        verified_sites = ImportSites(data)
    except Exception as e:
        cli.exit(f"Import data failed validation, refer to [cyan]cencli batch delete sites --example[/] for example formats.\n{repr(e)}")

    cache_sites: List[CacheSite | None] = [cli.cache.get_site_identifier(s.site_name, silent=True, exit_on_fail=False) for s in verified_sites]
    not_in_central = [name for name, data in zip(verified_sites, cache_sites) if data is None]

    if not_in_central:
        cli.econsole.print(f"[dark_orange3]:warning:[/]  [red]Skipping[/] {utils.color(not_in_central, 'red')} [italic]site{'s do' if len(not_in_central) > 1 else ' does'} not exist in Central.[/]")

    sites: List[CacheSite] = [s for s in cache_sites if s is not None]
    del_list = [s.id for s in sites]
    if not del_list:
        cli.exit("[italic dark_olive_green2]No sites remain after validation.[/]")

    site_names = utils.summarize_list([s.summary_text for s in sites], max=7)
    cli.console.print(f"The following {len(del_list)} sites will be [bright_red]deleted[/]:\n{site_names}", emoji=False)
    if cli.confirm(yes):
        resp: List[Response] = central.request(central.delete_site, del_list)
        if len(resp) == len(sites):
            doc_ids = [s.doc_id for s, r in zip(sites, resp) if r.ok]
            cli.central.request(cli.cache.update_site_db, data=doc_ids, remove=True)
        return resp


# TODO make sub-command clibatchdelete.py seperate out sites devices...
@app.command()
def delete(
    what: BatchDelArgs = cli.arguments.what,
    import_file: Path = cli.arguments.import_file,
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views (devices must be offline).  Devices will remain in inventory with subscriptions unchanged."),
    cop_inv_only: bool = typer.Option(False, "--cop-only", help="Only delete device from CoP inventory.  (Devices are not deleted from monitoring UI)", hidden=not config.is_cop,),
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Perform batch delete operations using import data from file.

    [cyan]cencli delete sites <IMPORT_FILE>[/] and
    [cyan]cencli delte groups <IMPORT_FILE>[/]
        Do what you'd expect.

    [cyan]cencli batch delete devices <IMPORT_FILE>[/]

    Delete devices will remove any subscriptions/licenses from the device and disassociate the device with the Aruba Central app in GreenLake.  It will then remove the device from the monitoring views, along with the historical data for the device.

    Note: devices can only be removed from monitoring views if they are in a down state.  This command will delay/wait for any Up devices to go Down after the subscriptions/assignment to Central is removed, but it can also be ran again.  It will pick up where it left off, skipping any steps that have already been performed.
    """
    if show_example:
        print(getattr(examples, f"delete_{what}"))
        return

    if not import_file:
        cli.exit(_invalid_msg("cencli batch delete [OPTIONS] [devices|sites|groups|labels] [IMPORT_FILE]"))

    data = cli._get_import_file(import_file, import_type=what, text_ok=what == "labels")

    if what == "devices":
        resp = cli.batch_delete_devices(data, ui_only=ui_only, cop_inv_only=cop_inv_only, yes=yes)
    elif what == "sites":
        resp = batch_delete_sites(data, yes=yes)
    elif what == "groups":
        resp = cli.batch_delete_groups(data, yes=yes)
    elif what == "labels":
        resp = cli.batch_delete_labels(data, yes=yes)
    cli.display_results(resp, tablefmt="action")


# TODO if from get inventory API endpoint subscriptions are under services key, if from endpoint file currently uses license key (maybe make subscription key)
def _build_sub_requests(devices: List[dict], unsub: bool = False) -> Tuple[List[dict], List[dict], List[BatchRequest]]:
    if "'license': " in str(devices):
        devices = [{**d, "services": d["license"]} for d in devices]
    elif "'subscription': " in str(devices):
        devices = [{**d, "services": d["subscription"]} for d in devices]

    subs = set([d["services"] for d in devices if d.get("services")])  # TODO Inventory actually returns a list for services if the device has multiple subs this would be an issue
    ignored = [d for d in devices if not d.get("services")]
    devices = [d for d in devices if d.get("services")]  # filter any devs that currently do not have subscription

    if ignored:
        log.warning(f"Ignored {len(ignored)} devices, no desired subscription provided", caption=True)

    try:
        subs = [cli.cache.LicenseTypes(s.lower().replace("_", "-").replace(" ", "-")).name for s in subs]
    except ValueError as e:
        sub_names = "\n".join(cli.cache.license_names)
        cli.exit(str(e).replace("ValidLicenseTypes", f'subscription name.\n[cyan]Valid subscriptions[/]: \n{sub_names}'))

    devs_by_sub = {s: [] for s in subs}
    for d in devices:
        devs_by_sub[d["services"].lower().replace("-", "_").replace(" ", "_")] += [d["serial"]]

    func = cli.central.unassign_licenses if unsub else cli.central.assign_licenses
    # Both Assign and unassign allow a max of 50 serials per call
    requests = [
        BatchRequest(func, serials=chunk, services=sub) for sub in devs_by_sub for chunk in utils.chunker(devs_by_sub[sub], 50)
    ]

    return devices, ignored, requests

@app.command()
def subscribe(
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Batch subscribe devices

    Assign subscription license to devices specified in import file.

    [italic]This command assumes devices have already been added to GreenLake,
    to add devices and assign subscription use [cyan]cencli batch add devices <IMPORT_FILE>[/][/]
    """
    if show_example:
        print(getattr(examples, "subscribe"))
        return
    elif not import_file:
        cli.exit(_invalid_msg("cencli batch subscribe [OPTIONS] [IMPORT_FILE]"))

    devices = cli._get_import_file(import_file, "devices")
    devices, ignored, sub_reqs = _build_sub_requests(devices)

    cli.display_results(data=devices, tablefmt="rich", title="Devices to be subscribed", caption=f'{len(devices)} devices will have subscriptions assigned')
    # print("[bright_green]All Devices Listed will have subscriptions assigned.[/]")
    if ignored:
        cli.display_results(data=ignored, tablefmt="rich", title="[bright_red]!![/] The following devices will be IGNORED [bright_red]!![/]", caption=f'{len(ignored)} devices will be ignored due to incomplete data')
    if cli.confirm(yes):
        resp = cli.central.batch_request(sub_reqs)
        cli.display_results(resp, tablefmt="action")

@app.command()
def unsubscribe(
    import_file: Path = cli.arguments.import_file,
    never_connected: bool = typer.Option(False, "-N", "--never-connected", help="Remove subscriptions from any devices in inventory that have never connected to Central", show_default=False),
    dis_cen: bool = typer.Option(False, "-D", "--dis-cen", help="Dissasociate the device from the Aruba Central App in Green Lake"),
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Batch Unsubscribe devices

    Unsubscribe devices specified in import file or all devices in the inventory that
    have never connected to Aruba Central ([cyan]-N[/]|[cyan]--never-connected[/])

    Use [cyan]-D[/]|[cyan]--dis-cen[/] flag to also dissasociate the devices from the Aruba Central app in Green Lake.
    """
    if show_example:
        print(getattr(examples, "unsubscribe"))
        return
    elif never_connected:
        resp = cli.cache.get_devices_with_inventory()
        if not resp:
            cli.display_results(resp, exit_on_fail=True)
        else:
            devices = [d for d in resp.output if d.get("status") is None and d["services"]]
            if dis_cen:
                resp = cli.batch_delete_devices(devices, yes=yes)
            else:
                devices, ignored, unsub_reqs = _build_sub_requests(devices, unsub=True)
                if not devices:
                    cli.exit("No devices with subscriptions found in inventory that have never connected.\nNoting to do.")

                cli.display_results(data=devices, tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
                print("[bright_green]All Devices Listed will have subscriptions unassigned.[/]")
                if cli.confirm(yes):
                    resp = cli.central.batch_request(unsub_reqs)
    elif not import_file:
        cli.exit(_invalid_msg("cencli batch unsubscribe [OPTIONS] [IMPORT_FILE]"))
    elif import_file:
        devices = cli._get_import_file(import_file, "devices")
        devices, ignored, unsub_reqs = _build_sub_requests(devices, unsub=True)

        cli.display_results(data=devices, tablefmt="rich", title="Devices to be unsubscribed", caption=f'{len(devices)} devices will be Unsubscribed')
        # print("[bright_green]All Devices Listed will have subscriptions unassigned.[/]")
        if ignored:
            cli.display_results(data=ignored, tablefmt="rich", title="[bright_red]!![/] The following devices will be IGNORED [bright_red]!![/]", caption=f'{len(ignored)} devices will be ignored due to incomplete data')

        if not unsub_reqs:
            cli.exit("Nothing to do")
        if cli.confirm(yes):
            resp = cli.central.batch_request(unsub_reqs)

    # if not dis_cen:
    #     inv_devs = [{**d, "services": None, "subscription_key": None, "subscription_expires": None} for r, d in zip(resp, devices) if r.ok]
    #     cache_resp = cli.cache.InvDB.update_multiple([(dev, cli.cache.Q.serial == dev["serial"]) for dev in inv_devs])
    #     if len(inv_devs) != len(cache_resp):
    #         log.warning(
    #             f'Inventory cache update may have failed.  Expected {len(inv_devs)} records to be updated, cache update resulted in {len(cache_resp)} records being updated'
    #             )

    cli.display_results(resp, tablefmt="action")
    if not dis_cen:
        inv_devs = [{"serial": serial, "services": None, "subscription_key": None, "subscription_expires": None} for req, resp in zip(unsub_reqs, resp) if resp.ok for serial in req.kwargs["serials"]]
        cli.central.request(cli.cache.update_inv_db, inv_devs)


@app.command()
def rename(
    what: BatchRenameArgs = cli.arguments.what,
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    lldp: bool = typer.Option(None, "--lldp", help="Automatic AP rename based on lldp info from upstream switch.",),
    lower: bool = typer.Option(False, "--lower", help="[LLDP rename] Convert LLDP result to all lower case.",),
    space: str = typer.Option(
        None,
        "-S",
        "--space",
        help="[LLDP rename] Replace spaces with provided character (best to wrap in single quotes) [grey42]{}[/]".format(escape("[default: '_']")),
        show_default=False,
    ),
    default_only: bool = typer.Option(False, "-D", "--default-only", help="[LLDP rename] Perform only on APs that still have default name.",),
    ap: str = typer.Option(None, metavar=iden.dev, help="[LLDP rename] Perform on specified AP", show_default=False,),
    label: str = typer.Option(None, help="[LLDP rename] Perform on APs with specified label", show_default=False,),
    group: str = typer.Option(None, help="[LLDP rename] Perform on APs in specified group", show_default=False,),
    site: str = typer.Option(None, metavar=iden.site, help="[LLDP rename] Perform on APs in specified site", show_default=False,),
    model: str = typer.Option(None, help="[LLDP rename] Perform on APs of specified model", show_default=False,),  # TODO model completion
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Perform AP rename in batch from import file or automatically based on LLDP"""
    if show_example:
        print(getattr(examples, f"rename_{what}"))
        return

    if str(import_file).lower() == "lldp":
        lldp = True
        import_file = None

    if not import_file and not lldp:
        cli.exit(
            _invalid_msg(
                "cencli batch rename [OPTIONS] aps [IMPORT_FILE]",
                provide="Provide [bright_green]IMPORT_FILE[/] argument, or one of [cyan]--lldp[/] or [cyan]--example[/]"
            )
        )

    if import_file:
        data = cli._get_import_file(import_file)
        conf_msg: list = ["\n[bright_green]Names gathered from import[/]:"]
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

        fstr = _lldp_rename_get_fstr()
        conf_msg: list = [f"\n[bright_green]Resulting AP names based on [/][cyan]{fstr}[/]:"]
        data = get_lldp_names(fstr, default_only=default_only, lower=lower, space=space, **kwargs)

    resp = None
    # transform flat csv struct to Dict[str, Dict[str, str]] {"<AP serial>": {"hostname": "<desired_name>"}}
    data = {
        i.get("serial", i.get("serial_number", i.get("serial_num", "ERROR"))):
        {
            k if k != "name" else "hostname": v for k, v in i.items() if k in ["name", "hostname"]
        } for i in data
    }

    calls = []
    for ap in data:  # keyed by serial num
        conf_msg += [f"  {ap}: [cyan]{data[ap]['hostname']}[/]"]
        calls.append(cli.central.BatchRequest(cli.central.update_ap_settings, ap, **data[ap]))

    if len(conf_msg) > 6:
        conf_msg = [*conf_msg[0:3], "...", *conf_msg[-3:]]
    print("\n".join(conf_msg))

    # We only spot check the last serial.  If first call in a batch_request fails the process stops.
    if ap not in cli.cache.devices_by_serial:
        print("\n:warning:  [italic]Device must be checked into Central to assign/change hostname.[/]")

    if cli.confirm(yes, prompt="\nProceed with AP rename?"):
        resp = cli.central.batch_request(calls)


    cli.display_results(resp, tablefmt="action")
    # cache update
    if import_file:
        cache_data = [cli.cache.get_dev_identifier(r.output) for r in resp if r.ok and r.status != 299]  # responds with str serial number
        cache_data = [{**dev, "name": data[dev["serial"]]["hostname"]}  for dev in cache_data]           # 299 is default, indicates no call was performed, this is returned when the current data matches what's already set for the dev
        cli.central.request(cli.cache.update_dev_db, data=cache_data)


@app.command()
def move(
    import_file: List[Path] = typer.Argument(None, autocompletion=lambda incomplete: [("devices", "batch move devices")] if incomplete and "devices".startswith(incomplete.lower()) else [], show_default=False,),
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
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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

    if not import_file:
        cli.exit(_invalid_msg("cencli batch move [OPTIONS] [IMPORT_FILE]"))
    elif len(import_file) > 2:
        cli.exit("Too many arguments.  Use [cyan]cencli batch move --help[/] for help.")
    else:
        import_file: Path = [f for f in import_file if not str(f).startswith("device")][0]  # allow unnecessary 'devices' sub-command
        if not import_file.exists():
            cli.exit(f"Invalid value for '[IMPORT_FILE]': Path '[cyan]{str(import_file)}[/]' does not exist.")
        resp = cli.batch_move_devices(import_file, yes=yes, do_group=do_group, do_site=do_site, do_label=do_label, cx_retain_config=cx_retain_config, cx_retain_force=cx_retain)
        cli.display_results(resp, tablefmt="action")


@app.command()
def archive(
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Batch archive devices based on import data from file.

    This will archive the devices in GreenLake
    """
    if show_example:
        print(examples.archive)
        return

    elif not import_file:
        cli.exit(_invalid_msg("cencli batch archive [OPTIONS] [IMPORT_FILE]"))
    else:
        data = cli._get_import_file(import_file, "devices", text_ok=True)
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
    import_file: Path = cli.arguments.import_file,
    show_example: bool = cli.options.show_example,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    debugv: bool = cli.options.debugv,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Batch unarchive devices based on import data from file.

    This will unarchive the devices (previously archived) in GreenLake
    """
    if show_example:
        print(examples.unarchive)
        return

    elif not import_file:
        cli.exit(_invalid_msg("cencli batch unarchive [OPTIONS] [IMPORT_FILE]"))
    else:
        data = cli._get_import_file(import_file, import_type="devices", text_ok=True)

    if not data:
        cli.exit("No data extracted from import file")
    else:
        serials = [dev["serial"] for dev in data]

    res = cli.central.request(cli.central.unarchive_devices, serials)
    if res:
        caption = res.output.get("message")
        if res.get("succeeded_devices"):
            title = "Devices successfully unarchived."
            data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
            cli.display_results(data=data, title=title, caption=caption)
        if res.get("failed_devices"):
            title = "These devices failed to unarchived."
            data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
            cli.display_results(data=data, title=title, caption=caption)
    else:
        cli.display_results(res, tablefmt="action")


@app.callback()
def callback():
    """Perform batch operations"""
    pass


if __name__ == "__main__":
    app()
