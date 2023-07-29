#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print


# Detect if called from pypi installed package or via cloned github repo (development)
# TODO should be able to do this in __init__
try:
    from centralcli import cli, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils
    else:
        print(pkg_dir.parts)
        raise e
from centralcli.constants import IdenMetaVars

iden = IdenMetaVars()
app = typer.Typer()

@app.command(short_help="Disconnect all WLAN clients from an AP optionally for a specific SSID",)
def all(
    device: str = typer.Argument(
        ...,
        metavar=iden.dev,
        help="The AP to disconnect clients from",
        autocompletion=cli.cache.dev_ap_completion,
        show_default=False,
    ),
    ssid: str = typer.Option(None, help="Kick all users connected to a specific SSID", show_default=None),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Disconnect all WLAN clients from an AP optionally for a specific SSID

    This command currently only applies to APs
    """
    dev = cli.cache.get_dev_identifier(device)
    _ssid_msg = "" if not ssid else f" on SSID [cyan]{ssid}[/]"
    print(f'Kick [bright_red]ALL[/] users connected to [cyan]{dev.name}[/]{_ssid_msg}')
    if yes or typer.confirm("\nproceed?", abort=True):
        resp = cli.central.request(
            cli.central.kick_users,
            dev.serial,
            kick_all=True,
            ssid=ssid
            )
        cli.display_results(resp, tablefmt="action")


# TODO rather than drop option have cache remove users with last_connected > 30 days
@app.command(short_help="Disconnect a WLAN client",)
def client(
    client: str = typer.Argument(..., metavar=iden.client, autocompletion=cli.cache.client_completion, show_default=False),
    refresh: bool = typer.Option(False, "--refresh", "-R", help="Cache is used to determine what AP the client is connected to, which could be [red]stale[/]. This forces a cache update."),
    drop: bool = typer.Option(False, "--drop", "-D", help="(implies -R): Drop all users from existing cache, then refresh.  By default any user that has ever connected is retained in the cache."),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                autocompletion=cli.cache.account_completion),
) -> None:
    """Disconnect a WLAN client.

    This command relies on [cyan]cached[/] client data to determine the AP the client is connected to.
    The cache is updated anytime a [cyan]show clients ...[/] is ran, or automatically if the client
    is not found in the cache.

    The [cyan]-R[/] flag can be used to force a cache refresh prior to performing the disconnect.
    """
    if refresh or drop:
        resp = cli.central.request(cli.cache.update_client_db, "wireless", truncate=drop)
        if not resp:
            cli.display_results(resp, exit_on_fail=True)

    client = cli.cache.get_client_identifier(client, exit_on_fail=True)

    print(f'Kick client [cyan]{client.name}[/], currently connected to [cyan]{client.connected_name}[/]')
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(
            cli.central.kick_users,
            client.connected_serial,
            mac=client.mac
        )
        cli.display_results(resp, tablefmt="action")

@app.callback()
def callback():
    """
    Kick (disconnect) WLAN clients
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
