#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import typer
from typing import Annotated, Optional
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

from centralcli.clioptions import CLIOptions

app = typer.Typer()
console = Console(emoji=False)
opts = CLIOptions()


@app.command()
def configs(
    yes: Annotated[Optional[bool], typer.Option("-Y", help="Bypass confirmation prompts - Assume Yes")] = False,
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
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
