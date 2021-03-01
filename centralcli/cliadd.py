#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from enum import Enum
from pathlib import Path
import sys
from typing import Tuple
import typer


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli
    else:
        print(pkg_dir.parts)
        raise e

app = typer.Typer()


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


@app.command(short_help="Add a group")
def group(
    group: str = typer.Argument(..., metavar="[GROUP NAME]"),
    group_password: str = typer.Argument(
        None,
        show_default=False,
        help="Group password is required. You will be prompted for password if not provided.",
    ),
    wired_tg: bool = typer.Option(False, "--wired-tg", help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(False, "--wlan-tg", help="Manage IAP configurations via templates"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    if not group_password:
        group_password = typer.prompt("Group Password", confirmation_prompt=True, hide_input=True,)
    _msg = f'{typer.style(f"Create group", fg="cyan")}'
    _msg = f'{_msg} {typer.style(group, fg="bright_green")}'

    _word = None
    if wired_tg:
        _word = "switches"
    if wlan_tg:
        _word = "instant APs" if not _word else f"{_word} and {'instant APs'}"

    if _word:
        _msg = f'{_msg} {typer.style(f"with {_word} managed via template?", fg="cyan")}'
    else:
        _msg = f'{_msg}{typer.style(f"?", fg="cyan")}'

    if yes or typer.confirm(_msg):
        resp = cli.central.request(cli.central.create_group, group, group_password, wired_tg=wired_tg, wlan_tg=wlan_tg)
        cli.display_results(resp)
        if resp:
            asyncio.run(
                cli.cache.update_group_db({'name': group, 'template group': {'Wired': wired_tg, 'Wireless': wlan_tg}})
            )


@app.command(short_help="Add WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]"),
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
    # psk: str = typer.Option(None, "--psk"),
    # _type: str = typer.Option(None, "--type"),
    hidden: bool = typer.Option(False, "--hidden", help="Make WLAN hidden"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
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
