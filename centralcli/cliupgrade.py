#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
import sys
import typer
from rich import print
from rich.markup import escape
from typing import TYPE_CHECKING


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

if TYPE_CHECKING:
    from .cache import CacheGroup

app = typer.Typer()


@app.command()
def device(
    device: str = cli.arguments.device,
    version: str = cli.arguments.version,
    at: datetime = cli.options.at,
    in_: str = cli.options.in_,
    reboot: bool = cli.options.reboot,
    yes: int = typer.Option(0, "-Y", "-y", "--yes", count=True, help="Bypass confirmation prompts [cyan]use '-yy'[/] to bypass all prompts (perform cache update if swarm_id is not populated yet for AP)", show_default=False),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Upgrade [dim italic](or Downgrade)[/] firmware on a device
    """
    forced = None
    dev = cli.cache.get_dev_identifier(device, conductor_only=True)
    if dev.generic_type == "ap":
        reboot = True
        if version and "beta" in version:  # beta for APs always looks like this "10.7.1.0-10.7.1.0-beta_91138"
            needless_prefix = version.split("-")[0]
            if not version.count(needless_prefix) == 2:
                version = f"{needless_prefix}-{version}"
    elif dev.type == "gw":
        forced = True
    at = None if not at else round(at.timestamp())
    if in_:
        at = cli.delta_to_start(in_, past=False).int_timestamp


    ver_msg = "Recommended version" if not version else version
    ver_msg = f'Upgrade [cyan]{dev.name}[/] to [green3]{ver_msg}[/]'
    if at:
        dt = DateTime(at)
        ver_msg = f'{ver_msg} [italic]at {dt}[/]'

    ver_msg = f"{ver_msg} and :recycle:  reboot" if reboot else f"{ver_msg} ('-R' not specified, [italic bright_red]device will not be rebooted[/])"

    print(ver_msg)
    cli.confirm(yes)  # aborts here if they don't confirm

    if dev.type == "ap":  # TODO need to validate this is the same behavior for 8.x IAP.
        if not dev.swack_id:
            print(f"\n[cyan]{dev.name}[/] lacks a swarm_id, may not be populated yet if it was recently added.")
            if yes > 1 or cli.confirm(prompt="\nRefresh cache now to check if it's populated"):
                cli.central.request(cli.cache.refresh_dev_db, dev_type="ap")
                dev = cli.cache.get_dev_identifier(dev.serial, dev_type="ap")

        if dev.swack_id:
            resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, swarm_id=dev.swack_id, firmware_version=version, reboot=reboot)
        else:
            cli.exit(f"Unable to perform Upgrade on {dev.summary_text}.  [cyan]swarm_id[/] is required for APs and the API is not returning a value for it yet.")
    else:
        resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, serial=dev.serial, firmware_version=version, reboot=reboot, forced=forced)
    cli.display_results(resp, tablefmt="action")


@app.command()
def group(
    group: str = typer.Argument(
        ...,
        metavar=iden_meta.group,
        help="Upgrade devices by group",
        autocompletion=cli.cache.group_completion,
        show_default=False,
    ),
    version: str = cli.arguments.version,
    dev_type: AllDevTypes = typer.Option(..., help="Upgrade a specific device type", show_default=False,),
    at: datetime = cli.options.at,
    in_: str = cli.options.in_,
    model: str = typer.Option(None, help=f"Upgrade a specific switch model [dim]{escape('[applies to AOS-SW switches only]')}[/]", show_default=False,),
    reboot: bool = cli.options.reboot,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Upgrade [dim italic](or Downgrade)[/] firmware on devices by group

    Device type must be provided.  For AOS-SW switches you can filter to a specific model via the --model flag.
    """
    group: CacheGroup = cli.cache.get_group_identifier(group)
    at = None if not at else round(at.timestamp())
    if in_:
        at = cli.delta_to_start(in_, past=False).int_timestamp

    ver_msg = ["[cyan]Upgrade[/]"] if not at else [f'Schedule [cyan]Upgrade[/] @ [italic cornflower_blue]{DateTime(at, "mdyt")}[/] for']

    if dev_type:
        if dev_type == "ap":
            reboot = True
            if version and "beta" in version:  # beta for APs always looks like this "10.7.1.0-10.7.1.0-beta_91138"
                needless_prefix = version.split("-")[0]
                if not version.count(needless_prefix) == 2:
                    version = f"{needless_prefix}-{version}"
        ver_msg += [lib_to_gen_plural(dev_type)]

    if model:
        if "sw" not in group.allowed_types:
            cli.exit(f"[cyan]--model[/] only applies to AOS-SW [cyan]{group.name}[/] AOS-SW is not configured as an allowed device type for this group.")
        elif "sw" not in [d["type"] for d in cli.cache.devices if d["group"] == group.name]:
            cli.exit(f"[cyan]--model[/] only applies to AOS-SW [cyan]{group.name}[/] does not appear to contain any AOS-SW switches.\nIf local cache is stale, run command again with hidden [cyan]-U[/] option to update the cache.")
        ver_msg += [f"model [bright_green]{model}[/]"]

    ver_msg += [f"in group [bright_green]{group.name}[/]"]

    if version:
        _version = [f"to [bright_green]{version}[/]"]
    else:
        _version = ["to [bright_green]Recommended version[/]"]
    ver_msg += _version
    ver_msg = " ".join(ver_msg)

    if reboot:
        ver_msg = f"{ver_msg} and :recycle:  reboot"
    else:
        ver_msg = f"{ver_msg} ('-R' not specified, device will not be rebooted)"

    print(ver_msg)
    if cli.confirm(yes):
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


@app.command()
def swarm(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        help="Upgrade will be performed on the cluster the AP belongs to.",
        autocompletion=cli.cache.dev_ap_completion,
        show_default=False,
    ),
    version: str = cli.arguments.version,
    at: datetime = cli.options.at,
    in_: str = cli.options.in_,
    reboot: bool = typer.Option(True, "--reboot", "-R", help="Automatically reboot device after firmware download", hidden=True),  # allow for consistency, not required or honored as APs always reboot.
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Upgrade [dim italic](or Downgrade)[/] firmware on devices in an IAP cluster
    """
    at = None if not at else round(at.timestamp())
    if in_:
        at = cli.delta_to_start(in_, past=False).int_timestamp

    dev = cli.cache.get_dev_identifier(device, dev_type="ap")
    swarm = dev.swack_id

    if not at:
        conf_msg = f"Upgrad{'e' if not yes else 'ing'} APs in swarm"
    else:
        conf_msg = f"Schedul{'e' if not yes else 'ing'} [cyan]Upgrade[/] @ [italic cornflower_blue]{DateTime(at, 'mdyt')}[/] for APs in swarm"
    if version:
        if "beta" in version:  # beta for APs always looks like this "10.7.1.0-10.7.1.0-beta_91138" we allow simplified 10.7.1.0-beta_91138
            needless_prefix = version.split("-")[0]
            if not version.count(needless_prefix) == 2:
                version = f"{needless_prefix}-{version}"
        conf_msg = f"{conf_msg} to [bright_green]{version}.[/]"
    else:
        conf_msg = f"{conf_msg} to [bright_green]Recommended version[/]"

    conf_msg = f"{conf_msg} :recycle:  [dim red italic]APs will automatically reboot after upgrade[/]."
    print(conf_msg)

    cli.confirm(yes)
    resp = cli.central.request(cli.central.upgrade_firmware, scheduled_at=at, swarm_id=swarm, firmware_version=version)
    cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Upgrade [dim italic](or Downgrade)[/] Firmware
    """
    pass


if __name__ == "__main__":
    app()
