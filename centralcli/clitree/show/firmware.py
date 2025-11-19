#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List

import typer
from rich.markup import escape

from centralcli import cleaner, common, log, render, utils
from centralcli.cache import CacheDevice, CacheGroup, CentralObject, api
from centralcli.client import BatchRequest
from centralcli.constants import DevTypes, FirmwareDeviceType, iden_meta

app = typer.Typer()


# TODO add support for APs use batch_reqs = [BatchRequest(api.firmware.get_swarm_firmware_details, dev.swack_id) for dev in devs]
# has to be done this way as typer does not show help if docstr is an f-string
device_help = f"""Show firmware details for device(s)

    Either provide one or more devices as arguments or [cyan]--dev-type[/]
    [cyan]--dev-type[/] can be one of cx, sw, gw, ap
    [italic cyan]cencli show {escape('[all|aps|switches|gateways]')}[/] includes the firmware version as well

    [cyan]cx[/], [cyan]sw[/] and the generic [cyan]switch[/] are allowed for [cyan]--dev-type[/] for consistency with other commands.
    API endpoint treats them all the same and returns all switches.

    :warning:  The APIs used by this command seem to no longer work for Gateways.
    """
@app.command(help=device_help)
def device(
    device: List[str] = typer.Argument(None, metavar=iden_meta.dev_many, autocompletion=common.cache.dev_completion, show_default=False,),
    dev_type: FirmwareDeviceType = typer.Option(None, help="Show firmware by device type", show_default=False,),
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    if device:
        devs = [common.cache.get_dev_identifier(dev, dev_type=["gw", "switch", "ap"], swack=True) for dev in device]
        batch_reqs = [BatchRequest(api.firmware.get_device_firmware_details if dev.type != "ap" else api.firmware.get_swarm_firmware_details, dev.serial if dev.type != "ap" else dev.swack_id) for dev in devs]
        if dev_type:
            log.warning(
                f'[cyan]--dev-type[/] [bright_green]{dev_type.value}[/] ignored as device{"s" if len(devs) > 1 else ""} [bright_green]{"[/], [bright_green]".join([dev.name for dev in devs])}[/] {"were" if len(devs) > 1 else "was"} specified.',
                caption=True
            )
    elif dev_type:
        if dev_type != "ap":
            batch_reqs = [BatchRequest(api.firmware.get_device_firmware_details_by_type, device_type=dev_type.value)]
        else:
            batch_reqs = [BatchRequest(api.firmware.get_all_swarms_firmware_details,)]
    else:
        common.exit("Provide one or more devices as arguments or [cyan]--dev-type[/]")

    batch_resp = api.session.batch_request(batch_reqs, continue_on_fail=True, retry_failed=True)

    resp = batch_resp
    if len(batch_resp) > 1:
        failed = [r for r in batch_resp if not r.ok]
        passed = [r for r in batch_resp if r.ok]

        if passed:  # combine outputs for multiple calls into a single table/resp
            rl = min([r.rl for r in passed])
            resp = passed[-1]
            resp.rl = rl
            resp.output = [r.output for r in passed]
            if failed:
                _ = [log.warning(f'Partial Failure {r.url.path} | {r.status} | {r.error}', caption=True) for r in failed]

    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title="Firmware Details",
        pager=pager,
        outfile=outfile,
        cleaner=cleaner.get_device_firmware_details
    )

swarms_help = f"""Show firmware details for swarms

    [italic cyan]cencli show {escape('[all|aps|switches|gateways]')}[/] includes the firmware version as well
    """
