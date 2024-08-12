#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import typer
from rich import print
from rich.console import Console

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli
    else:
        print(pkg_dir.parts)
        raise e


app = typer.Typer()
console = Console(emoji=False)


@app.command()
def configs(
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Export configs in mass.

    i.e. Collect device level configs for all gateways in a given group or site.
    or collect all device level configs system wide (supported on APs and Gateways)
    """
    raise NotImplementedError("This command is still being built.")



@app.callback()
def callback():
    """
    Collect configs in mass
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
