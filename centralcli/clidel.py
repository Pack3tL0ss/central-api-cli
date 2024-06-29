#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    from centralcli import cli, log, config, utils, Response, BatchRequest, clidelfirmware
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log, config, utils, Response, BatchRequest, clidelfirmware
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars
from centralcli.cache import CentralObject
from centralcli.exceptions import DevException

iden = IdenMetaVars()

app = typer.Typer()
app.add_typer(clidelfirmware.app, name="firmware")


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
    confirm_3 = f'{typer.style("Confirm", fg="cyan")} {typer.style("delete", fg="red")}'
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
    if yes or typer.confirm("Delete Webhook?", abort=True):
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
    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(cli.central.delete_template, template.group, template.name)
        cli.display_results(resp, tablefmt="action")
        # TODO update cache


# TODO return status indicating cache update success/failure
def update_dev_inv_cache(console: Console, batch_resp: List[Response], cache_devs: List[CentralObject], devs_in_monitoring: List[CentralObject], inv_del_serials: List[str], ui_only: bool = False) -> None:
    br = BatchRequest
    all_ok = True if all(r.ok for r in batch_resp) else False
    with console.status(f'Performing {"[bright_green]full[/] " if not all_ok else ""}device cache update...'):
        cache_update_reqs = []
        if cache_devs:
            if all_ok:
                cache_update_reqs += [br(cli.cache.update_dev_db, ([d.data for d in devs_in_monitoring],), remove=True)]
            else:
                cache_update_reqs += [br(cli.cache.update_dev_db)]

    with console.status(f'Performing {"[bright_green]full[/] " if not all_ok else ""}inventory cache update...'):
        if cache_devs or inv_del_serials and not ui_only:
            if all_ok:
                cache_update_reqs += [
                    br(
                        cli.cache.update_inv_db,
                        (list(set([*inv_del_serials, *[d.serial for d in devs_in_monitoring]])),),
                        remove=True
                    )
                ]
            else:
                cache_update_reqs += [br(cli.cache.update_inv_db)]

        # Update cache remove deleted items
        # TODO failure detection
        if cache_update_reqs:
            cache_res = cli.central.batch_request(cache_update_reqs)
            log.debug(f'cache update response: {cache_res}')


# TODO also coppied from clibatch need clishared or put in clicommon
def show_archive_results(res: Response) -> None:

    caption = res.output.get("message")
    action = res.url.name
    if res.get("succeeded_devices"):
        title = f"Devices successfully {action}d."
        data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
        cli.display_results(data=data, title=title, caption=caption)
    if res.get("failed_devices"):
        title = f"Devices that [bright_red]failed[/] to {action}d."
        data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
        cli.display_results(data=data, title=title, caption=caption)


