#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List
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


@app.command(short_help="Delete a certificate")
def certificate(
    name: str = typer.Argument(..., ),
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
    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("Delete", fg="bright_red")
    confirm_3 = typer.style(f"certificate {name}", fg="cyan")
    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3}"):
        resp = cli.central.request(cli.central.delete_certificate, name)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Delete a site")
def site(
    name: str = typer.Argument(...,),  # metavar=IdenMetaVars.site),
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
    site = cli.cache.get_site_identifier(name)
    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("Delete", fg="bright_red")
    confirm_3 = typer.style(f"site {name}", fg="cyan")
    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3}"):
        resp = cli.central.request(cli.central.delete_site, site.id)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Delete group(s)")
def group(
    groups: List[str] = typer.Argument(..., help="Group to delete (can provide more than one)."),
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
    groups = [cli.cache.get_group_identifier(g) for g in groups]
    reqs = [cli.central.BatchRequest(cli.central.delete_group, (g.name, )) for g in groups]

    _delim = typer.style(", ", fg="cyan")
    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("Delete", fg="bright_red")
    confirm_3 = typer.style("group" if len(groups) == 1 else "groups", fg="cyan")
    confirm_4 = f'{_delim.join(typer.style(g.name, fg="bright_green") for g in groups)}{typer.style("?", fg="cyan")}'

    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3} {confirm_4}"):
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp)


@app.command(short_help="Delete a WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]"),  # metavar=IdenMetaVars.site),
    name: str = typer.Argument(..., metavar="[WLAN NAME]"),  # metavar=IdenMetaVars.site),
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
    group = cli.cache.get_group_identifier(group)
    confirm_1 = typer.style("Please Confirm:", fg="cyan")
    confirm_2 = typer.style("Delete", fg="bright_red")
    confirm_3 = typer.style(f"Group {group.name}, WLAN {name}", fg="cyan")
    if yes or typer.confirm(f"{confirm_1} {confirm_2} {confirm_3}"):
        resp = cli.central.request(cli.central.delete_wlan, group.name, name)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.callback()
def callback():
    """
    Delete Aruba Central Objects.
    """
    pass


if __name__ == "__main__":
    app()
else:
    if len(sys.argv) > 2 and sys.argv[1] == 'delete':
        if sys.argv[2] == "sites":
            sys.argv[2] = "site"
        if sys.argv[2] == "groups":
            sys.argv[2] = "group"
        elif sys.argv[2] in ["certificates", "certs", "cert"]:
            sys.argv[2] = "certificate"
