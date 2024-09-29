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

from centralcli.constants import AllDevTypes, lib_to_api, lib_to_gen_plural, iden_meta # noqa
from centralcli.objects import DateTime

app = typer.Typer()

# TODO reboot flag Applicable only on MAS, aruba switches and controller since IAP reboots automatically after firmware download.
# can only specify one of group, swarm_id or serial parameters

# You can only specify one of group, swarm_id or serial parameters

@app.command()
def device(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        autocompletion=cli.cache.dev_completion,
        show_default=False,
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
    at: datetime = cli.options.at,
    in_: str = typer.Option(None, "--in", help="Upgrade device in <delta from now>, where d=days, h=hours, m=mins i.e.: [cyan]3h[/] [grey42]\[default: Now][/]", show_default=False,),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download [green3](APs will reboot regardless)[/]"),
    yes: int = typer.Option(0, "-Y", "-y", count=True, help="Bypass confirmation prompts [cyan]use '-yy'[/] to bypass all prompts (perform cache update if swarm_id is not populated yet for AP)", show_default=False),
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
    at = None if not at else round(at.timestamp())
    if in_:
        at = cli.delta_to_start(in_, past=False).int_timestamp


    ver_msg = "Recommended version" if not version else version
    ver_msg = f'Upgrade [cyan]{dev.name}[/] to [green3]{ver_msg}[/]'
    if at:
        dt = DateTime(at)
        ver_msg = f'{ver_msg} [italic]at {dt}[/]'

    ver_msg = f"{ver_msg} and reboot" if reboot else f"{ver_msg} ('-R' not specified, [italic bright_red]device will not be rebooted[/])"

    print(ver_msg)
    if cli.confirm(yes):
        if dev.type == "ap":  # TODO need to validate this is the same behavior for 8.x IAP.
            if not dev.swack_id:
                print(f"\n[cyan]{dev.name}[/] lacks a swarm_id, may not be populated yet if it was recently added.")
                if yes > 1 or typer.confirm("\nRefresh cache now to check if it's populated", abort=True):
                    cli.central.request(cli.cache.refresh_dev_db, dev_type="ap")
                    dev = cli.cache.get_dev_identifier(dev.serial, dev_type="ap")

            if dev.swack_id:
                resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, swarm_id=dev.swack_id, firmware_version=version, reboot=reboot)
            else:
                cli.exit(f"Unable to perform Upgrade on {dev.summary_text}.  [cyan]swarm_id[/] is required for APs and the API is not returning a value for it yet.")
        else:
            resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, serial=dev.serial, firmware_version=version, reboot=reboot)
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Upgrade firmware by group",)
def group(
    group: str = typer.Argument(
        ...,
        metavar=iden_meta.group,
        help="Upgrade devices by group",
        autocompletion=cli.cache.group_completion,
        show_default=False,
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
    at: datetime = cli.options.at,
    in_: str = typer.Option(None, "--in", help="Upgrade devices in <delta from now>, where d=days, h=hours, m=mins i.e.: [cyan]3h[/] [grey42]\[default: Now][/]", show_default=False,),
    dev_type: AllDevTypes = typer.Option(..., help="Upgrade a specific device type", show_default=False,),
    model: str = typer.Option(None, help="Upgrade a specific switch model [grey42]\[applies to AOS-SW switches only]", show_default=False,),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download (APs will reboot regardless)"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Update devices by group.

    Device type must be provided.  For AOS-SW switches you can filter to a specific model via the --model flag.
    """
    group = cli.cache.get_group_identifier(group)
    at = None if not at else round(at.timestamp())
    if in_:
        at = cli.delta_to_start(in_, past=False).int_timestamp

    ver_msg = [typer.style("Upgrade", fg="cyan")]
    if dev_type:
        if dev_type == "ap":
            reboot = True
        ver_msg += [lib_to_gen_plural(dev_type)]

    if model:
        if "sw" not in group.AllowedDevTypes:
            cli.exit(f"[cyan]--model[/] only applies to AOS-SW [cyan]{group.name}[/] AOS-SW is not configured as an allowed device type for this group.")
        elif "sw" not in [d["type"] for d in cli.cache.devices if d["group"] == group.name]:
            cli.exit(f"[cyan]--model[/] only applies to AOS-SW [cyan]{group.name}[/] does not appear to contain any AOS-SW switches.\nIf local cache is stale, run command again with hidden [cyan]-U[/] option to update the cache.")
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
        metavar=iden_meta.dev,
        help="Upgrade will be performed on the cluster the AP belongs to.",
        autocompletion=cli.cache.dev_ap_completion,
    ),
    version: str = typer.Argument(None, help="Version to upgrade to",),
    at: datetime = cli.options.at,
    in_: str = typer.Option(None, "--in", help="Upgrade devices in <delta from now>, where d=days, h=hours, m=mins i.e.: [cyan]3h[/] [grey42]\[default: Now][/]", show_default=False,),
    reboot: bool = typer.Option(False, "-R", help="Automatically reboot device after firmware download"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    at = None if not at else round(at.timestamp())
    if in_:
        at = cli.delta_to_start(in_, past=False).int_timestamp

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
