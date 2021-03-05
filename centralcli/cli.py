#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
import sys
from pathlib import Path
from typing import List

import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import clibatch, clicaas, clido, clishow, clidel, cliadd, cliupdate, cliupgrade, cliclone, cli, log, ic
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import clibatch, clicaas, clido, clishow, clidel, cliadd, cliupdate, cliupgrade, cliclone, cli, log, ic
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi  # noqa
from centralcli.constants import RefreshWhat, IdenMetaVars, arg_to_what  # noqa
iden = IdenMetaVars()

CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())

app = typer.Typer()
app.add_typer(clishow.app, name="show",)
app.add_typer(clido.app, name="do",)
app.add_typer(clidel.app, name="delete")
app.add_typer(cliadd.app, name="add",)
app.add_typer(cliclone.app, name="clone",)
app.add_typer(cliupdate.app, name="update",)
app.add_typer(cliupgrade.app, name="upgrade",)
app.add_typer(clibatch.app, name="batch",)
app.add_typer(clicaas.app, name="caas", hidden=True,)


class MoveArgs(str, Enum):
    site = "site"
    group = "group"


@app.command(
    short_help="Move device(s) to a defined group and/or site",
    help="Move device(s) to a defined group and/or site.",
    context_settings=CONTEXT_SETTINGS,
)
def move(
    device: List[str, ] = typer.Argument(None, metavar=f"[{iden.dev} ...]", autocompletion=cli.cache.dev_completion,),
    kw1: str = typer.Argument(
        None,
        metavar="",
        show_default=False,
        hidden=True,
        autocompletion=cli.cache.completion,
        # cache=["site", "group"],
    ),
    kw1_val: str = typer.Argument(None, metavar="[site <SITE>]", show_default=False),
    kw2: str = typer.Argument(
        None, metavar="",
        show_default=False,
        hidden=True,
        autocompletion=cli.cache.completion,
        # cache=["site", "group"],
    ),
    kw2_val: str = typer.Argument(None, metavar="[group <GROUP>]", show_default=False, help="[site and/or group required]"),
    _group: str = typer.Option(
        None,
        "--group",
        help="Group to Move device(s) to",
        hidden=True,
        autocompletion=cli.cache.completion,
        # cache="group",
    ),
    _site: str = typer.Option(
        None, "--site",
        help="Site to move device(s) to",
        hidden=True,
        autocompletion=cli.cache.completion,
        # cache="site",
    ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
    # yes_: bool = typer.Option(False, "-y", hidden=True),
) -> None:
    central = cli.central
    # yes = yes_ if yes_ else yes

    group, site, = None, None
    for a, b in zip([kw1, kw2], [kw1_val, kw2_val]):
        if a == "group":
            group = b
        elif a == "site":
            site = b
        else:
            device += tuple([aa for aa in [a, b] if aa and aa not in ["group", "site"]])

    if not device:
        typer.echo("Error: Missing argument '[[name|ip|mac-address|serial] ...]'.")
        raise typer.Exit(1)

    group = group or _group
    site = site or _site

    if not group and not site:
        typer.secho("Missing Required Argument, group and/or site is required.")
        raise typer.Exit(1)

    dev = [cli.cache.get_dev_identifier(d) for d in device]
    devs_by_type = {
    }
    dev_all_names, dev_all_serials = [], []
    for d in dev:
        if d.generic_type not in devs_by_type:
            devs_by_type[d.generic_type] = [d]
        else:
            devs_by_type[d.generic_type] += [d]
        dev_all_names += [d.name]
        dev_all_serials += [d.serial]

    _s = "," if len(dev_all_names) > 2 else " &"
    _s = typer.style(_s, fg="bright_green")
    _msg_devs = f'{_s} '.join(typer.style(n, fg="reset") for n in dev_all_names)
    _msg_end = typer.style("?", fg="bright_green")
    _msg = None

    if group:
        _group = cli.cache.get_group_identifier(group)
        _msg = [
            typer.style("Please Confirm: move", fg="bright_green"),
            _msg_devs,
            typer.style("to group", fg="bright_green"),
            typer.style((_group.name), fg='reset'),
        ]
        _msg = f"{' '.join(_msg)}{_msg_end}"
    if site:
        _site = cli.cache.get_site_identifier(site)
        if not _msg:
            _msg = [
                typer.style("Please Confirm: move", fg="bright_green"),
                _msg_devs,
                typer.style("to site", fg="bright_green"),
                typer.style((_site.name), fg='reset'),
            ]
            _msg = f"{' '.join(_msg)}{_msg_end}"
        else:
            _msg_site = typer.style((_site.name), fg=typer.colors.RESET)
            _msg = f'{_msg.replace("?", "")} {typer.style(f"and site", fg="bright_green")} {_msg_site}{_msg_end}'

    resp = None
    confirmed = True if yes or typer.confirm(_msg, abort=True) else False
    if confirmed and _group and _site:
        reqs = [central.BatchRequest(central.move_devices_to_group, _group.name, serial_nums=dev_all_serials)]
        for _type in devs_by_type:
            serials = [d.serial for d in devs_by_type[_type]]
            reqs += [
                central.BatchRequest(central.move_devices_to_site, _site.id, serial_nums=serials, device_type=_type)
            ]
        resp = central.batch_request(reqs)

    elif confirmed and _group:
        resp = cli.central.request(cli.central.move_devices_to_group, _group.name, serial_nums=dev_all_serials)

    elif confirmed and _site:
        for _type in devs_by_type:
            serials = [d.serial for d in devs_by_type[_type]]
            reqs = [
                central.BatchRequest(central.move_devices_to_site, _site.id, serial_nums=serials, device_type=_type)
            ]

        resp = central.batch_request(reqs)

    cli.display_results(resp, tablefmt="action")


@app.command(hidden=True)
def refresh(what: RefreshWhat = typer.Argument(...),
            debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
            default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
            account: str = typer.Option("central_info",
                                        envvar="ARUBACLI_ACCOUNT",
                                        help="The Aruba Central Account to use (must be defined in the config)",),
            ):
    """refresh <'token'|'cache'>"""

    central = CentralApi(account)

    if what.startswith("token"):
        from centralcli.response import Session
        Session(central.auth).refresh_token()
    else:  # cache is only other option
        cli.cache(refresh=True)


@app.command(hidden=True)
def method_test(method: str = typer.Argument(...),
                kwargs: List[str] = typer.Argument(None),
                do_json: bool = typer.Option(True, "--json", is_flag=True, help="Output in JSON"),
                do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
                do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
                do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in Table"),
                outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
                no_pager: bool = typer.Option(True, "--pager", help="Enable Paged Output"),
                update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
                default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                             callback=cli.default_callback),
                debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                           callback=cli.debug_callback),
                account: str = typer.Option("central_info",
                                            envvar="ARUBACLI_ACCOUNT",
                                            help="The Aruba Central Account to use (must be defined in the config)",
                                            callback=cli.account_name_callback),
                ) -> None:
    """dev testing commands to run CentralApi methods from command line

    Args:
        method (str, optional): CentralAPI method to test.
        kwargs (List[str], optional): list of args kwargs to pass to function.

    format: arg1 arg2 keyword=value keyword2=value
        or  arg1, arg2, keyword = value, keyword2=value

    Displays all attributes of Response object
    """
    cli.cache(refresh=update_cache)
    central = CentralApi(account)
    if not hasattr(central, method):
        from boilerplate.allcalls import AllCalls as central
        if not hasattr(central, method):
            ic()
            typer.secho(f"{method} does not exist", fg="red")
            raise typer.Exit(1)
    args = [k for k in kwargs if "=" not in k]
    kwargs = [k.replace(" =", "=").replace("= ", "=").replace(",", " ").replace("  ", " ") for k in kwargs]
    kwargs = [k.split("=") for k in kwargs if "=" in k]
    kwargs = {k[0]: k[1] for k in kwargs}

    typer.secho(f"session.{method}({', '.join(a for a in args)}, "
                f"{', '.join([f'{k}={kwargs[k]}' for k in kwargs]) if kwargs else ''})", fg="cyan")
    resp = central.request(getattr(central, method), *args, **kwargs)

    for k, v in resp.__dict__.items():
        if k != "output":
            if debug or not k.startswith("_"):
                typer.echo(f"  {typer.style(k, fg='cyan')}: {v}")

    tablefmt = cli.get_format(
        do_json, do_yaml, do_csv, do_table
    )

    typer.echo(f"\n{typer.style('CentralCLI Response Output', fg='cyan')}:")
    cli.display_results(resp, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)
    typer.echo(f"\n{typer.style('Raw Response Output', fg='cyan')}:")
    cli.display_results(data=resp.raw, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.callback()
def callback(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=cli.debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=cli.account_name_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
) -> None:
    """
    Aruba Central API CLI
    """
    ctx.help_option_names += ["?"]


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    # allow singular form and common synonyms for the defined show commands
    # show switches / show switch ...
    if len(sys.argv) > 2 and sys.argv[1] == 'show':
        sys.argv[2] = arg_to_what(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == 'update':
        _cmds = {
            "templates": "template",
            "variable": "variables"
        }
        sys.argv[2] = _cmds.get(sys.argv[2], sys.argv[2])
    # allow --tab --tabl for --table option
    for idx, a in enumerate(sys.argv):
        if len(a) <= 7 and a.startswith("--tab"):
            sys.argv[idx] = "--table"

    app()
