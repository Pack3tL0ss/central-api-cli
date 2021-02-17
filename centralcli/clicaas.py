#!/usr/bin/env python3

from pathlib import Path
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, caas
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, caas
    else:
        print(pkg_dir.parts)
        raise e

session = None
tty = utils.tty
app = typer.Typer()
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."


@app.command()
def bulk_edit(input_file: str = typer.Argument(None)):
    cli = caas.BuildCLI(session=session, filename=input_file)
    # TODO log cli
    if cli.cmds:
        for dev in cli.data:
            group_dev = f"{cli.data[dev]['_common'].get('group')}/{dev}"
            resp = session.caasapi(group_dev, cli.cmds)
            caas.eval_caas_response(resp)


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


@app.callback()
def callback():
    """
    Interact with Aruba Central CAAS API
    """
    pass


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()
