from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import tablib
import typer
from pydantic import ValidationError
from rich.markup import escape

from centralcli import cleaner, common, log, render, utils
from centralcli.cache import api
from centralcli.constants import APIAction
from centralcli.models.imports import ImportMACs, ImportMPSKs

from . import examples

if TYPE_CHECKING:
    from centralcli.cache import CacheMpskNetwork
    from centralcli.response import Response
    from centralcli.typedefs import CloudAuthUploadTypes

app = typer.Typer()


def batch_add_cloudauth(import_file: Path, upload_type: CloudAuthUploadTypes = "mac", *, ssid: CacheMpskNetwork = None, yes: bool = False) -> Response:
    data = common._get_import_file(import_file, upload_type)

    render.econsole.print(f"Upload{'' if not yes else 'ing'} [bright_green]{len(data)}[/] [cyan]{upload_type.upper()}s[/] defined in [cyan]{import_file.name}[/] to Cloud-Auth{f' for SSID: [cyan]{ssid.name}[/]' if upload_type == 'mpsk' else ''}")
    # cloudauth accepts csv files
    if upload_type == "mac":
        Model = ImportMACs
        upload_fields = {
            "mac": "Mac Address",
            "name": "Client Name"
        }
    elif upload_type == "mpsk":
        Model = ImportMPSKs
        upload_fields = {
            "name": "Name",
            "role": "Client Role",
            "status": "Status"
        }
        if "mpsk" in map(str.lower, data[0].keys()):  # pragma: no cover
            log.warning("MPSK can not be configured, this API only supports generation of random MPSKs, not user specified MPSKs.  It will fail if MPSK column is provided in the import.  Elliminating MPSK column.", show=True, caption=True)
    else:  # pragma: no cover
        raise ValueError(f"Invalid upload_type {upload_type}, Valid values 'mac', 'mpsk'")

    try:
        data = Model(data)
    except ValidationError as e:
        common.exit(utils.clean_validation_errors(e))

    data = data.model_dump()
    # CACHE cache update after successful upload

    # We use a uniform set of logical field headers/spacing/case. Need to convert to the random 💩 used by Central
    data = [{upload_fields[k]: mpsk[k] for k in mpsk} for mpsk in data]

    ds = tablib.Dataset().load(json.dumps(data), format="json")
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv") as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(ds.csv)
        log.debug(f"CloudAuth Temp file created at: {tmp_path}")

    if log.DEBUG:
        render.econsole.print(f"\nContents of file prepped for upload ({str(tmp_path)}):")
        render.econsole.print(tmp_path.read_text())

    render.confirm(yes)
    resp = api.session.request(api.cloudauth.upload, upload_type=upload_type, file=tmp_path, ssid=None if not ssid else ssid.name)
    tmp_path.unlink()
    log.debug(f"CloudAuth Temp file ({tmp_path}) deleted")

    return resp


@app.command()
def sites(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add sites based on data from required import file.

    Use [cyan]cencli batch add sites --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.add_sites)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch add sites [OPTIONS] [IMPORT_FILE]"))

    resp = common.batch_add_sites(import_file, yes=yes)
    render.display_results(resp, title="Batch Add Sites", cleaner=cleaner.sites)


@app.command()
def groups(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add groups based on data from required import file.

    Use [cyan]cencli batch add groups --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.add_groups)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch add groups [OPTIONS] [IMPORT_FILE]"))

    resp = common.batch_add_groups(import_file, yes=yes)

    render.display_results(resp, tablefmt="action", title="Batch Add Groups",)


