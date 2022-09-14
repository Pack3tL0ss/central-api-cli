#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from time import sleep
from typing import List

from rich import print
from rich.console import Console

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False

import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import (cli, cliadd, clibatch, clicaas, cliclone, clidel,
                            clirefresh, clishow, clitest, cliupdate, cliupgrade,
                            clitshoot, cliassign, cliunassign, models, cleaner, Response, config, log, utils)
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import (cli, cliadd, clibatch, clicaas, cliclone, clidel,
                                clirefresh, clishow, clitest, cliupdate, cliupgrade,
                                clitshoot, cliassign, cliunassign, models, cleaner, Response, config, log, utils)
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi  # noqa
from centralcli.cache import CentralObject
from centralcli.constants import (
    BlinkArgs, BounceArgs, IdenMetaVars,
    KickArgs, LicenseTypes, RenameArgs, StartArgs
)

iden = IdenMetaVars()

CONTEXT_SETTINGS = {
    # "token_normalize_func": lambda x: cli.normalize_tokens(x),
    "help_option_names": ["?", "--help"]
}

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
app.add_typer(clishow.app, name="show",)
app.add_typer(clidel.app, name="delete",)
app.add_typer(cliadd.app, name="add",)
app.add_typer(cliassign.app, name="assign",)
app.add_typer(cliunassign.app, name="unassign",)
app.add_typer(cliclone.app, name="clone",)
app.add_typer(cliupdate.app, name="update",)
app.add_typer(cliupgrade.app, name="upgrade",)
app.add_typer(clibatch.app, name="batch",)
app.add_typer(clicaas.app, name="caas", hidden=True,)
app.add_typer(clirefresh.app, name="refresh",)
app.add_typer(clitest.app, name="test",)
app.add_typer(clitshoot.app, name="tshoot",)


