#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
from sqlite3 import OperationalError
from time import sleep
from typing import TYPE_CHECKING

import asyncio
import shutil
from enum import Enum
from functools import partial
from pathlib import Path

import typer
from rich import print

from centralcli import common, config, render
from centralcli.constants import HelpObject
from centralcli.environment import env
from centralcli.strings import emoji
from centralcli.typedefs import StrPath
from centralcli.cache.sqlite import DBAction

if TYPE_CHECKING:
    from centralcli.objects.cache import CacheDevice, CacheInvDevice, CacheSite, CacheGroup

app = typer.Typer()


def toggle_bak_file(file: StrPath, *, conf_msg: str = None, yes: bool | None = None) -> Path:
    """Helper to rename file.  Will add or remove .bak or pytest.bak extension from provided file.

    If file currently ends with .bak/.pytest.bak it will be renamed without.
    If file lacks the .bak extension iy will be renamed with the .bak extension.

    Note: pytest is for restoration only.  The real cache is coppied to db.json.pytest.bak during
    test runs with mocked responses (to prevent mocked responses from mucking with the real cache).
    If the test run is aborted and pytest does not run cleanup, the cache would need to be restored
    manually.  restore_cache with --pytest option does this.

    Args:
        file (StrPath): The file to rename.  Either add or remove .bak extension.
        conf_msg (str, optional): Msg displayed prior to performing rename. Defaults to None.
        yes (bool | None, optional): Provide a bool Value to force the user to confirm via prompt. Defaults to None.

    Returns:
        Path: The new Path object after rename.

    Raises: typer.Exit is raised if the file does not exist or the rejects confirmation prompt.
    """
    file = file if isinstance(file, Path) else Path(file)
    pytest = False

    new_name = f"{str(file)}.bak" if file.suffix != ".bak" else str(file).removesuffix(".bak")
    if new_name.endswith("pytest"):
        pytest_cache = Path(new_name)
        new_name = new_name.removesuffix(".pytest")
        pytest = True

    new = Path(new_name)

    if pytest:
        shutil.copy(new, pytest_cache)  # we keep db.json.pytest for future mocked test runs.
    elif new.exists():
        common.exit(f"[cyan]{new.name}[/] [red]already exists[/] in {new.parent}.\nAborting...")
    if not file.exists():
        new_msg = "" if not new.exists() else f" and [dark_olive_green2]{new.name}[/] already exists."
        common.exit(f"[cyan]{file.name}[/] [red]not found[/]{new_msg} in {file.parent}. Nothing to do.\nAborting...")

    if conf_msg:
        render.econsole.print(conf_msg)
    if yes is not None:
        render.confirm(yes)

    new = file.rename(new)
    if new.exists():
        render.console.print("[bright_green]Success[/]")
    else:
        common.exit(f"Something may have gone wrong.  {new} doesn't appear to exist.")

    return new


