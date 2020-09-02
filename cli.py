#!/usr/bin/env python3

from enum import Enum
# from sys import argv
# from pprint import pprint
# from typing import Union
# from pathlib import Path
# from requests.sessions import session

import typer
# from typer.params import Argument
from lib.centralCLI import CentralApi, BuildCLI, utils
import os

_config_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config")
_def_import_file = os.path.join(_config_dir, "stored-tasks.yaml")

# import click_spinner  # NoQA


# -- break up arguments passed as single string from vscode promptString --
def get_arguments_from_import(import_file: str, key: str = None):
    args = utils.read_yaml(_import_file)
    if key and key in args:
        args = args[key]

    sys.argv += args

    return sys.argv


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
                if utils.valid_file(os.path.join(_config_dir, _import_file)):
                    _import_file = os.path.join(_config_dir, _import_file)

            if len(sys.argv) > 2:
                _import_key = sys.argv.pop(2)

        sys.argv = get_arguments_from_import(_import_file, key=_import_key)
except Exception:
    pass


app = typer.Typer()


class ShowLevel2(str, Enum):
    devices = "devices"
    # devices = "dev"
    switch = "switch"
    groups = "groups"
    sites = "sites"
    clients = "clients"
    aps = "ap"
    gateway = "gateway"
    # gateways = "gateways"
    template = "template"
    variables = "variables"


class TemplateLevel1(str, Enum):
    update = "update"
    delete = "delete"
    add = "add"


def caas_response(resp):
    if not resp.ok:
        typer.echo(f"[{resp.status_code}] {resp.text} {resp.reason}")
        return
    else:
        resp = resp.json()

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


# def _pretty(content: Union[str, list]):
#     '''A Convenience Function for Colorizing and echoing Text

#     Place text to be colorized in the text str as {{RED:This text will display as red}}
#     i.e.: "An {{RED:ERROR}} occured"  or "An {{RED:BOLD:ERROR}} occured"
#     With f strings: f"This is a {{RED:BOLD:{var}}} test."

#     Args:
#         content (str|list): Text to be colorized (or list of strings)
#     '''
#     if content.count("{") != content.count("}"):
#         typer.echo(f"malformed str passed to _pretty function\n\t{content}")
#     else:
#         _this = content
#         r_list = []
#         while True:
#             r_list.append(_this.split("{")[-1].split("}")[0])

# rep = []
# idx = 0
# start = 1
# while start > 0:
#   start = x.find('{', idx) + 1
#   end = x.find('}', start)
#   idx = end + 1
#   print(idx, start, end)
#   if end > 0 and start > 0:
#     rep.append((f"{{{x[start:end]}}}"))

    # _msg = typer.style(f"{key} not found in {import_file}.  No Data to Process", fg=typer.colors.RED, bold=True)
    # typer.echo(_msg)

@app.command()
def bulk_edit(input_file: str = typer.Argument(None)):
    session = CentralApi()
    cli = BuildCLI(session=session)
    # TODO log cli
    if cli.cmds:
        for dev in cli.data:
            group_dev = f"{cli.data[dev]['_common'].get('group')}/{dev}"
            resp = session.caasapi(group_dev, cli.cmds)
            caas_response(resp)


@app.command()
def show(what: ShowLevel2 = typer.Argument(...), dev_type: str = typer.Argument(None), group: str = None):
    _data = None
    _spin_txt = "Establishing Session with Aruba Central API Gateway..."
    session = utils.spinner(_spin_txt, CentralApi)

    if not dev_type:
        if what.startswith("gateway"):
            what, dev_type = "devices", "gateway"

        elif what.lower() in ["iap", "ap", "aps"]:
            what, dev_type = "devices", "iap"

        elif what.lower() == "switch":
            what, dev_type = "devices", "switch"

    if what == "devices":
        if dev_type:
            dev_type = "gateway" if dev_type == "gateways" else dev_type
            if not group:
                _data = session.get_dev_by_type(dev_type)
            else:
                _data = session.get_gateways_by_group(group)

    elif what == "groups":
        _data = session.get_all_groups()

    elif what == "template":
        if dev_type:
            if group:
                # dev_type is template name in this case
                _data = session.get_template(group, dev_type)
            else:
                # dev_type is device serial num in this case
                _data = session.get_variablised_template(dev_type)

    # if dev_type provided (serial_num) gets vars for that dev otherwise gets vars for all devs
    elif what == "variables":
        _data = session.get_variables(dev_type)

    # print(_data)
    if _data:
        typer.echo("\n--")
        if isinstance(_data, dict):
            _data = _data.get("data", _data)

        for _ in _data:
            if isinstance(_, list) and len(_) == 1:
                typer.echo(_[0])

            elif isinstance(_, dict):
                typer.echo("--")
                # _c_id, _c_name = None, None
                # if not cust_echo and k in ["customer_id", "customer_name"]:
                for k, v in _.items():
                    typer.echo(f"{k}: {v}")
            elif isinstance(_, str):
                if isinstance(_data, dict) and _data.get(_):
                    _key = typer.style(_, fg=typer.colors.CYAN)
                    typer.echo(f"{_key}:")
                    for k, v in sorted(_data[_].items()):
                        typer.echo(f"    {k}: {v}")
                else:
                    typer.echo(_)

        typer.echo("--\n")


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
                _spin_txt = "Establishing Session with Aruba Central API Gateway..."
                ses = utils.spinner(_spin_txt, CentralApi)
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

    session = CentralApi()
    # TODO move command gen to BuildCLI
    caas_response(session.caasapi(group_dev, cmds))
    # for c in cmds:
    #     typer.echo(c)


@app.command()
def import_vlan(import_file: str = typer.Argument(_def_import_file),
                key: str = None):
    if import_file == _def_import_file and not key:
        typer.echo("key is required when using the default import file")

    data = utils.read_yaml(import_file)
    if key:
        data = data.get(key)

    if data:
        args = data.get("arguments", [])
        kwargs = data.get("options", {})
        add_vlan(*args, **kwargs)


@app.command()
def batch(import_file: str = typer.Argument(_def_import_file),
          command: str = None, key: str = None):

    if import_file == _def_import_file and not key:
        typer.echo("key is required when using the default import file")
        # typer.Exit()

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
            _spin_txt = "Establishing Session with Aruba Central API Gateway..."
            # with click_spinner.spinner():
            ses = utils.spinner(_spin_txt, CentralApi)
            kwargs = {**kwargs, **{"cli_cmds": cmds}}

            _spin_txt = "Sending Commands to Aruba Central API Gateway..."
            resp = utils.spinner(_spin_txt, ses.caasapi, *args, **kwargs)
            caas_response(resp)


@app.command()
def test():
    # var = "XYZ"
    pass
    # _pretty(f"This is a {{RED:BOLD:{var}}} test.")
    # group_dev = "20:4C:03:26:28:4c"
    # mac = "20:4C:03:26:28:4c"
    # serial = "CNF7JSP0N0"
    # # show = "committed"
    # # cmds = ["vlan 123"]
    # ses = CentralApi()
    # # resp = ses.caasapi(group_dev, cmds)
    # # resp = ses.verify_add_dev(mac, serial)
    # resp = ses.add_dev(mac, serial)

    # pprint(resp)

    # TODO move command gen to BuildCLI
    # caas_response(session.caasapi(group_dev, cmds))
    # for c in cmds:
    #     typer.echo(c)


if __name__ == "__main__":
    app()
