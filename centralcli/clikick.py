#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import typer
from rich import print


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

from centralcli.constants import iden_meta
from .cache import CacheClient
from .models import Clients

app = typer.Typer()

@app.command(short_help="Disconnect all WLAN clients from an AP optionally for a specific SSID",)
def all(
    device: str = typer.Argument(
        ...,
        metavar=iden_meta.dev,
        help="The AP to disconnect clients from",
        autocompletion=cli.cache.dev_ap_completion,
        show_default=False,
    ),
    ssid: str = typer.Option(None, help="Kick all users connected to a specific SSID", show_default=None),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Disconnect all WLAN clients from an AP optionally for a specific SSID

    This command currently only applies to APs
    """
    dev = cli.cache.get_dev_identifier(device)
    _ssid_msg = "" if not ssid else f" on SSID [cyan]{ssid}[/]"
    print(f'Kick [bright_red]ALL[/] users connected to [cyan]{dev.name}[/]{_ssid_msg}')
    if cli.confirm(yes):
        resp = cli.central.request(
            cli.central.kick_users,
            dev.serial,
            kick_all=True,
            ssid=ssid
            )
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Disconnect a WLAN client",)
def client(
    client: str = typer.Argument(..., metavar=iden_meta.client, autocompletion=cli.cache.client_completion, show_default=False),
    refresh: bool = typer.Option(False, "--refresh", "-R", help="Cache is used to determine what AP the client is connected to, which could be [red]stale[/]. This forces a cache update."),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Disconnect a WLAN client.

    This command relies on [cyan]cached[/] client data to determine the AP the client is connected to.
    The cache is updated anytime a [cyan]show clients ...[/] is ran, or automatically if the client
    is not found in the cache.

    The [cyan]-R[/] flag can be used to force a cache refresh prior to performing the disconnect.
    """
    if refresh:
        resp = cli.central.request(cli.cache.refresh_client_db, client_type="wireless")
        if not resp:
            cli.display_results(resp, exit_on_fail=True)

    client: CacheClient = cli.cache.get_client_identifier(client, exit_on_fail=True)
    if not client.last_connected:
        if refresh:
            cli.exit(f"Client {client} is not connected.")
        else:
            client_resp = cli.central.request(cli.cache.refresh_client_db, mac=client.mac)
            if not client_resp:
                cli.econsole.print(f"client {client} is not online according to cache, Failure occured attempting to fetch client details from API.")
                cli.display_results(client_resp, exit_on_fail=True)

            _clients = [CacheClient(c) for c in Clients(client_resp.output)]
            online_client =  [c for c in _clients if c.last_connected is not None]
            if online_client:
                client = online_client[-1]
            else:
                client = _clients[-1]
                cli.exit(f"Client {client} is not online: Failure Stage: {client_resp.output[-1].get('failure_stage', '')}, Reason: {client_resp.output[-1].get('failure_reason', '')}")

    print(f'Kick client [cyan]{client.name}[/], currently connected to [cyan]{client.connected_name}[/]')
    if cli.confirm(yes):
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
