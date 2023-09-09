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
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
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
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
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

# TODO simplify do not allow batch delete via this command, only via batch delete
@app.command(short_help="Delete devices.")
def device(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion, show_default=False,),
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views.  App assignment and subscriptions remain intact."),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False, rich_help_panel="Common Options",
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Delete devices.

    Unassigns any subscriptions and removes the devices assignment with the Aruba Central app in GreenLake.
    Which makes it possible to add it to a different GreenLake WorkSpace.

    Devices are also removed from the Central monitoring views/UI (after waiting for them to disconnect).

    Use --ui-only to remove the device from monitoring views/UI only.

    [cyan]cencli unassign license <LICENSE> <DEVICES>[/] can also be used to unassign a specific license
    from a device(s), (device will remain associated with central App in GreenLake).
    """
    # TODO common string helpers
    # TODO update cache earlier as there are early exits... make more elegant

    br = cli.central.BatchRequest
    console = Console(emoji=False)

    cache_devs = [cli.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False) for d in devices]
    not_in_inventory = [d for d, c in zip(devices, cache_devs) if c is None]
    cache_devs = [c for c in cache_devs if c]
    serials_in = [d.serial for d in cache_devs]
    inv_del_serials = [s for s in serials_in if s in cli.cache.inventory_by_serial]

    # Devices in monitoring (have a status)
    aps = [dev for dev in cache_devs if dev.generic_type == "ap" and dev.status]
    switches = [dev for dev in cache_devs if dev.generic_type == "switch" and dev.status]
    gws = [dev for dev in cache_devs if dev.generic_type == "gw" and dev.status]
    devs_in_monitoring = [*aps, *switches, *gws]

    reqs = [] if ui_only or not inv_del_serials else [
        br(cli.central.archive_devices, (inv_del_serials,)),
        br(cli.central.unarchive_devices, (inv_del_serials,)),
    ]

    # deteremine what devices are currently in an Up state, so the request to del from UI can be delayed
    delayed_reqs = []
    for dev_type, _devs in zip(["ap", "switch", "gateway"], [aps, switches, gws]):
        if _devs:
            down_now =  [d.serial for d in _devs if d.status.lower() == "down"]
            up_now =  [d.serial for d in _devs if d.status.lower() == "up"]
            if [*down_now, *up_now]:
                func = getattr(cli.central, f"delete_{dev_type}")
                if down_now:
                    reqs += [br(func, s) for s in down_now]
                if up_now:
                    delayed_reqs += [br(func, s) for s in up_now]

    # warn about devices that were not found
    if not_in_inventory:
        if len(not_in_inventory) == 1:
            console.print(f"\n[dark_orange]Warning[/]: Skipping [cyan]{not_in_inventory[0]}[/] as it was not found in inventory.")
        else:
            console.print(f"\n[dark_orange]Warning[/]: Skipping the following as they were not found in inventory.")
            _ = [console.print(f"    [cyan]{d}[/]") for d in not_in_inventory]
        print("")

    _total_reqs = len(reqs) + len(delayed_reqs) if not ui_only else len(reqs)

    # None of the provided devices were found in cache or inventory
    if not _total_reqs > 0:
        print("Everything is as it should be, nothing to do.")
        raise typer.Exit(0)

    # construnct confirmation msg
    _msg = f"[bright_red]Delete[/] {cache_devs[0].summary_text}\n"  # TODO Verify is it still possible for cache_devs to be empty here?
    if len(cache_devs) > 1:
        _msg += "\n".join([f"       {d.summary_text}" for d in cache_devs[1:]])

    if ui_only:
        if delayed_reqs:
            print(f"{len(delayed_reqs)} of the {len(devices)} provided are currently online, devices can only be removed from UI if they are offline.")
            delayed_reqs = []
        if not reqs:
            print("No devices found to remove from UI... Exiting")
            raise typer.Exit(1)
        else:
            _msg += "\n[italic cyan]devices will be removed from UI only, Will appear again once they connect to Central.[/]"

    _msg += f"\n\n[italic dark_olive_green2]Will result in {_total_reqs} additional API Calls."

    # Perfrom initial delete actions (Any devs in inventory and any down devs in monitoring)
    console.print(_msg)
    if yes or typer.confirm("\nProceed?", abort=True):
        batch_resp = cli.central.batch_request(reqs)
        if not all([r.ok for r in batch_resp]):
            console.print("[bright_red]A Failure occured aborting remaining actions.[/]")
            cli.display_results(batch_resp, exit_on_fail=True, caption="Re-run command to perform remaining actions.")

    if not delayed_reqs:
        # if all reqs OK cache is updated by deleting specific items, otherwise it's a full cache refresh
        all_ok = True if all(r.ok for r in batch_resp) else False

        cache_update_reqs = []
        if cache_devs:
            if all_ok:
                cache_update_reqs += [br(cli.cache.update_dev_db, ([d.data for d in devs_in_monitoring],), remove=True)]
            else:
                cache_update_reqs += [br(cli.cache.update_dev_db)]

        if inv_del_serials:
            if all_ok:
                cache_update_reqs += [br(cli.cache.update_inv_db, (inv_del_serials,), remove=True)]
            else:
                cache_update_reqs += [br(cli.cache.update_inv_db)]

        # Update cache remove deleted items
        if cache_update_reqs:
            batch_res = cli.central.batch_request(cache_update_reqs)

        cli.display_results(batch_resp, tablefmt="action")
        raise typer.Exit(0)

    del_resp = []
    del_reqs_try = delayed_reqs.copy()
    _delay = 10 if not switches else 30  # switches take longer to drop off
    for _try in range(4):
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
            print(f"{len(del_reqs_try)} out of {len(delayed_reqs)} device{'s are' if len(del_reqs_try) > 1 else ' is'} still [bright_green]Up[/] in Central")
        else:
            break

    batch_resp += del_resp or _del_resp

    # FIXME cache update is flawed as this won't hit if there are not any delayed responses
    if batch_resp:
        with console.status("Performing cache updates..."):
            db_updates = []
            if devs_in_monitoring:  # Prepare db updates
                db_updates += [br(cli.cache.update_dev_db, data=[d.serial for d in devs_in_monitoring], remove=True)]
            if inv_del_serials:
                db_updates += [br(cli.cache.update_inv_db, data=inv_del_serials, remove=True)]
            if all([r.ok for r in batch_resp]):
                _ = cli.central.batch_request(db_updates)
            else:
                # if any failed to delete do full update
                # TODO could save 1 API call if we track the index for devices that failed, the reqs list and serial list
                # should match up.
                _ = cli.central.request(cli.cache.update_dev_db)
        cli.display_results(batch_resp, tablefmt="action")



@app.callback()
def callback():
    """
    Delete Aruba Central Objects.
    """
    pass


if __name__ == "__main__":
    app()
