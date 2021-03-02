#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from pathlib import Path
from enum import Enum
import sys
from typing import List
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, utils, cli, log, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, utils, cli, log, Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars


iden_meta_vars = IdenMetaVars()
tty = utils.tty
app = typer.Typer()


class BatchArgs(str, Enum):
    sites = "sites"
    aps = "aps"


class BatchDelArgs(str, Enum):
    sites = "sites"
    # aps = "aps"


class FstrInt:
    def __init__(self, val: int) -> None:
        self.i = val
        self.o = val + 1

    def __len__(self):
        return len(str(self.i))


def _get_full_int(val: List[str]) -> FstrInt:
    rv = []
    while True:
        for i in val:
            if i.isdigit():
                rv += [i]
            else:
                return FstrInt(int("".join(rv)) - 1)


def _lldp_rename_get_fstr():
    rtxt = typer.style("RESULT: ", fg=typer.colors.BRIGHT_BLUE)
    while True:
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
            "  '%m' The MAC of the AP NOTE: delimiters ':' are stripped from MAC\n"
            "  '%m[-4]'  The last 4 digits of the AP MAC\n"
            f"    {rtxt} 'eeff'\n\n"
            f"{typer.style('Examples:', fg='bright_green')}\n"
            f"  %h-1-AP%M-%m[-4]  {rtxt} SNAN-AP535-eeff\n"
            f"  %h[1-4]-%h-2%h-3.p%p.%M-ap  {rtxt} SNAN-IDF3sw1.p7.535-ap\n"
            f"  %h-1-%M.%m[-4]-ap  {rtxt} SNAN-535.eeff-ap\n"

        )
        fstr = typer.prompt("Enter Desired format string",)
        if "%%" in fstr:
            typer.clear()
            typer.secho(f"\n{fstr} appears to be invalid.  Should never be 2 consecutive '%'.\n", fg="red")
        else:
            return fstr


