#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List, TYPE_CHECKING
import sys
import typer
from rich import print
from rich.console import Console

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, config, Response, BatchRequest, clidelfirmware
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, config, Response, BatchRequest, clidelfirmware
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import iden_meta

from centralcli.cache import CacheSite, CacheLabel, CacheDevice

if TYPE_CHECKING:
    from .cache import CachePortal, CacheGroup, CacheTemplate, CacheGuest

app = typer.Typer()
app.add_typer(clidelfirmware.app, name="firmware")


@app.command(short_help="Delete a certificate")
def certificate(
    name: str = typer.Argument(..., show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    print(f"[bright_red]Delete[/] certificate [cyan]{name}[/]")
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.delete_certificate, name)
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Delete sites")
def site(
    sites: List[str] = typer.Argument(
        ...,
        help="Site(s) to delete (can provide more than one).",
        autocompletion=cli.cache.site_completion,
        show_default=False,
    ),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    sites: List[CacheSite] = [cli.cache.get_site_identifier(s) for s in sites]

    _del_msg = utils.summarize_list([s.summary_text for s in sites], max=7, color=None)
    print(f"[bright_red]Delet{'e' if not yes else 'ing'}[/] {len(sites)} site{'s' if len(sites) > 1 else ''}:\n{_del_msg}")

    if cli.confirm(yes):
        del_list = [s.id for s in sites]
        resp: List[Response] = cli.central.request(cli.central.delete_site, del_list)
        cli.display_results(resp, tablefmt="action")
        if len(sites) == len(resp):  # resp will be a single failed Response if the first one fails, otherwise all should be there.
            cache_del_list = [s.doc_id for r, s in zip(resp, sites) if r.ok]
            cli.central.request(cli.cache.update_site_db, data=cache_del_list, remove=True)


@app.command(name="label")
def label_(
    labels: List[str] = typer.Argument(..., metavar=iden_meta.label_many, autocompletion=cli.cache.label_completion, show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Delete label(s)

    Label can't have any devices associated with it to delete.
    """
    labels: List[CacheLabel] = [cli.cache.get_label_identifier(label) for label in labels]
    cli.batch_delete_labels([label.data for label in labels], yes=yes)


@app.command()
def portal(
    portals: List[str] = typer.Argument(..., metavar=iden_meta.label_many, autocompletion=cli.cache.portal_completion, show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Delete portal(s)

    Delete Guest Portal Profile(s)/Splash Page(s)
    """
    cache_portals: List[CachePortal] = [cli.cache.get_name_id_identifier('portal', portal) for portal in portals]
    reqs = [cli.central.BatchRequest(cli.central.delete_portal_profile, p.id) for p in cache_portals]

    portal_names = utils.summarize_list([p.name for p in cache_portals])
    if len(portals) == 1:
        cli.econsole.print(f'[red]Deleting[/] portal profile: {portal_names.strip()}.')
    else:
        cli.econsole.print(f'[red]Deleting[/] {len(cache_portals)} portal profiles:\n{portal_names}')

    if cli.confirm(yes):
        batch_resp = cli.central.batch_request(reqs)
        cli.display_results(batch_resp, tablefmt="action")
        if len(batch_resp) == len(cache_portals):
            doc_ids = [portal.doc_id for portal, resp in zip(cache_portals, batch_resp) if resp.ok]
            cli.central.request(cli.cache.update_portal_db, doc_ids, remove=True)



@app.command(short_help="Delete group(s)")
def group(
    groups: List[str] = typer.Argument(
        ...,
        help="Group to delete (can provide more than one).",
        autocompletion=cli.cache.group_completion,
        show_default=False,
    ),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    groups = [cli.cache.get_group_identifier(g) for g in groups]
    reqs = [cli.central.BatchRequest(cli.central.delete_group, g.name) for g in groups]

    _grp_msg = "\n".join([f"  [cyan]{g.name}[/]" for g in groups])
    _grp_msg = _grp_msg.lstrip() if len(groups) == 1 else f"\n{_grp_msg}"
    print(
        f"[bright_red]Delete[/] {'group ' if len(groups) == 1 else 'groups:'}{_grp_msg}"
    )
    if len(reqs) > 1:
        print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

    if cli.confirm(yes):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action")
        if resp:
            doc_ids = [g.doc_id for g, r in zip(groups, resp) if r.ok]
            cli.central.request(cli.cache.update_group_db, data=doc_ids, remove=True)


@app.command(short_help="Delete a WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]", autocompletion=cli.cache.group_completion),
    name: str = typer.Argument(..., metavar="[WLAN NAME]", autocompletion=lambda incomplete: tuple(["<WLAN NAME>"])),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    group = cli.cache.get_group_identifier(group)
    print(f"[bright_red]Delet{'e' if not yes else 'ing'}[/] SSID [cyan]{name}[/] configured in group [cyan]{group.name}[/]")
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.delete_wlan, group.name, name)
        cli.display_results(resp, tablefmt="action")


# TODO cache webhook name/id so they can be deleted by name
@app.command()
def webhook(
    wid: str = typer.Argument(..., help="Use [cyan]cencli show webhooks[/] to get the webhook id ([bright_green]wid[/])", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Delete Webhook

    This command requires the webhook id, which is not cached.
    Use [cyan]cencli show webhooks[/] to get the webhook id ([bright_green]wid[/]).
    """
    cli.econsole.print(f"\u26a0  Delet{'e' if not yes else 'ing'} Webhook {wid}", emoji=False)
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.delete_webhook, wid)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Delete a Template", no_args_is_help=True)
def template(
    template: str = typer.Argument(..., metavar=iden_meta.template, help="The name of the template", autocompletion=cli.cache.template_completion, show_default=False,),
    group: List[str] = typer.Argument(None, metavar=iden_meta.group, autocompletion=cli.cache.group_completion, show_default=False),
    _group: str = typer.Option(None, "--group", metavar=iden_meta.group, autocompletion=cli.cache.group_completion, show_default=False),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    # allow unnecessary keyword group "cencli delete template NAME group GROUP"
    if group:
        group = [g for g in group if g != "group"]
        group = None if not group else group[0]
    group = _group or group

    if group is not None:
        group: CacheGroup = cli.cache.get_group_identifier(group)
        group = group.name

    template: CacheTemplate = cli.cache.get_template_identifier(template, group=group)

    print(
        f"[bright_red]{'Delete' if not yes else 'Deleting'}[/] Template [cyan]{template.name}[/] from group [cyan]{template.group}[/]"
    )
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.delete_template, template.group, template.name)
        cli.display_results(resp, tablefmt="action", exit_on_fail=True)
        _ = cli.central.request(cli.cache.update_template_db, doc_ids=template.doc_id)


# TODO return status indicating cache update success/failure
def update_dev_inv_cache(console: Console, batch_resp: List[Response], cache_devs: List[CacheDevice], devs_in_monitoring: List[CacheDevice], inv_del_serials: List[str], ui_only: bool = False) -> None:
    br = BatchRequest
    all_ok = True if all(r.ok for r in batch_resp) else False
    inventory_devs = [d for d in cache_devs if d.db.name == "inventory"]
    cache_update_reqs = []
    with console.status(f'Performing {"[bright_green]full[/] " if not all_ok else ""}device cache update...'):
        if cache_devs:
            if all_ok:
                cache_update_reqs += [br(cli.cache.update_dev_db, [d.doc_id for d in devs_in_monitoring], remove=True)]
            else:
                cache_update_reqs += [br(cli.cache.refresh_dev_db)]

    with console.status(f'Performing {"[bright_green]full[/] " if not all_ok else ""}inventory cache update...'):
        if inventory_devs and not ui_only:
            if all_ok:
                cache_update_reqs += [
                    br(
                        cli.cache.update_inv_db,
                        [d.doc_id for d in inventory_devs],
                        remove=True
                    )
                ]
            else:
                cache_update_reqs += [br(cli.cache.refresh_inv_db)]

        # Update cache remove deleted items by doc_id
        if cache_update_reqs:
            _ = cli.central.batch_request(cache_update_reqs)


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
    devices: List[str] = cli.arguments.devices,
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views.  App assignment and subscriptions remain intact."),
    cop_inv_only: bool = typer.Option(False, "--cop-only", help="Only delete device from CoP inventory.", hidden=not config.is_cop,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Delete device(s).

    Unassigns any subscriptions and removes the devices assignment with the Aruba Central app in GreenLake.
    Which makes it possible to add it to a different GreenLake WorkSpace.

    Devices are also removed from the Central monitoring views/UI (after waiting for them to disconnect).

    Use --ui-only to remove the device from monitoring views/UI only.

    [cyan]cencli unassign license <LICENSE> <DEVICES>[/] can also be used to unassign a specific license
    from a device(s), (device will remain associated with central App in GreenLake).
    """
    # The provided input does not have to be the serial number batch_del_devices will use get_dev_identifier to look the dev
    # up.  It just validates the import has the `serial` field.
    data = [{"serial": d} for d in devices]
    cli.batch_delete_devices(data, ui_only=ui_only, cop_inv_only=cop_inv_only, yes=yes)


@app.command()
def guest(
    portal: str = typer.Argument(..., metavar=iden_meta.portal, autocompletion=cli.cache.portal_completion, show_default=False,),
    guest: str = typer.Argument(..., metavar=iden_meta.guest, autocompletion=cli.cache.guest_completion, show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Add a guest user to a configured portal"""
    portal: CachePortal = cli.cache.get_name_id_identifier("portal", portal)
    guest: CacheGuest = cli.cache.get_guest_identifier(guest, portal_id=portal.id)

    _msg = f"[red]:warning:  Delet{'e' if not yes else 'ing'}[/] Guest: [cyan]{guest.name}[/] from portal: [cyan]{portal.name}[/]"
    print(_msg)
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.delete_guest, portal_id=portal.id, guest_id=guest.id)
        cli.display_results(resp, tablefmt="action", exit_on_fail=True)  # exits here if call failed
        _ = cli.central.request(cli.cache.update_guest_db, guest.doc_id, remove=True)



@app.callback()
def callback():
    """
    Delete Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
