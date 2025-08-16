#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import typer

from centralcli import common, config, render
from centralcli.typedefs import StrPath

app = typer.Typer()


def toggle_bak_file(file: StrPath, *, conf_msg: str = None, yes: bool | None = None) -> Path:
    """Helper to rename file.  Will add or remove .bak extension from provided file.

    If file currently ends with .bak it will be renamed without .bak.
    If file lacks the .bak extension is will be renamed with .bak.

    Args:
        file (StrPath): The file to rename.  Either add or remove .bak extension.
        conf_msg (str, optional): Msg displayed prior to performing rename. Defaults to None.
        yes (bool | None, optional): Provide a bool Value to force the user to confirm via prompt. Defaults to None.

    Returns:
        Path: The new Path object after rename.

    Raises: typer.Exit is raised if the file does not exist or the rejects confirmation prompt.
    """
    file = file if isinstance(file, Path) else Path(file)

    new_name = f"{str(file)}.bak" if file.suffix != ".bak" else str(file).removesuffix(".bak")
    new = Path(new_name)

    if new.exists():
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
    conf_msg = f"Stash existing cache [cyan]{config.cache_file}[/] to [dark_olive_green2]{config.cache_file}.bak[/]"
    toggle_bak_file(config.cache_file, conf_msg=conf_msg, yes=yes)


@app.command()
def restore_cache(
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Restore previously stashed [cyan]cencli[/] cache file.

    Restores cache previously stashed with [cyan]cencli dev no-cache[/]
    """
    cache_bak = Path(f"{str(config.cache_file)}.bak")
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
            f"[{color}{'' if color not in ['black', 'gray0', 'gray7', 'gray11'] else ' on white'}]{color}[/]", color_cell, example_cell
        )

    console.print(table)


@app.command()
def emoji(
    debug: bool = common.options.debug,
    filter: str = typer.Option(None, "-e", "--emoji", help="Display only emoji with this value in the name", show_default=False,),
) -> None:
    """Show emojis available in the rich library."""
    from rich.columns import Columns
    from rich.console import Console
    from rich.emoji import EMOJI

    console = Console(record=True)

    columns = Columns(
        (f":{name}: {name}" for name in sorted(EMOJI.keys()) if "\u200D" not in name and (not filter or filter in name)),
        column_first=True,
    )

    console.print(columns)


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
    debug: bool = common.options.debug,
) -> None:
    """Delete raw capture file

    Typically done to allow it to be populated with new data.
    """
    if not config.capture_file.exists():
        common.exit(f"{config.capture_file} does not exist.")

    render.console.print(f"Delet{'ing' if yes else 'e'} active capture file [cyan italic]{config.capture_file}[/]...", end="")
    render.confirm(yes)
    config.capture_file.unlink()
    render.console.print(" [bright_green]Done[/]")


@app.callback()
def callback():
    """
    [dark_orange3]:warning:[/]  These commands are intended for development.  Use with caution.
    """
    pass


if __name__ == "__main__":
    app()
