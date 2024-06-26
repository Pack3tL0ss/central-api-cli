#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import sys
from pathlib import Path
from typing import List

import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, log, utils
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, log, utils
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi  # noqa

app = typer.Typer()

tty = utils.tty


# TODO add cache for webhooks
@app.command(short_help="Test WebHook")
def webhook(
    wid: str = typer.Argument(..., help="WebHook ID",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
):
    resp = cli.central.request(cli.central.test_webhook, wid)

    cli.display_results(resp, tablefmt="rich", title="WebHook Test Results")

@app.command(hidden=False, short_help="Test Central API methods directly", epilog="Output is displayed in yaml by default.")
def method(
    method: str = typer.Argument(..., autocompletion=cli.cache.method_test_completion),
    kwargs: List[str] = typer.Argument(None),
    _help: bool = typer.Option(False, "--doc", help="Get details on required args/keyword args for provided method."),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False),
    do_table: bool = typer.Option(False, "--table", is_flag=True, help="Output in Table", show_default=False),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    pager: bool = typer.Option(False, help="Enable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,
                                 callback=cli.default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Debug Logging",
                               callback=cli.debug_callback),
    debugv: bool = typer.Option(
        False, "--debugv",
        envvar="ARUBACLI_VERBOSE_DEBUG",
        help="Enable verbose Debug Logging",
        hidden=True,
        callback=cli.verbose_debug_callback,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
    ),
) -> None:
    """Dev testing commands to run CentralApi methods from command line.

    :warning:  This is a development aid.  Every API endpoint in Aruba Central
    has a corresponding method/function in Central CLI.  The functions are
    generated by a script that parses the OpenAPI specs, and are generally
    best-effort/not tested.  Once required by a command in Central CLI they
    are coppied, tweaked if necessary and renamed (those are tested).

    The auto generated functions follow a consistent naming format.
    {swagger drop down text}_{method ie get}_{descriptive stuff from schema}
    i.e.: configuration_add_blacklist_clients

    Tab completion returns available methods.

    Args:
        method (str): CentralAPI method to test.
        kwargs (List[str], optional): list of args kwargs to pass to function.

    format: arg1 arg2 keyword=value keyword2=value
        or  arg1, arg2, keyword = value, keyword2=value

    Examples: cencli test method platform_get_devices all_ap


        [dark_olive_green2]Use --doc flag to see docstr for for the python method, which
        provides details on the required args / kwargs.[/]
        [cyan]cencli test method platform_get_devices --doc[/]

    Command will output all attributes of the Response object, which includes the
    raw response from the Aruba Central API gateway.
    """
    # FIXME account only works if method is in central.py
    central = CentralApi(account)
    cli.cache(refresh=update_cache)
    if not hasattr(central, method):
        if account != "central_info":
            print("Testing methods only supports the --account option for methods in central.py")
            raise typer.Exit(1)
        bpdir = Path(__file__).parent / "boilerplate"
        all_calls = [
            importlib.import_module(f"centralcli.{bpdir.name}.{f.stem}") for f in bpdir.iterdir()
            if not f.name.startswith("_") and f.suffix == ".py"
        ]
        for m in all_calls:
            log.debug(f"Looking for {method} in {m.__file__.split('/')[-1]}")
            if hasattr(m.AllCalls(), method):
                central = m.AllCalls()
                break

    if not hasattr(central, method):
        typer.secho(f"{method} does not exist", fg="red")
        raise typer.Exit(1)

    if _help:
        if getattr(central, method).__doc__:
            old_ret = "Response: CentralAPI Response object"
            new_ret = "Response from Aruba Central API gateway."
            print(getattr(central, method).__doc__.replace(old_ret, new_ret))
        else:
            print(f"Sorry, {getattr(central, method).__name__}, lacks a docstr.  No help.")
        raise typer.Exit(0)

    kwargs = kwargs or {}
    kwargs = (
        "~".join(kwargs).replace("'", "").replace('"', '').replace("~=", "=").replace("=~", "=").replace(",~", "~").split("~")
    )
    args = [k if not k.isdigit() else int(k) for k in kwargs if k and "=" not in k]
    kwargs = [k.split("=") for k in kwargs if "=" in k]
    kwargs = {k[0]: k[1] if not k[1].isdigit() else int(k[1]) for k in kwargs}
    for arg in args:
        if isinstance(arg, str):
            if arg.startswith("[") and arg.endswith("]"):
                args[args.index(arg)] = [a if not a.isdigit() else int(a) for a in arg.strip("[]").split(",")]
    for k, v in kwargs.items():
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                kwargs[k] = [vv if not vv.isdigit() else int(vv) for vv in v.strip("[]").split(",")]
            if v.lower() in ["true", "false"]:
                kwargs[k] = True if v.lower() == "true" else False

    from rich.console import Console
    c = Console(file=outfile)

    req = (
        f"central.{method}({', '.join(str(a) for a in args)}{', ' if args else ''}"
        f"{', '.join([f'{k}={kwargs[k]}' for k in kwargs]) if kwargs else ''})"
    )

    resp = central.request(getattr(central, method), *args, **kwargs)
    if isinstance(resp.output, str) and "should be str" in resp.output and "bool" in resp.output:
        c.log(f"{resp.output}.  LAME!  Converting to str!")
        args = tuple([str(a).lower() if isinstance(a, bool) else a for a in args])
        kwargs = {k: str(v).lower() if isinstance(v, bool) else v for k, v in kwargs.items()}
        resp = central.request(getattr(central, method), *args, **kwargs)

    attrs = {
        k: v for k, v in resp.__dict__.items() if k not in ["output", "raw"] and (log.DEBUG or not k.startswith("_"))
    }

    c.print(req)
    c.print("\n".join([f"  {k}: {v}" for k, v in attrs.items()]))

    tablefmt = cli.get_format(
        do_json, do_yaml, do_csv, do_table, default="yaml"
    )

    if resp.raw and resp.output != resp.raw:
        typer.echo(f"\n{typer.style('CentralCLI Response Output', fg='bright_green')}:")
        cli.display_results(data=resp.output, tablefmt=tablefmt, pager=pager, outfile=outfile)
    if resp.raw:
        typer.echo(f"\n{typer.style('Raw Response Output', fg='bright_green')}:")
        cli.display_results(data=resp.raw, tablefmt="json", pager=pager, outfile=outfile)

@app.callback()
def callback():
    """
    Test Webhook or run a centralcli function directly (all Aruba Central API endpoints are available)
    """
    pass


if __name__ == "__main__":
    app()
