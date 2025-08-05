#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import typer
from rich.markup import escape

from centralcli import BatchRequest, cli, utils
from centralcli.cache import api
from centralcli.constants import CancelWhat, DevTypes, what_to_pretty

app = typer.Typer()

@app.command()
def upgrade(
    what: CancelWhat = cli.arguments.what,
    dev_or_group: list[str] = typer.Argument(..., help="device(s) or group(s) to cancel upgrade", autocompletion=cli.cache.group_dev_completion, show_default=False,),
    dev_type: DevTypes = typer.Option(None, help=f"[dim red]{escape('[required]')}[/] when Canceling group upgrade.", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    workspace: str = cli.options.workspace,
) -> None:
    """Cancel a previously initiated firmware upgrade."""
    if what == "device":
        devs = [cli.cache.get_dev_identifier(dev, conductor_only=True) for dev in dev_or_group]
        confirm_msg = f'Cancel [cyan]Upgrade[/] on [cyan]{utils.color([d.name for d in devs], "cyan")}[/]'
        reqs = []
        for dev in devs:
            if dev.type == "ap" and dev.is_aos10:
                kwargs = {"swarm_id": dev.swack_id}
            else:
                kwargs = {"serial": dev.serial}
            reqs += [BatchRequest(api.firmware.cancel_upgrade, **kwargs)]
    elif what == "group":
        if not dev_type:
            cli.exit("[cyan]--dev-type must be specified when cancelling group upgrade.")
        groups = [cli.cache.get_group_identifier(group) for group in dev_or_group]
        confirm_msg = f'[red]Cancel[/] Upgrade on [cyan]{what_to_pretty(dev_type)}[/] in group [cyan]{utils.color([g.name for g in groups], "cyan")}[/]'
        reqs = [
            BatchRequest(api.firmware.cancel_upgrade, group=group.name, device_type=dev_type.value)
            for group in groups
        ]
    else:  # swarm
        devs = [cli.cache.get_dev_identifier(dev, swack=True) for dev in dev_or_group]
        confirm_msg = f'Cancel [cyan]Upgrade[/] on swarm associated with [cyan]{utils.color([d.name for d in devs], "cyan")}[/]'
        swarm_ids = list(set([d.swack_id for d in devs if d.swack_id is not None]))
        reqs = [
            BatchRequest(api.firmware.cancel_upgrade, swarm_id=swarm)
            for swarm in swarm_ids
        ]

    cli.econsole.print(confirm_msg)
    if cli.confirm(yes):
        batch_resp = api.session.batch_request(reqs)
        cli.display_results(batch_resp, tablefmt="action")


@app.callback()
def callback():
    """
    Cancel previously initiated firmware upgrade
    """
    pass


if __name__ == "__main__":
    app()
