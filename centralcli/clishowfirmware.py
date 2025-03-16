#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
import typer
import sys
from typing import List
from pathlib import Path
from rich import print
from rich.markup import escape


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, log, cleaner, BatchRequest
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, log, cleaner, BatchRequest
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, lib_to_api, DevTypes, FirmwareDeviceType  # noqa
from centralcli.cache import CentralObject

app = typer.Typer()

tty = utils.tty
iden_meta = IdenMetaVars()



class ShowFirmwareKwags(str, Enum):
    group = "group"
    type = "type"

# TODO add support for APs use batch_reqs = [BatchRequest(cli.central.get_swarm_firmware_details, dev.swack_id) for dev in devs]
# has to be done this way as typer does not show help if docstr is an f-string
device_help = f"""Show firmware details for device(s)

    Either provide one or more devices as arguments or [cyan]--dev-type[/]
    [cyan]--dev-type[/] can be one of cx, sw, gw (not supported on APs)
    [italic cyan]cencli show {escape('[all|aps|switches|gateways]')}[/] includes the firmware version as well

    [cyan]cx[/], [cyan]sw[/] and the generic [cyan]switch[/] are allowed for [cyan]--dev-type[/] for consistency with other commands.
    API endpoint treats them all the same and returns all switches.
    """
@app.command(help=device_help)
def device(
    device: List[str] = typer.Argument(None, metavar=iden_meta.dev_many, autocompletion=cli.cache.dev_gw_switch_completion, show_default=False,),
    dev_type: FirmwareDeviceType = typer.Option(None, help="Show firmware by device type", show_default=False,),
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    if device:
        devs = [cli.cache.get_dev_identifier(dev, dev_type=["gw", "switch"], conductor_only=True) for dev in device]
        batch_reqs = [BatchRequest(cli.central.get_device_firmware_details if dev.type != "ap" else cli.central.get_swarm_firmware_details, dev.serial if dev.type != "ap" else dev.swack_id) for dev in devs]
        if dev_type:
            log.warning(
                f'[cyan]--dev-type[/] [bright_green]{dev_type.value}[/] ignored as device{"s" if len(devs) > 1 else ""} [bright_green]{"[/], [bright_green]".join([dev.name for dev in devs])}[/] {"were" if len(devs) > 1 else "was"} specified.',
                caption=True
            )
    elif dev_type:
        batch_reqs = [BatchRequest(cli.central.get_device_firmware_details_by_type, device_type=dev_type.value)]
    else:
        cli.exit("Provide one or more devices as arguments or [cyan]--dev-type[/]")

    batch_resp = cli.central.batch_request(batch_reqs, continue_on_fail=True, retry_failed=True)

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

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    cli.display_results(
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
def swarms(
    device: List[str] = typer.Argument(None, help="Show firmware for the swarm the provided device(s) belongs to", metavar=iden_meta.dev_many, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    group: str = cli.options.group,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show firmware details for swarm by specifying any AP in the swarm

    Multiple devices can be specified.  Output will include details for each unique swarm.
    """
    central = cli.central

    if device:
        devs = [cli.cache.get_dev_identifier(dev, dev_type="ap", conductor_only=True) for dev in device]
        batch_reqs = [BatchRequest(cli.central.get_swarm_firmware_details, dev.swack_id) for dev in devs]
    else:
        if group:
            group: CentralObject = cli.cache.get_group_identifier(group)
            kwargs = {"group": group.name}
        else:
            kwargs = {}

        batch_reqs = [BatchRequest(cli.central.get_all_swarms_firmware_details, **kwargs)]

    batch_resp = central.batch_request(batch_reqs, continue_on_fail=True, retry_failed=True)
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


    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    cli.display_results(
        resp,
        tablefmt=tablefmt,
        title="Firmware Details",
        pager=pager,
        outfile=outfile,
        cleaner=cleaner.get_swarm_firmware_details
    )


@app.command(short_help="Show firmware compliance details")
def compliance(
    device_type: DevTypes = typer.Argument(..., show_default=False,),
    group: List[str] = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion, show_default=False,),
    group_name: str = typer.Option(None, "--group", help="Filter by group", autocompletion=cli.cache.group_completion, show_default=False,),
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Show firmware compliance details for a group/device type
    """
    central = cli.central
    group = group or utils.listify(group_name)
    group = None if not group else group

    if group:
        if len(group) > 2:  # Allows user to add unnecessary "group" keyword before the group
            cli.exit(f"Unknown extra arguments in {[x for x in list(group)[0:-1] if x.lower() != 'group']}")
        group = group[-1]
        group: CentralObject = cli.cache.get_group_identifier(group)

    # TODO make device_type optional add 'all' keyword and implied 'all' if no device_type
    #      add macro method to get compliance for all device_types.
    kwargs = {
        'device_type': device_type,
        'group': None if not group else group.name
    }

    resp = central.request(central.get_firmware_compliance, **kwargs)
    if resp.status == 404 and resp.output.lower() == "not found":
        resp.output = (
            f"Invalid URL or No compliance set for {device_type.lower()} "
            f"{'Globally' if group is None else f'in group {group.name}'}"
        )
        typer.echo(str(resp).replace("404", typer.style("404", fg="red")))
    else:
        tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

        cli.display_results(
            resp,
            tablefmt=tablefmt,
            title=f"{'Global ' if not group else f'{group.name} '}Firmware Compliance",
            pager=pager,
            outfile=outfile
        )

@app.command("list")
def _list(
    device: str = typer.Argument(None, help="Device to get firmware list for", metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    dev_type: DevTypes = typer.Option(None, help="Get firmware list for a device type", show_default=False,),
    swarm: bool = typer.Option(False, "--swarm", "-s", help="Get available firmware for IAP cluster associated with provided device", show_default=False,),
    swarm_id: str = typer.Option(None, help="Get available firmware for specified IAP cluster", show_default=False,),
    verbose: int = cli.options.verbose,
    do_json: bool = cli.options.do_json,
    do_yaml: bool = cli.options.do_yaml,
    do_csv: bool = cli.options.do_csv,
    do_table: bool = cli.options.do_table,
    raw: bool = cli.options.raw,
    outfile: Path = cli.options.outfile,
    pager: bool = cli.options.pager,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
):
    """Show available firmware list for a specific device or a type of device
    """
    caption = None if verbose else "\u2139  Showing a single screens worth of the most recent versions, to see full list use [cyan]-v[/] (verbose)"

    dev: CentralObject = device if not device else cli.cache.get_dev_identifier(device, conductor_only=True,)

    # API-FLAW # HACK API at least for AOS10 APs returns Invalid Value for device <serial>, convert to --dev-type
    if dev and dev.type == "ap":
        if swarm:
            swarm_id = dev.swack_id
        else:
            dev_type = "ap"
        dev = None

    kwargs = {
        "device_type": dev_type,
        "swarm_id": swarm_id,
        "serial": None if dev is None else dev.serial
    }

    kwargs = utils.strip_none(kwargs)

    if not kwargs:
        cli.exit("[bright_red]Missing Argument / Option[/].  One of [cyan]<device(name|serial|mac|ip)>[/] (argument), [cyan]--dev-type <ap|gw|switch>[/], or [cyan]--swarm_id <id>[/] is required.")
    elif len(kwargs) > 1:
        cli.exit("[bright_red]Invalid combination[/] specify only [bold]one[/] of [bright_green]DEVICE[/] (argument), [cyan]--dev-type[/], [bold]OR[/] [cyan]--swarm-id[/].")

    tablefmt = cli.get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_table=do_table)

    title = f"Available firmware versions for {list(kwargs.keys())[0].replace('_', ' ')}: {list(kwargs.values())[0]}"
    if "device_type" in kwargs:
        title = f'{title.split(":")[0]} {dev_type}'
    elif dev:
        title = f'{title.split("serial")[0]} device [cyan]{dev.name}[/]'


    resp = cli.central.request(cli.central.get_firmware_version_list, **kwargs)
    cli.display_results(
        resp,
        tablefmt=tablefmt, title=title, caption=caption, pager=pager, outfile=outfile, set_width_cols={"version": {"min": 25}}, cleaner=cleaner.get_fw_version_list, format=tablefmt, verbose=bool(verbose))


@app.callback()
def callback():
    """
    Show Firmware / compliance details
    """
    pass


if __name__ == "__main__":
    app()
