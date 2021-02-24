#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from enum import Enum
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, utils, cli, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, utils, cli, Response
    else:
        print(pkg_dir.parts)
        raise e

tty = utils.tty
app = typer.Typer()


class BatchArgs(str, Enum):
    sites = "sites"
    aps = "aps"


class BatchDelArgs(str, Enum):
    sites = "sites"
    # aps = "aps"


def do_lldp_rename(fstr: str) -> Response:
    _all_aps = cli.central.request(cli.central.get_devices, "aps", status="Up")
    _keys = ["name", "mac", "model"]
    _all_aps = utils.listify(_all_aps)
    ap_dict = {d["serial"]: {k: d[k] for k in d.output if k in _keys} for d in _all_aps}
    fstr_to_key = {
        "h": "neighborHostName",
        "m": "mac",
        "p": "remotePort",
        "M": "model"
    }
    req_list, name_list = [], []
    if ap_dict:
        for ap in ap_dict:
            ap_dict[ap]["mac"] = utils.Mac(ap_dict[ap]["mac"]).clean
            _lldp = cli.central.request(cli.central.get_ap_lldp_neighbor, ap)
            if _lldp:
                ap_dict[ap]["neighborHostName"] = _lldp.output[-1]["neighborHostName"]
                ap_dict[ap]["remotePort"] = _lldp.output[-1]["remotePort"]

            st = 0
            x = ''
            # TODO all int values assume 1 digit int.
            for idx, c in enumerate(fstr):
                if not idx >= st:
                    continue
                if c == '%':
                    _src = ap_dict[ap][fstr_to_key[fstr[idx + 1]]]
                    if fstr[idx + 2] != "[":
                        if fstr[idx + 2] == "%" or fstr[idx + 3] == "%":
                            x = f'{x}{_src}'
                            st = idx + 2
                        else:
                            x = f'{x}{_src.split(fstr[idx + 2])[int(fstr[idx + 3]) - 1]}'
                            st = idx + 4
                    else:
                        if fstr[idx + 3] == "-":
                            x = f'{x}{"".join(_src[-int(fstr[idx + 4]):])}'
                            st = idx + 6
                        else:
                            x = f'{x}{"".join(_src[slice(int(fstr[idx + 3]) - 1, int(fstr[idx + 5]))])}'
                            st = idx + 7
                else:
                    x = f'{x}{c}'
            req_list += [cli.central.BatchRequest(cli.central.update_ap_settings, (ap, x))]
            name_list += [x]

    typer.secho(f"Resulting AP names based on '{fstr}':")
    if len(name_list) <= 6:
        typer.echo("\n".join(name_list))
    else:
        typer.echo("\n".join(
                [
                    *name_list[0:3],
                    "...",
                    *name_list[-3:]
                ]
            )
        )

    if typer.confirm("Proceed with AP Rename?"):
        return cli.central.batch_request(req_list)


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
                        "site_name": i.get("site_name", i.get("site", i.get("name"))),
                        "site_address": {k: v for k, v in i.items() if k not in ["site", "site_name"]}
                    }
                    for i in data.dict
                ]
            else:  # geoloc
                data = [
                    {
                        "site_name": i.get("site_name", i.get("site", i.get("name"))),
                        "geolocation": {k: v for k, v in i.items() if k not in ["site", "site_name"]}
                    }
                    for i in data.dict
                ]

        resp = central.request(central.create_site, site_list=data)

    cli.display_results(resp)


@app.command()
def delete(
    what: BatchDelArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(..., exists=True, readable=True),
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
    """Perform batch Delete operations using import data from file."""
    yes = yes_ if yes_ else yes
    central = cli.central
    data = config.get_file_data(import_file)
    if hasattr(data, "dict"):  # csv
        data = data.dict

    resp = None
    if what == "sites":
        del_list = []
        _msg_list = []
        for i in data:
            if isinstance(i, str) and isinstance(data[i], dict):
                i = {"name": i, **data[i]} if "name" not in i and "site_name" not in i else data[i]
            found = False
            for key in ["site_id", "id"]:
                if key in i:
                    del_list += [i[key]]
                    _msg_list += [i.get("site_name", i.get("site", i.get("name", f"id: {i[key]}")))]
                    found = True
                    break

            if not found:
                if i.get("site_name", i.get("site", i.get("name"))):
                    site = cli.cache.get_site_identifier(i.get("site_name", i.get("site", i.get("name"))))
                    _msg_list += [site.name]
                    del_list += [site.id]
                    break
                else:
                    typer.secho("Error getting site ids from import, unable to find required key", fg="red")
                    raise typer.Exit(1)

        typer.secho("\nSites to delete:", fg="bright_green")
        typer.echo("\n".join(_msg_list))
        if typer.confirm(f"\nDelete {len(del_list)} sites"):
            resp = central.request(central.delete_site, del_list)
        else:
            raise typer.Abort()

    cli.display_results(resp)
    cli.cache.check_fresh(site_db=True)


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
            "  This function will automatically rename APs based on a combination of\n"
            "  information from the upstream switch (via LLDP) and from the AP itself.\n\n"
            "    Values used in the examples below: \n"
            "      switch hostname (%h): 'SNAN-IDF3-sw1'\n"
            "      switch port (%p): 7\n"
            "      AP mac (%m): aa:bb:cc:dd:ee:ff\n"
            "      AP model (%M): 535\n\n"
            f"{typer.style('Format String Syntax:', fg='bright_green')}\n"
            "  '%h[1:2]'  will use the first 2 characters of the switches hostname.\n"
            f"    {rtxt} 'SN'\n"
            "  '%h[2:4]'  will use characters 2 through 4 of the switches hostname.\n"
            f"    {rtxt} 'NAN'\n"
            "  '%h-1'  will split the hostname into parts separating on '-' and use\n"
            "  the firt segment.\n"
            f"    {rtxt} 'SNAN\n"
            "  '%p'  represents the interface.\n"
            f"    {rtxt} '7'\n"
            "  '%p/3'  seperates the port string on / and uses the 3rd segment.\n"
            f"    {rtxt} (given port 1/1/7): '7'\n"
            f"  '%M'  represents the the AP model.\n"
            f"    {rtxt} '535'\n"
            "  '%m' The MAC of the AP\n"
            "  '%m[-4]'  The last 4 digits of the AP MAC\n"
            f"    {rtxt} 'eeff' NOTE: delimiters ':' are stripped\n\n"
            f"{typer.style('Examples:', fg='bright_green')}\n"
            f"  %h-1-AP%M-%m[-4]  {rtxt} SNAN-AP535-eeff\n"
            f"  %h[1-4]-%h-2%h-3.p%p.%M-ap  {rtxt} SNAN-IDF3sw1.p7.535-ap\n"

        )
        fstr = typer.prompt("Enter Desired format string")
        resp = do_lldp_rename(fstr)
    else:
        typer.secho("import file Argument is required if --lldp flag not provided", fg="red")

    cli.display_results(resp)


@app.callback()
def callback():
    """
    Perform batch operations.
    """
    pass


if __name__ == "__main__":
    app()