@app.command(
    help="Move device(s) to a defined group and/or site.",
)
def move(
    device: List[str, ] = typer.Argument(None, metavar=iden.dev_many, autocompletion=cli.cache.dev_kwarg_completion),
    kw1: str = typer.Argument(
        None,
        metavar="",
        show_default=False,
        hidden=True,
    ),
    kw1_val: str = typer.Argument(
        None,
        metavar="[site <SITE>]",
        show_default=False,
    ),
    kw2: str = typer.Argument(
        None, metavar="",
        show_default=False,
        hidden=True,
    ),
    kw2_val: str = typer.Argument(
        None,
        metavar="[group <GROUP>]",
        show_default=False,
        help="[site and/or group required]",
    ),
    _group: str = typer.Option(
        None,
        "--group",
        help="Group to Move device(s) to",
        hidden=True,
        autocompletion=cli.cache.group_completion,
    ),
    _site: str = typer.Option(
        None, "--site",
        help="Site to move device(s) to",
        hidden=True,
        autocompletion=cli.cache.site_completion,
    ),
    reset_group: bool = typer.Option(
        False,
        "--reset-group",
        show_default=False,
        help="Reset group membership.  (move to the defined default group)",
    ),
    cx_retain_config: bool = typer.Option(False, "-k", help="Keep config intact for CX switches during move"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    central = cli.central
    console = Console()

    group, site, = None, None
    for a, b in zip([kw1, kw2], [kw1_val, kw2_val]):
        if a == "group":
            group = b
        elif a == "site":
            site = b
        else:
            device += tuple([aa for aa in [a, b] if aa and aa not in ["group", "site"]])

    # Don't think it's possible to hit this (typer or cache lookup will fail first)
    # if not device and not import_file:
    #     print("Missing Required argument '[[name|ip|mac|serial] ...]'.")
    #     raise typer.Exit(1)

    group = group or _group

    if reset_group and not group:
        default_group_resp = cli.central.request(cli.central.get_default_group)
        default_group = default_group_resp.output
        group = default_group
    elif reset_group and group:
        print(f"Warning [cyan italic]--reset-group[/] flag ignored as destination group {group} was provided")

    site = site or _site
    _site = cli.cache.get_site_identifier(site)

    if not group and not site:
        print("Missing Required Argument, group and/or site is required.")
        raise typer.Exit(1)

    # TODO improve logic.  if they are moving to a group we can use inventory as backup
    # BUT if they are moving to a site it has to be connected to central first.  So would need to be in cache
    dev = [cli.cache.get_dev_identifier(d, include_inventory=True) for d in device]
    if any([d is None for d in dev]):
        # cache lookup failed... will happen if device has not connected yet
        inv = cli.central.request(cli.central.get_device_inventory)
        inventory = [models.Inventory(**i) for i in cleaner.get_device_inventory(inv.output)]
        for idx, (from_input, from_cache) in enumerate(zip(device, dev)):
            if from_cache is None:
                inv_dev = [d for d in inventory if d.serial == from_input.upper()]
                if not inv_dev:
                    print(f"Unable to find match for {from_input} Aborting.")
                    raise typer.Exit(1)
                else:
                    dev[idx] = CentralObject("dev", inv_dev[0].dict())
                    # TODO add Exit(1) if device has not connected and they try to move it to a site

    devs_by_type, devs_by_site = {}, {}
    dev_all_names, dev_all_serials, = [], []
    for d in dev:
        if d.generic_type not in devs_by_type:
            devs_by_type[d.generic_type] = [d]
        else:
            devs_by_type[d.generic_type] += [d]
        dev_all_names += [f"[reset][cyan]{d.name}[/]|[cyan]{d.serial}[/]"]
        dev_all_serials += [d.serial]

        if site and d.get("site"):
            if d.site == _site.name:  # device is already in desired site
                console.print(f"[dark_orange]:warning:[/] {d.rich_help_text} is already in Site: {_site.summary_text}")
                if not group:  # remove serial from devs_by_type if already in desired site, and site move is the only operation
                    _ = devs_by_type[d.generic_type].pop(len(devs_by_type[d.generic_type]) - 1)
                    if not devs_by_type[d.generic_type]:  # if type list is empty remove the type
                        del devs_by_type[d.generic_type]
                continue

            if f"{d.site}~|~{d.generic_type}" not in devs_by_site:
                devs_by_site[f"{d.site}~|~{d.generic_type}"] = [d]
            else:
                devs_by_site[f"{d.site}~|~{d.generic_type}"] += [d]

    if len(dev_all_names) > 2:
        _msg_devs = ", ".join(dev_all_names)
    else:
        _msg_devs = " & ".join(dev_all_names)

    confirm_msg = f"[bright_green]Move[/] {_msg_devs}\n"
    if group:
        _group = CentralObject("group", {"name": "unprovisioned"}) if group.lower() == "unprovisioned" else cli.cache.get_group_identifier(group)
        confirm_msg += f"  To Group: [cyan]{_group.name}[/]\n"
        if cx_retain_config:
            confirm_msg += f"  [italic]Config for CX switches will be preserved during move.[/]\n"
    if site:
        # _site = cli.cache.get_site_identifier(site)
        confirm_msg += f"  To Site: [cyan]{_site.name}[/]\n"
        if devs_by_site:
            confirm_msg += "\n  [italic bright_red]Devices will be removed from current sites.[/]\n"

    print(confirm_msg)
    confirmed = True if yes or typer.confirm("\nProceed?", abort=True) else False
    # TODO currently will ask to confirm even if it will result in no calls (dev already in site) Need to build reqs list
    #      Then ask for confirmation if there are reqs to perform...  Need to refactor/simplify

    # TODO can probably be cleaner.  list of site_rm_reqs, list of group/site mv reqs do requests at end
    # If devices are associated with a site currently remove them from that site first
    # FIXME moving 3 devices from one site to another no longer works correctly (disassociated 2 then 1, (2 calls) then added 1)
    # FIXME completion flaw  cencli move barn--ap ... given barn- -ap was the completion [barn-303p.2c30-ap, barn-518.2816-ap]
    resp, site_rm_resp, reqs = None, None, []
    if confirmed and _site and devs_by_site:
        site_remove_reqs = []
        for [site_name, dev_type], devs in zip([k.split("~|~") for k in devs_by_site.keys()], list(devs_by_site.values())):
            site_remove_reqs += [
                central.BatchRequest(
                    central.remove_devices_from_site,
                    cli.cache.get_site_identifier(site_name).id,
                    serial_nums=[d.serial for d in devs],
                    device_type=dev_type,
                )
            ]
        site_rm_resp = central.batch_request(site_remove_reqs)
        if not all(r.ok for r in site_rm_resp):
            cli.display_results(site_rm_resp, tablefmt="action", exit_on_fail=True)

    # run both group and site move in parallel
    if confirmed and _group and _site:
        reqs = [central.BatchRequest(central.move_devices_to_group, _group.name, serial_nums=dev_all_serials, cx_retain_config=cx_retain_config)]
        site_remove_reqs = []
        for _type in devs_by_type:
            serials = [d.serial for d in devs_by_type[_type]]
            reqs += [
                central.BatchRequest(central.move_devices_to_site, _site.id, serial_nums=serials, device_type=_type)
            ]

        resp = central.batch_request(reqs)

    # only moving group via single API call
    elif confirmed and _group:
        resp = [
            cli.central.request(cli.central.move_devices_to_group, _group.name, serial_nums=dev_all_serials)
        ]

    # only moving site, potentially multiple calls (for each device_type)
    # TODO this will issue the call even if the device is found to already be in the site
    # the cache can get out of sync because this move op does not update the cache  Need to do that and part of that
    # problem is solved.  partial workup to avoid in scratch, but cache update should be done first
    elif confirmed and _site:
        for _type in devs_by_type:
            serials = [d.serial for d in devs_by_type[_type] if d.site != _site.name]
            if serials:
                reqs = [
                    central.BatchRequest(central.move_devices_to_site, _site.id, serial_nums=serials, device_type=_type)
                ]

        resp = Response(url="Error", error=f"These devices are already in site {_site.name}") if not reqs else central.batch_request(reqs)

    if site_rm_resp:
        resp = [*site_rm_resp, *resp]

    cli.display_results(resp, tablefmt="action")  #, ok_status=500)
    # TODO update cache when device succesfully moved
    # TODO ok_status is not used in display_results anymore, impacted colorization I think?  Need to verify.


@app.command(short_help="Bounce Interface or PoE on Interface")
def bounce(
    what: BounceArgs = typer.Argument(...),
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_switch_completion),
    port: str = typer.Argument(..., autocompletion=lambda incomplete: []),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    command = 'bounce_poe_port' if what == 'poe' else 'bounce_interface'
    print(f"Bounce [cyan]{what}[/] on [cyan]{dev.name}[/] port [cyan]{port}[/]")
    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.request(cli.central.send_bounce_command_to_device, dev.serial, command, port)
        cli.display_results(resp, tablefmt="action")
        # typer.secho(str(resp), fg="green" if resp else "red")
        # !! removing this for now Central ALWAYS returns:
        # !!   reason: Sending command to device. state: QUEUED, even after command execution.
        # if resp and resp.get('task_id'):
        #     resp = cli.central.request(session.get_task_status, resp.task_id)
        #     typer.secho(str(resp), fg="green" if resp else "red")

    else:
        raise typer.Abort()


@app.command(help="Remove a device from a site")
def remove(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.remove_completion),
    # _device: List[str] = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.completion),
    # _site_kw: RemoveArgs = typer.Argument(None),
    site: str = typer.Argument(
        ...,
        metavar="[site <SITE>]",
        show_default=False,
        autocompletion=cli.cache.remove_completion
    ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    devices = (d for d in devices if d != "site")
    devices = [cli.cache.get_dev_identifier(dev) for dev in devices]
    site = cli.cache.get_site_identifier(site)

    # TODO add confirmation method builder to output class
    print(
        f"Remove {', '.join([f'[bright_green]{dev.name}[/bright_green]' for dev in devices])} from site [bright_green]{site.name}"
    )
    if yes or typer.confirm("\nProceed?"):
        devs_by_type = {
        }
        for d in devices:
            if d.generic_type not in devs_by_type:
                devs_by_type[d.generic_type] = [d.serial]
            else:
                devs_by_type[d.generic_type] += [d.serial]
        reqs = [
            cli.central.BatchRequest(
                cli.central.remove_devices_from_site,
                site.id,
                serial_nums=serials,
                device_type=dev_type) for dev_type, serials in devs_by_type.items()
        ]
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Reboot a device")
def reboot(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_completion,),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    # TODO add swarm cache and support for central.send_command_to_swarm

    console = Console(emoji=False)
    _msg = "Reboot" if not yes else "Rebooting"
    _msg = f"{_msg} [cyan]{dev.rich_help_text}[/]"
    console.print(_msg)

    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'reboot')
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Blink LED")
def blink(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_switch_ap_completion),
    action: BlinkArgs = typer.Argument(..., ),  # metavar="Device: [on|off|<# of secs to blink>]"),
    secs: int = typer.Argument(None, metavar="SECONDS", help="Blink for _ seconds."),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes", hidden=True),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes  # Not using confirmation for blink but will allow -Y
    command = f'blink_led_{action}'
    dev = cli.cache.get_dev_identifier(device, dev_type=["switch", "ap"])
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, command, duration=secs)
    cli.display_results(resp, tablefmt="action")


@app.command(help="Factory Default A Switch (ArubaOS-SW only)")
def nuke(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_switch_completion),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    if dev.type != "sw":
        print(f"[bright_red]ERROR:[/] This command only applies to AOS-SW (switches), not {dev.type.upper()}")
        raise typer.Exit(1)

    _msg = "Factory Default" if not yes else "Factory Defaulting"
    print(f"[bright_red blink]{_msg}[/] [cyan]{dev.name}[/]|[cyan]{dev.serial}[/]")
    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'erase_configuration')
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Save Device Running Config to Startup")
def save(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_completion),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'save_configuration')
    cli.display_results(resp, tablefmt="action")


