#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

import typer
from rich import print

from centralcli import cleaner, common, render
from centralcli.clicommon import APIClients
from centralcli.constants import IdenMetaVars, SortTsCmdOptions, TSDevTypes, lib_to_api  # noqa

api_clients = APIClients()
api = api_clients.classic

app = typer.Typer()

iden_meta = IdenMetaVars()


@app.command()
def results(
    device: str = common.arguments.device,
    session_id: str = typer.Argument(
        None,
        help="The session id of a previously run troubleshooting session",
        show_default=False,
    ),
    clean: bool = typer.Option(
        False,
        "--clean",
        help="Clean response, don't send through any formatters.  [grey42 italic]Useful for excessively long output[/]",
        show_default=False,
    ),
    outfile: Path = common.options.outfile,
    pager: bool = common.options.pager,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """
    Show Troubleshooting results from a previously run troubleshooting session.

    Use [cyan]cencli tshoot...[/] to start a troubleshooting session.

    """
    dev = common.cache.get_dev_identifier(device)

    # Fetch session ID if not provided
    if not session_id:
        resp = api.session.request(api.tshooting.get_ts_session_id, dev.serial)
        if resp.ok and "session_id" in resp.output:
            session_id = resp.output["session_id"]
        else:
            print(f"No session id provided, unable to find active session id for {dev.name}")
            render.display_results(resp, exit_on_fail=True)

    title = f"Troubleshooting output for {dev.name} session {session_id}"

    resp = api.session.request(api.tshooting.get_ts_output, dev.serial, session_id=session_id)
    if not resp or resp.output.get("status", "") != "COMPLETED":
        render.display_results(resp, title=title, tablefmt="rich",)
    else:
        if "output" in resp.output:
            _output = resp.output["output"]
            del resp.output["output"]
            render.display_results(resp, tablefmt="action")
            resp.output = _output

        render.display_results(resp, pager=pager, outfile=outfile, tablefmt="simple" if not clean else "clean")


@app.command()
def commands(
    device_type: TSDevTypes = typer.Argument(..., metavar=iden_meta.dev_types_w_mas, show_default=False,),
    sort_by: SortTsCmdOptions = common.options.sort_by,
    reverse: bool = common.options.reverse,
    pager: bool = common.options.pager,
    default: bool = common.options.default,
    debug: bool = common.options.debug,
    workspace: str = common.options.workspace,
) -> None:
    """
    Show available troubleshooting commands for a given device type.

    Use [cyan]cencli ts ...[/] to start a troubleshooting session.
    """
    if sort_by == "id":
        sort_by = None
    dev_type = lib_to_api(device_type, "tshoot")

    resp = api.session.request(api.tshooting.get_ts_commands, device_type=dev_type,)
    render.display_results(resp, sort_by=sort_by, reverse=reverse, cleaner=cleaner.show_ts_commands)


@app.callback()
def callback():
    """
    Show troubleshooting session details or available commands
    """
    pass


if __name__ == "__main__":
    app()
