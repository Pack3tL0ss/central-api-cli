#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
from functools import partial
from pathlib import Path

import typer

from centralcli import common, config, render
from centralcli.typedefs import StrPath

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
    conf_msg = f"Stash existing cache [cyan]{config.cache_file}[/] to [dark_olive_green2]{config.cache_file}.bak[/]"
    toggle_bak_file(config.cache_file, conf_msg=conf_msg, yes=yes)


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
    cache_bak = Path(f"{str(config.cache_file)}.{'bak' if not pytest else 'pytest.bak'}")
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
            render.econsole.print(f"  [italic][dark_orange3]:warning:[/]  This will delete the file.  Use [cyan]-b[/]|[cyan]--bak[/] option to stash (rename) the file to [cyan]{bak_file.name}[/][/italic]")
        func = config.capture_file.unlink

    render.confirm(yes)
    func()
    render.console.print("[bright_green]Done[/]")


@app.callback()
def callback():
    """
    [dark_orange3]:warning:[/]  These commands are intended for development.  Use with caution.
    """
    pass


if __name__ == "__main__":
    app()
