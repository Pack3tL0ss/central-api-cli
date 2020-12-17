#!\usr\bin\env python3

from os import environ
from pathlib import Path
from typing import List

import sys
import typer

from centralCLI import config, log, utils
from centralCLI.central import BuildCLI, CentralApi
from centralCLI.constants import (DoArgs, ShowArgs, SortOptions, StatusOptions, TemplateLevel1,
                                  arg_to_what, devices)

STRIP_KEYS = ["data", "devices", "mcs", "group", "clients", "sites", "switches", "aps"]
SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()


def eval_resp(resp):
    if not resp.ok:
        typer.echo(f"{typer.style('ERROR:', fg=typer.colors.RED)} "
                   f"{resp.output.get('description', resp.error).replace('Error: ', '')}"
                   )
    else:
        return resp.output


def caas_response(resp):
    if not resp.ok:
        typer.echo(f"[{resp.status_code}] {resp.error} \n{resp.output}")
        return
    else:
        resp = resp.output

    print()
    lines = "-" * 22
    typer.echo(lines)
    if resp.get("_global_result", {}).get("status", '') == 0:
        typer.echo("Global Result: Success")
    else:
        typer.echo("Global Result: Failure")
    typer.echo(lines)
    _bypass = None
    if resp.get("cli_cmds_result"):
        typer.echo("\n -- Command Results --")
        for cmd_resp in resp["cli_cmds_result"]:
            for _c, _r in cmd_resp.items():
                _r_code = _r.get("status")
                if _r_code == 0:
                    _r_pretty = "OK"
                else:
                    _r_pretty = f"ERROR {_r_code}"
                _r_txt = _r.get("status_str")
                typer.echo(f" [{_bypass or _r_pretty}] {_c}")
                if not _r_code == 0:
                    _bypass = "bypassed"
                    if _r_txt:
                        typer.echo(f"\t{_r_txt}\n")
                    typer.echo("-" * 65)
                    typer.echo("!! Remaining Commands bypassed due to Error in previous object !!")
                    typer.echo("-" * 65)
                elif _r_txt and not _bypass:
                    typer.echo(f"\t{_r_txt}")
        print()


@app.command()
def bulk_edit(input_file: str = typer.Argument(None)):
    # session = _refresh_tokens(account)
    cli = BuildCLI(session=session)
    # TODO log cli
    if cli.cmds:
        for dev in cli.data:
            group_dev = f"{cli.data[dev]['_common'].get('group')}/{dev}"
            resp = session.caasapi(group_dev, cli.cmds)
            caas_response(resp)


# @app.command()
# def show(what: ShowLevel1 = typer.Argument(...),
#          dev_type: str = typer.Argument(None),
#          group: str = typer.Option(None, help="Filter Output by group"),
#          json: bool = typer.Option(False, "-j", is_flag=True, help="Output in JSON"),
#          output: str = typer.Option("simple", help="Output to table format"),
#          # account: str = typer.Option(None, "account", help="Pass the account name from the config file"),
#          id: int = typer.Option(None, help="ID field used for certain commands")
#          ):


show_help = ["all (devices)", "switch[es]", "ap[s]", "gateway[s]", "group[s]", "site[s]",
             "clients", "template[s]", "variables", "certs"]


