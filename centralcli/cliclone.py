#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer


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


@app.command(short_help="Clone a group")
def group(
    clone_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CLONE]", autocompletion=cli.cache.group_completion),
    new_group: str = typer.Argument(..., metavar="[NAME OF GROUP TO CREATE]"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes

    _msg = f'{typer.style(f"Clone group", fg="cyan")}'
    _msg = f'{_msg} {typer.style(clone_group, fg="bright_green")}'
    _msg = f'{_msg} {typer.style("to new group", fg="cyan")}'
    _msg = f'{_msg} {typer.style(new_group, fg="bright_green")}'
    _msg = f'{_msg}{typer.style("?", fg="cyan")}'

    if yes or typer.confirm(_msg):
        resp = cli.central.request(cli.central.clone_group, clone_group, new_group)
        cli.display_results(resp)


@app.callback()
def callback():
    """
    Clone Aruba Central Groups
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