# FIXME appears this is not currently state aware, have it only do the API calls not reflected in current state
@app.command()
def devices(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    # TODO need subscription_id
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add devices based on data from required import file.

    Use [cyan]cencli batch add devices --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.add_devices)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch add devices [OPTIONS] [IMPORT_FILE]"))

    resp = common.batch_add_devices(import_file, yes=yes)
    if [r for r in resp if not r.ok and r.url.path.endswith("/subscriptions/assign")]:  # pragma: no cover # TOGLP will add to tests once adjusted to use GLP
        log.warning("Aruba Central took issue with some of the devices when attempting to assign subscription.  It will stop processing when this occurs, meaning valid devices may not have their license assigned.", caption=True, log=True)
        log.info(f"Use [cyan]cencli batch verify devices {import_file}[/] to check status of license assignment.", caption=True)

    render.display_results(resp, tablefmt="action", title="Batch Add devices",)


@app.command()
def labels(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    ssid: str = typer.Option(None, "--ssid", help="SSID to associate mpsk definitions with [grey42 italic]Required and valid only with mpsk argument[/]", autocompletion=common.cache.mpsk_network_completion, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add labels based on data from required import file.

    Use [cyan]cencli batch add labels --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.add_labels)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch add labels [OPTIONS] [IMPORT_FILE]"))

    resp = common.batch_add_labels(import_file, yes=yes)
    render.display_results(resp, tablefmt="action", title="Batch Add Labels",)


@app.command()
def variables(
    import_file: Path = common.arguments.get("import_file", help="Path to file with variables"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add variables for devices based on data from required import file.

    Use [cyan]cencli batch add variables --example[/] to see example import file formats.
    [italic]Accepts same format as Aruba Central UI, but also accepts .yaml[/]
    """
    if show_example:
        render.console.print(examples.add_variables)
        return
    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch add variables [OPTIONS] [IMPORT_FILE]"))

    common.batch_add_update_replace_variables(import_file, action=APIAction.ADD, yes=yes)


@app.command()
def macs(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add MACs [dim italic](cloud-auth)[/] based on data from required import file.

    Use [cyan]cencli batch add macs --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.add_macs)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch add macs [OPTIONS] [IMPORT_FILE]"))

    resp = batch_add_cloudauth(import_file, upload_type="mac", yes=yes)
    caption = (
        "\nUse [cyan]cencli show cloud-auth upload[/] to see the status of the import.\n"
        "Use [cyan]cencli show cloud-auth registered-macs[/] to see all registered macs."
    )

    render.display_results(resp, tablefmt="action", title="Batch Add MACs (cloud-auth)", caption=caption, cleaner=cleaner.cloudauth_upload_status)


@app.command()
def mpsk(
    import_file: Path = common.arguments.import_file,
    ssid: str = typer.Option(None, "--ssid", help=f"SSID to associate mpsk definitions with [dim red]{escape('[required')}[/] [italic](unless using --example)[/][dim red]{escape(']')}[/]", autocompletion=common.cache.mpsk_network_completion, show_default=False,),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch add mpsk based on data from required import file.

    Use [cyan]cencli batch add mpsk --example[/] to see example import file formats.
    """
    if show_example:
        render.console.print(examples.add_mpsk)
        return

    if not import_file or not ssid:
        common.exit(render._batch_invalid_msg("cencli batch add mpsk --ssid <SSID> [IMPORT_FILE]", provide="Provide [bright_green]IMPORT_FILE[/] & [cyan]--ssid[/] [magenta]<SSID>[/] or [cyan]--example[/]"))

    ssid: CacheMpskNetwork = common.cache.get_mpsk_network_identifier(ssid)
    resp = batch_add_cloudauth(import_file, upload_type="mpsk", ssid=ssid, yes=yes)
    caption = [
        "[dim italic]Use [cyan]cencli show cloud-auth upload mpsk[/] to see the status of the import.",
        f"Use [cyan]cencli show mpsk named {ssid.name} -v[/] to determine the randomly generated MPSKs[/dim italic]"
    ]

    render.display_results(resp, tablefmt="action", title="Batch Add MPSK", caption=caption, cleaner=cleaner.cloudauth_upload_status)

@app.callback()
def callback():
    """Perform batch add operations."""
    pass


if __name__ == "__main__":
    app()