@app.command(short_help="Show Details about Aruba Central Objects")
def show(what: ShowArgs = typer.Argument(..., metavar=f"[{f'|'.join(show_help)}]"),
         #  args: List[str] = typer.Argument(None, hidden=True),
         args: str = typer.Argument(None, hidden=True),
         group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),
         label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
         dev_id: int = typer.Option(None, "--id", metavar="<id>", help="Filter by id"),
         status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
         pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
         do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
         do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
         do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
         do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
         do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
         outfile: Path = typer.Option(None, writable=True),
         sort_by: SortOptions = typer.Option(None, "--sort"),
         no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
         ):

    what = arg_to_what.get(what)

    # -- // Peform GET Call \\ --
    resp = None
    if what in devices:
        params = {
            "group": group,
            "status": None if not status else status.title(),
            "label": label,
            "public_ip_address": pub_ip,
            "calculate_client_count": do_clients,
            "show_resource_details": do_stats,
            "sort": None if not sort_by else sort_by._value_
        }
        params = {k: v for k, v in params.items() if v is not None}
        if what == "all":
            # resp = utils.spinner(SPIN_TXT_DATA, session.get_all_devices)
            resp = utils.spinner(SPIN_TXT_DATA, session.get_all_devicesv2, **params)
        else:
            resp = utils.spinner(SPIN_TXT_DATA, session.get_devices, what, **params)
        # elif not group:
        #     resp = utils.spinner(SPIN_TXT_DATA, session.get_dev_by_type, what)
        # else:
        #     # resp = utils.spinner(SPIN_TXT_DATA, session.get_gateways_by_group, group)
        #     # TODO this is a very different dataset... will determine most ideal to return
        #     resp = utils.spinner(SPIN_TXT_DATA, session.get_devices(), what, group=group, **params)

    elif what == "groups":  # VERIFIED
        resp = session.get_all_groups()  # simple list of str

    elif what == "sites":  # VERIFIED
        if dev_id is None:
            resp = session.get_all_sites()  # VERIFIED
        else:
            resp = session.get_site_details(dev_id)  # VERIFIED

    elif what == "template":
        if not args:
            typer.echo(
                typer.style("template keyword requires additional argument: <template name | serial>", fg="red")
            )
            raise typer.Exit(1)
        elif group:
            # args is template name in this case
            resp = utils.spinner(SPIN_TXT_DATA, session.get_template, group, args)
        else:
            # TODO lookup by name, ip address, etc
            # args is device serial num in this case
            resp = session.get_variablised_template(args)  # VERIFIED

    # if what provided (serial_num) gets vars for that dev otherwise gets vars for all devs
    elif what == "variables":
        resp = session.get_variables(args)

    elif what == "certs":
        resp = session.get_certificates()

    elif what == "clients":
        resp = session.get_clients(args)

    data = None if not resp else eval_resp(resp)

    if data:
        # TODO enable cleaner in Response... will benefit all command paths
        if isinstance(data, dict):
            for wtf in STRIP_KEYS:
                if wtf in data:
                    data = data[wtf]
                    break

        # if isinstance(data, str):
        #     data = data.splitlines()
            # typer.echo_via_pager(data) if len(data) > tty.rows else typer.echo(data)

        if do_json is True:
            tablefmt = "json"
        elif do_yaml is True:
            tablefmt = "yaml"
        elif do_csv is True:
            tablefmt = "csv"
        # elif output:
        #     tablefmt = output
        else:
            tablefmt = "simple"
        outdata = utils.output(data, tablefmt)
        typer.echo_via_pager(outdata) if not no_pager and len(outdata) > tty.rows else typer.echo(outdata)

        # -- // Output to file \\ --
        if outfile and outdata:
            if outfile.parent.resolve() == config.base_dir.resolve():
                outfile = config.outdir / outfile

            print(
                typer.style(f"\nWriting output to {outfile.relative_to(Path.cwd())}... ", fg="cyan"),
                end=""
            )
            outfile.write_text(outdata.file)  # typer.unstyle(outdata) also works
            typer.secho("Done", fg="green")

    else:
        typer.echo("No Data Returned")


@app.command()
def template(operation: TemplateLevel1 = typer.Argument(...),
             what: str = typer.Argument(...),
             device: str = typer.Argument(None),
             variable: str = typer.Argument(None),
             value: str = typer.Argument(None)
             ):

    if operation == "update":
        if what == "variable":
            if variable and value and device:
                ses = utils.spinner(SPIN_TXT_AUTH, CentralApi)
                payload = {"variables": {variable: value}}
                _resp = ses.update_variables(device, payload)
                if _resp:
                    typer.echo(f"{typer.style('Success', fg=typer.colors.GREEN)}")
                else:
                    typer.echo(f"{typer.style('Error Returned', fg=typer.colors.RED)}")


