#!/usr/bin/env python3

import asyncio
import time
from pathlib import Path
from typing import Any, List, Union
# import clishow
# import clido
from tinydb import TinyDB
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response, caas, clishow, clido
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response, caas, clishow, clido
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi
from centralcli.constants import (TemplateLevel1,
                                  RefreshWhat, arg_to_what)


TinyDB.default_table_name = "devices"

STRIP_KEYS = ["data", "devices", "mcs", "group", "clients", "sites", "switches", "aps"]
SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()
app.add_typer(clishow.app, name="show")
app.add_typer(clido.app, name="do")


class AcctMsg:
    def __init__(self, account: str = None, msg: str = None) -> None:
        self.account = account
        self.msg = msg

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if self.msg and hasattr(self, self.msg):
            return getattr(self, self.msg)
        else:
            return self.initial

    @property
    def initial(self):
        acct_clr = f"{typer.style(self.account, fg='cyan')}"
        return (
            f"{typer.style(f'Using Account: {acct_clr}.', fg='magenta')}  "
            f"{typer.style(f'Account setting is sticky.  ', fg='red', blink=True)}"
            f"\n  {acct_clr} {typer.style(f'will be used for subsequent commands until', fg='magenta')}"
            f"\n  {typer.style('--account <account name> or `-d` (revert to default). is used.', fg='magenta')}"
        )

    @property
    def previous(self):
        return (
            f"{typer.style(f'Using previously specified account: ', fg='magenta')}"
            f"{typer.style(self.account, fg='cyan', blink=True)}.  "
            f"\n{typer.style('Use `--account <account name>` to switch to another account.', fg='magenta')}"
            f"\n{typer.style('    or `-d` flag to revert to default account.', fg='magenta')}"
        )

    @property
    def forgot(self):
        typer.style(
            "Forget option set for account, and expiration has passed.  reverting to default account",
            fg="magenta"
        )

    @property
    def will_forget(self):
        return typer.style(
            f'Forget options is configured, will revert to default account '
            f'{typer.style(f"{config.forget_account_after} mins", fg="cyan")}'
            f'{typer.style(" after last command.", fg="magenta")}',
            fg="magenta"
        )

    @property
    def previous_will_forget(self):
        return f'{self.previous}\n\n{self.will_forget}'


def default_callback(ctx: typer.Context, default: bool):
    if ctx.resilient_parsing:  # tab completion, return without validating
        return

    if default and config.sticky_account_file.is_file():
        typer.secho('Using default central account', fg="cyan")
        config.sticky_account_file.unlink()


# TODO ?? make more sense to have this return the ArubaCentralBase object ??
def account_name_callback(ctx: typer.Context, account: str):
    if ctx.resilient_parsing:  # tab completion, return without validating
        return account

    # -- // sticky last account caching and messaging \\ --
    if account == "central_info":
        if config.sticky_account_file.is_file():
            last_account, last_cmd_ts = config.sticky_account_file.read_text().split('\n')
            last_cmd_ts = float(last_cmd_ts)

            # delete last_account file if they've configured forget_account_after
            if config.forget_account_after:
                if time.time() > last_cmd_ts + (config.forget_account_after * 60):
                    config.sticky_account_file.unlink(missing_ok=True)
                    typer.echo(AcctMsg(msg="forgot"))
                else:
                    account = last_account
                    typer.echo(AcctMsg(account, msg='previous_will_forget'))
            else:
                account = last_account
                typer.echo(AcctMsg(account, msg='previous'))
    else:
        if account in config.data:
            config.sticky_account_file.write_text(f'{account}\n{round(time.time(), 2)}')
            typer.echo(AcctMsg(account))

    if account in config.data:
        config.account = account
        global session
        session = CentralApi(account)
        global cache
        cache = Cache(session)
        return account
    else:
        strip_keys = ['central_info', 'ssl_verify', 'token_store', 'forget_account_after', 'debug', 'debugv', 'limit']
        typer.echo(f"{typer.style('ERROR:', fg=typer.colors.RED)} "
                   f"The specified account: '{account}' is not defined in the config @\n"
                   f"{config.file}\n\n")

        _accounts = [k for k in config.data.keys() if k not in strip_keys]
        if _accounts:
            typer.echo(f"The following accounts are defined {_accounts}\n"
                       f"The default account 'central_info' is used if no account is specified via --account flag.\n"
                       f"or the ARUBACLI_ACCOUNT environment variable.\n")
        else:
            if not config.data:
                # TODO prompt user for details
                typer.secho("Configuration doesn't exist", fg="red")
            else:
                typer.secho("No accounts defined in config", fg="red")

        if account != "central_info" and "central_info" not in config.data:
            typer.echo(f"{typer.style('WARNING:', fg='yellow')} "
                       f"'central_info' is not defined in the config.  This is the default when not overriden by\n"
                       f"--account parameter or ARUBACLI_ACCOUNT environment variable.")

        raise typer.Exit(code=1)