def do_lldp_rename(fstr: str, **kwargs) -> Response:
    resp = cli.central.request(cli.central.get_devices, "aps", status="Up", **kwargs)

    if not resp:
        cli.display_results(resp, exit_on_fail=True)
    elif not resp.output:
        filters = ", ".join([f"{k}: {v}" for k, v in kwargs.items()])
        resp.output = {
            "description": "API called was successful but returned no results.",
            "error": f"No Up APs found matching provided filters ({filters})."
        }
        resp.ok = False
        cli.display_results(resp, exit_on_fail=True)

    _all_aps = utils.listify(resp.output)
    _keys = ["name", "mac", "model"]
    ap_dict = {d["serial"]: {k: d[k] for k in d if k in _keys} for d in _all_aps}
    fstr_to_key = {
        "h": "neighborHostName",
        "m": "mac",
        "p": "remotePort",
        "M": "model"
    }
    req_list, name_list, shown_promt = [], [], False
    if ap_dict:
        for ap in ap_dict:
            ap_dict[ap]["mac"] = utils.Mac(ap_dict[ap]["mac"]).clean
            _lldp = cli.central.request(cli.central.get_ap_lldp_neighbor, ap)
            if _lldp:
                ap_dict[ap]["neighborHostName"] = _lldp.output[-1]["neighborHostName"]
                ap_dict[ap]["remotePort"] = _lldp.output[-1]["remotePort"]

            while True:
                st = 0
                x = ''
                try:
                    # TODO all int values assume 1 digit int.
                    for idx, c in enumerate(fstr):
                        if not idx >= st:
                            continue
                        if c == '%':
                            if fstr[idx + 1] not in fstr_to_key.keys():
                                _e1 = typer.style(
                                        f"Invalid source specifier ({fstr[idx + 1]}) in format string {fstr}: ",
                                        fg="red"
                                )
                                _e2 = "Valid values:\n{}".format(
                                    ", ".join(fstr_to_key.keys())
                                )
                                typer.echo(f"{_e1}\n{_e2}")
                                raise KeyError(f"{fstr[idx + 1]} is not valid")

                            _src = ap_dict[ap][fstr_to_key[fstr[idx + 1]]]
                            if fstr[idx + 2] != "[":
                                if fstr[idx + 2] == "%" or fstr[idx + 3] == "%":
                                    x = f'{x}{_src}'
                                    st = idx + 2
                                else:
                                    try:
                                        fi = _get_full_int(fstr[idx + 3:])
                                        x = f'{x}{_src.split(fstr[idx + 2])[fi.i]}'
                                        st = idx + 3 + len(fi)
                                    except IndexError:
                                        _e1 = ", ".join(_src.split(fstr[idx + 2]))
                                        _e2 = len(_src.split(fstr[idx + 2]))
                                        typer.secho(
                                            f"\nCan't use segment {fi.o} of '{_e1}'\n"
                                            f"  It only has {_e2} segments.\n",
                                            fg="red"
                                        )
                                        raise
                            else:  # +2 is '['
                                if fstr[idx + 3] == "-":
                                    try:
                                        fi = _get_full_int(fstr[idx + 4:])
                                        x = f'{x}{"".join(_src[-fi.o:])}'
                                        st = idx + 4 + len(fi) + 1  # +1 for closing ']'
                                    except IndexError:
                                        typer.secho(
                                            f"Can't extract the final {fi.o} characters from {_src}"
                                            f"It's only {len(_src)} characters."
                                        )
                                        raise
                                else:  # +2 is '[' +3: should be int [1:4]
                                    fi = _get_full_int(fstr[idx + 3:])
                                    fi2 = _get_full_int(fstr[idx + 3 + len(fi) + 1:])  # +1 for expected ':'
                                    if len(_src[slice(fi.i, fi2.o)]) < fi2.o - fi.i:
                                        _e1 = typer.style(
                                            f"\n{fstr} wants to take characters "
                                            f"\n{fi.o} through {fi2.o}"
                                            f"\n\"from {_src}\" (slice ends at character {len(_src[slice(fi.i, fi2.o)])}).",
                                            fg="red"
                                        )
                                        if not shown_promt and typer.confirm(
                                            f"{_e1}"
                                            f"\n\nResult will be \""
                                            f"{typer.style(''.join(_src[slice(fi.i, fi2.o)]), fg='bright_green')}\""
                                            " for this segment."
                                            "\nOK to continue?"
                                        ):
                                            shown_promt = True
                                            x = f'{x}{"".join(_src[slice(fi.i, fi2.o)])}'
                                            st = idx + 3 + len(fi) + len(fi2) + 2  # +2 for : and ]
                                        else:
                                            raise typer.Abort()
                        else:
                            x = f'{x}{c}'
                    req_list += [cli.central.BatchRequest(cli.central.update_ap_settings, (ap, x))]
                    name_list += [f"  {x}"]
                    break
                except typer.Abort:
                    fstr = _lldp_rename_get_fstr()
                except Exception as e:
                    log.exception(f"LLDP rename exception while parsing {fstr}\n{e}", show=log.DEBUG)
                    typer.secho(f"\nThere Appears to be a problem with {fstr}: {e.__class__.__name__}", fg="red")
                    if typer.confirm("Do you want to edit the fomat string and try again?", abort="True"):
                        fstr = _lldp_rename_get_fstr()

    typer.secho(f"Resulting AP names based on '{fstr}':", fg="bright_green")
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

    if typer.confirm("Proceed with AP Rename?", abort=True):
        return cli.central.batch_request(req_list)


