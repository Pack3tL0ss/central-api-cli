#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
import sys
import typer
from rich import print


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

from centralcli.constants import AllDevTypes, lib_to_api, lib_to_gen_plural # noqa

app = typer.Typer()

# TODO reboot flag Applicable only on MAS, aruba switches and controller since IAP reboots automatically after firmware download.
# can only specify one of group, swarm_id or serial parameters

@app.command(short_help="Upgrade firmware on a specific device",)
def device(
    device: str = typer.Argument(
        ...,
        metavar="Device: [serial #|name|ip address|mac address]",
        autocompletion=cli.cache.dev_completion,
    ),
    version: str = typer.Argument(
        None,
        help="Version to upgrade to [Default: recommended version]",
        show_default=False,
        autocompletion=lambda incomplete: [
            m for m in [
                ("<firmware version>", "The version of firmware to upgrade to."),
                *[m for m in cli.cache.null_completion(incomplete)]
            ]
        ],
    ),
    at: datetime = typer.Option(
        None,
        help="When to schedule upgrade. format: 'mm/dd/yyyy_hh:mm' or 'dd_hh:mm' (implies current month) [Default: Now]",
        show_default=False,
        formats=["%m/%d/%Y_%H:%M", "%d_%H:%M"],
        ),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download (APs will reboot regardless)"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    dev = cli.cache.get_dev_identifier(device)
    if dev.generic_type == "ap":
        reboot = True
    at = None if not at else int(round(at.timestamp()))

    ver_msg = "Recommended version" if not version else version
    ver_msg = f"{ver_msg} and reboot" if reboot else f"{ver_msg} ('-R' not specified, device will not be rebooted)"

    if yes or typer.confirm(
        typer.style(
            f"Upgrade {dev.name} to {ver_msg}?",
            fg="bright_green",
        ),
        abort=True,
    ):
        resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, serial=dev.serial,
                                   firmware_version=version, reboot=reboot)
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Upgrade firmware by group",)
def group(
    group: str = typer.Argument(
        ...,
        metavar="[GROUP NAME]",
        help="Upgrade devices by group",
        autocompletion=cli.cache.group_completion,
    ),
    version: str = typer.Argument(
        None,
        help="Version to upgrade to [Default: recommended version]",
        show_default=False,
        autocompletion=lambda incomplete: [
            m for m in [
                ("<firmware version>", "The version of firmware to upgrade to."),
                *[m for m in cli.cache.null_completion(incomplete)]
            ]
        ],
    ),
    at: datetime = typer.Option(
        None,
        help="When to schedule upgrade. format: 'mm/dd/yyyy hh:mm' or 'dd hh:mm' (implies current month) [Default: Now]",
        show_default=False,
        formats=["%m/%d/%Y %H:%M", "%d %H:%M"],
        ),
    dev_type: AllDevTypes = typer.Option(..., help="Upgrade a specific device type",),
    model: str = typer.Option(None, help="[applies to switches only] Upgrade a specific switch model"),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download (APs will reboot regardless)"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",  show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                ),
) -> None:
    yes = yes_ if yes_ else yes
    group = cli.cache.get_group_identifier(group)
    at = None if not at else int(round(at.timestamp()))

    ver_msg = [typer.style("Upgrade", fg="cyan")]
    if dev_type:
        if dev_type == "ap":
            reboot = True
        ver_msg += [lib_to_gen_plural(dev_type)]
        dev_type = lib_to_api("upgrade", dev_type)

    if model:
        ver_msg += [f"model {typer.style(f'{model}', fg='bright_green')}"]

    ver_msg += [f"in group {typer.style(f'{group.name}', fg='bright_green')}"]

    if version:
        _version = [f"to {typer.style(version, fg='bright_green')}"]
    else:
        _version = [f"to {typer.style('Recommended version', fg='bright_green')}"]
    ver_msg += _version
    ver_msg = " ".join(ver_msg)

    if reboot:
        ver_msg = f"{ver_msg} and reboot"
    else:
        ver_msg = f"{ver_msg} ('-R' not specified, device will not be rebooted)"

    if yes or typer.confirm(
        f"{ver_msg}?",
        abort=True,
    ):
        resp = cli.central.request(
            cli.central.upgrade_firmware,
            scheduled_at=at,
            group=group.name,
            device_type=dev_type,
            firmware_version=version,
            model=model,
            reboot=reboot
        )
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Upgrade firmware for an IAP cluster",)
def swarm(
    swarm: str = typer.Argument(
        None,
        metavar="[IAP VC NAME|IAP SWARM ID|AP NAME|AP SERIAL|AP MAC]",
        help="Upgrade firmware on an IAP cluster.  For AP name,serial,mac it will upgrade the cluster that AP belongs to.",
    ),
    version: str = typer.Argument(None, help="Version to upgrade to",),
    at: datetime = typer.Option(
        None,
        help="When to schedule upgrade. format: 'mm/dd/yyyy hh:mm' or 'dd hh:mm' (implies current month) [Default: Now]",
        show_default=False,
        formats=["%m/%d/%Y %H:%M", "%d %H:%M"],
        ),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    at = None if not at else int(round(datetime.timestamp(at)))

    # swarm = cli.cache.get_swarm_identifier(swarm)
    class SwarmTemp:  # Temporary until swarm cache built
        def __init__(self, swarm_id):
            self.id = swarm_id
    swarm = SwarmTemp(swarm)

    ver_msg = [typer.style("Upgrade APs in swarm", fg="cyan")]
    if version:
        _version = [f"to {typer.style('Recommended version', fg='bright_green')}"]
    else:
        _version = [f"to {typer.style(version, fg='bright_green')}"]
    ver_msg += _version

    if reboot:
        ver_msg += [typer.style("and reboot?", fg="cyan")]
    ver_msg = " ".join(ver_msg)

    if yes or typer.confirm(ver_msg, abort=True):
        resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, swarm_id=swarm.id, reboot=reboot)
        cli.display_results(resp)


@app.callback()
def callback():
    """
    Upgrade Firmware
    """
    pass


if __name__ == "__main__":
    app()