@app.command(short_help="Sync/Refresh device config with Aruba Central")
def sync(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_completion),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'config_sync')
    cli.display_results(resp, tablefmt="action")


# XXX Doesn't actually appear to be valid for any group rename
# TODO non batch rename AP
@app.command(help="Rename an Access Point", hidden=False)
def rename(
    what: RenameArgs = typer.Argument(...,),
    group_ap: str = typer.Argument(..., metavar=f"AP{iden.dev}", autocompletion=cli.cache.dev_kwarg_completion),
    new_name: str = typer.Argument(...),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    if what == "group":
        group_ap = cli.cache.get_group_identifier(group_ap)
        print(f"Please Confirm: rename group [red]{group_ap.name}[/red] -> [bright_green]{new_name}[/bright_green]")
        if yes or typer.confirm("proceed?", abort=True):
            resp = cli.central.request(cli.central.update_group_name, group_ap.name, new_name)

            # API-FLAW Doesn't actually appear to be valid for any group type
            if not resp and "group already has AOS_10X version set" in resp.output.get("description", ""):
                resp.output["description"] = f"{group_ap.name} is an AOS_10X group, " \
                    "rename only supported on AOS_8X groups. Use clone."

            cli.display_results(resp, tablefmt="action")

    elif what == "ap":
        group_ap = cli.cache.get_dev_identifier(group_ap, dev_type="ap")
        print(f"Please Confirm: rename ap [bright_red]{group_ap.name}[/] -> [bright_green]{new_name}[/]")
        print("    [italic]Will result in 2 API calls[/italic]\n")
        if yes or typer.confirm("Proceed?", abort=True):
            resp = cli.central.request(cli.central.update_ap_settings, group_ap.serial, new_name)
            cli.display_results(resp, tablefmt="action")


# TODO cache show clients get details for client make this easier
# currently requires the serial of the device the client is connected to
@app.command(help="Disconnect a WLAN client",)
def kick(
    device: str = typer.Argument(
        ...,
        metavar=f"CONNECTED_DEVICE{iden.dev}",
        autocompletion=cli.cache.dev_ap_completion
    ),
    what: KickArgs = typer.Argument(...,),
    who: str = typer.Argument(None, help="[<mac>|<wlan/ssid>]",),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Disconnect a client.

    This command currently only applies to APs
    """
    # TODO cache the client details so they don't have to specify the connected_device but can
    # kick client by hostname/username/ip/mac/...
    yes = yes_ if yes_ else yes
    if device in ["all", "mac", "wlan"]:
        typer.secho(f"Missing device parameter required before keyword {device}", fg="red")
        raise typer.Exit(1)
    dev = cli.cache.get_dev_identifier(device)
    if what == "mac":
        if not who:
            typer.secho("Missing argument <mac address>", fg="red")
            raise typer.Exit(1)
        mac = utils.Mac(who)
        who = mac.cols
        if not mac:
            typer.secho(f"{mac.orig} does not appear to be a valid mac address", fg="red")
            raise typer.Exit(1)

    _who = f" {who}" if who else " "
    if yes or typer.confirm(typer.style(f"Please Confirm: kick {what}{_who} on {dev.name}", fg="cyan"), abort=True):
        resp = cli.central.request(
            cli.central.kick_users,
            dev.serial,
            kick_all=True if what == "all" else False,
            mac=None if what != "mac" else mac.cols,
            ssid=None if what != "wlan" else who,
            )
        cli.display_results(resp, tablefmt="action")
        # typer.secho(str(resp), fg="green" if resp else "red")


# TODO get the account, port and process details (start_time, pid) cache
# add cache.RunDB or InfoDB to use to store this kind of stuff
@app.command(short_help="Start WebHook Proxy", hidden=not hook_enabled)
def start(
    what: StartArgs = typer.Argument(
        ...,
        # metavar=f"hook-proxy",
    ),
    port: int = typer.Option(None, help="Port to listen on (overrides config value if provided"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    yes_both: bool = typer.Option(False, "-YY", help="Bypass all confirmations, including killing current process if running."),
    yes_both_: bool = typer.Option(False, "-yy", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Start WebHook Proxy Service on this system in the background

    Requires optional hook-proxy component 'pip3 install centralcli[hook-proxy]'

    """
    yes = yes_ if yes_ else yes
    yes_both = yes_both_ if yes_both_ else yes_both
    def terminate_process(pid):
        p = psutil.Process(pid)
        for _ in range(2):
            p.terminate()
            if p.status() != 'Terminated':
                p.kill()
            else:
                break

    def get_pid():
        for p in psutil.process_iter(attrs=["name", "cmdline"]):
            if p.info["cmdline"] and True in ["wh_proxy" in x for x in p.info["cmdline"][1:]]:
                return p.pid # if p.ppid() == 1 else p.ppid()

    pid = get_pid()
    if pid:
        _abort = True if not port or port == int(config.wh_port) else False
        print(f"Webhook proxy is currently running (process id {pid}).")
        if yes_both or typer.confirm("Terminate existing process", abort=_abort):
            terminate_process(pid)
            print("[cyan]Process Terminated")

    # ["nohup", sys.executable, "-m", "centralcli.wh_proxy", "--port", str(port), "--account", config.account],
    print(f"Webhook Proxy will listen on {port or config.wh_port}")
    if yes or yes_both or typer.confirm("\nProceed?", abort=True):
        console = Console()
        port = port or config.wh_port
        with console.status("Starting Webhook Proxy..."):
            p = subprocess.Popen(
                ["nohup", sys.executable, "-m", "centralcli.wh_proxy", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            sleep(2)

        with console.status("Ensuring startup success...", spinner="dots2"):
            sleep(8)

        proc = psutil.Process(p.pid)
        if not psutil.pid_exists(p.pid) or proc.status() not in ["running", "sleeping"]:
            output = [line.decode("utf-8").rstrip() for line in p.stdout if not line.decode("utf-8").startswith("nohup")]
            print("\n".join(output))
            print(f"\n[red]WebHook Proxy Startup Failed")
        else:
            print(f"[{p.pid}] WebHook Proxy Started.")


@app.command(short_help="Stop WebHook Proxy", hidden=not hook_enabled)
def stop(
    what: StartArgs = typer.Argument(
        ...,
        # metavar=f"hook-proxy",
    ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Stop WebHook Proxy (background process).
    """
    yes = yes_ if yes_ else yes
    def terminate_process(pid):
        console = Console(emoji=False)
        with console.status("Terminating Webhook Proxy..."):
            p = psutil.Process(pid)
            for _ in range(2):
                p.terminate()
                sleep(2)

                if p.is_running():
                    p.kill()
                else:
                    return True

        with console.status("Waiting for WebHook Proxy to die..."):
            _pass = 0
            while p.is_running() or _pass < 8:
                sleep(1)
                if not p.is_running():
                    return True
                _pass += 1

        return False


    def _get_process_info():
        for p in psutil.process_iter(attrs=["name", "cmdline"]):
            if "wh_proxy" in str(p.cmdline()[1:]):
                return p.pid, p.cmdline()[-1]

    proc = _get_process_info()
    if proc:
        print(f"[{proc[0]}] WebHook Proxy is listening on port: {proc[1]}")
        if yes or typer.confirm("Terminate existing process", abort=True):
            dead = terminate_process(proc[0])
            print("[cyan]WebHook process terminated" if dead else "Terminate may have [bright_red]failed[/] verify process.")
            raise typer.Exit(0 if dead else 1)
    else:
        print("WebHook Proxy is not running.")
        raise typer.Exit(0)

# TODO Unhide once impact of archive is known post GreenLake... still licensed and shows in device list.
@app.command(help="Archive devices", hidden=True)
def archive(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    yes = yes_ if yes_ else yes
    devices = [cli.cache.get_dev_identifier(dev) for dev in devices]

    # TODO add confirmation method builder to output class
    _dev_str = "\n".join([f"- [cyan]{str(dev).lstrip()}[/]" for dev in devices])
    _msg = f"[bright_green]Archive Devices[/]:"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([f'[cyan]{dev.name}|{dev.serial}|{dev.mac}[/]' for dev in devices])
        _msg = f"{_msg}:\n{_dev_msg}"
    else:
        dev = devices[0]
        _msg = f"{_msg} [cyan]{dev.name}|{dev.serial}|{dev.mac}[/]"
    print(_msg)
    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.request(cli.central.archive_devices, [d.serial for d in devices])
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="convert j2 templates")
def convert(
    template: Path = typer.Argument(..., help="j2 template to convert", exists=True),
    var_file: Path = typer.Argument(
        None,
        help="Optional variable file, will automatically look for file with same name as template and supported extension/format.",
        exists=True,
        ),
    outfile: Path = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, "--pager", help="Enable Paged Output"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Convert specified j2 template into final form based on variable file.

    --var-file is optional, If not provided cencli will look in the same dir as the template
    for a file with the same name and supported extension.

    cencli supports most common extension for variable import:
    '.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf', '.xls', '.xlsx'

    """
    if not var_file:
        var_file = [
            template.parent / f"{template.stem}{sfx}"
            for sfx in config.valid_suffix
            if Path.joinpath(template.parent, f"{template.stem}{sfx}").exists()
        ]
        if not var_file:
            print(f":x: No variable file found matching template base-name [cyan]{template.stem}[/]")
            print(f"and valid extension: [cyan]{'[/], [cyan]'.join(config.valid_suffix)}[/].")
            raise typer.Exit(1)
        elif  len(var_file) > 1:
            print(f":x: Too many matches, found [cyan]{len(var_file)}[/] files with base-name [cyan]{template.stem}[/].")
            raise typer.Exit(1)
        else:
            var_file = var_file[0]
    final_config = utils.generate_template(template, var_file=var_file)
    cli.display_results(data=final_config.splitlines(), outfile=outfile)




def all_commands_callback(ctx: typer.Context, update_cache: bool):
    if not ctx.resilient_parsing:
        account, debug, debugv, default, update_cache = None, None, None, None, None
        for idx, arg in enumerate(sys.argv):
            if arg == "--debug":
                debug = True
            if arg == "--debugv":
                debugv = True
            elif arg == "-d":
                default = True
            elif arg == "--account" and "-d" not in sys.argv:
                account = sys.argv[idx + 1]
            elif arg == "-U":
                update_cache = True
            elif arg.startswith("-") and not arg.startswith("--"):
                if "d" in arg:
                    default = True
                if "U" in arg:
                    update_cache = True

        account = account or os.environ.get("ARUBACLI_ACCOUNT")
        debug = debug or os.environ.get("ARUBACLI_DEBUG", False)

        if default:
            default = cli.default_callback(ctx, True)
        # elif account:
        else:
            cli.account_name_callback(ctx, account=account)

        if debug:
            cli.debug_callback(ctx, debug=debug)
        if debugv:
            log.DEBUG = config.debug = log.verbose = config.debugv = debugv
            _ = sys.argv.pop(sys.argv.index("--debugv"))
        if update_cache:
            cli.cache(refresh=True)
            _ = sys.argv.pop(sys.argv.index("-U"))
            # TODO can do cache update here once update is removed from all commands
            pass


@app.callback()
def callback(
    # ctx: typer.Context,``
    debug: bool = typer.Option(False, "--debug", is_flag=True, envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
                            #    callback=all_commands_callback),
    debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging",),
                            #    callback=all_commands_callback),
    default: bool = typer.Option(
        False,
        "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
    update_cache: bool = typer.Option(False, "-U", hidden=True, lazy=True, callback=all_commands_callback),
) -> None:
    """
    Aruba Central API CLI
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()

click_object = typer.main.get_command(app)  # exposed for documentation
