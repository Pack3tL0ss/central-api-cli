#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer

from centralcli import common, render
from centralcli.cache import CacheClient, api
from centralcli.constants import iden_meta
from centralcli.models.cache import Clients

app = typer.Typer()

@app.command()
def all(
    device: str = common.arguments.get(
        "device",
        help="The AP to disconnect clients from",
        autocompletion=common.cache.dev_ap_completion,
    ),
    ssid: str = common.options.get("ssid", help="Kick all users connected to a specific SSID"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Disconnect all WLAN clients from an AP optionally for a specific SSID

    This command currently only applies to APs
    """
    dev = common.cache.get_dev_identifier(device)
    _ssid_msg = "" if not ssid else f" on SSID [cyan]{ssid}[/]"
    render.econsole.print(f'Kick [bright_red]ALL[/] users connected to [cyan]{dev.name}[/]{_ssid_msg}', emoji=False)
    render.confirm(yes)

    resp = api.session.request(
        api.device_management.kick_users,
        dev.serial,
        kick_all=True if not ssid else False,
        ssid=ssid
    )
    render.display_results(resp, tablefmt="action")


@app.command(short_help="Disconnect a WLAN client",)
def client(
    client: str = typer.Argument(..., metavar=iden_meta.client, autocompletion=common.cache.client_completion, show_default=False),
    refresh: bool = typer.Option(False, "--refresh", "-R", help="Cache is used to determine what AP the client is connected to, which could be [red]stale[/]. This forces a cache update."),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Disconnect a WLAN client.

    This command relies on [cyan]cached[/] client data to determine the AP the client is connected to.
    The cache is updated anytime a [cyan]show clients ...[/] is ran, or automatically if the client
    is not found in the cache.

    The [cyan]-R[/] flag can be used to force a cache refresh prior to performing the disconnect.
    """
    if refresh:
        resp = api.session.request(common.cache.refresh_client_db, client_type="wireless")
        if not resp:
            render.display_results(resp, exit_on_fail=True)

    client: CacheClient = common.cache.get_client_identifier(client, exit_on_fail=True)
    if not client.last_connected:
        if refresh:
            common.exit(f"Client {client} is not connected.")
        else:
            client_resp = api.session.request(common.cache.refresh_client_db, mac=client.mac)
            if not client_resp:
                render.econsole.print(f"[dark_orange3]:warning:[/]  {client.summary_text} is not online according to cache.\nThe following [red]failure[/] occured attempting to fetch current client details from API.\n")
                render.display_results(client_resp, exit_on_fail=True)

            _clients = [CacheClient(c) for c in Clients(client_resp.output)]
            online_client =  [c for c in _clients if c.last_connected is not None]
            if online_client:
                client = online_client[-1]
            else:
                client = _clients[-1]
                common.exit(f"Client {client} is not online: Failure Stage: {client_resp.output[-1].get('failure_stage', '')}, Reason: {client_resp.output[-1].get('failure_reason', '')}")

    render.econsole.print(f'Kick client [cyan]{client.name}[/], currently connected to [cyan]{client.connected_name}[/]', emoji=False)
    render.confirm(yes)
    resp = api.session.request(
        api.device_management.kick_users,
        client.connected_serial,
        mac=client.mac
    )
    render.display_results(resp, tablefmt="action")

@app.callback()
def callback():
    """
    Kick (disconnect) WLAN clients
    """
    ...


if __name__ == "__main__":
    app()
