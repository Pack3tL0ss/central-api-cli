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

from centralcli.constants import AllDevTypes, lib_to_api, lib_to_gen_plural, IdenMetaVars # noqa

iden = IdenMetaVars()
app = typer.Typer()

# TODO reboot flag Applicable only on MAS, aruba switches and controller since IAP reboots automatically after firmware download.
# can only specify one of group, swarm_id or serial parameters

# You can only specify one of group, swarm_id or serial parameters

@app.command()
def device(
    device: str = typer.Argument(
        ...,
        metavar=iden.dev, show_default=False,
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
        help="When to schedule upgrade. format: 'mm/dd/yyyy_hh:mm' or 'dd_hh:mm' (implies current month) [default: Now]",
        show_default=False,
        formats=["%m/%d/%Y_%H:%M", "%d_%H:%M"],
        ),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download [green3](APs will reboot regardless)[/]"),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    """Upgrade firmware on a device
    """
    dev = cli.cache.get_dev_identifier(device, conductor_only=True)
    if dev.generic_type == "ap":
        reboot = True
    at = None if not at else int(round(at.timestamp()))

    ver_msg = "Recommended version" if not version else version
    ver_msg = f'Upgrade [cyan]{dev.name}[/] to [green3]{ver_msg}[/]'
    ver_msg = f"{ver_msg} and reboot" if reboot else f"{ver_msg} ('-R' not specified, [italic bright_red]device will not be rebooted[/])"

    print(ver_msg)
    if yes or typer.confirm("\nProceed?", abort=True):
        if dev.type == "ap":  # TODO need to validate this is the same behavior for 8.x IAP.
            # For AOS10 AP need to specifiy serial number as the swarm_id in payload to upgrade individual AP
            resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, swarm_id=dev.swack_id, firmware_version=version, reboot=reboot)
        else:
            resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, serial=dev.serial, firmware_version=version, reboot=reboot)
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Upgrade firmware by group",)
def group(
    group: str = typer.Argument(
        ...,
        metavar=iden.group,
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
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",  show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                ),
) -> None:
    """Update devices by group.

    Device type must be provided.  For switches you can/should filter to a specific switch model via the --model flag.
    """
    group = cli.cache.get_group_identifier(group)
    at = None if not at else int(round(at.timestamp()))

    ver_msg = [typer.style("Upgrade", fg="cyan")]
    if dev_type:
        if dev_type == "ap":
            reboot = True
        ver_msg += [lib_to_gen_plural(dev_type)]
        dev_type = lib_to_api("firmware", dev_type)

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

    if yes or typer.confirm(f"{ver_msg}?",abort=True,):
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
    device: str = typer.Argument(
        ...,
        metavar=iden.dev,
        help="Upgrade will be performed on the cluster the AP belongs to.",
        autocompletion=cli.cache.dev_ap_completion,
    ),
    version: str = typer.Argument(None, help="Version to upgrade to",),
    at: datetime = typer.Option(
        None,
        help="When to schedule upgrade. format: 'mm/dd/yyyy hh:mm' or 'dd hh:mm' (implies current month) [Default: Now]",
        show_default=False,
        formats=["%m/%d/%Y %H:%M", "%d %H:%M"],
        ),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download"),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    at = None if not at else int(round(datetime.timestamp(at)))

    dev = cli.cache.get_dev_identifier(device, dev_type="ap")
    swarm = dev.swack_id

    ver_msg = [typer.style("Upgrade APs in swarm", fg="cyan")]
    if version:
        _version = [f"to {typer.style(version, fg='bright_green')}"]
    else:
        _version = [f"to {typer.style('Recommended version', fg='bright_green')}"]
    ver_msg += _version

    if reboot:
        ver_msg += [typer.style("and reboot?", fg="cyan")]
    ver_msg = " ".join(ver_msg)

    if yes or typer.confirm(ver_msg, abort=True):
        resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, swarm_id=swarm, reboot=reboot, firmware_version=version)
        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Upgrade Firmware
    """
    pass


if __name__ == "__main__":
    app()
