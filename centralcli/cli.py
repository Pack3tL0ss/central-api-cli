#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from pathlib import Path
from time import sleep
from typing import List
import typer
import asyncio

from rich import print
from rich.console import Console

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False

err_console = Console(stderr=True)
clean_console = Console(emoji=False)

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import (Response, cleaner, cli, cliadd, cliassign,
                            clibatch, clicaas, cliclone, clidel, clikick, cliset,
                            clirefresh, clirename, clishow, clitest, clitshoot,
                            cliunassign, cliupdate, cliupgrade, cliexport,
                            config, log, models, utils)
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import (Response, cleaner, cli, cliadd, cliassign,
                                clibatch, clicaas, cliclone, clidel, clikick,
                                cliset, clirefresh, clirename, clishow, clitest,
                                clitshoot, cliunassign, cliupdate, cliupgrade,
                                cliexport, config, log, models, utils)
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.cache import CentralObject  # noqa
from centralcli.central import CentralApi  # noqa
from centralcli.constants import (BlinkArgs, BounceArgs, IdenMetaVars, StartArgs, ResetArgs, EnableDisableArgs,)  #noqa

iden = IdenMetaVars()

CONTEXT_SETTINGS = {
    # "token_normalize_func": lambda x: cli.normalize_tokens(x),
    "help_option_names": ["?", "--help"]
}

app = typer.Typer(context_settings=CONTEXT_SETTINGS, rich_markup_mode="rich")
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
app.add_typer(clirename.app, name="rename",)
app.add_typer(clikick.app, name="kick",)
app.add_typer(cliset.app, name="set",)
app.add_typer(cliexport.app, name="export", hidden=True)  # TODO remove once implemented