def debug_callback(debug: bool):
    if debug:
        log.DEBUG = config.debug = debug


@app.command()
def bulk_edit(input_file: str = typer.Argument(None)):
    cli = caas.BuildCLI(session=session)
    # TODO log cli
    if cli.cmds:
        for dev in cli.data:
            group_dev = f"{cli.data[dev]['_common'].get('group')}/{dev}"
            resp = session.caasapi(group_dev, cli.cmds)
            caas.eval_caas_response(resp)


def eval_resp(resp: Response, pad: int = 0) -> Any:
    if not resp.ok:
        msg = f"{' ' * pad}{typer.style('ERROR:', fg=typer.colors.RED)} "
        if isinstance(resp.output, dict):
            msg += f"{resp.output.get('description', resp.error).replace('Error: ', '')}"
        else:
            msg += str(resp.output)

        typer.echo(msg)
    else:
        return resp.output


# TODO combine eval_resp and display_results
def display_results(data: Union[List[dict], List[str]], tablefmt: str = "simple",
                    pager=True, outfile: Path = None) -> Union[list, dict]:
    outdata = utils.output(data, tablefmt)
    typer.echo_via_pager(outdata) if pager and len(outdata) > tty.rows else typer.echo(outdata)

    # -- // Output to file \\ --
    if outfile and outdata:
        if outfile.parent.resolve() == config.base_dir.resolve():
            config.outdir.mkdir(exist_ok=True)
            outfile = config.outdir / outfile

        print(
            typer.style(f"\nWriting output to {outfile}... ", fg="cyan"),
            end=""
        )
        outfile.write_text(outdata.file)  # typer.unstyle(outdata) also works
        typer.secho("Done", fg="green")


show_help = ["all (devices)", "device[s] (same as 'all' unless followed by device identifier)", "switch[es]", "ap[s]",
             "gateway[s]", "group[s]", "site[s]", "clients", "template[s]", "variables", "certs"]
args_metavar_dev = "[name|ip|mac-address|serial]"
args_metavar_site = "[name|site_id|address|city|state|zip]"
args_metavar = f"""Optional Identifying Attribute: device: {args_metavar_dev} site: {args_metavar_site}"""


