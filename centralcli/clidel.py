#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List
import sys
import typer
import asyncio

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log
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
    sites: List[str] = typer.Argument(..., help="Site(s) to delete (can provide more than one)."),  # metavar=IdenMetaVars.site),
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
    sites = [cli.cache.get_site_identifier(s) for s in sites]

    _del_msg = [
        f"  {typer.style(s.name, fg='reset')}" for s in sites
    ]
    if len(_del_msg) > 7:
        _del_msg = [*_del_msg[0:3], "  ...", *_del_msg[-3:]]
    _del_msg = "\n".join(_del_msg)
    confirm_1 = typer.style("About to", fg="cyan")
    confirm_2 = typer.style("Delete:", fg="bright_red")
    confirm_3 = f'{typer.style(f"Confirm", fg="cyan")} {typer.style(f"delete", fg="red")}'
    confirm_3 = f'{confirm_3} {typer.style(f"{len(sites)} sites?", fg="cyan")}'
    _msg = f"{confirm_1} {confirm_2}\n{_del_msg}\n{confirm_3}"

    if yes or typer.confirm(_msg, abort=True):
        del_list = [s.id for s in sites]
        resp = cli.central.request(cli.central.delete_site, del_list)
        cli.display_results(resp)
        if resp:
            cache_del_res = asyncio.run(cli.cache.update_site_db(data=del_list, remove=True))
            if len(cache_del_res) != len(del_list):
                log.warning(
                    f"Attempt to delete entries from Site Cache returned {len(cache_del_res)} "
                    f"but we tried to delete {len(del_list)}",
                    show=True
                )


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
        if resp:
            asyncio.run(cli.cache.update_group_db(data=[{"name": g.name} for g in groups], remove=True))


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
