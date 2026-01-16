#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import common, render, config, utils
from centralcli.constants import APIAction

from . import examples

app = typer.Typer()


@app.command()
def aps(
    import_file: Path = common.arguments.import_file,
    show_example: bool = common.options.show_example,
    reboot: bool = typer.Option(False, "--reboot", "-R", help="Automatically reboot device if IP or VLAN is changed [dim italic]Reboot is required for changes to take effect when IP or VLAN settings are changed[/]"),
    banner_file: Path = common.options.banner_file,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update per-ap-settings, ap-altitude, banner, etc. (at AP level) in mass based on settings from import file

    When [cyan]--banner-file <file>[/] is provided.  Only the banner is processed.  The import_file is used as the variable file if the banner_file is a .j2 file.
    i.e. Most common scenario... banner_file is a j2 with {{ hostname }} which is converted to the value from the hostname field in the import file.

    Use [cyan]--example[/] to see expected import file format and required fields.
    """
    if show_example:
        render.console.print(examples.update_aps)
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch update aps [OPTIONS] [IMPORT_FILE]"))


    data = common._get_import_file(import_file, "devices")

    if banner_file:
        render.econsole.print(f"[deep_sky_blue]:information:[/]  When --banner-file is provided.  Only the banner is processed.  re-run the command without banner to process any other updates from {import_file.name}")

    common.batch_update_aps(data, yes=yes, reboot=reboot)


@app.command(hidden=not config.glp.ok)
def devices(
    import_file: Path = common.arguments.import_file,
    _tags: list[str] = typer.Argument(None, metavar="", hidden=True),  # HACK because list[str] does not work for typer.Option
    tags: list[str] = common.options.tags,
    sub: str = common.options.get(
        "subscription",
        help="Assign this subscription to [bright_green]all[/] devices found in import [red italic](overrides subscription in import if defined)[/]",
        autocompletion=common.cache.sub_completion,
    ),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update devices in [green]GreenLake[/]

    updates can be provided via command line :triangular_flag: or in the import_file

    Command Line flags (--tags, --archive, --sub) will be applied to all devices found in the import.
    [cyan]--tags[/] is cumulative.  Meaning any tags found in the import are created along with tags specified on the command line.
    [italic]if the same tag is provided, the tag in the import wins.[/]

    All other :triangular_flag: provided on the command line will override any value found in the import for that device.
    [italic]i.e. --sub advanced-ap would override anything found in an optional "subscription" field in the import file.

    Use [cyan]--example[/] to see expected import file format and required fields.
    """
    _tags = _tags or []  # in case they use the form --tags tagname=tagvalue which would not populate _tags
    tag_dict = None if not tags else common.parse_var_value_list([*tags, *_tags], error_name="tags")
    if show_example:
        render.console.print(
            f"{utils.color(['csv', 'yaml', 'json'], color_str='cyan')} with the following fields [red]serial[/], {utils.color(['tags', 'subscription'], color_str='cyan')}\n"
            "    [italic][red]red[/] fields are required. All others are optional.[/]"
        )
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch update devices [OPTIONS] [IMPORT_FILE]"))

    data = common._get_import_file(import_file, import_type="devices", subscriptions=True)
    resp = common.batch_update_glp_devices(data, tags=tag_dict, subscription=sub, yes=yes)
    render.display_results(resp, tablefmt="action")


@app.command()
def ap_banner(
    import_file: Path = common.arguments.import_file,
    banner_file: Path = common.arguments.banner_file,
    _banner_file: Path = common.options.get("banner_file", hidden=True),
    banner: bool = common.options.banner,
    group_level: bool = typer.Option(False, "-G", "--groups", help=f"Treat import file as group import, update ap group level configs.  {render.help_block('Update applied at device level, import expected to be device import')}"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    debugv: bool = common.options.debugv,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update banner (MOTD) text for APs at group or device level

    When the banner_file is a [cyan].j2[/] file.  It is processed as a jinja2 template with variables coming from the import_file.
    i.e. Most common scenario... banner_file is a j2 with {{ hostname }} which is converted to the value from the hostname field in the import file.


    Use [cyan]--example[/] to see expected import file format and required fields.
    """
    if show_example:
        render.console.print("Expects .yaml, .json, or .csv file with [cyan]serial[/] unless [cyan]-G[/]|[cyan]--groups[/] is used.  Then expects the same with [cyan]name[/] [dim italic](The group name)[/]")
        render.console.print("Any other keys/values provided in the import will be used as variables if [cyan]banner_file[/] provided is a Jinja2 template [dim italic](.j2 file)[/]")
        render.econsole.print(
            "--------------------- [bright_green].yaml example for[/] [magenta]APs[/] ---------------------\n"
            "- serial: CN12345678\n"
            "  hostname: barn.615.ab12\n"
        )
        render.econsole.print(
            "--------------------- [bright_green].csv example for[/] [magenta]Groups[/] ---------------------\n"
            "name,some_var\n"
            "group_name,some_value\n"
        )

        render.econsole.print("[dark_olive_green2]See [cyan]batch update aps --example[/cyan] for expanded example device import_file format[/]")
        render.econsole.print("[dark_olive_green2]See [cyan]batch add groups --example[/cyan] for expanded example group import_file format[/]")
        return

    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch update ap-banner [OPTIONS] [IMPORT_FILE] [BANNER_FILE]"))

    is_tmp_file = False
    if banner:  # pragma: no cover requires tty
        banner_file = common.get_banner_from_user()
        is_tmp_file = True

    banner_file = banner_file or _banner_file
    if not banner_file:
        common.exit("Missing required argument 'banner_file'")

    data = common._get_import_file(import_file, "devices" if not group_level else "groups")
    common.batch_update_ap_banner(data, banner_file, group_level=group_level, yes=yes)
    if is_tmp_file:  # pragma: no cover
        banner_file.unlink(missing_ok=True)

@app.command()
def variables(
    import_file: Path = common.arguments.get("import_file", help="Path to file with variables"),
    replace: bool = typer.Option(False, "-R", "--replace", help=f"Replace all existing variables with the variables provided {render.help_block('existing variables are retained unless updated in this payload')}"),
    show_example: bool = common.options.show_example,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Batch update/replace variables for devices based on data from required import file.

    Use [cyan]cencli batch update variables --example[/] to see example import file formats.
    [italic]Accepts same format as Aruba Central UI, but also accepts .yaml[/]

    [cyan]-R[/]|[cyan]--replace[/] :triangular_flag: Will flush all existing variables (for the devices in the import_file) and replace with the variables from the import_file.
    By default: Existing variables not in the import_file are left intact.
    """
    if show_example:
        render.console.print(examples.update_variables)
        return
    if not import_file:
        common.exit(render._batch_invalid_msg("cencli batch update variables [OPTIONS] [IMPORT_FILE]"))

    action = APIAction.REPLACE if replace else APIAction.UPDATE
    common.batch_add_update_replace_variables(import_file, action=action, yes=yes)


@app.callback()
def callback():
    """Batch update devices (GreenLake Inventory) / aps / variables."""
    pass


if __name__ == "__main__":
    app()