@app.command()
def add(
    what: BatchArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(..., exists=True),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", callback=cli.default_callback, show_default=False
    ),
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
    yes = yes_ if yes_ else yes
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
        site_names = [
            d.get("site_name", "ERROR") for d in data
        ]
        if len(site_names) > 7:
            site_names = [*site_names[0:3], "...", *site_names[-3:]]
        _msg = [
            typer.style("Batch Add Sites:", fg="cyan"),
            typer.style(
                "\n".join([typer.style(f'  {n}', fg="bright_green" if n != "..." else "reset") for n in site_names])
            ),
            typer.style("Proceed with Site Additions?", fg="cyan")
        ]
        _msg = "\n".join(_msg)
        if yes or typer.confirm(_msg, abort=True):
            resp = central.request(central.create_site, site_list=data)
            if resp:
                cache_data = [{k.replace("site_", ""): v for k, v in d.items()} for d in resp.output]
                cache_res = asyncio.run(cli.cache.update_site_db(data=cache_data))
                if len(cache_res) != len(data):
                    log.warning(
                        "Attempted to add entries to Site Cache after batch import.  Cache Response "
                        f"{len(cache_res)} but we added {len(data)} sites.",
                        show=True
                    )

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
                i = {"site_name": i, **data[i]} if "name" not in i and "site_name" not in i else data[i]

            if "site_id" not in i and "id" not in i:
                if "site_name" in i or "name" in i:
                    _name = i.get("site_name", i.get("name"))
                    _id = cli.cache.get_site_identifier(_name).id
                    found = True
                    _msg_list += [_name]
                    del_list += [_id]
            else:
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

        if len(_msg_list) > 7:
            _msg_list = [*_msg_list[0:3], "...", *_msg_list[-3:]]
        typer.secho("\nSites to delete:", fg="bright_green")
        typer.echo("\n".join([f"  {m}" for m in _msg_list]))
        if yes or typer.confirm(f"\n{typer.style('Delete', fg='red')} {len(del_list)} sites", abort=True):
            resp = central.request(central.delete_site, del_list)
            if resp:
                cache_del_res = asyncio.run(cli.cache.update_site_db(data=del_list, remove=True))
                if len(cache_del_res) != len(del_list):
                    log.warning(
                        f"Attempt to delete entries from Site Cache returned {len(cache_del_res)} "
                        f"but we tried to delete {len(del_list)} sites.",
                        show=True
                    )

    cli.display_results(resp)


@app.command()
def rename(
    what: BatchArgs = typer.Argument(...,),
    import_file: Path = typer.Argument(None, metavar="['lldp'|IMPORT FILE PATH]"),
    lldp: bool = typer.Option(None, help="Automatic AP rename based on lldp info from upstream switch.",),
    ap: str = typer.Option(None, metavar=iden_meta_vars.dev, help="[LLDP rename] Perform on specified AP",),
    label: str = typer.Option(None, help="[LLDP rename] Perform on APs with specified label",),
    group: str = typer.Option(None, help="[LLDP rename] Perform on APs in specified group",),
    site: str = typer.Option(None, metavar=iden_meta_vars.site, help="[LLDP rename] Perform on APs in specified site",),
    model: str = typer.Option(None, help="[LLDP rename] Perform on APs of specified model",),
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
    yes = yes_ if yes_ else yes

    if str(import_file).lower() == "lldp":
        lldp = True
        import_file = None

    central = cli.central
    if import_file:
        if not import_file.exists():
            typer.secho(f"Error: {import_file} not found.", fg="red")
            raise typer.Exit(1)

        data = config.get_file_data(import_file)

        resp = None
        if what == "aps":
            # transform flat csv struct to dict with dict with AP serials as keys
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

            calls, conf_msg = [], [typer.style("Names Gathered from import:", fg="bright_green")]
            for ap in data:  # serial num
                conf_msg += [f"  {ap}: {data[ap]['hostname']}"]
                calls.append(central.BatchRequest(central.update_ap_settings, (ap,), data[ap]))

            if len(conf_msg) > 6:
                conf_msg = [*conf_msg[0:3], "...", *conf_msg[-3:]]
            typer.echo("\n".join(conf_msg))

            if yes or typer.confirm("Proceed with AP rename?", abort=True):
                resp = central.batch_request(calls)

    elif lldp:
        kwargs = {}
        if group:
            kwargs["group"] = cli.cache.get_group_identifier(group).name
        if ap:
            kwargs["serial"] = cli.cache.get_dev_identifier(ap, dev_type="ap").serial
        if site:
            kwargs["site"] = cli.cache.get_site_identifier(site).name
        if model:
            kwargs["model"] = model
        if label:
            kwargs["label"] = label

        resp = do_lldp_rename(_lldp_rename_get_fstr(), **kwargs)
    else:
        typer.secho("import file Argument is required if --lldp flag not provided", fg="red")

    cli.display_results(resp, exit_on_fail=True)


@app.callback()
def callback():
    """
    Perform batch operations.
    """
    pass


if __name__ == "__main__":
    app()
