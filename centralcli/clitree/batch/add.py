from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import tablib
import typer
from pydantic import RootModel, ValidationError

from centralcli import cleaner, common, log, render
from centralcli.cache import api
from centralcli.models.imports import ImportMACs, ImportMPSKs

from . import examples

if TYPE_CHECKING:
    from centralcli.cache import CacheMpskNetwork
    from centralcli.response import Response
    from centralcli.typedefs import CloudAuthUploadTypes

app = typer.Typer()


def batch_add_cloudauth(upload_type: CloudAuthUploadTypes = "mac", import_file: Path = None, *, ssid: CacheMpskNetwork = None, data: bool = None, yes: bool = False) -> Response:
    if import_file is not None:
        data = common._get_import_file(import_file, upload_type)
    elif not data:
        common.exit("[red]Error!![/] No import file provided")

    render.econsole.print(f"Upload{'' if not yes else 'ing'} [bright_green]{len(data)}[/] [cyan]{upload_type.upper()}s[/] defined in [cyan]{import_file.name}[/] to Cloud-Auth{f' for SSID: [cyan]{ssid.name}[/]' if upload_type == 'mpsk' else ''}")
    # cloudauth accepts csv files
    if upload_type in ["mpsk", "mac"]:
        if upload_type == "mac":
            Model = ImportMACs
            upload_fields = {
                "mac": "Mac Address",
                "name": "Client Name"
            }
        else:
            Model = ImportMPSKs
            upload_fields = {
                "name": "Name",
                "role": "Client Role",
                "status": "Status"
            }
            if "mpsk" in map(str.lower, data[0].keys()):
                log.warning("MPSK can not be configured, this API only supports generation of random MPSKs, not user specified MPSKs.  It will fail if MPSK column is provided in the import.  Elliminating MPSK column.", show=True, caption=True)

        try:
            data = Model(data)
        except ValidationError as e:
            common.exit(''.join(str(e).splitlines(keepends=True)[0:-1]))  # strip off the "for further information ... errors.pydantic.dev..."

        data: RootModel = data.model_dump()
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

    if render.confirm(yes):
        resp = api.session.request(api.cloudauth.cloudauth_upload, upload_type=upload_type, file=tmp_path, ssid=None if not ssid else ssid.name)
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
    if resp.ok:
        try:
            resp.output = cleaner.sites(resp.output)
        except Exception as e:  # pragma: no cover
            log.error(f"Error cleaning output of batch site addition {repr(e)}", caption=True, log=True)

    render.display_results(resp, title="Batch Add Sites",)


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
    if [r for r in resp if not r.ok and r.url.path.endswith("/subscriptions/assign")]:
        log.warning("Aruba Central took issue with some of the devices when attempting to assign subscription.  It will typically stop processing when this occurs, meaning valid devices may not have their license assigned.", caption=True)
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

    resp = batch_add_cloudauth("mac", import_file, yes=yes)
    caption = (
        "\nUse [cyan]cencli show cloud-auth upload[/] to see the status of the import.\n"
        "Use [cyan]cencli show cloud-auth registered-macs[/] to see all registered macs."
    )
    if resp.ok:
        try:
            resp.output = cleaner.cloudauth_upload_status(resp.output)
        except Exception as e:  # pragma: no cover
            log.error(f"Error cleaning output of cloud auth mac upload {repr(e)}", caption=True, log=True)

    render.display_results(resp, tablefmt="action", title="Batch Add MACs (cloud-auth)", caption=caption)


@app.command()
def mpsk(
    import_file: Path = common.arguments.import_file,
    ssid: str = typer.Option(None, "--ssid", help="SSID to associate mpsk definitions with", autocompletion=common.cache.mpsk_network_completion, show_default=False,),
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
    resp = batch_add_cloudauth("mpsk", import_file, ssid=ssid, yes=yes)
    caption = [
        "[dim italic]Use [cyan]cencli show cloud-auth upload mpsk[/] to see the status of the import.",
        f"Use [cyan]cencli show mpsk named {ssid.name} -v[/] to determine the randomly generated MPSKs[/dim italic]"
    ]

    render.display_results(resp, tablefmt="action", title="Batch Add MPSK", caption=caption)

@app.callback()
def callback():
    """Perform batch add operations."""
    pass


if __name__ == "__main__":
    app()