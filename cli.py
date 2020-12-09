#!/usr/bin/env python3

from enum import Enum


import typer
from lib.centralCLI.central import CentralApi, BuildCLI, utils, config, log

# from pathlib import Path
# import os


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."


def get_arguments_from_import(import_file: str, key: str = None) -> list:
    """Get arguments from default import_file (stored_tasks.yaml)

    Args:
        import_file (str): name of import file
        key (str, optional): return single value for specific key if provided. Defaults to None.

    Returns:
        list: updated sys.argv list.
    """
    args = utils.read_yaml(_import_file)
    if key and key in args:
        args = args[key]

    sys.argv += args

    return sys.argv


# -- break up arguments passed as single string from vscode promptString --
import sys  # NoQA
sys.argv[0] = 'cencli'
try:
    if len(sys.argv) > 1:
        if " " in sys.argv[1] or not sys.argv[1]:
            vsc_args = sys.argv.pop(1)
            if vsc_args:
                if "\\'" in vsc_args:
                    _loc = vsc_args.find("\\'")
                    _before = vsc_args[:_loc - 1]
                    _str_end = vsc_args.find("\\'", _loc + 1)
                    sys.argv += _before.split()
                    sys.argv += [f"{vsc_args[_loc + 2:_str_end]}"]
                    sys.argv += vsc_args[_str_end + 2:].split()
                else:
                    sys.argv += vsc_args.split()

    if len(sys.argv) > 2:
        _import_file, _import_key = None, None
        if sys.argv[2].endswith((".yaml", ".yml")):
            _import_file = sys.argv.pop(2)
            if not utils.valid_file(_import_file):
                if utils.valid_file(config.dir.joinpath(_import_file)):
                    _import_file = config.dir.joinpath(_import_file)

            if len(sys.argv) > 2:
                _import_key = sys.argv.pop(2)

        sys.argv = get_arguments_from_import(_import_file, key=_import_key)
except Exception:
    pass


app = typer.Typer()


class ShowLevel1(str, Enum):
    devices = "devices"
    switch = "switch"
    groups = "groups"
    sites = "sites"
    # site_details = "site_details"
    clients = "clients"
    ap = "ap"
    gateway = "gateway"
    template = "template"
    variables = "variables"
    certs = "certs"


class TemplateLevel1(str, Enum):
    update = "update"
    delete = "delete"
    add = "add"


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


@app.command()
def show(what: ShowLevel1 = typer.Argument(...),
         dev_type: str = typer.Argument(None),
         group: str = None,
         json: bool = typer.Option(False, "-j", is_flag=True, help="Output in JSON"),
         output: str = typer.Option("simple", help="Output to table format"),
         #  account: str = typer.Option("central_info", help="Pass the account name from the config file"),
         id: int = typer.Option(None, help="ID field used for certain commands")
         ):

    # session = _refresh_tokens(account)
    if not dev_type:
        if what.startswith("gateway"):
            what, dev_type = "devices", "gateway"

        elif what.lower() in ["iap", "ap", "aps"]:
            what, dev_type = "devices", "iap"

        elif what.lower() == "switch":
            what, dev_type = "devices", "switch"

    # -- // Peform GET Call \\ --
    resp = None
    if what == "devices":
        if dev_type:
            dev_type = "gateway" if dev_type == "gateways" else dev_type
            if not group:
                resp = utils.spinner(SPIN_TXT_DATA, session.get_dev_by_type, dev_type)
            else:
                resp = utils.spinner(SPIN_TXT_DATA, session.get_gateways_by_group, group)

    elif what == "groups":
        resp = session.get_all_groups()

    elif what == "sites":
        if id is None:
            resp = session.get_all_sites()
        else:
            resp = session.get_site_details(id)

    # elif what == "site_details":
    #     resp = session.get_site_details(id)

    elif what == "template":
        if dev_type:
            if group:
                # dev_type is template name in this case
                resp = utils.spinner(SPIN_TXT_DATA, session.get_template, group, dev_type)
            else:
                # dev_type is device serial num in this case
                resp = session.get_variablised_template(dev_type)

    # if dev_type provided (serial_num) gets vars for that dev otherwise gets vars for all devs
    elif what == "variables":
        resp = session.get_variables(dev_type)

    elif what == "certs":
        resp = session.get_certificates()

    elif what == "clients":
        resp = session.get_wlan_clients()
        # wired = session.get_wired_clients()
        # resp = {**wlan.output, **wired.output}

    data = None if not resp else eval_resp(resp)

    if data:
        # typer.echo("\n--")
        # Strip needless inconsistent json key from dict if present
        if isinstance(data, dict):
            data = data.get("data", data)

        if isinstance(data, dict):
            data = data.get("devices", data)

        if isinstance(data, dict):
            data = data.get("mcs", data)

        if isinstance(data, dict):
            data = data.get("group", data)
            data = data.get("clients", data)

        if isinstance(data, dict):
            data = data.get("sites", data)

        if isinstance(data, dict):  # site_details is returned as a dict instead of a list
            data = [data]

        # if isinstance(data, dict):
        #     data = data.get("site_details", data)
        # print(data)
        if isinstance(data, str):
            typer.echo_via_pager(data)
        # else:
        #     _global_displayed = False
        #     for _ in data:
        #         if isinstance(_, list) and len(_) == 1:
        #             typer.echo(_[0])

        #         elif isinstance(_, dict):
        #             if not _global_displayed and _.get("customer_id"):
        #                 typer.echo(f"customer_id: {_['customer_id']}")
        #                 typer.echo(f"customer_name: {_['customer_name']}")
        #                 _global_displayed = True
        #             typer.echo("--")
        #             for k, v in _.items():
        #                 # strip needless return keys from displayed output
        #                 if k not in ["customer_id", "customer_name"]:
        #                     typer.echo(f"{k}: {v}")
        #         elif isinstance(_, str):
        #             if isinstance(data, dict) and data.get(_):
        #                 _key = typer.style(_, fg=typer.colors.CYAN)
        #                 typer.echo(f"{_key}:")
        #                 for k, v in sorted(data[_].items()):
        #                     typer.echo(f"    {k}: {v}")
        #             else:
        #                 typer.echo(_)

        # typer.echo("--\n")
        if json is True:
            tablefmt = "json"
        elif output:
            tablefmt = output
        else:
            tablefmt = "simple"
        typer.echo(utils.output(data, tablefmt))


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
        raise typer.exit()

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


def _refresh_tokens(account_name: str) -> CentralApi:
    # access token in config is overriden stored in tok file in config dir
    session = utils.spinner(SPIN_TXT_AUTH, CentralApi, account_name)
    central = session.central

    token = central.loadToken()
    if token:  # Verifying we don't need to refresh at every launch
        # refresh token on every launch
        token = central.refreshToken(token)
        if token:
            central.storeToken(token)
            central.central_info["token"] = token

    return session


# extract account from arguments
account = "central_info"
if "--account" in sys.argv:
    idx = sys.argv.index("--account")
    for i in range(idx, idx + 2):
        account = sys.argv.pop(idx)


if account not in config.data:
    typer.echo(f"{typer.style('ERROR:', fg=typer.colors.RED)} "
               f"The specified account: '{account}' not defined in config.")

# debug flag ~ additional loggin, and all logs are echoed to tty
if "--debug" in sys.argv:
    config.DEBUG = True
    log.setLevel(10)  # DEBUG
    _ = sys.argv.pop(sys.argv.index("--debug"))

log.debug(" ".join(sys.argv))
session = _refresh_tokens(account)

app()
