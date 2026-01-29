from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError
import typer

from centralcli import common, config, render, utils, log, api_clients
from centralcli.cache import CacheSite
from centralcli.constants import AllDevTypes
from centralcli.models.imports import ImportSites

from . import examples

if TYPE_CHECKING:
    from centralcli.response import Response

api = api_clients.classic
glp_api = api_clients.glp

app = typer.Typer()


def batch_delete_sites(data: list | dict, *, yes: bool = False) -> list[Response]:
    del_list = []
    if isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):
        data = [{"site_name": k, **data[k]} for k in data]

    try:
        verified_sites = ImportSites(data)
    except ValidationError as e:
        _msg = utils.clean_validation_errors(e)
        common.exit(f"Import data failed validation, refer to [cyan]cencli batch delete sites --example[/] for example formats.\n{_msg}")

    cache_sites: list[CacheSite | None] = [common.cache.get_site_identifier(s.site_name, silent=True, exit_on_fail=False) for s in verified_sites]
    not_in_central = [model.site_name for model, data in zip(verified_sites, cache_sites) if data is None]

    if not_in_central:
        render.econsole.print(f"[dark_orange3]:warning:[/]  [red]Skipping[/] {utils.color(not_in_central, 'red')} [italic]site{'s do' if len(not_in_central) > 1 else ' does'} not exist in Central.[/]")

    sites: list[CacheSite] = [s for s in cache_sites if s is not None]
    del_list = [s.id for s in sites]
    if not del_list:
        common.exit("[italic dark_olive_green2]No sites remain after validation.[/]")

    site_names = utils.summarize_list([s.summary_text for s in sites], max=7)
    render.econsole.print(f"The following {len(del_list)} sites will be [bright_red]deleted[/]:\n{site_names}", emoji=False)
    render.confirm(yes)
    resp: list[Response] = api.session.request(api.central.delete_site, del_list)

    # cache update
    try:
        doc_ids = [s.doc_id for s, r in zip(sites, resp) if r.ok]
        api.session.request(common.cache.update_site_db, data=doc_ids, remove=True)
    except Exception as e:  # pragma: no cover
        log.error(f"{repr(e)} occured during attempt to update sites cache", caption=True, log=True)
        log.exception(e)

    return resp


@app.command()
def sites(
    import_file: Path = common.arguments.get("import_file"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch delete sites based on data from required import file.

    Use [cyan]cencli batch delete sites --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.delete_sites)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch delete sites [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, import_type="sites",)
    resp = batch_delete_sites(data, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.command()
def groups(
    import_file: Path = common.arguments.get("import_file",),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch delete groups based on data from required import file.

    Use [cyan]cencli batch delete groups --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.delete_groups)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch delete groups [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, import_type="groups",)
    resp = common.batch_delete_groups(data, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.command()
def devices(
    import_file: Path = common.arguments.import_file,
    ui_only: bool = typer.Option(False, "--ui-only", help="Only delete device from UI/Monitoring views (devices must be offline).  Devices will remain in inventory with subscriptions unchanged."),
    dev_type: AllDevTypes = typer.Option(None, "--dev-type", help="Only delete devices of a given type. [dim italic]Applies/Only valid with [cyan]--no-sub or --site[/]", show_default=False,),
    cop_inv_only: bool = typer.Option(False, "--cop-only", help="Only delete device from CoP inventory.  (Devices are not deleted from monitoring UI)", hidden=not config.is_cop,),
    unsubscribed: bool = typer.Option(False, "--no-sub", help="Disassociate from the Aruba Central Service in GLP all devices that have no subscription assigned"),
    site: str = common.options.get("site", help="Delete all devices from a given site."),
    no_refresh: bool = common.options.get("no_refresh", help="Don't refresh the cache prior to collecting devices to delete.  [dim italic]Applies to --no-sub and --site options[/]"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch delete devices based on data from import file, delete all devices that lack a subscription, or delete all devices associated with a provided site.

    Use [cyan]cencli batch delete devices --example[/] to see example import file formats.

    [cyan]cencli batch delete devices <IMPORT_FILE>[/]

    Delete devices will remove any subscriptions/licenses from the device and disassociate the device with the Aruba Central app in GreenLake.  It will then remove the device from the monitoring views, along with the historical data for the device.

    Note: devices can only be removed from monitoring views if they are in a down state.  This command will delay/wait for any Up devices to go Down after the subscriptions/assignment to Central is removed, but it can also be ran again.  It will pick up where it left off, skipping any steps that have already been performed.
    """
    if show_example:
        render.console.print(examples.delete_devices)
        return

    usage_msg = "cencli batch delete devices [OPTIONS] [IMPORT_FILE]"

    if import_file:
        if unsubscribed:
            common.exit(render._batch_invalid_msg(usage_msg, provide="Provide [bright_green]IMPORT_FILE[/] or [cyan]--no-sub[/] [red]not both[/]"))
        if dev_type:
            common.exit("[cyan]--dev-type[/] option is currently only valid in combination with [cyan]--no-sub[/].")
        data = common._get_import_file(import_file, import_type="devices",)
    elif unsubscribed:
        resp = common.cache.get_devices_with_inventory(device_type=dev_type, no_refresh=no_refresh)
        if not resp:
            render.display_results(resp, exit_on_fail=True)
        data = [d for d in resp.output if d["subscription_key"] is None]
    elif site:
        resp = common.cache.get_devices_with_inventory(device_type=dev_type, no_refresh=no_refresh)
        cache_site = common.cache.get_site_identifier(site)
        data = [d for d in resp.output if (d.get("site") or "") == cache_site.name]
    else:
        common.exit(render._batch_invalid_msg(usage_msg, provide="Provide [bright_green]IMPORT_FILE[/], [cyan]--no-sub[/] or [cyan]--example[/]"))

    resp = common.batch_delete_devices(data, ui_only=ui_only, cop_inv_only=cop_inv_only, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.command()
def labels(
    import_file: Path = common.arguments.import_file,
    no_devs: bool = typer.Option(False, "--no-devs", help="Delete all labels that have no devices assigned"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch delete labels based on data from import file or delete all labels with no devices assigned.

    Use [cyan]cencli batch delete labels --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.delete_labels)
        return

    usage_msg = "cencli batch delete labels [OPTIONS] [IMPORT_FILE]"

    if import_file:
        if no_devs:
            common.exit(render._batch_invalid_msg(usage_msg, provide="Provide [bright_green]IMPORT_FILE[/] or [cyan]--no-devs[/] [red]not both[/]"))

        data = common._get_import_file(import_file, import_type="labels", text_ok=True)
    elif no_devs:
        resp = api.session.request(common.cache.refresh_label_db)
        if not resp:
            render.display_results(resp, exit_on_fail=True)
        data = [{"name": d["label_name"]} for d in resp.output if not d["associated_device_count"]]
    else:
        common.exit(render._batch_invalid_msg(usage_msg, provide="Provide [bright_green]IMPORT_FILE[/], [cyan]--no-devs[/] or [cyan]--example[/]"))

    resp = common.batch_delete_labels(data, yes=yes)
    render.display_results(resp, tablefmt="action")

@app.callback()
def callback():
    """Perform batch delete operations"""
    pass


if __name__ == "__main__":
    app()