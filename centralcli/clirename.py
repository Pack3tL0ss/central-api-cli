#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, cliupdate
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, cliupdate
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars # noqa

iden = IdenMetaVars()
app = typer.Typer()


@app.command()
def site(
    site: str = typer.Argument(..., metavar=iden.site, autocompletion=cli.cache.site_completion, show_default=False,),
    new_name: str = typer.Argument(..., show_default=False,),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
) -> None:
    """
    :office: [bright_green]Rename A Site.[/] :office:
    """

    site = cli.cache.get_site_identifier(site)
    print(f"Please Confirm: rename site [red]{site.name}[/red] -> [bright_green]{new_name}[/bright_green]")
    if yes or typer.confirm("proceed?", abort=True):
        print()
        cliupdate.site(site.name, address=None, city=None, state=None, zipcode=None, country=None, new_name=new_name, lat=None, lon=None, yes=True, default=default, account=account)


@app.command()
def ap(
    ap: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    new_name: str = typer.Argument(..., show_default=False,),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
) -> None:
    """
    [bright_green]Rename an Access Point[/]
    """
    ap = cli.cache.get_dev_identifier(ap, dev_type="ap")
    print(f"Please Confirm: rename ap [bright_red]{ap.name}[/] -> [bright_green]{new_name}[/]")
    print("    [italic]Will result in 2 API calls[/italic]\n")
    if yes or typer.confirm("Proceed?", abort=True):
        resp = cli.central.request(cli.central.update_ap_settings, ap.serial, new_name)
        cli.display_results(resp, tablefmt="action")


@app.command()
def group(
    group: str = typer.Argument(..., metavar=iden.group, autocompletion=cli.cache.group_completion, show_default=False,),
    new_name: str = typer.Argument(..., show_default=False,),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
) -> None:
    """
    [green3]Rename a group.[/] [red]AOS8 Only use clone for AOS10 groups[/]

    :pile_of_poo:[red]WARNING: the API endpoint has limited scope where this command will work.[/]:pile_of_poo:
    :pile_of_poo:[red]Clone (or build a new group) are the only options if it does not work.[/]:pile_of_poo:
    """
    yes = yes_ if yes_ else yes
    group = cli.cache.get_group_identifier(group)

    print(f"Please Confirm: rename group [red]{group.name}[/red] -> [bright_green]{new_name}[/bright_green]")
    if yes or typer.confirm("proceed?", abort=True):
        resp = cli.central.request(cli.central.update_group_name, group.name, new_name)

        # API-FLAW Doesn't actually appear to be valid for any group type
        if not resp and "group already has AOS_10X version set" in resp.output.get("description", ""):
            resp.output["description"] = f"{group.name} is an AOS_10X group, " \
                "rename only supported on AOS_8X groups. Use clone."

        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Rename Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()