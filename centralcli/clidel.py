#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from pathlib import Path
from time import sleep
from typing import List
import sys
import typer
import asyncio
from rich import print
from rich.console import Console
from rich.progress import track

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, log, config, models, cleaner, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log, config, models, cleaner, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars
from centralcli.cache import CentralObject

iden = IdenMetaVars()

app = typer.Typer()


@app.command(short_help="Delete a certificate")
def certificate(
    name: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("Delete", fg="bright_red")
    confirm_3 = typer.style(f"certificate {name}", fg="cyan")
    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3}"):
        resp = cli.central.request(cli.central.delete_certificate, name)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Delete sites")
def site(
    sites: List[str] = typer.Argument(
        ...,
        help="Site(s) to delete (can provide more than one).",
        autocompletion=cli.cache.site_completion,
    ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    sites = [cli.cache.get_site_identifier(s) for s in sites]

    _del_msg = [
        f"  {typer.style(s.name, fg='reset')}" for s in sites
    ]
    if len(_del_msg) > 7:
        _del_msg = [*_del_msg[0:3], "  ...", *_del_msg[-3:]]
    _del_msg = "\n".join(_del_msg)
    confirm_1 = typer.style("About to", fg="cyan")
    confirm_2 = typer.style("Delete:", fg="bright_red")
    confirm_3 = f'{typer.style(f"Confirm", fg="cyan")} {typer.style(f"delete", fg="red")}'
    confirm_3 = f'{confirm_3} {typer.style(f"{len(sites)} sites?", fg="cyan")}'
    _msg = f"{confirm_1} {confirm_2}\n{_del_msg}\n{confirm_3}"

    if yes or typer.confirm(_msg, abort=True):
        del_list = [s.id for s in sites]
        resp = cli.central.request(cli.central.delete_site, del_list)
        cli.display_results(resp, tablefmt="action")
        if resp:
            cache_del_res = asyncio.run(cli.cache.update_site_db(data=del_list, remove=True))
            if len(cache_del_res) != len(del_list):
                log.warning(
                    f"Attempt to delete entries from Site Cache returned {len(cache_del_res)} "
                    f"but we tried to delete {len(del_list)}",
                    show=True
                )


@app.command(help="Delete a label")
def label(
    label: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    label = cli.cache.get_label_identifier(label)
    _msg = "Deleting" if yes else "Delete"
    print(f"{_msg} label [cyan]{label.name}[/]")
    if yes or typer.confirm("Proceed?"):
        resp = cli.central.request(cli.central.delete_label, label.id)
        cli.display_results(resp, tablefmt="action")
        if resp.ok:
            asyncio.run(cli.cache.update_label_db(label, remove=True))


@app.command(short_help="Delete group(s)")
def group(
    groups: List[str] = typer.Argument(
        ...,
        help="Group to delete (can provide more than one).",
        autocompletion=cli.cache.group_completion
    ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    groups = [cli.cache.get_group_identifier(g) for g in groups]
    reqs = [cli.central.BatchRequest(cli.central.delete_group, (g.name, )) for g in groups]

    _grp_msg = "\n".join([f"  [cyan]{g.name}[/]" for g in groups])
    _grp_msg = _grp_msg.lstrip() if len(groups) == 1 else f"\n{_grp_msg}"
    print(
        f"[bright_red]Delete[/] {'group ' if len(groups) == 1 else 'groups:'}{_grp_msg}"
    )
    if len(reqs) > 1:
        print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")
        if resp:
            upd_res = asyncio.run(cli.cache.update_group_db(data=[{"name": g.name} for g in groups], remove=True))
            log.debug(f"cache update to remove deleted groups returns {upd_res}")


@app.command(short_help="Delete a WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]", autocompletion=cli.cache.group_completion),
    name: str = typer.Argument(..., metavar="[WLAN NAME]", autocompletion=lambda incomplete: tuple(["<WLAN NAME>"])),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    group = cli.cache.get_group_identifier(group)
    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("Delete", fg="bright_red")
    confirm_3 = typer.style(f"Group {group.name}, WLAN {name}", fg="cyan")
    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3}", abort=True):
        resp = cli.central.request(cli.central.delete_wlan, group.name, name)
        cli.display_results(resp, tablefmt="action")


class DelFirmwareArgs(str, Enum):
    compliance = "compliance"


class FirmwareDevType(str, Enum):
    ap = "ap"
    gateway = "gateway"
    switch = "switch"


@app.command(short_help="Delete/Clear firmware compliance")
def firmware(
    what: DelFirmwareArgs = typer.Argument(...),
    device_type: FirmwareDevType = typer.Argument(
        ...,
        metavar=iden.generic_dev_types,
        autocompletion=lambda incomplete: [x for x in ["ap", "gw", "switch"] if x.startswith(incomplete.lower())]
    ),
    _group: List[str] = typer.Argument(None, metavar="[GROUP-NAME]", autocompletion=cli.cache.group_completion),
    group_name: str = typer.Option(None, "--group", help="Filter by group", autocompletion=cli.cache.group_completion),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    _type_to_name = {
        "ap": "IAP",
        "gateway": "CONTROLLER",
        "switch": "HP"
    }
    yes = yes_ if yes_ else yes

    if len(_group) > 2:
        typer.echo(f"Unknown extra arguments in {[x for x in list(_group)[0:-1] if x.lower() != 'group']}")
        raise typer.Exit(1)

    _group = None if not _group else _group[-1]
    group = _group or group_name
    if group:
        group = cli.cache.get_group_identifier(group).name

    kwargs = {
        'device_type': _type_to_name.get(device_type.lower(), device_type),
        'group': group
    }

    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("remove", fg="bright_red")
    confirm_3 = typer.style(f"compliance for {device_type} {'Globally?' if not group else f'in group {group}?'}", fg="cyan")
    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3}", abort=True):
        resp = cli.central.request(cli.central.delete_firmware_compliance, **kwargs)
        if resp.status == 404 and resp.output.lower() == "not found":
            resp.output = (
                f"Invalid URL or No compliance set for {device_type.lower()} "
                f"{'Globally' if not group else f'in group {group}'}"
            )
            typer.echo(str(resp).replace("404", typer.style("404", fg="red")))
        else:
            cli.display_results(resp, tablefmt="action")

# TODO cache webhook name/id so they can be deleted by name
@app.command(help="Delete WebHook")
def webhook(
    id_: str = typer.Argument(...,),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    if yes or typer.confirm(f"Delete Webhook?", abort=True):
        resp = cli.central.request(cli.central.delete_webhook, id_)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Delete a Template")
def template(
    template: str = typer.Argument(..., help="The name of the template", autocompletion=cli.cache.template_completion),
    kw1: str = typer.Argument(None, metavar="[group GROUP]", autocompletion=lambda incomplete: ["group"]),
    val1: str = typer.Argument(None, hidden=True, autocompletion=cli.cache.group_completion),
    _group: str = typer.Option(None),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    group = kw1 if kw1 is None or kw1.lower.strip() != "group" else None
    group = _group or group or val1

    if group is not None:
        group = cli.cache.get_group_identifier(group)
        group = group.name
    template = cli.cache.get_template_identifier(template, group=group)

    print(
        f"{'Delete' if not yes else 'Deleting'} Template [cyan]{template.name}[/] from group [cyan]{template.group}[/]"
    )
    if yes or typer.confirm(f"Proceed?", abort=True):
        resp = cli.central.request(cli.central.delete_template, template.group, template.name)
        cli.display_results(resp, tablefmt="action")
        # TODO update cache


@app.command(short_help="Delete devices.")
def device(
    devices: List[str] = typer.Argument(None, metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    show_example: bool = typer.Option(
        False, "--example",
        help="Show Example import file format.",
        show_default=False,
    ),
    import_file: Path = typer.Option(
        None,
        "--from-file",
        exists=True,
        readable=True,
        help="Provide devices via import file"
    ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False,
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Delete devices.

    This command will unassign any licenses associated to the device, along with reseting any
    group, site, labels.

    Use --retain-group, --retain-site, --retain-labels to skip any of those steps.
    `cencli unassign license <LICENSE> <DEVICES>` can also be used to unassign a specific license
    from a device(s).

    NOTE: The Aruba Central API gateway currently does not have an API endpoint to remove
    the device assignment in GreenLake.
    """
    yes = yes_ if yes_ else yes
    if show_example:
        print("\nAccepts the following keys (include as header row for csv import):")
        print("[cyan]serial[/],[cyan]license[/]")
        print("Where '[cyan]license[/]' (remove only a specified license from device) are optional.")
        print("\n[italic]Note: if license is not specified, any license(s) currently assigned will be unassigned.[/]")
        print("\n[bright_green].csv example[reset]:\n")
        print("serial,license")
        print("CN12345678,foundation_switch_6300")
        print("CN12345679,advanced_ap")
        print("CN12345680,advanced_ap")
        print("\nAny other keys that exist in the file will be ignored")
        print("\n[italic]Note: yaml and json also supported (hint: list of dicts, optionally under a devices key).[/]")
        # print("          [italic]Also supports a simple list of serial numbers with no header 1 per line.[reset]")  # TODO implement this
        # TODO document examples and uncomment below.  provide examples for all format/types
        # print("See https://central-api-cli.readthedocs.io for full examples.")
        return

    # TODO common string helpers
    if  not devices and not import_file:
        print("""
Usage: cencli delete device [OPTIONS] [DEVICES]
Try 'cencli delete device ?' for help.

Error: Invalid combination of arguments / options.
Either provide --import-file <path to file> option or devices argument OR
provide --show_example for example import_file format
        """)
        raise typer.Exit(1)
    if devices and import_file:
        print("""
Usage: cencli delete device [OPTIONS] [DEVICES]
Try 'cencli delete device ?' for help.

Error: Invalid combination of arguments / options.
providing devices on the command line
[bright_red]OR[/] the [cyan]--import-file[/] option
Not both.
        """)
        raise typer.Exit(1)

    br = cli.central.BatchRequest
    console = Console(emoji=False)
    resp = None

    cache_devs = []
    serials_in = []

    if import_file:
        data = config.get_file_data(import_file)
        if hasattr(data, "dict"):  # csv
            data = data.dict
        data = data if "devices" not in data else data["devices"]

        for dev in data:
            if isinstance(dev, dict) and "serial" in dev:
                serials_in += [dev["serial"].upper()]
            else:
                serials_in += [dev.upper()]
        devices = serials_in
        cache_devs = [cli.cache.get_dev_identifier(d, silent=True, include_inventory=True) for d in serials_in]
    else:
        cache_devs = [cli.cache.get_dev_identifier(d, silent=True, include_inventory=True) for d in devices]
        serials_in = [d.serial for d in cache_devs]

    resp = cli.cache.get_devices_with_inventory(no_refresh=False)
    if not resp.ok:
        cli.display_results(resp, stash=False, exit_on_fail=True)
    combined_devs = [CentralObject("dev", data=r) for r in resp.output]

    # validate all serials from import are in inventory and build lic removal list
    _msg = ""
    licenses_to_remove = {}
    for s in serials_in:
        this_services = [i.get("services") for i in combined_devs if i["serial"] == s and i.get("services")]
        for lic in this_services:
            lic = lic.lower().replace(" ", "_")
            licenses_to_remove[lic] = [*licenses_to_remove.get(lic, []), s]

    for lic in licenses_to_remove:
        _msg += f"License [bright_green]{lic}[/bright_green] will be [bright_red]removed[/] from:\n"
        # if len(licenses_to_remove[lic]) > 1:
        for serial in licenses_to_remove[lic]:
            this_inv = [i for i in combined_devs if i.serial == serial]
            if not this_inv:
                print("DEV NOTE: logic error building confirmation msg")
                raise typer.Exit(1)
            this_inv = this_inv[0]
            _msg = f"{_msg}    {this_inv.summary_text}\n"
        # else:
        #     serial = licenses_to_remove[lic][0]
        #     this_inv = [i for i in combined_devs if i.serial == serial]
        #     if not this_inv:
        #         print("DEV NOTE: logic error building confirmation msg")
        #         raise typer.Exit(1)
        #     this_inv = this_inv[0]
        #     _msg = f"{_msg}    {this_inv.summary_text}\n"

    lic_reqs = [br(cli.central.unassign_licenses, serials=serials, services=services) for services, serials in licenses_to_remove.items()]
    inv_cache_delete_serials = [serial for v in licenses_to_remove.values() for serial in v]

    # delete the devices from monitoring app.  They would be in cache
    del_reqs = []
    # devices in inventory have status of None
    aps = [dev for dev in combined_devs if dev.generic_type == "ap" and dev.status and dev.serial in serials_in]
    switches = [dev for dev in combined_devs if dev.generic_type == "switch" and dev.status and dev.serial in serials_in]
    gws = [dev for dev in combined_devs if dev.generic_type == "gw" and dev.status and dev.serial in serials_in]
    dev_cache_delete_serials = [d.serial for d in [*aps, *switches, *gws]]

    _msg_del = ""
    for dev_type, _devs in zip(["ap", "switch", "gateway"], [aps, switches, gws]):
        if _devs:
            func = getattr(cli.central, f"delete_{dev_type}")
            del_reqs += [br(func, d.serial) for d in _devs]
            # func = getattr(cli.central, f"delete_{dev_type}")
            _msg_del += "\n".join([f'    {d.summary_text}' for d in _devs])
            _msg_del += "\n"

    if _msg_del:
        _msg = f"{_msg}The Following devices will be [bright_red]deleted[/] [italic](only applies to devices that have connected)[/]:\n"
        _msg += f"{_msg_del}"
        _msg += f"\n    [italic]**Devices will be deleted from Central Monitoring views."
        _msg += f"\n    [italic]  Unassociating the device with Central in GreenLake currently must be done in GreenLake UI.\n"

    r_cnt = len(lic_reqs) + len(del_reqs)
    if not yes:
        _msg += f"\n[italic dark_olive_green2]{r_cnt}-{r_cnt + 1} additional API calls will be perfomed[/]"

    if r_cnt > 0:
        console.print(_msg)
    else:
        print("Everything is as it should be, nothing to do.")
        raise typer.Exit(0)

    if yes or typer.confirm("\nProceed?", abort=True):
        # unassign license, this causes dev to go down, reqd b4 you can remove from mon app
        lic_resp, del_resp, resp = [], [], []
        if lic_reqs:
            lic_resp += cli.central.batch_request([*lic_reqs])

        resp += lic_resp

        # TODO need loop and retry for devices that take longer to show down in mon
        if (not lic_reqs or all([r.ok for r in lic_resp])) and del_reqs:
            del_reqs_try = del_reqs.copy()
            _delay = 10 if not switches else 30  # switches take longer to drop off
            for _try in range(0,4):
                if lic_reqs or _try > 0:
                    _word = "more " if _try > 0 else ""
                    _prefix = "" if _try == 0 else f"\[Attempt {_try + 1}] "
                    _delay -= (5 * _try) # reduce delay by 5 secs for each request
                    for _ in track(range(_delay), description=f"{_prefix}[green]Allowing {_word}time for devices to disconnect."):
                        sleep(1)

                _del_resp = cli.central.batch_request(del_reqs_try, continue_on_fail=True)
                if _try == 3:
                    if not all([r.ok for r in _del_resp]):
                        print("\n:warning: Retries exceeded. Devices still remain Up in central and cannot be deleted.  This command can be re-ran once they have disconnected.")
                    del_resp += _del_resp
                else:
                    del_resp += [r for r in _del_resp if r.ok or isinstance(r.output, dict) and r.output.get("error_code", "") != "0007"]

                del_reqs_try = [del_reqs_try[idx] for idx, r in enumerate(_del_resp) if not r.ok and isinstance(r.output, dict) and r.output.get("error_code", "") == "0007"]
                if del_reqs_try:
                    print(f"{len(del_reqs_try)} out of {len(del_reqs)} device{'s are' if len(del_reqs_try) > 1 else ' is'} still [bright_green]Up[/] in Central")
                else:
                    break

            resp += del_resp or _del_resp

        if resp:
            with console.status("Performing cache updates..."):
                db_updates = []
                if dev_cache_delete_serials:
                    db_updates += [br(cli.cache.update_dev_db, data=dev_cache_delete_serials, remove=True)]
                # if inv_cache_delete_serials:  # can't remove from inv_db until we have GL API to remove association
                #     db_updates += [br(cli.cache.update_inv_db, data=dev_cache_delete_serials, remove=True)]
                if all([r.ok for r in resp]):
                    _ = cli.central.batch_request(db_updates)
                else:
                    # if any failed to delete do full update
                    # TODO could save 1 API call if we track the index for devices that failed, the reqs list and serial list
                    # should match up.
                    _ = cli.central.request(cli.cache.update_dev_db)
            cli.display_results(resp, tablefmt="action")



@app.callback()
def callback():
    """
    Delete Aruba Central Objects.
    """
    pass


if __name__ == "__main__":
    app()