@app.command()
def template(operation: TemplateLevel1 = typer.Argument(...),
             what: str = typer.Argument(None, hidden=False, metavar="['variable']",
                                        help="Optional variable keyword to indicate variable update"),
             device: str = typer.Argument(None, metavar=args_metavar_dev),
             variable: str = typer.Argument(None, help="[Variable operations] What Variable To Update"),
             value: str = typer.Argument(None, help="[Variable operations] The Value to assign"),
             template: Path = typer.Option(None, help="Path to file containing new template"),
             group: str = typer.Option(None, metavar="<Device Group>", help="Required for Update Template"),
             device_type: str = typer.Option(None, "--dev-type", metavar="[IAP|ArubaSwitch|MobilityController|CX]>",
                                             help="[Templates] Filter by Device Type"),
             version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by version"),
             model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
             debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                        callback=debug_callback),
             account: str = typer.Option("central_info",
                                         envvar="ARUBACLI_ACCOUNT",
                                         help="The Aruba Central Account to use (must be defined in the config)",
                                         callback=account_name_callback),
             ):
    # TODO cache template names
    if operation == "update":
        if what == "variable":
            if variable and value and device:
                # ses = utils.spinner(SPIN_TXT_AUTH, CentralApi)
                # cache = Cache(session)
                device = cache.get_dev_identifier(device)
                payload = {"variables": {variable: value}}
                _resp = session.update_variables(device, payload)
                if _resp:
                    log.info(f"Template Variable Updated {variable} -> {value}", show=False)
                    typer.echo(f"{typer.style('Success', fg=typer.colors.GREEN)}")
                else:
                    log.error(f"Template Update Variables {variable} -> {value} retuned error\n{_resp.output}", show=False)
                    typer.echo(f"{typer.style('Error Returned', fg=typer.colors.RED)} {_resp.error}")
        else:  # delete or add template, what becomes device/template identifier
            kwargs = {
                "group": group,
                "name": what,
                "device_type": device_type,
                "version": version,
                "model": model
            }
            payload = None
            do_prompt = False
            if template:
                if not template.is_file() or template.stat().st_size > 0:
                    typer.secho(f"{template} not found or invalid.", fg="red")
                    do_prompt = True
            else:
                typer.secho("template file not provided (--template <path/to/file>)", fg="cyan")
                do_prompt = True

            if do_prompt:
                payload = utils.get_multiline_input("Paste in new template contents then press CTRL-D", typer.secho, fg="cyan")
                payload = "\n".join(payload).encode()

            _resp = session.update_existing_template(**kwargs, template=template, payload=payload)
            if _resp:
                log.info(f"Template {what} Updated {_resp.output}", show=False)
                typer.secho(_resp.output, fg="green")
            else:
                log.error(f"Template {what} Update from {template} Failed. {_resp.error}", show=False)
                typer.secho(_resp.output, fg="red")


@app.command()
def add_vlan(group_dev: str = typer.Argument(...), pvid: str = typer.Argument(...), ip: str = typer.Argument(None),
             mask: str = typer.Argument("255.255.255.0"), name: str = None, description: str = None,
             interface: str = None, vrid: str = None, vrrp_ip: str = None, vrrp_pri: int = None):
    cmds = []
    cmds += [f"vlan {pvid}", "!"]
    if name:
        cmds += [f"vlan-name {name}", "!", f"vlan {name} {pvid}", "!"]
    if ip:
        _fallback_desc = f"VLAN{pvid}-SVI"
        cmds += [f"interface vlan {pvid}", f"description {description or name or _fallback_desc}", f"ip address {ip} {mask}", "!"]
    if vrid:
        cmds += [f"vrrp {vrid}", f"ip address {vrrp_ip}", f"vlan {pvid}"]
        if vrrp_pri:
            cmds += [f"priority {vrrp_pri}"]
        cmds += ["no shutdown", "!"]

    # TODO move command gen to BuildCLI
    caas.eval_caas_response(session.caasapi(group_dev, cmds))


@app.command()
def import_vlan(import_file: str = typer.Argument(config.stored_tasks_file),
                key: str = None):
    if import_file == config.stored_tasks_file and not key:
        typer.echo("key is required when using the default import file")

    data = utils.read_yaml(import_file)
    if key:
        data = data.get(key)

    if data:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        add_vlan(*args, **kwargs)


@app.command()
def caas_batch(import_file: Path = typer.Argument(config.stored_tasks_file),
               command: str = None, key: str = None):

    if import_file == config.stored_tasks_file and not key:
        typer.echo("key is required when using the default import file")
        raise typer.Exit()

    data = utils.read_yaml(import_file)
    if key:
        data = data.get(key)

    if not data:
        _msg = typer.style(f"{key} not found in {import_file}.  No Data to Process", fg=typer.colors.RED, bold=True)
        typer.echo(_msg)
    else:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        cmds = data.get("cmds", [])

        if not args:
            typer.secho("import data requires an argument specifying the group / device")
            raise typer.Exit(1)

        if command:
            try:
                exec(f"fn = {command}")
                fn(*args, **kwargs)  # type: ignore # NoQA
            except AttributeError:
                typer.echo(f"{command} doesn't appear to be valid")
        elif cmds:
            kwargs = {**kwargs, **{"cli_cmds": cmds}}
            resp = utils.spinner(SPIN_TXT_CMDS, session.caasapi, *args, **kwargs)
            caas.eval_caas_response(resp)


