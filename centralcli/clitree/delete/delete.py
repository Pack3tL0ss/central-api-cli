#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, List

import typer
from rich import print

from centralcli import common, config, render, utils
from centralcli.cache import CacheCert, CacheLabel, CacheSite, api
from centralcli.client import BatchRequest
from centralcli.constants import iden_meta
from centralcli.response import Response

from . import firmware

if TYPE_CHECKING:
    from centralcli.cache import CacheGroup, CacheGuest, CachePortal, CacheTemplate


app = typer.Typer()
app.add_typer(firmware.app, name="firmware")


@app.command()
def cert(
    name: str = typer.Argument(..., autocompletion=common.cache.cert_completion, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete a certificate."""
    cert: CacheCert = common.cache.get_cert_identifier(name)
    render.econsole.print(f"[bright_red]Delet{'e' if not yes else 'ing'}[/] certificate [cyan]{cert.name}[/]")

    render.confirm(yes)
    resp = api.session.request(api.configuration.delete_certificate, cert.name)
    render.display_results(resp, tablefmt="action", exit_on_fail=True)
    api.session.request(common.cache.update_cert_db, cert.doc_id, remove=True)


@app.command(short_help="Delete sites")
def site(
    sites: List[str] = typer.Argument(
        ...,
        help="Site(s) to delete (can provide more than one).",
        autocompletion=common.cache.site_completion,
        show_default=False,
    ),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    sites: List[CacheSite] = [common.cache.get_site_identifier(s) for s in sites]

    _del_msg = utils.summarize_list([s.summary_text for s in sites], max=7, color=None)
    render.econsole.print(f"[bright_red]Delet{'e' if not yes else 'ing'}[/] {len(sites)} site{'s' if len(sites) > 1 else ''}:\n{_del_msg}")

    if render.confirm(yes):
        del_list = [s.id for s in sites]
        resp: List[Response] = api.session.request(api.central.delete_site, del_list)
        render.display_results(resp, tablefmt="action")
        if len(sites) == len(resp):  # resp will be a single failed Response if the first one fails, otherwise all should be there.
            cache_del_list = [s.doc_id for r, s in zip(resp, sites) if r.ok]
            api.session.request(common.cache.update_site_db, data=cache_del_list, remove=True)


@app.command(name="label")
def label_(
    labels: List[str] = typer.Argument(..., metavar=iden_meta.label_many, autocompletion=common.cache.label_completion, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete label(s)

    Label can't have any devices associated with it to delete.
    """
    labels: List[CacheLabel] = [common.cache.get_label_identifier(label) for label in labels]
    common.batch_delete_labels([label.data for label in labels], yes=yes)


@app.command()
def portal(
    portals: List[str] = typer.Argument(..., metavar=iden_meta.label_many, autocompletion=common.cache.portal_completion, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete portal(s)

    Delete Guest Portal Profile(s)/Splash Page(s)
    """
    cache_portals: List[CachePortal] = [common.cache.get_name_id_identifier('portal', portal) for portal in portals]
    reqs = [BatchRequest(api.guest.delete_portal_profile, p.id) for p in cache_portals]

    portal_names = utils.summarize_list([p.name for p in cache_portals])
    if len(portals) == 1:
        render.econsole.print(f'[red]Deleting[/] portal profile: {portal_names.strip()}.')
    else:
        render.econsole.print(f'[red]Deleting[/] {len(cache_portals)} portal profiles:\n{portal_names}')

    if render.confirm(yes):
        batch_resp = api.session.batch_request(reqs)
        render.display_results(batch_resp, tablefmt="action")
        if len(batch_resp) == len(cache_portals):
            doc_ids = [portal.doc_id for portal, resp in zip(cache_portals, batch_resp) if resp.ok]
            api.session.request(common.cache.update_portal_db, doc_ids, remove=True)



@app.command()
def group(
    groups: List[str] = typer.Argument(
        ...,
        help="Group to delete (can provide more than one).",
        autocompletion=common.cache.group_completion,
        show_default=False,
    ),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete group(s)"""
    groups: list[CacheGroup] = [common.cache.get_group_identifier(g) for g in groups]
    reqs = [BatchRequest(api.configuration.delete_group, g.name) for g in groups]

    _grp_msg = "\n".join([f"  [cyan]{g.name}[/]" for g in groups])
    _grp_msg = _grp_msg.lstrip() if len(groups) == 1 else f"\n{_grp_msg}"
    print(
        f"[bright_red]Delete[/] {'group ' if len(groups) == 1 else 'groups:'}{_grp_msg}"
    )
    if len(reqs) > 1:  # TODO common function in clicommon or utils
        print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

    if render.confirm(yes):
        resp = api.session.batch_request(reqs)
        render.display_results(resp, tablefmt="action")
        if resp:
            doc_ids = [g.doc_id for g, r in zip(groups, resp) if r.ok]
            api.session.request(common.cache.update_group_db, data=doc_ids, remove=True)


@app.command(short_help="Delete a WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]", autocompletion=common.cache.group_completion),
    name: str = typer.Argument(..., metavar="[WLAN NAME]", autocompletion=lambda incomplete: tuple(["<WLAN NAME>"])),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    group: CacheGroup = common.cache.get_group_identifier(group)
    print(f"[bright_red]Delet{'e' if not yes else 'ing'}[/] SSID [cyan]{name}[/] configured in group [cyan]{group.name}[/]")
    if render.confirm(yes):
        resp = api.session.request(api.configuration.delete_wlan, group.name, name)
        render.display_results(resp, tablefmt="action")


# CACHE cache webhook name/id so they can be deleted by name
@app.command()
def webhook(
    wid: str = typer.Argument(..., help="Use [cyan]cencli show webhooks[/] to get the webhook id ([bright_green]wid[/])", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete Webhook

    This command requires the webhook id, which is not cached.
    Use [cyan]cencli show webhooks[/] to get the webhook id ([bright_green]wid[/]).
    """
    render.econsole.print(f"\u26a0  Delet{'e' if not yes else 'ing'} Webhook {wid}", emoji=False)
    if render.confirm(yes):
        resp = api.session.request(api.central.delete_webhook, wid)
        render.display_results(resp, tablefmt="action")


@app.command(no_args_is_help=True)
def template(
    template: str = typer.Argument(..., metavar=iden_meta.template, help="The name of the template", autocompletion=common.cache.template_completion, show_default=False,),
    group: List[str] = typer.Argument(None, metavar=iden_meta.group, autocompletion=common.cache.group_completion, show_default=False),
    _group: str = typer.Option(None, "--group", metavar=iden_meta.group, autocompletion=common.cache.group_completion, show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete a Template."""
    # allow unnecessary keyword group "cencli delete template NAME group GROUP"
    if group:
        group = [g for g in group if g != "group"]
        group = None if not group else group[0]
    group = _group or group

    if group is not None:
        group: CacheGroup = common.cache.get_group_identifier(group)
        group = group.name

    template: CacheTemplate = common.cache.get_template_identifier(template, group=group)

    print(
        f"[bright_red]{'Delete' if not yes else 'Deleting'}[/] Template [cyan]{template.name}[/] from group [cyan]{template.group}[/]"
    )
    if render.confirm(yes):
        resp = api.session.request(api.configuration.delete_template, template.group, template.name)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)
        _ = api.session.request(common.cache.update_template_db, doc_ids=template.doc_id)


# TOGLP
@app.command()
def device(
    devices: List[str] = common.arguments.devices,
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views.  App assignment and subscriptions remain intact. [dim italic]Device(s) must be [red]offline[/red][/]"),
    cop_inv_only: bool = typer.Option(False, "--cop-only", help="Only delete device from CoP inventory.", hidden=not config.is_cop,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Delete device(s).

    Unassigns any subscriptions and removes the devices assignment with the Aruba Central app in GreenLake.
    Which makes it possible to add it to a different GreenLake WorkSpace.

    Devices are also removed from the Central monitoring views/UI (after waiting for them to disconnect).

    Use --ui-only to remove the device from monitoring views/UI only.

    [cyan]cencli unassign license <LICENSE> <DEVICES>[/] can also be used to unassign a specific license
    from a device(s), (device will remain associated with central App in GreenLake).

    [italic][yellow]:information:[/yellow]  Use [cyan]cencli batch delete devices <IMPORT FILE>[/] to delete devices in mass based on entries in an import file.[/italic]
    """
    # The provided input does not have to be the serial number batch_del_devices will use get_dev_identifier to look the dev
    # up.  It just validates the import has the `serial` field.
    data = [{"serial": d} for d in devices]
    common.batch_delete_devices(data, ui_only=ui_only, cop_inv_only=cop_inv_only, yes=yes)


@app.command()
def guest(
    portal: str = typer.Argument(..., metavar=iden_meta.portal, autocompletion=common.cache.portal_completion, show_default=False,),
    guest: str = typer.Argument(..., metavar=iden_meta.guest, autocompletion=common.cache.guest_completion, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add a guest user to a configured portal"""
    portal: CachePortal = common.cache.get_name_id_identifier("portal", portal)
    guest: CacheGuest = common.cache.get_guest_identifier(guest, portal_id=portal.id)

    _msg = f"[red]:warning:  Delet{'e' if not yes else 'ing'}[/] Guest: [cyan]{guest.name}[/] from portal: [cyan]{portal.name}[/]"
    print(_msg)
    if render.confirm(yes):
        resp = api.session.request(api.guest.delete_guest, portal_id=portal.id, guest_id=guest.id)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)  # exits here if call failed
        _ = api.session.request(common.cache.update_guest_db, guest.doc_id, remove=True)



@app.callback()
def callback():
    """
    Delete Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
