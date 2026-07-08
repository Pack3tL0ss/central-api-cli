from __future__ import annotations

from pathlib import Path

import typer
from pydantic import ValidationError

from centralcli import api_clients, common, config, log, render, utils
from centralcli.cache.sqlite import DBAction
from centralcli.constants import AllDevTypes
from centralcli.models.imports import ImportSites
from centralcli.objects.cache import CacheSite
from centralcli.response import BatchResponse
from centralcli.strings import emoji

from . import examples

api = api_clients.classic
glp_api = api_clients.glp

app = typer.Typer()


def batch_delete_sites(data: list | dict, *, import_file: Path, yes: bool = False, no_refresh: bool = False) -> BatchResponse:
    sites_by_id = {}
    retry_data = []
    if isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):
        data = [{"site_name": k, **data[k]} for k in data]

    try:
        verified_sites = ImportSites(data)
    except ValidationError as e:
        _msg = utils.clean_validation_errors(e)
        common.exit(f"Import data failed validation, refer to [cyan]cencli batch delete sites --example[/] for example formats.\n{_msg}")

    with render.Spinner(f"Fetching site ids for {len(verified_sites)} sites from cache"):
        cache_sites: list[CacheSite | None] = common.cache.bulk_site_cache_lookup([s.site_name for s in verified_sites], refresh_on_fail=not no_refresh)
        not_in_central = [model.site_name for model, csite in zip(verified_sites, cache_sites) if csite is None]

    if not_in_central:
        _msg_pfx = ":arrow_double_down: [red]Skipping[/]"
        _msg_sfx = f"site{'s do' if len(not_in_central) > 1 else ' does'} [red]not exist[/] in Central"
        _msg = f"{_msg_pfx} {len(not_in_central)} site{'s' if len(not_in_central) > 1 else ''} [dim italic]{_msg_sfx}[/]\n" if not config.debug else f"{_msg_pfx} {utils.color(not_in_central, 'red')} [italic]{_msg_sfx}[/]\n"
        render.econsole.print(_msg)

    sites: list[CacheSite] = [s for s in cache_sites if s is not None]
    if not sites:
        common.exit("[italic dark_olive_green2]No sites remain after validation.[/]")

    sites_by_id = {s.id: s for s in sites}
    conf_msg = utils.summarize_list(sites, max=14, pad=3)
    conf_msg2 = f" {len(sites)} sites" if len(sites) > 1 else " site"
    render.econsole.print(f"{emoji.delete}  [bright_red]Delet{'ing' if yes else 'e'}[/] The following{conf_msg2}:\n   {conf_msg.lstrip()}", emoji=False)
    render.confirm(yes)
    batch_resp = BatchResponse(api.session.request(api.central.delete_site, list(sites_by_id.keys()), continue_on_fail=True))

    # cache update
    try:
        update_data = [{"name": s.name} for res, s in zip(batch_resp.responses, sites) if res.ok]
        retry_data = [dict(s) for res, s in zip(batch_resp.responses, sites) if not res.ok]
        if update_data:
            api.session.request(common.cache.update_site_db, data=update_data, action=DBAction.DELETE)
    except Exception as e:  # pragma: no cover
        log.exception(f"{repr(e)} occured during attempt to update sites cache", caption=True, log=True)

    if retry_data:
        log_sfx = ""
        if batch_resp.passed:
            retry_file = import_file.parent / f"{import_file.stem}-retry.csv"
            log_sfx = f" Retry file created: {retry_file}"
            try:
                key_order = ["name", "id"]
                retry_data = utils.format_table(retry_data, key_order=key_order)
                csv_str = render.get_csv_string(retry_data)
                render.write_file(retry_file, csv_str)
            except Exception as e:
                log.exception(f"{repr(e)} during attempt to write retry file after site deletes.")

        log.warning(f"{len(batch_resp.failed)} of {len(batch_resp)} site delete requests [red]failed[/].{log_sfx}", caption=True)

    return batch_resp


@app.command()
def sites(
    import_file: Path = common.arguments.get("import_file"),
    show_example: bool = common.options.show_example,
    no_refresh: bool = common.options.get("no_refresh", help=f"Do not trigger a cache update {render.help_block('Refresh is performed if any devices are not found in Cache')}"),
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

    data = common._get_import_file(import_file, import_type="sites", text_ok=True)
    batch_resp = batch_delete_sites(data, import_file=import_file, yes=yes, no_refresh=no_refresh)
    render.display_results([*batch_resp.passed, *batch_resp.failed], title=f"Delete {len(batch_resp)} site{'s' if len(batch_resp) > 1 else ''} from [cyan]{config.workspace}[/] workspace", tablefmt="action")


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
    do_retry: bool = common.options.do_retry,
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
    if any([unsubscribed, site]):
        no_refresh = True  # Only necessary if they are deleting by site or all unsubed devs.  Otherwise cache will update on demand if devs from import are not found.

    if import_file:
        if unsubscribed:
            common.exit(render._batch_invalid_msg(usage_msg, provide="Provide [bright_green]IMPORT_FILE[/] or [cyan]--no-sub[/] [red]not both[/]"))
        if dev_type:
            common.exit("[cyan]--dev-type[/] option is currently only valid in combination with [cyan]--no-sub[/].")
        data = common._get_import_file(import_file, import_type="devices",)
    elif unsubscribed:
        # inv_devs = common.cache.bulk_inv_cache_lookup(dev_type=dev_type, refresh=not no_refresh)  # TODO No Mock Response...
        # inv_devs_by_serial = {d.serial: d for d in inv_devs}
        # mon_devs = common.cache.bulk_dev_cache_lookup(serial_numbers=list(inv_devs_by_serial.keys()), refresh=not no_refresh)
        # inv_devs_by_serial = {d.serial: d for d in mon_devs}
        # GET_/devices/v1/devices?offset=0&limit=2000&filter=serialNumber eq 'VG2410034937' or serialNumber eq 'CNMBL2H0Z3' or serialNumber eq 'VG2410037886' or serialNumber eq 'CP0059018' or serialNumber eq 'CNHPKLB030' or serialNumber eq 'CP0044573' or serialNumber eq 'CNP5L2H1BC' or serialNumber eq 'VG2410033000' or serialNumber eq 'CNF7JSP0N0' or serialNumber eq 'CNMBL2H0ZL' or serialNumber eq 'VG2410034746'
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

    resp = common.batch_delete_devices(data, ui_only=ui_only, cop_inv_only=cop_inv_only, no_refresh=no_refresh, yes=yes, do_retry=do_retry)
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