@app.command()
def swarm(
    device: List[str] = typer.Argument(None, help="Show firmware for the swarm(s) the provided device(s) belongs to", metavar=iden_meta.dev_many, autocompletion=common.cache.dev_ap_completion, show_default=False,),
    group: str = common.options.group,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Show firmware details for swarm(s) by specifying any AP in the swarm

    Multiple devices can be specified.  Output will include details for each unique swarm.
    """
    title = "Firmware Details"
    if device:
        devs: list[CacheDevice] = [common.cache.get_dev_identifier(dev, dev_type="ap", swack=True) for dev in device]
        batch_reqs = [BatchRequest(api.firmware.get_swarm_firmware_details, dev.swack_id) for dev in devs]
        if len(devs) == 1:
            title = f"{title} for swarm with id {devs[0].swack_id}"
    else:
        kwargs = {}
        if group:
            group: CacheGroup = common.cache.get_group_identifier(group)
            kwargs = {"group": group.name}

        batch_reqs = [BatchRequest(api.firmware.get_all_swarms_firmware_details, **kwargs)]

    batch_resp = api.session.batch_request(batch_reqs, continue_on_fail=True, retry_failed=True)
    failed = [r for r in batch_resp if not r.ok]
    passed = [r for r in batch_resp if r.ok]

    if passed:  # combine outputs for multiple calls into a single table/resp
        if len(passed) > 1:
            rl = min([r.rl for r in passed])
            resp = passed[-1]
            resp.rl = rl
            resp.output = [r.output for r in passed]
        else:
            resp = passed[0]

        if failed:
            _ = [log.warning(f'Partial Failure {r.url.path} | {r.status} | {r.error}', caption=True) for r in failed]
    else:  # all failed
        resp = batch_resp


    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        pager=pager,
        exit_on_fail=True,
        outfile=outfile,
        fold_cols="swarm id",
        cleaner=cleaner.get_swarm_firmware_details
    )


@app.command()
def compliance(
    device_type: DevTypes = common.arguments.device_type,
    group: List[str] = common.arguments.get("group", default=None, help=f"Show compliance for group {common.help_block('Global Compliance')}"),
    group_: str = common.options.get("group", "--group", "-G", help=f"Show compliance for group {common.help_block('Global Compliance')}"),
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Show firmware compliance details for a group/device type."""
    group = group or utils.listify(group_)
    group = None if not group else [g for g in group if g.lower() != "group"]  # Allows user to add unnecessary "group" keyword before the group

    if group:
        if len(group) > 1:
            common.exit(f"Unknown extra arguments: {group[-1]}.  Only 1 group is allowed.")
        group = group[-1]
        group: CentralObject = common.cache.get_group_identifier(group)

    # TODO make device_type optional add 'all' keyword and implied 'all' if no device_type
    #      add macro method to get compliance for all device_types.
    kwargs = {
        'device_type': device_type,
        'group': None if not group else group.name
    }

    resp = api.session.request(api.firmware.get_firmware_compliance, **kwargs)
    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)
    if resp.status == 404:
        resp.output = (
            f"Invalid URL or No compliance set for {device_type.lower()} "
            f"{'Globally' if group is None else f'in group {group.name}'}"
        )

    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=f"{'Global ' if not group else f'{group.name} '}Firmware Compliance",
        pager=pager,
        outfile=outfile,
        exit_on_fail=False
    )
    common.exit(code=0 if any([resp.ok, resp.status == 404]) else 1)

@app.command("list")
def _list(
    device: str = typer.Argument(None, help="Device to get firmware list for", metavar=iden_meta.dev, autocompletion=common.cache.dev_completion, show_default=False,),
    dev_type: DevTypes = typer.Option(None, help="Get firmware list for a device type", show_default=False,),
    swarm: bool = common.options.get("swarm", help="Get available firmware for IAP cluster associated with provided device"),
    swarm_id: str = typer.Option(None, help="Get available firmware for specified IAP cluster", show_default=False,),
    verbose: int = common.options.verbose,
    do_json: bool = common.options.do_json,
    do_yaml: bool = common.options.do_yaml,
    do_csv: bool = common.options.do_csv,
    do_table: bool = common.options.do_table,
    raw: bool = common.options.raw,
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
):
    """Show available firmware list for a specific device or a type of device."""
    dev: CacheDevice = device if not device else common.cache.get_dev_identifier(device, swack=True,)

    # API-FLAW # HACK API at least for AOS10 APs returns Invalid Value for device <serial>, convert to --dev-type
    if dev is not None and dev.type == "ap":
        if swarm:
            swarm_id = dev.swack_id
        else:
            dev_type = DevTypes.ap
        dev = None
    elif dev is not None and dev.type == "gw":  # Endpoint now returns "API does not support cluster gateway" so we just use the dev.type.
        dev_type = DevTypes.gw
        dev = None

    kwargs = {
        "device_type": dev_type,
        "swarm_id": swarm_id,
        "serial": None if dev is None else dev.serial
    }

    kwargs = utils.strip_none(kwargs)

    if not kwargs:
        common.exit("[bright_red]Missing Argument / Option[/].  One of [cyan]<device(name|serial|mac|ip)>[/] (argument), [cyan]--dev-type <ap|gw|switch>[/], or [cyan]--swarm_id <id>[/] is required.")
    elif len(kwargs) > 1:
        common.exit("[bright_red]Invalid combination[/] specify only [bold]one[/] of [bright_green]DEVICE[/] (argument), [cyan]--dev-type[/], [bold]OR[/] [cyan]--swarm-id[/].")

    tablefmt = common.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    title = f"Available firmware versions for {list(kwargs.keys())[0].replace('_', ' ')}: {list(kwargs.values())[0]}"
    if "device_type" in kwargs:
        title = f'{title.split(":")[0]} {dev_type.value}'
    elif dev:
        title = f'{title.split("serial")[0]} device [cyan]{dev.name}[/]'


    resp = api.session.request(api.firmware.get_firmware_version_list, **kwargs)
    caption = None if not resp.ok or verbose or len(resp.output) + 7 <= render.console.height else "\u2139  Showing a single screens worth of the most recent versions, to see full list use [cyan]-v[/] (verbose)"
    render.display_results(
        resp,
        tablefmt=tablefmt,
        title=title,
        caption=caption,
        pager=pager,
        outfile=outfile,
        set_width_cols={"version": {"min": 25}},
        cleaner=cleaner.get_fw_version_list,
        format=tablefmt,
        verbose=bool(verbose)
    )


@app.callback()
def callback():
    """
    Show Firmware / compliance details
    """
    pass


if __name__ == "__main__":
    app()
