#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from enum import Enum
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, cli, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, cli, Response
    else:
        print(pkg_dir.parts)
        raise e

tty = utils.tty
app = typer.Typer()


class BatchArgs(str, Enum):
    sites = "sites"
    aps = "aps"


def do_lldp_rename(fstr: str) -> Response:
    pass


@app.command()
def add(
    what: BatchArgs = typer.Argument(...,),
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
) -> None:
    """Perform batch Add operations using import data from file."""
    central = cli.central
    data = config.get_file_data(import_file)

    resp = None
    if what == "sites":
        if import_file.suffix in [".csv", ".tsv", ".dbf", ".xls", ".xlsx"]:
            # TODO Exception handler
            if "address" in str(data.headers) and len(data.headers) > 3:  # address info
                data = [
                    {
                        "site_name": i.get("site_name", i.get("site", "ERROR")),
                        "site_address": {k: v for k, v in i.items() if k not in ["site", "site_name"]}
                    }
                    for i in data.dict
                ]
            else:  # geoloc
                data = [
                    {
                        "site_name": i.get("site_name", i.get("site", "ERROR")),
                        "geolocation": {k: v for k, v in i.items() if k not in ["site", "site_name"]}
                    }
                    for i in data.dict
                ]

        resp = central.request(central.create_site, site_list=data)

    cli.display_results(resp)


@app.command()
def rename(
    what: BatchArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(None, exists=True),
    lldp: bool = typer.Option(None, help="Automatic AP rename based on lldp info from upstream switch.",),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
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
) -> None:
    """Perform AP rename in batch from import file or automatically based on LLDP"""
    central = cli.central
    if import_file:
        data = config.get_file_data(import_file)

        resp = None
        if what == "aps":
            if import_file.suffix in [".csv", ".tsv", ".dbf", ".xls", ".xlsx"]:
                if data and len(data.headers) < 3:
                    if "name" in data.headers:
                        data = [{k if k != "name" else "hostname": d[k] for k in d} for d in data.dict]
                        data.headers["hostname"] = data.headers.pop(
                            data.headers.index(data.headers["name"])
                        )
                    data = {
                        i.get("serial", i.get("serial_number", i.get("serial_num", "ERROR"))):
                        {k: v for k, v in i.items() if not k.startswith("serial")} for i in data.dict
                    }
            calls = []
            for ap in data:
                calls.append(central.BatchRequest(central.update_ap_settings, (ap,), data[ap]))

            resp = central.batch_request(calls)

    elif lldp:
        rtxt = typer.style("RESULT: ", fg=typer.colors.BRIGHT_BLUE)
        typer.secho("Rename APs based on LLDP:", fg="bright_green")
        typer.echo(
            "This function will automatically rename APs based on a combination of\n"
            "information from the upstream switch (via LLDP) and from the AP itself.\n\n"
            "Please provide a format string based on these examples:\n"
            "  For the examples: hostname 'SNANTX-IDF3-sw1, AP on port 7\n"
            "                    AP mac aa:bb:cc:dd:ee:ff\n"
            f"{typer.style('Format String Examples:', fg='cyan')}\n"
            "  Upstream switches hostname: \n"
            "      '%h[1:4]%'    will use the first 3 characters of the switches hostname.\n"
            f"         {rtxt} 'SNAN'\n"
            "      '%H-1%'    will split the hostname into parts separating on '-' and use\n"
            f"         the firt segment.  {rtxt} 'SNANTX\n"
            f"      '%p%'    represents the interface.  {rtxt} '7'\n"
            "                   note: an interface in the form 1/1/12 is converted to 1_1_12\n"
            "       '%p/3%    seperates the port string on / and uses the 3rd segment.\n"
            "        '%m% or %m[-4] = last 4 digits of the AP MAC\n"
            "        '%m:1% would split on : and take the 1st segment.\n"
        )
        fstr = typer.prompt("Enter Desired format string:")
        do_lldp_rename(fstr)
    else:
        typer.secho("import file Argument is required if --lldp flag not provided", fg="red")

    cli.display_results(resp)


@app.callback()
def callback():
    """
    Perform batch operations.
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()
