#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from enum import Enum
from pathlib import Path
import sys
from typing import List, Tuple
import typer
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import GatewayRole, LicenseTypes

app = typer.Typer()
color = utils.color


class AddWlanArgs(str, Enum):
    type = "type"
    psk = "psk"
    vlan = "vlan"
    zone = "zone"
    ssid = "ssid"
    bw_limit_up = "bw_limit_up"
    bw_limit_down = "bw_limit_down"
    bw_limit_user_up = "bw_limit_user_up"
    bw_limit_user_down = "bw_limit_user_down"
    portal_profile = "portal_profile"


class AddGroupArgs(str, Enum):
    serial = "serial"
    group = "group"
    mac = "mac"


# TODO update completion with mac oui, serial prefix
@app.command(short_help="Add a Device to Aruba Central.")
def device(
    kw1: AddGroupArgs = typer.Argument(..., hidden=True, metavar="",),
    val1: str = typer.Argument(..., metavar="serial [SERIAL NUM]", hidden=False, autocompletion=cli.cache.smg_kw_completion),
    kw2: str = typer.Argument(..., hidden=True, metavar="", autocompletion=cli.cache.smg_kw_completion),
    val2: str = typer.Argument(..., metavar="mac [MAC ADDRESS]", hidden=False, autocompletion=cli.cache.smg_kw_completion),
    kw3: str = typer.Argument(None, metavar="", hidden=True, autocompletion=cli.cache.smg_kw_completion),
    val3: str = typer.Argument(None, metavar="group [GROUP]", help="pre-assign device to group",
                               autocompletion=cli.cache.smg_kw_completion),
    _: str = typer.Argument(None, metavar="", hidden=True, autocompletion=cli.cache.null_completion),
    _group: str = typer.Option(None, "--group", autocompletion=cli.cache.group_completion, hidden=True),
    license: List[LicenseTypes] = typer.Option(None, "--license", help="Assign license subscription(s) to device"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    kwd_vars = [kw1, kw2, kw3]
    vals = [val1, val2, val3]
    kwargs = {
        "mac": None,
        "serial": None,
        "group": None,
        "license": license
    }

    if _:
        print("DEVELOPER NOTE Null completion item has value... being ignored.")
    for name, value in zip(kwd_vars, vals):
        if name and name not in kwargs:
            print(f"[bright_red][blink]Error[/bright_red]: {name} in invalid")
            raise typer.Exit(1)
        else:
            kwargs[name] = value

    kwargs["group"] = kwargs["group"] or _group

    # Error if both serial and mac are not provided
    if not kwargs["mac"] or not kwargs["serial"]:
        print("[bright_red][blink]Error[/bright_red]: both serial number and mac address are required.")
        raise typer.Exit(1)

    api_kwd = {"serial": "serial_num", "mac": "mac_address"}
    kwargs = {api_kwd.get(k, k): v for k, v in kwargs.items() if v}

    _msg = [f"Add device: [bright_green]{kwargs['serial_num']}|{kwargs['mac_address']}[/bright_green]"]
    if "group" in kwargs and kwargs["group"]:
        _msg += [f"\n  Pre-Assign to Group: [bright_green]{kwargs['group']}[/bright_green]"]
    if "license" in kwargs and kwargs["license"]:
        _lic_msg = [lic._value_ for lic in kwargs["license"]]
        _lic_msg = _lic_msg if len(kwargs["license"]) > 1 else _lic_msg[0]
        _msg += [
            f"\n  Assign License{'s' if len(kwargs['license']) > 1 else ''}: [bright_green]{_lic_msg}[/bright_green]"
        ]
        kwargs["license"] = [lic.replace("-", "_") for lic in kwargs["license"]]

    print("".join(_msg))

    # if yes or typer.confirm(_msg, abort=True):
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.add_devices, **kwargs)
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Add a group", help="Add a group")
def group(
    group: str = typer.Argument(..., metavar="[GROUP NAME]", autocompletion=cli.cache.group_completion),
    # group_password: str = typer.Argument(
    #     None,
    #     show_default=False,
    #     help="Group password is required. You will be prompted for password if not provided.",
    #     autocompletion=lambda incomplete: incomplete
    # ),
    wired_tg: bool = typer.Option(False, "--wired-tg", help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(False, "--wlan-tg", help="Manage AP configurations via templates"),
    gw_role: GatewayRole = typer.Option(None, metavar="[branch|vpnc|wlan]"),
    aos10: bool = typer.Option(None, "--aos10", is_flag=True, help="Create AOS10 Group (default Instant)", show_default=False),
    microbranch: bool = typer.Option(
        None,
        "--mb",
        is_flag=True,
        help="Configure Group for MicroBranch APs (AOS10 only)",
        show_default=False,
    ),
    ap: bool = typer.Option(None, "--ap", help="Allow APs in group"),
    sw: bool = typer.Option(None, "--sw", help="Allow ArubaOS-SW switches in group."),
    cx: bool = typer.Option(None, "--cx", help="Allow ArubaOS-CX switches in group."),
    gw: bool = typer.Option(None, "--gw", help="Allow gateways in group."),
    mon_only_sw: bool = typer.Option(False, "--mon-only-sw", help="Monitor Only for ArubaOS-SW"),
    mon_only_cx: bool = typer.Option(False, "--mon_only_cx", help="Monitor Only for ArubaOS-CX", hidden=True),
    # ap_user: str = typer.Option("admin", help="Provide user for AP group"),  # TODO build func to update group pass
    # ap_passwd: str = typer.Option(None, help="Provide password for AP group (use single quotes)"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    debugv: bool = typer.Option(
        False, "--debugv",
        envvar="ARUBACLI_VERBOSE_DEBUG",
        help="Enable verbose Debug Logging",
        callback=cli.verbose_debug_callback,
        hidden=True,
    ),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    # if not group_password:
    #     group_password = typer.prompt("Group Password", confirmation_prompt=True, hide_input=True,)

    # else:
    #     _msg = f'{_msg}{typer.style(f"?", fg="cyan")}'

    allowed_types = []
    if ap:
        allowed_types += ["ap"]
    if sw:
        allowed_types += ["sw"]
    if cx:
        allowed_types += ["cx"]
    if gw:
        allowed_types += ["gw"]
    if not allowed_types:
        allowed_types = ["ap", "gw", "cx", "sw"]
    _arch = "Instant" if not aos10 else "AOS10"

    # -- // Error on combinations that are not allowed by API \\ --
    if not aos10 and microbranch:
        print(
            f"[bright_red]Microbranch is only valid if group is configured as AOS10 group ({color('--aos10')})."
        )
        raise typer.Exit(1)
    if (mon_only_sw or mon_only_cx) and wired_tg:
        print("[bright_red]Error: Monitor only is not valid for template group.")
        raise typer.Exit(1)
    if not [t for t in allowed_types if allowed_types in ["cx", "sw"]] and (mon_only_sw or mon_only_cx):
        print("[bright_red]Error: Monitor only is not valid without '--sw' or '--cx' (Allowed Device Types)")
        raise typer.Exit(1)
    if gw_role and gw_role == "wlan" and not aos10:
        print("[bright_red]WLAN role for Gateways requires the group be configured as AOS10 via --aos10 option.")
        raise typer.Exit(1)
    if all([x is None for x in [ap, sw, cx, gw]]):
        print("[green]No Allowed devices provided. Allowing all device types.")
        print("[reset]  NOTE: Device Types can be added once group is created, but not removed.\n")

    _arch_msg = f"[bright_green]{_arch} "
    _msg = f"[cyan]Create {'' if aos10 is None else _arch_msg}[cyan]group [bright_green]{group}[/bright_green]"
    _msg = f"{_msg}\n    [cyan]Allowed Device Types[/cyan]: [bright_green]{allowed_types}[/bright_green]"

    if wired_tg:
        _msg = f"{_msg}\n    [cyan]switches[/cyan]: [bright_green]Template Group[/bright_green]"
    if wlan_tg:
        _msg = f"{_msg}\n    [cyan]APs[/cyan]: [bright_green]Template Group[/bright_green]"
    if gw_role:
        _msg = f"{_msg}\n    [cyan]Gateway Role[/cyan]: [bright_green]{gw_role}[/bright_green]"
    if microbranch:
        _msg = f"{_msg}\n    [cyan]AP Role[/cyan]: [bright_green]Microbranch[/bright_green]"
    if mon_only_sw:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-SW: [bright_green]True[/bright_green]"
    if mon_only_cx:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-CX: [bright_green]True[/bright_green]"
    print(f"{_msg}\n")

    if yes or typer.confirm("Proceed with values?"):
        resp = cli.central.request(
            cli.central.create_group,
            group,
            wired_tg=wired_tg,
            wlan_tg=wlan_tg,
            allowed_types=allowed_types,
            aos10=aos10,
            microbranch=microbranch,
            gw_role=gw_role,
            monitor_only_sw=mon_only_sw,
        )
        cli.display_results(resp, tablefmt="action")
        if resp:
            asyncio.run(
                cli.cache.update_group_db({'name': group, 'template group': {'Wired': wired_tg, 'Wireless': wlan_tg}})
            )


# TODO autocompletion
@app.command(short_help="Add WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]", autocompletion=cli.cache.group_completion),
    name: str = typer.Argument(..., ),
    kw1: Tuple[AddWlanArgs, str] = typer.Argument(("psk", None), metavar="psk [WPA PASSPHRASE]",),
    kw2: Tuple[AddWlanArgs, str] = typer.Argument(("type", "employee"), metavar="type ['employee'|'guest']",),
    kw3: Tuple[AddWlanArgs, str] = typer.Argument(("vlan", ""), metavar="vlan [VLAN]",),
    kw4: Tuple[AddWlanArgs, str] = typer.Argument(("zone", ""), metavar="zone [ZONE]",),
    kw5: Tuple[AddWlanArgs, str] = typer.Argument(("ssid", None), metavar="ssid [SSID]",),
    kw6: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_up", ""), metavar="bw-limit-up [LIMIT]",),
    kw7: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_down", ""), metavar="bw-limit-down [LIMIT]",),
    kw8: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_user_up", ""), metavar="bw-limit-user-up [LIMIT]",),
    kw9: Tuple[AddWlanArgs, str] = typer.Argument(
        ("bw_limit_user_down", ""),
        metavar="bw-limit-user-down [LIMIT]",
    ),
    kw10: Tuple[AddWlanArgs, str] = typer.Argument(
        ("portal_profile", ""),
        metavar="portal-profile [PORTAL PROFILE]",
    ),
    hidden: bool = typer.Option(False, "--hidden", help="Make WLAN hidden"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    group = cli.cache.get_group_identifier(group)
    kwarg_list = [kw1, kw2, kw3, kw4, kw5, kw6, kw7, kw8, kw9, kw10]
    _to_name = {
        "psk": "wpa_passphrase",
        "ssid": "essid",
        "bw_limit_up": "bandwidth_limit_up",
        "bw_limit_down": "bandwidth_limit_down",
        "bw_limit_user_up": "bandwidth_limit_peruser_up",
        "bw_limit_user_down": "bandwidth_limit_peruser_down",
        "portal_profile": "captive_profile_name",
    }
    kwargs = {_to_name.get(kw[0], kw[0]): kw[1] for kw in kwarg_list}
    if hidden:
        kwargs["hide_ssid"] = True

    if not kwargs["wpa_passphrase"]:
        typer.secho("psk/passphrase is currently required for this command")
        raise typer.Exit(1)

    if yes or typer.confirm(typer.style(f"Please Confirm Add wlan {name} to {group.name}", fg="cyan")):
        resp = cli.central.request(cli.central.create_wlan, group.name, name, **kwargs)
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.callback()
def callback():
    """
    Add devices / objects.
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
