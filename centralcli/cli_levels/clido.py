#!/usr/bin/env python3

import time
from pathlib import Path
from typing import Any, List, Union
from tinydb import TinyDB
import sys
import typer
# import central

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi
from centralcli.constants import BlinkArgs, CycleArgs

# from centralapi import CentralApi, Cache, Response, log, config
# from centralapi.constants import BlinkArgs, CycleArgs, arg_to_what
# from centralapi.utils import Utils
# utils = Utils()

TinyDB.default_table_name = "devices"

STRIP_KEYS = ["data", "devices", "mcs", "group", "clients", "sites", "switches", "aps"]
SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()


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
    '''
    Allows easy switching between configured central accounts.

    Setting is sticky, only has to be set once, then that account will be used
    until another account is specified via --account or -d flag is used to revert
    back to default.
    '''
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


@app.command(short_help="Bounce Interface or PoE on Interface")
def bounce(
    what: CycleArgs = typer.Argument(...),
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    port: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    serial = cache.get_dev_identifier(device)
    command = 'bounce_poe_port' if what == 'poe' else 'bounce_interface'
    if yes or typer.confirm(typer.style(f"Please Confirm {what} {device} {port}", fg="cyan")):
        resp = session.request(session.send_bounce_command_to_device, serial, command, port)
        typer.secho(str(resp), fg="green" if resp else "red")
        # !! removing this for now Central ALWAYS returns:
        # !!   reason: Sending command to device. state: QUEUED, even after command execution.
        # if resp and resp.get('task_id'):
        #     resp = session.request(session.get_task_status, resp.task_id)
        #     typer.secho(str(resp), fg="green" if resp else "red")

    else:
        raise typer.Abort()


@app.command(short_help="Reboot a device")
def reboot(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    serial = cache.get_dev_identifier(device)
    reboot_msg = f"{typer.style('*reboot*', fg='red')} {typer.style(f'{device}', fg='cyan')}"
    if yes or typer.confirm(typer.style(f"Please Confirm: {reboot_msg}", fg="cyan")):
        resp = session.request(session.send_command_to_device, serial, 'reboot')
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="Blink LED")
def blink(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    action: BlinkArgs = typer.Argument(..., ),  # metavar="Device: [on|off|<# of secs to blink>]"),
    secs: int = typer.Argument(None, metavar="SECONDS", help="Blink for _ seconds."),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    command = f'blink_led_{action}'
    serial = cache.get_dev_identifier(device)
    resp = session.request(session.send_command_to_device, serial, command, duration=secs)
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Factory Default A Device")
def nuke(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    serial = cache.get_dev_identifier(device)
    nuke_msg = f"{typer.style('*Factory Default*', fg='red')} {typer.style(f'{device}', fg='cyan')}"
    if yes or typer.confirm(typer.style(f"Please Confirm: {nuke_msg}", fg="cyan")):
        resp = session.request(session.send_command_to_device, serial, 'erase_configuration')
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="Save Device Running Config to Startup")
def save(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    serial = cache.get_dev_identifier(device)
    resp = session.request(session.send_command_to_device, serial, 'save_configuration')
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Sync/Refresh device config with Aruba Central")
def sync(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    serial = cache.get_dev_identifier(device)
    resp = session.request(session.send_command_to_device, serial, 'config_sync')
    typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Update existing or add new Variables for a device/template")
def update_vars(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    var_value: List[str] = typer.Argument(..., help="comma seperated list 'variable = value, variable2 = value2'"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    serial = cache.get_dev_identifier(device)
    vars, vals, get_next = [], [], False
    for var in var_value:
        if var == '=':
            continue
        if '=' not in var:
            if get_next:
                vals += [var]
                get_next = False
            else:
                vars += [var]
                get_next = True
        else:
            _ = var.split('=')
            vars += _[0]
            vals += _[1]
            get_next = False

    if len(vars) != len(vals):
        typer.secho("something went wrong parsing variables.  Unequal length for Variables vs Values")
        raise typer.Exit(1)

    var_dict = {k: v for k, v in zip(vars, vals)}

    typer.secho(f"Please Confirm: Update {device}", fg="cyan")
    [typer.echo(f'    {k}: {v}') for k, v in var_dict.items()]
    if typer.confirm(typer.style("Proceed with these values", fg="cyan")):
        resp = session.request(session.update_variables, serial, **var_dict)
        typer.secho(str(resp), fg="green" if resp else "red")


@app.command(short_help="Move device to a defined group")
def move(
    device: str = typer.Argument(..., metavar="Device: [serial #|name|ip address|mac address]"),
    group: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
) -> None:
    yes = yes_ if yes_ else yes
    serial = cache.get_dev_identifier(device)
    group = cache.get_group_identifier(group)
    if yes or typer.confirm(typer.style(f"Please Confirm: move {device} to group {group}", fg="cyan")):
        resp = session.request(session.move_dev_to_group, group, serial)
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.callback()
def callback():
    """
    Perform device / interface / client actions.
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()