@app.command()
def no_config(
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Configure [cyan]cencli[/] as if there is no config.

    Renames [cyan]config.yaml[/] --> [dark_olive_green2]config.yaml.bak[/]

    So cencli can be tested as if no config exists.
    [dim italic]Primarily to test 1st run wizard and behavior when no config is present.[/]
    """
    conf_msg = f"Stash existing config [cyan]{config.file}[/] to [dark_olive_green2]{config.file}.bak[/]"
    toggle_bak_file(config.file, conf_msg=conf_msg, yes=yes)


@app.command()
def restore_config(
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Restore previously stashed [cyan]cencli[/] configuration file.

    Renames [cyan]config.yaml.bak[/] --> [dark_olive_green2]config.yaml[/]

    Restores file stashed with [cyan]cencli dev no-config[/]
    """
    config_bak = Path(f"{str(config.file)}.bak")
    conf_msg = f"Restoring [cyan]cencli[/] configuration from [cyan]{config_bak.name}[/]..."
    toggle_bak_file(config_bak, conf_msg=conf_msg)


@app.command()
def new_config(
    yes: bool = common.options.yes,
    overwrite: bool = typer.Option(False, "-o", "--overwrite", help=f"Overwrite existing bak file if one exists.  {render.help_block('exit if bak file already exists')}"),
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Restore v2 cencli config from previously stashed/created config.yaml.v2.bak

    Provided the existing config is a V1 config:
        coppies [cyan]config.yaml[/] --> [dark_olive_green2]config.yaml.v1.bak[/]
        coppies [cyan]config.yaml.v2.bak[/] --> [dark_olive_green2]config.yaml[/]
    """
    v1_bak_file = config.dir / "config.yaml.v1.bak"
    v2_bak_file = config.dir / "config.yaml.v2.bak"
    if not config.is_old_cfg:
        common.exit(f"{config.file} appears to be a v2 config.")
    if not v2_bak_file.exists():
        common.exit(f"{v2_bak_file} not found.")
    if not overwrite and v1_bak_file.exists() and config.file.exists():
        common.exit(f"{v1_bak_file.name} exists.  Use [cyan]--overwrite[/]|[cyan]-o[/] to overwrite.")

    conf_msg = [] if not config.file.exists() else [
        f"Stash{'' if not yes else 'ing'} existing config [cyan]{config.file.name}[/] to [dark_olive_green2]{v1_bak_file.name}[/]",
    ]
    conf_msg += [
        f"Restor{'e' if not yes else 'ing'} v2 config [cyan]{v2_bak_file.name}[/] to [dark_olive_green2]{config.file.name}[/]",
    ]

    render.econsole.print("\n".join(conf_msg))
    render.confirm(yes)
    if config.file.exists():
        shutil.copy(config.file, v1_bak_file)
    shutil.copy(v2_bak_file, config.file)


@app.command()
def old_config(
    yes: bool = common.options.yes,
    overwrite: bool = typer.Option(False, "-o", "--overwrite", help=f"Overwrite existing bak file if one exists.  {render.help_block('exit if bak file already exists')}"),
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Restore v1 cencli config from previously stashed/created config.yaml.v1.bak

    Provided the existing config is a V1 config:
        coppies [cyan]config.yaml[/] --> [dark_olive_green2]config.yaml.v2.bak[/]
        coppies [cyan]config.yaml.v1.bak[/] --> [dark_olive_green2]config.yaml[/]
    """
    v1_bak_file = config.dir / "config.yaml.v1.bak"
    v2_bak_file = config.dir / "config.yaml.v2.bak"
    if config.is_old_cfg:
        common.exit(f"{config.file} appears to be a v1 config.")
    if not v1_bak_file.exists():
        common.exit(f"{v1_bak_file} not found.")
    if not overwrite and v2_bak_file.exists() and config.file.exists():
        common.exit(f"{v2_bak_file.name} exists.  Use [cyan]--overwrite[/]|[cyan]-o[/] to overwrite.")

    conf_msg = [] if not config.file.exists() else [
        f"Stash{'' if not yes else 'ing'} existing config [cyan]{config.file.name}[/] to [dark_olive_green2]{v2_bak_file.name}[/]",
    ]
    conf_msg += [
        f"Restor{'e' if not yes else 'ing'} v1 config [cyan]{v1_bak_file.name}[/] to [dark_olive_green2]{config.file.name}[/]",
    ]

    render.econsole.print("\n".join(conf_msg))
    render.confirm(yes)
    if config.file.exists():
        shutil.copy(config.file, v2_bak_file)
    shutil.copy(v1_bak_file, config.file)


@app.command()
def no_cache(
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Configure [cyan]cencli[/] as if there is no cache.

    Adds (renames) cache file appending .bak to the file name.

    So cencli can be tested as if no cache exists.
    """
    conf_msg = f"Stash existing cache [cyan]{config.cache.file}[/] to [dark_olive_green2]{config.cache.file}.bak[/]"
    toggle_bak_file(config.cache.file, conf_msg=conf_msg, yes=yes)


@app.command()
def restore_cache(
    pytest: bool = typer.Option(False, "--pytest", help="Restore cache from aborted pytest run 'db.json.pytest.bak'", show_default=False,),
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Restore previously stashed [cyan]cencli[/] cache file.

    Restores cache previously stashed with [cyan]cencli dev no-cache[/]

    :information:  Use [cyan]--pytest[/] :triangular_flag: to restore real cache in the event a test run
    is aborted and pytest teardown did not restore it.
    """
    cache_bak = Path(f"{str(config.cache.file)}.{'bak' if not pytest else 'pytest.bak'}")
    conf_msg = f"Restoring [cyan]cencli[/] cache from [cyan]{cache_bak.name}[/]..."
    toggle_bak_file(cache_bak, conf_msg=conf_msg)


@app.command()
def colors(
    debug: bool = common.options.debug,
    filter: str = typer.Option(None, "-c", "--color", help="Display only colors with this value in the name", show_default=False,),
) -> None:
    """Show text in each color available in the rich library.
    """
    from rich.color import ANSI_COLOR_NAMES
    from rich.console import Console
    from rich.markup import escape
    from rich.table import Table
    from rich.text import Text

    console = Console()

    table = Table(show_footer=False, show_edge=True)
    max_color_name = max([len(color) for color in ANSI_COLOR_NAMES])
    table.add_column("Name", justify="right", width=max_color_name)
    table.add_column("Color", width=15)
    table.add_column("Example")

    colors = sorted(ANSI_COLOR_NAMES.keys())
    for color in colors:
        if filter and filter not in color:
            continue
        elif "grey" in color:
            continue
        color_cell = Text(" " * 10, style=f"on {color}")
        example_cell = (
            f"[{color}]The quick brown {escape('[dim]')} [dim]fox jumps over[/dim] {escape('[italic]')} [italic]the lazy dog[/italic]. "
            f"1234567890!? {escape('[bold]')} [bold]Pack my box with five dozen liquor jugs[/bold][/]"
        )
        table.add_row(
            f"[{color}{'' if color not in ['black', 'gray0', 'gray3', 'gray7', 'gray11', 'navy_blue'] else ' on white'}]{color}[/]", color_cell, example_cell
        )

    console.print(table)


@app.command("emoji")
def emoji_(
    debug: bool = common.options.debug,
    filter: str = typer.Option(None, "-e", "--emoji", help="Display only emoji with this value in the name", show_default=False,),
    unicode: bool = typer.Option(False, "-u", help="show unicode characters"),
) -> None:
    """Show emojis available in the rich library."""
    from rich.columns import Columns
    from rich.console import Console
    from rich.emoji import EMOJI

    console = Console(record=True)

    if not unicode:
        columns = Columns(
            (f":{name}: {name}" for name in sorted(EMOJI.keys()) if "\u200D" not in name and (not filter or filter in name)),
            column_first=True,
        )
    else:
        columns = Columns(
            (f":{name}: {value!a} {name}" for name, value in sorted(EMOJI.items()) if "\u200D" not in name and (not filter or filter in name)),
            column_first=True,
        )

    console.print(columns)


@app.command()
def show_raw(
    line: int = typer.Argument(None, help="Show raw capture from this line in raw_capture file", show_default=False,),
    debug: bool = common.options.debug,
) -> None:
    """Pretty prints active raw capture in file JSON format

    [italic]Contents of the active raw capture file are not valid JSON.
    This command makes the necessary adjustments without modifying the
    contents of the file.[/]
    """
    if not config.capture_file.exists():
        common.exit(f"{config.capture_file} does not exist.")

    lines = config.capture_file.read_text()
    if not line:
        render.console.print(lines)
    else:
        output = lines.splitlines()[line].rstrip(",")
        from rich import print_json
        print_json(output)


@app.command()
def close_raw(
    debug: bool = common.options.debug,
) -> None:
    """Adds closing ] to raw capture file"""
    if not config.capture_file.exists():
        common.exit(f"{config.capture_file} does not exist.")

    config.closed_capture_file.write_text(f"{config.capture_file.read_text().rstrip().rstrip(',')}\n]")

    render.console.print(f"Raw Capture file {config.capture_file} coppied to {config.closed_capture_file} with closing ] to ensure proper JSON.")


@app.command()
def clear_raw(
    yes: bool = common.options.yes,
    bak: bool = typer.Option(False, "-b", "--bak", help=f"Stash active raw capture file... [italic]add [cyan].bak[/] extension[/].  {render.help_block('raw capture file is deleted')}"),
    debug: bool = common.options.debug,
) -> None:
    """Delete [italic](or stash)[/] raw capture file

    This results in any new captures being sent to a fresh raw capture file.
    """
    if not config.capture_file.exists():
        common.exit(f"{config.capture_file} does not exist.")

    sfx = '...' if yes else '?'
    bak_file = config.capture_file.parent / f"{config.capture_file.name}.bak"
    if bak:
        func = partial(config.capture_file.rename, bak_file)
        render.econsole.print(f"[medium_spring_green]Stash{'ing' if yes else ''}[/] active capture file [red italic]{config.capture_file.name}[/] :arrow_right: [bright_green]{bak_file.name}[/]{sfx}")
    else:
        render.econsole.print(f":wastebasket:  [red]Delet{'ing' if yes else 'e'}[/] active capture file [cyan italic]{config.capture_file.name}[/]{sfx}")
        if not yes:
            render.econsole.print(f"  [italic]{emoji.warn} This will delete the file.  Use [cyan]-b[/]|[cyan]--bak[/] option to stash (rename) the file to [cyan]{bak_file.name}[/][/italic]")
        func = config.capture_file.unlink

    render.confirm(yes)
    func()
    render.console.print("[bright_green]Done[/]")


@app.command()
def help_text(
    cache_object: list[HelpObject] = typer.Argument(None, help="The cache object to show summary text for. Defaults to all.", show_default=False),
) -> None:
    """Show help / summary text for all Cache Objects"""
    from centralcli import cache, utils
    from centralcli.objects.cache import CacheInvMonDevice, CacheDevice, CacheInvDevice
    serials = set([*list(cache.inventory_by_serial.keys()), *list(cache.devices_by_serial.keys())])
    invmondevs = [CacheInvMonDevice(None if s not in cache.inventory_by_serial else CacheInvDevice(cache.inventory_by_serial[s]), None if s not in cache.devices_by_serial else CacheDevice(cache.devices_by_serial[s])) for s in serials]
    ignore_emoji = [":cd:", ":ab:"]

    def show(tables: str | list[str] = None):
        cache_name = ["groups", "sites", "devices", "inventory", "invmondevs", "certs", "clients", "buildings", "floor-aps", "guests", "labels", "mpsks", "mpsk-nets", "portals", "subs", "certs", "templates"]
        cache_list = [cache.groups, cache.sites, cache.devices, cache.inventory, invmondevs, cache.certs, cache.clients, cache.floor_plan_buildings, cache.floor_plan_aps, cache.guests, cache.labels, cache.mpsk, cache.mpsk_networks, cache.portals, cache.subscriptions, cache.certs, cache.templates]
        items = list(zip(cache_name, cache_list)) if not tables else [(t, cache_list[cache_name.index(t)]) for t in utils.listify(tables)]
        for name, c in items:
            render.console.rule(name)
            for obj in list(c)[0:4 if not tables else len(list(c))]:
                render.console.print(f"{'typer':>14}: ", end="")
                typer.echo(obj.help_text)
                render.console.print(f"{'rich.Text':>14}: ", end="")
                render.console.print(obj.text)
                # render.console.print(f"{'rich_help_text':>14}: ", end="")
                # render.console.print(obj.rich_help_text, emoji=all([e not in obj.text.plain.lower() for e in ignore_emoji]))
                render.console.print(f"{'summary_ext':>14}: ", end="")
                render.console.print(obj.summary_text, emoji=all([e not in obj.text.plain.lower() for e in ignore_emoji]))

    show(None if not cache_object else [c.value for c in cache_object])


class CacheArgs(str, Enum):
    devices = "devices"
    inventory = "inventory"
    sites = "sites"
    groups = "groups"
    labels = "labels"
# full list in constants.CacheArgs


@app.command()
def cache_del(
    cache_table: CacheArgs = typer.Argument(..., help="Cache to remove item from", show_default=False),
    query_str: str = typer.Argument(..., help="The query string to search the cache for, for the record to remove", show_default=False),
    yes: bool = common.options.yes,
    mock: bool = typer.Option(False, help="Remove an item from the mock cache", show_default=False),  # this is handled in __init__
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Remove an item from the cache"""
    from centralcli import cache
    lookups = {
        CacheArgs.devices: (cache.get_dev_identifier, cache.update_dev_db),
        CacheArgs.inventory: (cache.get_inv_identifier, cache.update_inv_db),
        CacheArgs.sites: (cache.get_site_identifier, cache.update_site_db),
        CacheArgs.groups: (cache.get_group_identifier, cache.update_group_db),
        CacheArgs.labels: (cache.get_label_identifier, cache.update_label_db),
    }
    qry_func, update_func = lookups.get(cache_table, (None, None))
    if not qry_func:
        common.exit(f"cache-del for {cache_table} not implemented yet.")
    _match: CacheDevice | CacheInvDevice | CacheSite | CacheGroup = qry_func(query_str, retry=False)
    if _match is None:
        common.exit(f"[cyan]{query_str}[/] was [red]not found[/] in [cyan]{cache_table.value}[/] cache.  Nothing to delete.", code=0)
    if env.is_pytest:
        render.console.print(f"{emoji.info} [italic]Updating cache for [bright_green]mock[/] [dim](pytest)[/] workspace.[/italic]\n")
    elif config.workspace != config.default_workspace:
        render.console.print(f"{emoji.info} [italic]Updating cache for [bright_green]{config.workspace}[/] workspace.[/italic]\n")
    render.console.print(f"{emoji.warn} [bold red]Remov{'ing' if yes else 'e'}[/] {_match.summary_text} from [spring_green1]{cache_table.name}[/] cache.", emoji=False)
    render.confirm(yes)
    cache_resp = asyncio.run(update_func(dict(_match), action=DBAction.DELETE))
    render.console.print(f"[bright_green]:heavy_check_mark:  [dim]{update_func.__name__}...[/] Success[/]" if cache_resp else f":x:  [dim]{update_func.__name__}...[/] Failure")
    common.exit(code=int(not cache_resp))


@app.command()
def cache_update(
    cache_table: CacheArgs = typer.Argument(..., help="Cache table to update", show_default=False),
    query_str: str = typer.Argument(..., help="The query string to search the cache for, for the record to Update", show_default=False),
    key: str = typer.Argument(..., help="The key field to update", show_default=False),
    value: str = typer.Argument(..., help="The value to update the key field with", show_default=False),
    yes: bool = common.options.yes,
    mock: bool = typer.Option(False, help="Update an item in the mock cache", show_default=False),  # this is handled in __init__
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update an item in the cache"""
    if key == "status":
        value = value.capitalize()
    from centralcli import cache
    lookups = {
        CacheArgs.devices: (cache.get_dev_identifier, cache.update_dev_db),
        CacheArgs.inventory: (cache.get_inv_identifier, cache.update_inv_db),
        CacheArgs.sites: (cache.get_site_identifier, cache.update_site_db),
        CacheArgs.groups: (cache.get_group_identifier, cache.update_group_db),
    }
    qry_func, update_func = lookups.get(cache_table, (None, None))
    if not qry_func:
        common.exit(f"cache-update for {cache_table} not implemented yet.")
    _match = qry_func(query_str, retry=False)
    if _match is None:
        common.exit(f"{emoji.info} [cyan]{query_str}[/] was [red]not found[/] in [cyan]{cache_table.value}[/] cache.  Nothing to Update.", code=0)
    if not hasattr(_match, key):
        common.exit(f"[cyan]{key}[/] does not appear to be an attribute of [cyan]{cache_table.value}[/] cache.")
    if getattr(_match, key) == value:
        common.exit(f"{emoji.info} [cyan]{_match.summary_text}[/]\n   Already has desired value [bold green]{value}[/] for [cyan]{key}[/]. No Update necessary.", code=0, emoji=False)

    if env.is_pytest:
        render.console.print(f"{emoji.info} [italic]Updating cache for [bright_green]mock[/] [dim](pytest)[/] workspace.[/italic]\n")
    elif config.workspace != config.default_workspace:
        render.console.print(f"{emoji.info} [italic]Updating cache for [bright_green]{config.workspace}[/] workspace.[/italic]\n")

    render.console.print(f"{emoji.warn} [bold green]Updat{'ing' if yes else 'e'}[/] {_match.summary_text} from [spring_green1]{cache_table.name}[/] cache.\n   [bold green]Update[/] [cyan]{key}[/] --> [green]{value}[/]", emoji=False)
    render.confirm(yes)
    update_data = {**dict(_match), key: value}
    cache_resp = asyncio.run(update_func(update_data))
    render.console.print(f"[bright_green]:heavy_check_mark:  [dim]{update_func.__name__}...[/] Success[/]" if cache_resp else f":x:  [dim]{update_func.__name__}...[/] Failure")
    common.exit(int(not cache_resp))


@app.command()
def cache_lookup(
    cache_table: CacheArgs = typer.Argument(..., help="Cache to query", show_default=False),
    query_str: str = typer.Argument(..., help="The query string", show_default=False),
    yes: bool = common.options.yes,
    mock: bool = typer.Option(False, help="Lookup an item in the mock cache", show_default=False),  # this is handled in __init__
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Lookup an item in the cache"""
    from centralcli import cache
    lookups = {
        CacheArgs.devices: (cache.get_dev_identifier, cache.update_dev_db),
        CacheArgs.inventory: (cache.get_inv_identifier, cache.update_inv_db),
        CacheArgs.sites: (cache.get_site_identifier, cache.update_site_db),
        CacheArgs.groups: (cache.get_group_identifier, cache.update_group_db),
    }
    qry_func, update_func = lookups.get(cache_table, (None, None))
    if not qry_func:
        common.exit(f"cache-update for {cache_table} not implemented yet.")

    for _ in range(2):
        try:
            _match: CacheDevice | CacheInvDevice | CacheSite | CacheArgs = qry_func(query_str, retry=False)
            break
        except OperationalError as e:
            if "database is locked" in repr(e):
                sleep(1)
                continue
            else:
                raise e

    if env.is_pytest:
        render.console.print(f"{emoji.info} [italic]Cache lookup for [bright_green]mock[/] [dim](pytest)[/] workspace.[/italic]\n")
    elif config.workspace != config.default_workspace:
        render.console.print(f"{emoji.info} [italic]Cache lookup for [bright_green]{config.workspace}[/] workspace.[/italic]\n")
    if _match is None:
        common.exit(f"{emoji.info} [cyan]{query_str}[/] was [red]not found[/] in [cyan]{cache_table.value}[/] cache.", code=1)

    render.console.print(_match, emoji=False)
    render.display_results(data=_match.data, tablefmt="yaml")


@app.command()
def ws_change(
    workspace_list: list[str] = typer.Argument(
        None,
        help="A list of workspaces to verify workspace changes within a CLI session (command)",
        autocompletion=common.cache.workspace_completion,
        show_default=False,
    ),
    yes: bool = common.options.yes,
    mock: bool = typer.Option(False, help="Remove an item from the mock cache", show_default=False),  # this is handled in __init__
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Test mid command workspace switching functionality"""
    from centralcli.clitree.show.show import _get_cencli_config

    for idx, (ws, serial) in enumerate(zip([config.workspace, "kfc", "ge"], ["CNR4LHJ08G", "CNC7J0T11X", "CNGFJ0TJX5"])):
        if idx > 0:
            config.workspace = ws

        print(render.render_title(f"{'Starting ' if idx == 0 else ''}Workspace [bright_green]{config.workspace} Config[/]"))
        _get_cencli_config(brief=True)

        from centralcli import api_clients
        print(render.render_title(f"Workspace [bright_green]{config.workspace} Classic API info[/]"))
        render.display_results(data=api_clients.classic.session.auth.central_info, tablefmt="yaml")

        print(render.render_title(f"Workspace [bright_green]{config.workspace} GLP API info[/]"))
        glp_data = {
            "token info": api_clients.glp.session.auth.token_info,
            "central info": api_clients.glp.session.auth.central_info,
        }
        render.display_results(data=glp_data, tablefmt="yaml")

        print(render.render_title(f"Workspace [bright_green]{config.workspace} GLP Cache Inventory refresh test call using serial# {serial}[/]"))
        resp = api_clients.glp.session.request(common.cache.refresh_inv_db, serial_numbers=(serial,))
        print(resp._response.request_info.headers["authorization"])
        render.display_results(resp, title="glp API test call", exit_on_fail=False)

        print(render.render_title(f"Workspace [bright_green]{config.workspace} GLP direct Inventory test call using serial# {serial}[/]"))
        resp = api_clients.glp.session.request(api_clients.glp.devices.get_devices, serial_numbers=(serial,))
        print(resp._response.request_info.headers["authorization"])
        print(resp.output[0].get("id") or resp.error)

        if idx != 2:
            render.pause()


@app.callback(no_args_is_help=True)
def callback():
    """
    [dark_orange3]:warning:[/]  These commands are intended for development.  Use with caution.
    """
    pass


if __name__ == "__main__":
    app()
