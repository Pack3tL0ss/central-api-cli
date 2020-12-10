#!/usr/bin/env python3

from enum import Enum
from typing import List
from pathlib import Path
import sys
import typer

app = typer.Typer()


app = typer.Typer()
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


class Filter:
    def __init__(self):
        self.group: str = typer.Argument(None)
        self.label: str = typer.Argument(None)
        self.stackid: str = typer.Argument(None)  # stack_id
        self.status: str = typer.Argument(None)
        self.fields: str = typer.Argument(None)
        # show_stats  -s
        # calc_clients -n
        self.pub_ip: str = typer.Argument(None)
        self.limit: str = typer.Argument(None)
        self.offset: str = typer.Argument(None)


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


# show_dev_opts = ["switches", "switch", "ap", "aps", "gateway", "gateway", "controller", "controllers"]
@app.command()
def show2(what: ShowLevel1 = typer.Argument(..., ), filters: List[str] = typer.Argument(None),
          json: bool = typer.Option(False, "-j", is_flag=True, help="Output in JSON")):
    #  sort_by: str = typer.Option(None, "-sort")):
    # filters = sort_by = ""
    typer.echo(f"Show {what} {filters} {'sort_by'}")


@app.command()
def show(what: ShowLevel1 = typer.Argument(...), filters: List[str] = typer.Argument(None),
         do_json: bool = typer.Option(False, "-j", is_flag=True, help="Output in JSON"),
         do_yaml: bool = typer.Option(False, "-y", is_flag=True, help="Output in YAML"),
         sort_by: SortOptions = typer.Option(None, "--sort")):
    # filters = sort_by = ""
    typer.echo(f"Show {what} {filters} {'sort_by'}")


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
    typer.echo(f"About to execute command: {ctx.invoked_subcommand}")


if __name__ == "__main__":
    sys.argv = massage_args()
    app()