# TODO see if can change kw1 to "group" kw2 to "site" and unhide
@app.command()
def move(
    device: List[str, ] = typer.Argument(None, metavar=iden.dev_many, autocompletion=cli.cache.dev_kwarg_completion, show_default=False,),
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
        help="[cyan]site[/] keyword followed by the site name.",
        hidden=False,
    ),
    kw2: str = typer.Argument(
        None,
        metavar="",
        show_default=False,
        hidden=True,
    ),
    kw2_val: str = typer.Argument(
        None,
        metavar="[group <GROUP>]",
        show_default=False,
        help="[cyan]group[/] keyword followed by the group name.  [grey42 italic]\[site and/or group required][/]",
        hidden=False,
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
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Move device(s) to a defined group and/or site.
    """
    central = cli.central

    # For the benefit of the help text
    # kw1_val = site
    # kw2_val = group
    # TODO reverted as breaks completion logic would need to modif dev_kwarg_completion
    group, site, = None, None
    device = device or ()
    for a, b in zip([kw1, kw2], [kw1_val, kw2_val]):
        if a == "group":
            group = b
        elif a == "site":
            site = b
        else:
            device += tuple([aa for aa in [a, b] if aa and aa not in ["group", "site"]])

    group = group or _group

    # TODO can likely remove reset-group option
    if reset_group and not group:
        default_group_resp = cli.central.request(cli.central.get_default_group)
        default_group = default_group_resp.output
        group = default_group
    elif reset_group and group:
        print(f"Warning [cyan italic]--reset-group[/] flag ignored as destination group {group} was provided")

    site = site or _site
    if site:
        _site = cli.cache.get_site_identifier(site)

    if not group and not site:
        cli.exit("Missing Required Argument, group and/or site is required.")

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
                clean_console.print(f"\u26a0  {d.rich_help_text} is already in Site: {_site.summary_text}")  # \u26a0 is :warning: we need emoji off
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

    # Build confirmation message
    confirm_msg = f"[bright_green]Move[/] {_msg_devs}\n"
    if group:
        _group = CentralObject("group", {"name": "unprovisioned"}) if group.lower() == "unprovisioned" else cli.cache.get_group_identifier(group)
        confirm_msg += f"  To Group: [cyan]{_group.name}[/]\n"
        if cx_retain_config:
            confirm_msg += "  [italic]Config for CX switches will be preserved during move.[/]\n"
    if site:
        # _site = cli.cache.get_site_identifier(site)
        confirm_msg += f"  To Site: [cyan]{_site.name}[/]\n"
        if devs_by_site:
            confirm_msg += "\n  [italic bright_red]Devices will be removed from current sites.[/]\n"

    clean_console.print(confirm_msg)
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
            cli.central.request(cli.central.move_devices_to_group, _group.name, serial_nums=dev_all_serials, cx_retain_config=cx_retain_config)
        ]

    # only moving site, potentially multiple calls (for each device_type)
    # TODO this will issue the call even if the device is found to already be in the site
    # the cache can get out of sync because this move op does not update the cache  Need to do that and part of that
    # problem is solved.  partial workup to avoid in scratch, but cache update should be done first
    elif confirmed and _site:
        reqs, site_move_devs = [], []
        for _type in devs_by_type:
            _this_devs = [d for d in devs_by_type[_type] if d.site != _site.name]
            serials = [d.serial for d in _this_devs]
            site_move_devs += _this_devs

            if serials:
                reqs += [
                    central.BatchRequest(central.move_devices_to_site, _site.id, serial_nums=serials, device_type=_type)
                ]

        resp = [Response(url="Error", error=f"These devices are already in site {_site.name}")] if not reqs else central.batch_request(reqs)
        if all([r.ok for r in resp]):
            asyncio.run(cli.cache.update_dev_db(data=[{**dev.data, "site": _site.name} for dev in site_move_devs]))


    if site_rm_resp:
        resp = [*site_rm_resp, *resp]

    cli.display_results(resp, tablefmt="action")  #, ok_status=500)
    # TODO update cache when device succesfully moved
    # TODO ok_status is not used in display_results anymore, impacted colorization I think?  Need to verify.


@app.command()
def bounce(
    what: BounceArgs = typer.Argument(..., show_default=False),
    device: str = typer.Argument(..., metavar=iden.dev, show_default=False, autocompletion=cli.cache.dev_switch_completion),
    ports: List[str] = typer.Argument(..., autocompletion=lambda incomplete: [], show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Bounce interface(s) or PoE on interface(s) (Valid on switches)

    Ranges are supported:
    [cyan]cencli bounce interface edge3 1/1/1-1/1/4 2/1/1-2/1/4[/] will bounce the 8 interfaces in those ranges
    [cyan]cencli bounce interface edge3 1/1/1-1/1/4,2/1/1-2/1/4[/] comma seperated similar to swich CLI is also valid

    [italic dark_olive_green2]Results in 1 API call per interface[/]
    """
    dev = cli.cache.get_dev_identifier(device, conductor_only=True)
    command = 'bounce_poe_port' if what == 'poe' else 'bounce_interface'
    ports = utils.get_interfaces_from_range(ports)

    print(f"Bounce [cyan]{what}[/] on [cyan]{dev.name}[/]: interface{'s' if len(ports) > 1 else ''} [cyan]{', '.join(ports)}[/]")
    print(f"[italic dark_olive_green2]{len(ports)} API calls will be performed.[/]\n")
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.batch_request([cli.central.BatchRequest(cli.central.send_bounce_command_to_device, (dev.serial, command, p,)) for p in ports])
        cli.display_results(resp, tablefmt="action")
        # We don't check the task status because central seems to show the state as QUEUED even after execution appears complete


@app.command()
def remove(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.remove_completion),
    site: str = typer.Argument(
        ...,
        metavar="[site <SITE>]",
        show_default=False,
        autocompletion=cli.cache.remove_completion
    ),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Remove a device from a site
    """
    devices = (d for d in devices if d != "site")
    devices = [cli.cache.get_dev_identifier(dev) for dev in devices]
    site = cli.cache.get_site_identifier(site)

    print(
        f"Remove {', '.join([f'[bright_green]{dev.name}[/bright_green]' for dev in devices])} from site [bright_green]{site.name}"
    )
    if yes or typer.confirm("\nProceed?", abort=True):
        devs_by_type = {}
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


@app.command()
def reboot(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    swarm: bool = typer.Option(False, "-s", "--swarm", help="Reboot the swarm [grey42 italic](IAP cluster)[/] associated with the provided device (AP)."),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Reboot a device

    Use --swarm to reboot the swarm associated with the specified device (The device can be any AP in the swarm)
    """
    dev: CentralObject = cli.cache.get_dev_identifier(device, conductor_only=True)

    conf_msg = dev.rich_help_text
    func = cli.central.send_command_to_device
    arg = dev.serial

    if swarm:
        if dev.generic_type != "ap":
            print(f":warning:  Ignoring [green]-s[/]|[cyan]--swarm[/], as it only applies to APs not {dev.type}\n")
        elif dev.version.startswith("10."):
            print(":warning:  Ignoring [green]-s[/]|[cyan]--swarm[/] option, as it only applies to [cyan]AOS8[/] IAP\n")
        else:
            func = cli.central.send_command_to_swarm
            arg = dev.swack_id
            conf_msg = f'the [cyan]swarm {dev.name}[/] belongs to'
            # TODO reboot swarm has not been tested

    console = Console(emoji=False)
    _msg = "Reboot" if not yes else "Rebooting"
    _msg = f"{_msg} {conf_msg}"

    console.print(_msg)
    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(func, arg, 'reboot')
        cli.display_results(resp, tablefmt="action")


@app.command()
def reset(
    what: ResetArgs = typer.Argument("overlay"),
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_ap_gw_completion, show_default=False),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Reset overlay control connection (OTO/ORO)
    """
    # Not sure this works on APs/MB AP
    dev = cli.cache.get_dev_identifier(device, dev_type=("gw", "ap",))

    console = Console(emoji=False)
    _msg = "Reset" if not yes else "Resetting"
    _msg = f"{_msg} ORO connection for [cyan]{dev.rich_help_text}[/]"
    console.print(_msg)

    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(cli.central.reset_overlay_connection, dev.serial)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Blink LED")
def blink(
    device: str = typer.Argument(..., show_default=False, metavar=iden.dev, autocompletion=cli.cache.dev_switch_ap_completion),
    action: BlinkArgs = typer.Argument(..., show_default=False),  # metavar="Device: [on|off|<# of secs to blink>]"),
    secs: int = typer.Argument(None, metavar="SECONDS", help="Blink for {secs} seconds.", show_default=False,),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    command = f'blink_led_{action}'
    dev = cli.cache.get_dev_identifier(device, dev_type=["switch", "ap"])
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, command, duration=secs)
    cli.display_results(resp, tablefmt="action")


@app.command()
def nuke(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_switch_ap_completion),
    swarm: bool = typer.Option(False, "-s", "--swarm", help="Factory Default the swarm [grey42 italic](IAP cluster)[/] associated with the provided device (AP)."),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Reset a device to factory default, erase all configuration (Valid on ArubaOS-SW or IAP Clusters)

    :warning:  For AOS8 IAP this command is only valid for entire cluster, not individual APs -s|--swarm option is required.
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=["ap", "switch"])
    if dev.type == "cx":
        cli.exit("This command only applies to [cyan]AOS-SW[/] switches, not [cyan]CX[/]")

    conf_msg = dev.rich_help_text
    if dev.generic_type == "switch":
        func = cli.central.send_command_to_device
        arg = dev.serial
        if swarm:
            print(f":warning:  Ignoring -s|--swarm option, as it only applies to APs not {dev.type}\n")
    else:  # AP all others will error in get_dev_identifier
        func = cli.central.send_command_to_swarm
        arg = dev.swack_id
        if dev.version.startswith("10."):
            cli.exit("This command is only valid for [cyan]AOS8[/] IAP clusters not [cyan]AOS10[/] APs")
        elif not swarm:
            cli.exit("This command is only valid for the entire swarm in AOS8, not individual APs.  Use [green]-s[/]|[cyan]--swarm[/] to default the entire IAP cluster")
        else:
            conf_msg = f'the [cyan]swarm {dev.name}[/] belongs to'

    console = Console(emoji=False)
    _msg = "Factory Default" if not yes else "Factory Defaulting"
    _msg = f"[bright_red blink]{_msg}[/] {conf_msg}"
    console.print(_msg)
    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(func, arg, 'erase_configuration')
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
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Sync/Refresh device config with Aruba Central

    Only valid for gateways (aka controllers)
    """
    dev = cli.cache.get_dev_identifier(device, dev_type="gw")
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'config_sync')
    cli.display_results(resp, tablefmt="action")


