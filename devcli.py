#!/usr/bin/env python3

import ipaddress
from enum import Enum
from typing import List
from pathlib import Path
import sys
from click.termui import style
import typer
from typing import Dict

app = typer.Typer(options_metavar="WHAT TO SHOW")


app = typer.Typer(options_metavar="Filtering and output flags")
# show_app = typer.Typer()
# app.add_typer(show_app, name="show")
# users_app = typer.Typer()
# app.add_typer(users_app, name="users")


class ShowLevel1(str, Enum):
    devices = "devices"
    device = "device"
    switch = "switch"
    groups = "groups"
    sites = "sites"
    clients = "clients"
    ap = "ap"
    aps = "aps"
    gateway = "gateway"
    gateways = "gateways"
    template = "template"
    variables = "variables"
    certs = "certs"


class ShowFilters(str, Enum):
    group = "group"
    label = "label"
    stack_id = "stack_id"
    status = "status"
    fields = "fields"
    # show_stats  -s
    # calc_clients -n
    pub_ip = "pub_ip"
    limit = "limit"
    offset = "offset"


class SortOptions(str, Enum):
    name_asc = "+name"
    name_des = "-name"
    mac_asc = "+mac"
    mac_des = "-mac"
    serial_asc = "+serial"
    serial_des = "-serial"


class ACStatus(str, Enum):
    up = "up"
    down = "down"


# Enum(valid_filters = [
#     group: str = typer.Argument(None),
#     label: str = typer.Argument(None),
#     stack_id: str = typer.Argument("stackid", None),
#     status: str = typer.Argument(None),
#     fields: str = typer.Argument(None),
#     pub_ip: str = typer.Argument(None),
#     limit: str = typer.Argument(None),
#     offset: str = typer.Argument(None)
# ])

def massage_args() -> List[str]:
    sys.argv[0] = Path(__file__).stem
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
    except Exception:
        pass
    finally:
        return sys.argv


# switch_meta = ["switches", "switch", "ap", "aps", "gateway", "gateway", "controller", "controllers"]
L = typer.style("[", fg="cyan")
R = typer.style("]", fg="cyan")
M = typer.style("|", fg="cyan")
show_dev_opts = [f"switch[es]", f"ap[s]", f"gateway[s]", f"controller[s]"]
# # show_stats  -s
# # calc_clients -n
@app.command()
def show(what: ShowLevel1 = typer.Argument(..., metavar=f"{L}{f'{M}'.join(show_dev_opts)}{R}"),
         group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),
         label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
         id: int = typer.Option(None, metavar="<id>", help="Filter by id"),
         status: ACStatus = typer.Option(None, help="Filter by device status"),
         pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
        #  limit: int = typer.Option(None),
        #  offset: int = typer.Option(None),
         do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
         do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
         do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
         do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
         do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client ..."),
         sort_by: SortOptions = typer.Option(None, "--sort")):
        # _filter_names = ["group", "label", "stack_id", "status", "fields", "pub_ip", "limit", "offset"]
        # _valid_filters = [group, label, stackid, status, fields, pub_ip, limit, offset]
        # filters = [f"{k}: {v} " for k, v in zip(_filter_names, _valid_filters) if v]
        # typer.echo(f"Show {what} {filters} sort_by: {sort_by} json:{do_json}, yaml:{do_yaml} csv:{do_csv}")
    _ = {typer.echo(f"{typer.style(k, fg='green')}: {v}") for k, v in locals().items()}
    pass


@app.command()
def show2(what: ShowLevel1 = typer.Argument(...), filters: List[str] = typer.Argument(None),
          do_json: bool = typer.Option(False, "-j", is_flag=True, help="Output in JSON"),
          do_yaml: bool = typer.Option(False, "-y", is_flag=True, help="Output in YAML"),
          sort_by: SortOptions = typer.Option(None, "--sort")):
    # filters = sort_by = ""
    typer.echo(f"Show {what} {filters} sort_by: {sort_by} json:{do_json}, yaml:{do_yaml}")


# @show_app.command("delete")
# def items_delete(item: str):
#     typer.echo(f"Deleting item: {item}")


# @show_app.command("sell")
# def items_sell(item: str):
#     typer.echo(f"Selling item: {item}")


# @users_app.command("create")
# def users_create(user_name: str):
#     typer.echo(f"Creating user: {user_name}")


# @users_app.command("delete")
# def users_delete(user_name: str):
#     typer.echo(f"Deleting user: {user_name}")


@app.callback()
def main(ctx: typer.Context):
    """
    Central API CLI App.
    """
    # typer.echo(f"About to execute command: {ctx.invoked_subcommand}")
    typer.secho(f"{' '.join(sys.argv[1:])}", fg='green')


if __name__ == "__main__":
    sys.argv = massage_args()
    app()