# TODO simplify do not allow batch delete via this command, only via batch delete
@app.command(short_help="Delete devices.")
def device(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion, show_default=False,),
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views.  App assignment and subscriptions remain intact."),
    cop_inv_only: bool = typer.Option(False, "--cop-only", help="Only delete device from CoP inventory.", hidden=True),
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

    # TODO Literally copy/paste from clibatch.py (slightly modified)... maybe move some things to clishared or clicommon
    cache_devs = [cli.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False) for d in devices]
    not_in_inventory = [d for d, c in zip(devices, cache_devs) if c is None]
    cache_devs = [c for c in cache_devs if c]
    serials_in = [d.serial for d in cache_devs]
    inv_del_serials = [s for s in serials_in if s in cli.cache.inventory_by_serial]

    # Devices in monitoring (have a status)
    aps, switches, stacks, gws, _stack_ids = [], [], [], [], []
    # TODO profile these (1 loop vs multiple list comprehensions)
    for dev in cache_devs:
        if not dev.status:
            continue
        elif dev.generic_type == "ap":
            aps += [dev]
        elif dev.generic_type == "gw":
            gws += [dev]
        elif dev.generic_type == "switch":
            if dev.swack_id is None:
                switches += [dev]
            elif dev.swack_id in _stack_ids:
                continue
            else:
                _stack_ids += [dev.swack_id]
                stacks += [dev]
        else:
            raise DevException(f'Unexpected device type {dev.generic_type}')

    # aps = [dev for dev in cache_devs if dev.generic_type == "ap" and dev.status]
    # switches = [dev for dev in cache_devs if dev.generic_type == "switch" and dev.status]  # FIXME Need to use stack_id for stacks
    # gws = [dev for dev in cache_devs if dev.generic_type == "gw" and dev.status]
    devs_in_monitoring = [*aps, *switches, *stacks, *gws]

    # archive / unarchive removes any subscriptions (less calls than determining the subscriptions for each then unsubscribing)
    # It's OK to send both despite unarchive depending on archive completing first, as the first call is always done solo to check if tokens need refreshed.
    arch_reqs = [] if ui_only or not inv_del_serials else [
        br(cli.central.archive_devices, (inv_del_serials,)),
        br(cli.central.unarchive_devices, (inv_del_serials,)),
    ]

    # cop only delete devices from GreenLake inventory
    cop_del_reqs = [] if not inv_del_serials or not config.is_cop else [
        br(cli.central.cop_delete_device_from_inventory, (inv_del_serials,))
    ]

    # build reqs to remove devs from monit views.  Down devs now, Up devs delayed to allow time to disc.
    mon_del_reqs, delayed_mon_del_reqs = [], []
    for dev_type, _devs in zip(["ap", "switch", "stack", "gateway"], [aps, switches, stacks, gws]):
        if _devs:
            down_now =  [d.serial if dev_type != "stack" else d.swack_id for d in _devs if d.status.lower() == "down"]
            up_now =  [d.serial if dev_type != "stack" else d.swack_id for d in _devs if d.status.lower() == "up"]
            if [*down_now, *up_now]:
                func = getattr(cli.central, f"delete_{dev_type}")
                if down_now:
                    mon_del_reqs += [br(func, s) for s in down_now]
                if up_now:
                    delayed_mon_del_reqs += [br(func, s) for s in up_now]

    # warn about devices that were not found
    if not_in_inventory:
        if len(not_in_inventory) == 1:
            console.print(f"\n[dark_orange]Warning[/]: Skipping [cyan]{not_in_inventory[0]}[/] as it was not found in inventory.")
        else:
            console.print("\n[dark_orange]Warning[/]: Skipping the following as they were not found in inventory.")
            _ = [console.print(f"    [cyan]{d}[/]") for d in not_in_inventory]
        print("")

    # None of the provided devices were found in cache or inventory
    if not [*arch_reqs, *mon_del_reqs, *delayed_mon_del_reqs, *cop_del_reqs]:
        print("Everything is as it should be, nothing to do.")
        raise typer.Exit(0)

    # construnct confirmation msg
    _msg = f"[bright_red]Delete[/] {cache_devs[0].summary_text}\n"
    if len(cache_devs) > 1:
        _msg += "\n".join([f"       {d.summary_text}" for d in cache_devs[1:]])

    if ui_only:
        _total_reqs = len(mon_del_reqs)
    elif cop_inv_only:
        _total_reqs = len(cop_del_reqs)
    else:
        _total_reqs = len([*arch_reqs, *cop_del_reqs, *mon_del_reqs, *delayed_mon_del_reqs])

    if ui_only:
        if delayed_mon_del_reqs:
            print(f"{len(delayed_mon_del_reqs)} of the {len(serials_in)} provided are currently online, devices can only be removed from UI if they are offline.")
            delayed_mon_del_reqs = []
        if not mon_del_reqs:
            print("No devices found to remove from UI... Exiting")
            raise typer.Exit(1)
        else:
            _msg += "\n[italic cyan]devices will be removed from UI only, Will appear again once they connect to Central.[/]"

    _msg += f"\n\n[italic dark_olive_green2]Will result in {_total_reqs} additional API Calls."

    # Perfrom initial delete actions (Any devs in inventory and any down devs in monitoring)
    console.print(_msg)
    batch_resp = []
    if yes or typer.confirm("\nProceed?", abort=True):
        if not cop_inv_only:
            batch_resp = cli.central.batch_request([*arch_reqs, *mon_del_reqs])
            if arch_reqs and len(batch_resp) >= 2:
                # if archive requests all pass we summarize the result.
                if all([r.ok for r in batch_resp[0:2]]) and all([not r.get("failed_devices") for r in batch_resp[0:2]]):
                    batch_resp[0].output = batch_resp[0].output.get("message")
                    batch_resp[1].output = f'  {batch_resp[1].output.get("message", "")}\n  Subscriptions successfully removed for {len(batch_resp[1].output.get("succeeded_devices"))} devices.\n  [italic]archive/unarchive flushes all subscriptions for a device.'
                else:
                    show_archive_results(batch_resp[0])  # archive
                    show_archive_results(batch_resp[1])  # unarchive
                    batch_resp = batch_resp[2:]

            if not all([r.ok for r in batch_resp]):  # EARLY EXIT ON FAILURE
                # console.print("[bright_red]A Failure occured aborting remaining actions.[/]")
                log.warning("[bright_red]A Failure occured aborting remaining actions.[/]", caption=True)
                # console.print("[italic]Cache has not been updated, [cyan]cencli show all -v[/ cyan] will result in a full cache update.[/ italic]")
                # log.warning("[italic]Cache has not been updated, [cyan]cencli show all -v[/ cyan] will result in a full cache update.[/ italic]", caption=True)
                update_dev_inv_cache(console, batch_resp=batch_resp, cache_devs=cache_devs, devs_in_monitoring=devs_in_monitoring, inv_del_serials=inv_del_serials, ui_only=ui_only)

                cli.display_results(batch_resp, exit_on_fail=True, caption="A Failure occured, Re-run command to perform remaining actions.", tablefmt="action")

    if not delayed_mon_del_reqs and not cop_del_reqs:
        # if all reqs OK cache is updated by deleting specific items, otherwise it's a full cache refresh
        update_dev_inv_cache(console, batch_resp=batch_resp, cache_devs=cache_devs, devs_in_monitoring=devs_in_monitoring, inv_del_serials=inv_del_serials, ui_only=ui_only)

        cli.display_results(batch_resp, tablefmt="action")
        raise typer.Exit(0)

    elif delayed_mon_del_reqs and not cop_inv_only:
        del_resp = []
        del_reqs_try = delayed_mon_del_reqs.copy()
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
                    print("\n[dark_orange]:warning:[/] Retries exceeded. Devices still remain Up in central and cannot be deleted.  This command can be re-ran once they have disconnected.")
                del_resp += _del_resp
            else:
                del_resp += [r for r in _del_resp if r.ok or isinstance(r.output, dict) and r.output.get("error_code", "") != "0007"]

            del_reqs_try = [del_reqs_try[idx] for idx, r in enumerate(_del_resp) if not r.ok and isinstance(r.output, dict) and r.output.get("error_code", "") == "0007"]
            if del_reqs_try:
                print(f"{len(del_reqs_try)} out of {len([*mon_del_reqs, *delayed_mon_del_reqs])} device{'s are' if len(del_reqs_try) > 1 else ' is'} still [bright_green]Up[/] in Central")
            else:
                break

        batch_resp += del_resp or _del_resp

    # On COP delete devices from GreenLake inventory (only available on CoP)
    # TODO test against a cop system
    # TODO add to cencli delete device ...
    cop_del_resp = []
    if cop_del_reqs:
        cop_del_resp = cli.central.batch_request(cop_del_reqs)
        if not all(r.ok for r in cop_del_resp):
            log.error("[bright_red]Errors occured during CoP GreenLake delete", caption=True)

        #     cli.display_results(cop_del_resp, tablefmt="action")
        # else:
        #     # display results (below) with results of previous calls
        #     batch_resp += cop_del_resp

    # TODO need to update cache after ui-only delete
    # TODO need to improve logic throughout and update inventory cache
    if batch_resp:
        update_dev_inv_cache(console, batch_resp=batch_resp, cache_devs=cache_devs, devs_in_monitoring=devs_in_monitoring, inv_del_serials=inv_del_serials, ui_only=ui_only)

        if cop_del_resp:
            batch_resp += cop_del_resp
    elif cop_inv_only and cop_del_resp:
        batch_resp = cop_del_resp

    if batch_resp:
        cli.display_results(batch_resp, tablefmt="action")



@app.callback()
def callback():
    """
    Delete Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
