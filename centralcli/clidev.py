#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, config
    else:
        print(pkg_dir.parts)
        raise e

from .typedefs import StrPath

app = typer.Typer()
color = utils.color


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

    if not file.exists():
        new_msg = "" if not new.exists() else f" and [dark_olive_green2]{new.name}[/] already exists."
        cli.exit(f"[cyan]{file.name}[/] [red]not found[/]{new_msg} in {file.parent}. Nothing to do.\nAborting...")

    if conf_msg:
        cli.econsole.print(conf_msg)
    if yes is not None:
        cli.confirm(yes)

    new = file.rename(new)
    if new.exists():
        cli.console.print("[bright_green]Success[/]")
    else:
        cli.exit(f"Something may have gone wrong.  {new} doesn't appear to exist.")

    return new


@app.command()
def no_config(
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
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
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Configure [cyan]cencli[/] as if there is no cache.

    Adds (renames) cache file appending .bak to the file name.

    So cencli can be tested as if no cache exists.
    """
    conf_msg = f"Stash existing cache [cyan]{config.cache_file}[/] to [dark_olive_green2]{config.cache_file}.bak[/]"
    toggle_bak_file(config.cache_file, conf_msg=conf_msg, yes=yes)


@app.command()
def restore_cache(
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Restore previously stashed [cyan]cencli[/] cache file.

    Restores cache previously stashed with [cyan]cencli dev no-cache[/]
    """
    cache_bak = Path(f"{str(config.cache_file)}.bak")
    conf_msg = f"Restoring [cyan]cencli[/] cache from [cyan]{cache_bak.name}[/]..."
    toggle_bak_file(cache_bak, conf_msg=conf_msg)


@app.callback()
def callback():
    """
    [dark_orange3]:warning:[/]  These commands are intended for development.  Use with caution.
    """
    pass


if __name__ == "__main__":
    app()