@app.command()
def batch(
    import_file: Path = typer.Argument(None, exists=True),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
    command: str = None, key: str = None
) -> None:
    data = config.get_file_data(import_file)

    #
    if import_file.sfx in ['.csv', '.tsv', '.dbf', '.xls', '.xlsx']:
        # TODO do more than this quick and dirty data validation.
        if data and len(data.headers) > 3:
            data = [
                {'site_name': i['site_name'], 'site_address': {k: v for k, v in i.items() if k != 'site_name'}} for i in data.dict
            ]
        else:
            data = [
                {'site_name': i['site_name'], 'geolocation': {k: v for k, v in i.items() if k != 'site_name'}} for i in data.dict
            ]

    # TODO move callback def to cli.py so methods in central.py are usable as module for other scripts
    # without callback or with a different custom callback unrelated to centralcli
    resp = session.request(session.create_site, site_list=data)
    resp_data = eval_resp(resp)
    display_results(resp_data)


@app.command()
def refresh(what: RefreshWhat = typer.Argument(...),
            debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                       callback=debug_callback),
            account: str = typer.Option("central_info",
                                        envvar="ARUBACLI_ACCOUNT",
                                        help="The Aruba Central Account to use (must be defined in the config)",
                                        callback=account_name_callback),):
    """refresh <'token'|'cache'>"""

    session = CentralApi(account)
    central = session.central

    if what.startswith("token"):
        Response(central).refresh_token()
    else:  # cache is only other option
        Cache(session=session, refresh=True)


@app.command()
def method_test(method: str = typer.Argument(...),
                kwargs: List[str] = typer.Argument(None),
                do_json: bool = typer.Option(True, "--json", is_flag=True, help="Output in JSON"),
                do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
                do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
                do_table: bool = typer.Option(False, "--simple", is_flag=True, help="Output in Table"),
                do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
                outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
                no_pager: bool = typer.Option(True, "--pager", help="Enable Paged Output"),
                update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
                debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                           callback=debug_callback),
                account: str = typer.Option("central_info",
                                            envvar="ARUBACLI_ACCOUNT",
                                            help="The Aruba Central Account to use (must be defined in the config)",
                                            callback=account_name_callback),
                ) -> None:
    """dev testing commands to run CentralApi methods from command line

    Args:
        method (str, optional): CentralAPI method to test.
        kwargs (List[str], optional): list of args kwargs to pass to function.

    format: arg1 arg2 keyword=value keyword2=value
        or  arg1, arg2, keyword = value, keyword2=value

    Displays all attributes of Response object
    """
    session = CentralApi(account)
    if not hasattr(session, method):
        typer.secho(f"{method} does not exist", fg="red")
        raise typer.Exit(1)
    args = [k for k in kwargs if "=" not in k]
    kwargs = [k.replace(" =", "=").replace("= ", "=").replace(",", " ").replace("  ", " ") for k in kwargs]
    kwargs = [k.split("=") for k in kwargs if "=" in k]
    kwargs = {k[0]: k[1] for k in kwargs}

    typer.secho(f"session.{method}({', '.join(a for a in args)}, "
                f"{', '.join([f'{k}={kwargs[k]}' for k in kwargs]) if kwargs else ''})", fg="cyan")
    resp = session.request(getattr(session, method), *args, **kwargs)

    for k, v in resp.__dict__.items():
        if k != "output":
            if debug or not k.startswith("_"):
                typer.echo(f"  {typer.style(k, fg='cyan')}: {v}")

    data = eval_resp(resp, pad=2)

    if data:
        if do_yaml is True:
            tablefmt = "yaml"
        elif do_csv is True:
            tablefmt = "csv"
        elif do_rich is True:
            tablefmt = "rich"
        elif do_table is True:
            tablefmt = "simple"
        else:
            tablefmt = "json"

        typer.echo(f"\n{typer.style('CentralCLI Response Output', fg='cyan')}:")
        display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)
        data = asyncio.run(resp._response.json())
        if data:
            typer.echo(f"\n{typer.style('Raw Response Output', fg='cyan')}:")
            display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.callback()
def callback():
    """
    Aruba Central API CLI
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == 'show':
        sys.argv[2] = arg_to_what(sys.argv[2])

    app()
