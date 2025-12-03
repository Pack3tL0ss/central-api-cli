#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import typer
from rich.markup import escape

from centralcli import common, render, utils
from centralcli.cache import api
from centralcli.client import BatchRequest
from centralcli.constants import AllDevTypes, iden_meta, lib_to_gen_plural  # noqa
from centralcli.objects import DateTime

if TYPE_CHECKING:
    from centralcli.cache import CacheGroup

app = typer.Typer()


@app.command()
def device(
    devices: list[str] = common.arguments.get("devices", default=None),
    version: str = common.arguments.version,
    at: datetime = common.options.at,
    in_: str = common.options.in_,
    reboot: bool = common.options.reboot,
    yes: int = typer.Option(0, "-Y", "-y", "--yes", count=True, help="Bypass confirmation prompts [cyan]use '-yy'[/] to bypass all prompts (perform cache update if swarm_id is not populated yet for AP)", show_default=False),
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Upgrade [dim italic](or Downgrade)[/] firmware on device(s).
    """
    if version and not devices:  # If only 1 device and no version is provided typer puts the value in version not devices
        devices = [version]
        version = None
    elif not version and not devices:  # TODO find if way to call help text
        common.exit(
            "Missing required Argument [cyan]devices[/] (multiple allowed)\n\n"
            "[yellow]Usage:[/] cencli upgrade device [OPTIONS]  DEVICE... [italic](multiple allowed)[/] [VERSION]\n"
            "Try [cyan]cencli upgrade device ?[/] for help."
        )

    devs = [common.cache.get_dev_identifier(dev, swack=True) for dev in devices]
    dev_types = list(set([dev.type for dev in devs]))
    if len(set([t if t not in ["ap", "gw"] else "apgw" for t in dev_types])) > 1:  # ap and gw can be upgraded together
        common.exit(f"Specifying multiple devices of different types ({utils.summarize_list(dev_types, pad=0, sep=', ')}) does not make sense (other than APs and GWs).  All devices should be compatible with the same software/version.")

    batch_reqs = []
    ap_version = None
    for dev in devs:
        if dev.generic_type == "ap":
            ap_version = version
            if version and "beta" in version:  # beta for APs always looks like this "10.7.1.0-10.7.1.0-beta_91138"
                needless_prefix = version.split("-")[0]
                if not version.count(needless_prefix) == 2:
                    ap_version = f"{needless_prefix}-{version}"
            if not dev.swack_id:  # pragma: no cover
                render.econsole.print(f"\n[cyan]{dev.name}[/] lacks a swarm_id, may not be populated yet if it was recently added.")
                if yes > 1 or render.confirm(prompt="\nRefresh cache now to check if it's populated?"):
                    api.session.request(common.cache.refresh_dev_db, dev_type="ap")
                    dev = common.cache.get_dev_identifier(dev.serial, dev_type="ap")
                if not dev.swack_id:
                    common.exit(f"Unable to perform Upgrade on {dev.summary_text}.  [cyan]swarm_id[/] is required for APs and the API is not returning a value for it yet.")
            batch_reqs += [BatchRequest(api.firmware.upgrade_firmware, scheduled_at=at, swarm_id=dev.swack_id, firmware_version=ap_version)]
        else:
            batch_reqs += [BatchRequest(api.firmware.upgrade_firmware, scheduled_at=at, serial=dev.serial, firmware_version=version, reboot=reboot, forced=None if not dev.type == "gw" else True)]

    at = None if not at else round(at.timestamp())
    if in_:
        at = common.delta_to_start(in_, past=False).int_timestamp

    ver_msg = f"Upgrad{'ing' if yes else 'e'}"
    ver_msg = f"{ver_msg} [cyan]{dev.name}[/]" if len(devs) == 1 else f"{ver_msg} the following devices"
    ver_msg = f"{ver_msg} to the recommended version" if not version else f"{ver_msg} to [green3]{version}[/]"
    if at:
        dt = DateTime(at)
        ver_msg = f'{ver_msg} [italic]at {dt}[/]'

    if len(dev_types) > 1 and not reboot:  # This can only happen with ap and gw in the list of devices
        ver_msg = f"{ver_msg}.  :recycle:  APs will reboot [dim italic]always the case for APs[/] Gateways will not as '-R' not specified. [italic bright_red]Gateways will not be rebooted[/]!!"
    else:
        ver_msg = f"{ver_msg} and :recycle:  reboot" if reboot or "ap" in dev_types else f"{ver_msg} ('-R' not specified, [italic bright_red]device will not be rebooted[/])"

    render.econsole.print(ver_msg)
    if len(devs) > 1:
        render.econsole.print(utils.summarize_list([dev.rich_help_text for dev in devs], max=9, color=None).removeprefix("\n"), emoji=False)
    render.confirm(yes)  # aborts here if they don't confirm
    batch_resp = api.session.batch_request(batch_reqs)

    render.display_results(batch_resp, tablefmt="action")


@app.command()
def group(
    group: str = common.arguments.get("group", help="Upgrade devices by group",),
    version: str = common.arguments.version,
    dev_type: AllDevTypes = typer.Option(..., help="Upgrade a specific device type", show_default=False,),
    at: datetime = common.options.at,
    in_: str = common.options.in_,
    model: str = typer.Option(None, help=f"Upgrade a specific switch model [dim]{escape('[applies to AOS-SW switches only]')}[/]", show_default=False,),
    reboot: bool = common.options.reboot,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Upgrade [dim italic](or Downgrade)[/] firmware on devices by group

    Device type must be provided.  For AOS-SW switches you can filter to a specific model via the --model flag.
    """
    group: CacheGroup = common.cache.get_group_identifier(group)
    at = None if not at else round(at.timestamp())
    if in_:
        at = common.delta_to_start(in_, past=False).int_timestamp

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
            common.exit(f"[cyan]--model[/] only applies to AOS-SW [cyan]{group.name}[/] AOS-SW is not configured as an allowed device type for this group.")
        elif "sw" not in [d["type"] for d in common.cache.devices if d["group"] == group.name]:
            common.exit(
                f"[cyan]--model[/] only applies to AOS-SW [cyan]{group.name}[/] does not appear to contain any AOS-SW switches.\n"
                "If local cache is stale, Use [cyan]cencli refresh cache[/] to perform a full cache update."
            )
        ver_msg += [f"model [bright_green]{model}[/]"]

    ver_msg += [f"in group [bright_green]{group.name}[/]"]

    if version:
        _version = [f"to [bright_green]{version}[/]"]
    else:
        _version = ["to [bright_green]Recommended version[/]"]
    ver_msg += _version
    ver_msg = " ".join(ver_msg)

    ver_msg = f"{ver_msg} and :recycle:  reboot" if reboot else f"{ver_msg} ('-R' not specified, device will not be rebooted)"

    render.econsole.print(ver_msg)
    if render.confirm(yes):
        resp = api.session.request(
            api.firmware.upgrade_firmware,
            scheduled_at=at,
            group=group.name,
            device_type=dev_type,
            firmware_version=version,
            model=model,
            reboot=reboot
        )
        render.display_results(resp, tablefmt="action")


@app.command()
def swarm(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        help="Upgrade will be performed on the cluster the AP belongs to.",
        autocompletion=common.cache.dev_ap_completion,
        show_default=False,
    ),
    version: str = common.arguments.version,
    at: datetime = common.options.at,
    in_: str = common.options.in_,
    reboot: bool = typer.Option(True, "--reboot", "-R", help="Automatically reboot device after firmware download", hidden=True),  # allow for consistency, not required or honored as APs always reboot.
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Upgrade [dim italic](or Downgrade)[/] firmware on devices in an IAP cluster
    """
    at = None if not at else round(at.timestamp())
    if in_:
        at = common.delta_to_start(in_, past=False).int_timestamp

    dev = common.cache.get_dev_identifier(device, dev_type="ap", swack_only=True)
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

    render.econsole.print(conf_msg)
    render.confirm(yes)
    resp = api.session.request(api.firmware.upgrade_firmware, scheduled_at=at, swarm_id=swarm, firmware_version=version)
    render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Upgrade [dim italic](or Downgrade)[/] Firmware
    """
    pass


if __name__ == "__main__":
    app()