@app.command()
def do(what: DoArgs = typer.Argument(...),
       # args: str = typer.Argument(..., metavar="Identifying Attributes: [serial #|name|ip address|mac address]"),
       args: str = typer.Argument(None, metavar="identifying attribute i.e. port #, required for some actions."),
       serial: str = typer.Option(None),
       name: str = typer.Option(None),
       ip: str = typer.Option(None),
       mac: str = typer.Option(None),
       yes: bool = typer.Option(False, "-Y", metavar="Bypass confirmation prompts - Assume Yes"),
       ) -> None:

    # serial_num is currently only real option until cache/lookup is implemented
    kwargs = {
        "serial_num": serial,
        "name": name,
        "ip": ip,
        "mac": None if not mac else utils.Mac(mac)
    }
    typer.echo("\n".join([f"{k}: {v}" for k, v in locals().items()]))

    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    if typer.confirm(typer.style(f"Please Confirm {what} {args}", fg="cyan")):
        resp = getattr(session, what.replace("-", "_"))(args, **kwargs)
        typer.echo(resp)
        if resp.ok:
            typer.echo(f"{typer.style('Success', fg='green')} command Queued.")
            resp = session.get_task_status(resp.task_id)
            typer.secho(f"Task Status: {resp.get('reason', '')}, State: {resp.state}", fg="green" if resp.ok else "red")

    else:
        raise typer.Abort()
    # if what == "bounce-poe":
    #     resp = session.bounce_poe(args2, )
    # elif what == "bounce-interface":
    #     typer.echo(f"{what}, {args}, {yes}")
    # elif what == "reboot":
    #     pass


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
    caas_response(session.caasapi(group_dev, cmds))


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
def batch(import_file: str = typer.Argument(config.stored_tasks_file),
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
            pass  # TODO error msg import data requires an argument specifying the group / device

        if command:
            try:
                exec(f"fn = {command}")
                fn(*args, **kwargs)  # type: ignore # NoQA
            except AttributeError:
                typer.echo(f"{command} doesn't appear to be valid")
        elif cmds:
            # if "!" not in cmds:
            #     cmds = '^!^'.join(cmds).split("^")
            # with click_spinner.spinner():
            # ses = utils.spinner(SPIN_TXT_AUTH, CentralApi)
            kwargs = {**kwargs, **{"cli_cmds": cmds}}
            resp = utils.spinner(SPIN_TXT_CMDS, session.caasapi, *args, **kwargs)
            caas_response(resp)


@app.command()
def refresh_tokens():
    pass


@app.command()
def method_test(method: str = typer.Argument(...),
                kwargs: List[str] = typer.Argument(None)
                ):
    """dev testing commands to run CentralApi methods from command line

    Args:
        method (str, optional): CentralAPI method to test.
        kwargs (List[str], optional): list of args kwargs to pass to function.

    format: arg1 arg2 keyword=value keyword2=value
        or  arg1, arg2, keyword = value, keyword2=value

    Displays all attributes of Response object
   """
    if not hasattr(session, method):
        typer.secho(f"{method} does not exist", fg="red")
        raise typer.Exit(1)
    args = [k for k in kwargs if "=" not in k]
    kwargs = [k.replace(" =", "=").replace("= ", "=").replace(",", " ").replace("  ", " ") for k in kwargs]
    kwargs = [k.split("=") for k in kwargs if "=" in k]
    kwargs = {k[0]: k[1] for k in kwargs}

    typer.secho(f"session.{method}({(args)}, {kwargs})", fg="green")
    resp = getattr(session, method)(*args, **kwargs)
    for k, v in resp.__dict__.items():
        typer.echo(f"{k}: {v}")


def _refresh_tokens(account_name: str) -> CentralApi:
    # access token in config is overriden stored in tok file in config dir
    if not config.DEBUG:
        session = utils.spinner(SPIN_TXT_AUTH, CentralApi, account_name)
    else:
        session = CentralApi(account_name)

    central = session.central

    token = central.loadToken()
    if token:  # Verifying we don't need to refresh at every launch
        # refresh token on every launch
        token = central.refreshToken(token)
        if token:
            central.storeToken(token)
            central.central_info["token"] = token

    return session


# ---- // RUN \\ ----

# extract account from arguments or environment variables
account = environ.get('ARUBACLI_ACCOUNT', "central_info")

if "--account" in sys.argv:
    idx = sys.argv.index("--account")
    for i in range(idx, idx + 2):
        account = sys.argv.pop(idx)

# Abort if account
if account not in config.data:
    typer.echo(f"{typer.style('ERROR:', fg=typer.colors.RED)} "
               f"The specified account: '{account}' not defined in config.")
    raise typer.Exit(1)

# debug flag ~ additional logging, and all logs are echoed to tty
if ("--debug" in sys.argv) or (environ.get('ARUBACLI_DEBUG') == "1"):
    config.DEBUG = log.DEBUG = log.show = True
    log.setLevel("DEBUG")
    if "--debug" in sys.argv:
        _ = sys.argv.pop(sys.argv.index("--debug"))

log.debug(" ".join(sys.argv))
session = _refresh_tokens(account)

app()
