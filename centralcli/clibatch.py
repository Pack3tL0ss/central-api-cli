#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from enum import Enum
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, cli
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, cli
    else:
        print(pkg_dir.parts)
        raise e

tty = utils.tty
app = typer.Typer()


class BatchArgs(str, Enum):
    sites = "sites"
    # groups = "groups"


@app.command()
def add(
    what: BatchArgs = typer.Argument(
        ...,
    ),
    import_file: Path = typer.Argument(..., exists=True),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", callback=cli.default_callback),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", callback=cli.debug_callback
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        callback=cli.account_name_callback,
    ),
    command: str = None,
    key: str = None,
) -> None:
    """Perform batch Add operations using import data from file."""
    central = cli.central
    data = config.get_file_data(import_file)

    resp = None
    if what == "sites":
        if import_file.suffix in [".csv", ".tsv", ".dbf", ".xls", ".xlsx"]:
            # TODO do more than this quick and dirty data validation.
            if data and len(data.headers) > 3:  # address info
                data = [
                    {"site_name": i["site_name"], "site_address": {k: v for k, v in i.items() if k != "site_name"}}
                    for i in data.dict
                ]
            else:  # geoloc
                data = [
                    {"site_name": i["site_name"], "geolocation": {k: v for k, v in i.items() if k != "site_name"}}
                    for i in data.dict
                ]

        resp = central.request(central.create_site, site_list=data)

    resp_data = cli.eval_resp(resp)
    cli.display_results(resp_data)


@app.callback()
def callback():
    """
    Perform batch operations using data from import file.
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()