# TODO get the account, port and process details (start_time, pid) cache
# add cache.RunDB or InfoDB to use to store this kind of stuff
@app.command(short_help="Start WebHook Proxy", hidden=not hook_enabled)
def start(
    what: StartArgs = typer.Argument(
        "hook-proxy",
        help="See documentation for info on what each webhook receiver does",
    ),
    port: int = typer.Option(config.wh_port, help="Port to listen on (overrides config value if provided)", show_default=True),
    yes: int = typer.Option(0, "-Y", "-y", count=True, help="Bypass confirmation prompts [cyan]use '-yy'[/] to bypass all prompts (including killing current process if running)", metavar="", show_default=False),
    collect: bool = typer.Option(False, "--collect", "-c", help="Store raw webhooks in local json file", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Start WebHook Proxy Service on this system in the background

    Currently 2 webhook automations:
    For Both automations the URL to configure as the webhook destination is [cyan]http://localhost/api/webhook[/] (currently http)

    [cyan]hook-proxy[/]:
      - Gathers status of all branch tunnels at launch, and utilizes webhooks to keep a local DB up to date.
      - Presents it's own REST API that can be polled for branch/tunnel status:
        See [cyan]http://localhost:port/api/docs[/] for available endpoints / schema details.

    [cyan]hook2snow[/]:
      - [bright_red]!!![/]This integration is incomplete, as the customer that requested it ended up going a different route with the webhooks.
      - Queries alerts API at launch to gather any "Open" items.
      - Receives webhooks from Aruba Central, and creates or resolves incidents in Service-Now via SNOW REST API

    [italic]Requires optional hook-proxy component '[bright_green]pip3 install -U centralcli\[hook-proxy][reset]'
    """
    if config.deprecation_warning:  # TODO remove at 2.0.0+
        print(config.deprecation_warning)
    svc = "wh_proxy" if what == "hook-proxy" else "wh2snow"
    yes_both = True if yes > 1 else False
    yes = True if yes else False
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
            if p.info["cmdline"] and True in [svc in x for x in p.info["cmdline"][1:]]:
                return p.pid # if p.ppid() == 1 else p.ppid()

    pid = get_pid()
    if pid:
        _abort = True if not port or port == int(config.webhook.port) else False
        print(f"Webhook proxy is currently running (process id {pid}).")
        if yes_both or typer.confirm("Terminate existing process", abort=_abort):
            terminate_process(pid)
            print("[cyan]Process Terminated")

    # ["nohup", sys.executable, "-m", "centralcli.wh_proxy", "--port", str(port), "--account", config.account],
    config_port = 9143 if not config.webhook else config.webhook.port
    print(f"Webhook Proxy will listen on port {port or config_port}")
    if yes or yes_both or typer.confirm("\nProceed?", abort=True):
        console = Console()
        port = port or config.webhook.port
        cmd = ["nohup", sys.executable, "-m", f"centralcli.{svc}", str(port)]
        if collect:
             cmd += ["-c"]
        with console.status("Starting Webhook Proxy..."):
            p = subprocess.Popen(
                cmd,
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
            print("\nWebHook Proxy Startup [red]Failed[/].")
        else:
            print(f"[{p.pid}] WebHook Proxy [bright_green]Started[/].")


@app.command(short_help="Stop WebHook Proxy", hidden=not hook_enabled)
def stop(
    what: StartArgs = typer.Argument(
        ...,
        # metavar=f"hook-proxy",
    ),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Stop WebHook Proxy (background process).
    """
    svc = "wh_proxy" if what == "hook-proxy" else "wh2snow"
    # TODO move these out of this function and just call them from both start/stop
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
            if svc in str(p.cmdline()[1:]):
                for flag in p.cmdline()[::-1]:
                    if flag.startswith("-"):
                        continue
                    elif flag.isdigit():
                        port = flag
                        break
                return p.pid, port

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

@app.command(short_help="Archive devices", hidden=False)
def archive(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Archive devices.  This has less meaning/usefulness with the transition to GreenLake.

    cencli archive <devices>, followed by cencli unarchive <devices> removes any subscriptions
    and the devices assignment to the Aruba Central App in GreenLake.

    Archive removes the GreenLake assignment, but the device can't be added to a different account
    until it's unarchived.

    Just use cencli deleve device ... or cencli batch delete devices
    """
    devices: List[CentralObject] = [cli.cache.get_dev_identifier(dev, silent=True, include_inventory=True) for dev in devices]

    # TODO add confirmation method builder to output class
    _msg = "[bright_green]Archive devices[/]:"
    if len(devices) > 1:
        _dev_msg = '\n    '.join([dev.rich_help_text for dev in devices])
        _msg = f"{_msg}\n    {_dev_msg}\n"
    else:
        dev = devices[0]
        _msg = f"{_msg} {dev.rich_help_text}"

    console = Console(emoji=False)
    console.print(_msg)
    if yes or typer.confirm("\nProceed?"):
        resp = cli.central.request(cli.central.archive_devices, [d.serial for d in devices])
        cli.display_results(resp, tablefmt="action")



@app.command()
def unarchive(
    serials: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Unacrchive devices

    Remove previously archived devices from archive.

    Specify device by serial.  (archived devices will not be in Inventory cache for name lookup)
    """
    serials: List[CentralObject] = [cli.cache.get_dev_identifier(dev, silent=True, retry=False, include_inventory=True, exit_on_fail=False) or dev for dev in serials]

    _msg = "[bright_green]Unarchive devices[/]:"
    if serials and any([isinstance(d, CentralObject) for d in serials]):
        if len(serials) > 1:
            _dev_msg = '\n    '.join([dev if not isinstance(dev, CentralObject) else dev.rich_help_text for dev in serials])
            _msg = f"{_msg}\n    {_dev_msg}\n"
        else:
            dev = serials[0]
            _msg = f"{_msg} {dev if not isinstance(dev, CentralObject) else dev.rich_help_text}"
        serials: List[str] = [d if not isinstance(d, CentralObject) else d.serial for d in serials]
    else:
        _dev_msg = '\n    '.join(serials)
        _msg = f"{_msg}\n    {_dev_msg}\n"
    print(_msg)

    resp = cli.central.request(cli.central.unarchive_devices, serials)
    cli.display_results(resp, tablefmt="action")


@app.command(hidden=True)
def enable(
    what: EnableDisableArgs = typer.Argument("auto-sub"),
    services: List[cli.cache.LicenseTypes] = typer.Argument(..., show_default=False),  # type: ignore
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Enable auto subscribe for service.

    Enabling auto subscribe sets the level (i.e. foundation/advanced) for all devices of the same type as the subscription provided.
    i.e. `enable auto-sub advanced-switch-6300` will enable auto subscribe for all switch tiers (6100, 6200, etc)
    """

    _msg = "[bright_green]Enable[/] auto-subscribe for license"
    if len(services) > 1:
        _svc_msg = '\n    '.join([s.name for s in services])
        _msg = f'{_msg}s:\n    {_svc_msg}\n'
    else:
        svc = services[0]
        _msg = f'{_msg} {svc.name}'
    print(_msg)
    print('\n[dark_orange]!![/] Enabling auto-subscribe applies the specified tier (i.e. foundation/advanced) for [green bold]all[/] devices of the same type.')
    print('[cyan]enable auto-sub advanced-switch-6300[/] will result in [green bold]all[/] switch models being set to auto-subscribe the advanced license appropriate for that model.')
    print('Not just the 6300 models.')
    if yes or typer.confirm("\nProceed?", abort=True):
        services = [s.name for s in services]

        resp = cli.central.request(cli.central.enable_auto_subscribe, services=services)
        cli.display_results(resp, tablefmt="action")


@app.command(hidden=True)
def disable(
    what: EnableDisableArgs = typer.Argument("auto-sub"),
    services: List[cli.cache.LicenseTypes] = typer.Argument(..., show_default=False),  # type: ignore
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Disable auto subscribe for service.

    Disabling auto subscribe removes auto-subscribe for all models of the same type.
    i.e. `disable auto-sub advanced-switch-6300` will disable auto subscribe for all switch tiers (6100, 6200, etc)
    """

    _msg = "[bright_green]Disable[/] auto-subscribe for license"
    if len(services) > 1:
        _svc_msg = '\n    '.join([s.name for s in services])
        _msg = f'{_msg}s:\n    {_svc_msg}\n'
    else:
        svc = services[0]
        _msg = f'{_msg} {svc.name}'
    print(_msg)
    print('\n[dark_orange]!![/] Disabling auto subscribe removes auto-subscribe for all models of the same type.')
    print('[cyan]disable auto-sub advanced-switch-6300[/] will result in auto-subscribe being disabled for [green bold]all[/] switch models.')
    print('Not just the 6300.')
    if yes or typer.confirm("\nProceed?", abort=True):
        services = [s.name for s in services]

        resp = cli.central.request(cli.central.enable_auto_subscribe, services=services)
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
    '.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf'

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
    # --raw and --debug-limit are honored and stripped out in init
    if ctx.resilient_parsing:
        config.is_completion = True
    if not ctx.resilient_parsing:
        version, account, debug, debugv, default, update_cache = None, None, None, None, None, None
        for idx, arg in enumerate(sys.argv[1:]):
            if idx == 0 and arg in ["-v", "-V", "--version"]:
                version = True
            if arg == "--debug":
                debug = True
            if arg == "--debugv":
                debugv = True
            elif arg == "-d":
                default = True
            elif arg == "--account" and "-d" not in sys.argv:
                account = sys.argv[idx + 2]  # sys.argv enumeration is starting at index 1 so need to adjust idx by 2 for next arg
            elif arg == "-U":
                update_cache = True
            elif arg.startswith("-") and not arg.startswith("--"):  # -dU is allowed
                if "d" in arg:
                    default = True
                if "U" in arg:
                    update_cache = True

        account = account or os.environ.get("ARUBACLI_ACCOUNT")
        debug = debug or os.environ.get("ARUBACLI_DEBUG", False)

        if version:
            cli.version_callback(ctx)
            raise typer.Exit(0)
        if default:
            if "--account " in str(sys.argv) and account not in ["central_info", "default"]:
                err_console.print(f":warning:  Both [cyan]-d[/] and [cyan]--account[/] flag used.  Honoring [cyan]-d[/], ignoring account [cyan]{account}[/]")
                account = config.default_account
            cli.account_name_callback(ctx, account=config.default_account, default=True)
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
    version: bool = typer.Option(False, "--version", "-V", "-v", case_sensitive=False, is_flag=True, help="Show current cencli version, and latest available version.",),
    debug: bool = typer.Option(False, "--debug", is_flag=True, envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
                            #    callback=all_commands_callback),
    debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging", hidden=True,),
                            #    callback=all_commands_callback),
    default: bool = typer.Option(
        False,
        "-d",
        is_flag=True,
        help="Use default central account",
        show_default=False,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
    update_cache: bool = typer.Option(False, "-U", hidden=True, lazy=True, callback=all_commands_callback),
) -> None:
    """
    Aruba Central API CLI
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()

# click_object = typer.main.get_command(app)  # exposed for documentation
