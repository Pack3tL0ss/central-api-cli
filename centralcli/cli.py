#!/usr/bin/env python3

from pathlib import Path
from typing import Any, List
from tinydb import TinyDB
import sys
import typer

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response, caas
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response, caas
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi
# import caas
from centralcli.constants import (DoArgs, ShowArgs, SortOptions, StatusOptions, TemplateLevel1,
                                  RefreshWhat, arg_to_what, devices)


TinyDB.default_table_name = "devices"

STRIP_KEYS = ["data", "devices", "mcs", "group", "clients", "sites", "switches", "aps"]
SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty

app = typer.Typer()


# TODO ?? make more sense to have this return the ArubaCentralBase object ??
def account_name_callback(ctx: typer.Context, account: str):
    if ctx.resilient_parsing:  # tab completion, return without validating
        return account

    if account not in config.data:
        strip_keys = ['central_info', 'ssl_verify', 'token_store']
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

    global session
    session = CentralApi(account)
    return account


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


def eval_resp(resp) -> Any:
    if not resp.ok:
        typer.echo(f"{typer.style('ERROR:', fg=typer.colors.RED)} "
                   f"{resp.output.get('description', resp.error).replace('Error: ', '')}"
                   )
    else:
        return resp.output


show_help = ["all (devices)", "device[s] (same as 'all' unless followed by device identifier)", "switch[es]", "ap[s]",
             "gateway[s]", "group[s]", "site[s]", "clients", "template[s]", "variables", "certs"]
args_metavar_dev = "[name|ip|mac-address|serial]"
args_metavar_site = "[name|site_id|address|city|state|zip]"
args_metavar = f"""Optional Identifying Attribute: device: {args_metavar_dev} site: {args_metavar_site}"""


@app.command(short_help="Show Details about Aruba Central Objects")
def show(what: ShowArgs = typer.Argument(..., metavar=f"[{f'|'.join(show_help)}]"),
         args: List[str] = typer.Argument(None, metavar=args_metavar, hidden=False),
         #  args: str = typer.Argument(None, hidden=True),
         group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
         label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
         dev_id: int = typer.Option(None, "--id", metavar="<id>", help="Filter by id"),
         status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
         state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
         pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
         name: str = typer.Option(None, metavar="<Template Name>", help="[Templates] Filter by Template Name"),
         device_type: str = typer.Option(None, "--dev-type", metavar="[IAP|ArubaSwitch|MobilityController|CX]>",
                                         help="[Templates] Filter by Device Type"),
         version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by dev version Template is assigned to"),
         model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
         #  variablised: str = typer.Option(False, "--with-vars",
         #                                  help="[Templates] Show Template with variable place-holders and vars."),
         do_stats: bool = typer.Option(False, "--stats", is_flag=True, help="Show device statistics"),
         do_clients: bool = typer.Option(False, "--clients", is_flag=True, help="Calculate client count (per device)"),
         sort_by: SortOptions = typer.Option(None, "--sort"),
         do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
         do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
         do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
         do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
         outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
         no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
         update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
         debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                    callback=debug_callback),
         account: str = typer.Option("central_info",
                                     envvar="ARUBACLI_ACCOUNT",
                                     help="The Aruba Central Account to use (must be defined in the config)",
                                     callback=account_name_callback),
         ):

    what = arg_to_what.get(what)

    # load cache to support friendly identifiers
    cache = Cache(session, refresh=update_cache)

    if group:
        group = cache.get_group_identifier(group)
        if not group:
            raise typer.Exit(1)

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

        # status and state keywords both allowed
        if params["status"] is None and state is not None:
            params["status"] = state.title()

        params = {k: v for k, v in params.items() if v is not None}

        if what == "device":
            if args:
                what, serial = cache.get_dev_identifier(args, ret_field="type-serial")

                if what and serial:
                    resp = session.get_dev_details(what, serial)
            else:  # show devices ... equiv to show all
                resp = session.get_all_devicesv2()

        elif what == "all":
            # if cache was updated this session get the data from there given no params (expected result may differ)
            if session.get_all_devicesv2 in cache.updated and len(params) == 2 and list(params.values()).count(False) == 2:
                resp = Response(ok=True, output=cache.devices)
            else:
                resp = session.get_all_devicesv2(**params)
        elif args:
            serial = cache.get_dev_identifier(args)
            resp = session.get_dev_details(what, serial)
            # device details is a lot of data default to yaml output, default horizontal would typically overrun tty
            if True not in [do_csv, do_json]:
                do_yaml = True
        else:
            resp = session.get_devices(what, **params)

    elif what == "groups":
        if session.get_all_groups in cache.updated:
            resp = Response(output=cache.groups)
        else:
            resp = session.get_all_groups()  # List[str]

    elif what == "sites":
        if args:
            dev_id = cache.get_site_identifier(args)

        if dev_id is None:
            if session.get_all_sites in cache.updated:
                resp = Response(output=cache.sites)
            else:
                resp = session.get_all_sites()
        else:
            resp = session.get_site_details(dev_id)

    # -- // SHOW TEMPLATE \\ --
    elif what == "template":
        params = {
            "name": name,
            "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
            "version": version,
            "model": model
        }

        params = {k: v for k, v in params.items() if v is not None}

        if args:
            if len(args) > 1:
                log.error(f"Only expecting 1 argument for show template, ignoring {args[1:]}", show=True)
            args = args[0]

        if not args:
            if not group:  # show templates
                if session.get_all_templates in cache.updated:
                    resp = Response(output=cache.templates)
                else:
                    resp = session.get_all_templates(**params)
            else:  # show templates --group <group name>
                resp = session.get_all_templates_in_group(group, **params)
        elif group:  # show template <arg> --group <group_name>
            _args = cache.get_template_identifier(args)
            if _args:  # name of template
                resp = session.get_template(group, args)
            else:
                _args = cache.get_dev_identifier(args)
                if _args:
                    typer.secho(f"{args} Does not match a Template name, but does match device with serial {_args}", fg="cyan")
                    typer.secho(f"Fetching Variablised Template for {args}", fg="cyan")
                    msg = (
                        f"{typer.style(f'--group {group} is not required for device specific template output.  ', fg='cyan')}"
                        f"{typer.style(f'ignoring --group {group}', fg='red')}"
                        )
                    typer.echo(msg)
                    resp = session.get_variablised_template(_args)
        else:  # provided args but no group
            _args = cache.get_dev_identifier(args)
            if _args:  # assume arg is device identifier 1st
                resp = session.get_variablised_template(_args)
            else:  # next try template names
                _args = cache.get_template_identifier(args, ret_field="group-name")
                if _args:
                    group, tmplt_name = _args[0], _args[1]
                    resp = session.get_template(group, tmplt_name)
                else:
                    raise typer.Exit(1)

    elif what == "variables":
        # switch default output to json for show variables
        if True not in [do_csv, do_yaml]:
            do_json = True

        if args and args != "all":
            args = cache.get_dev_identifier(args)

        resp = session.get_variables(args)

    elif what == "certs":
        resp = session.get_certificates()

    elif what == "clients":
        resp = session.get_clients(args)

    elif what == "cache":
        do_json = True
        resp = Response(ok=True, output=cache.all)

    # TODO remove after verifying we never return a NoneType
    if resp is None:
        print("Developer Message: resp returned NoneType")

    data = eval_resp(resp)

    if data:
        if do_json is True:
            tablefmt = "json"
        elif do_yaml is True:
            tablefmt = "yaml"
        elif do_csv is True:
            tablefmt = "csv"
        elif do_rich is True:
            tablefmt = "rich"
        else:
            tablefmt = "simple"

        outdata = utils.output(data, tablefmt)
        typer.echo_via_pager(outdata) if not no_pager and len(outdata) > tty.rows else typer.echo(outdata)

        # -- // Output to file \\ --
        if outfile and outdata:
            if outfile.parent.resolve() == config.base_dir.resolve():
                config.outdir.mkdir(exist_ok=True)
                outfile = config.outdir / outfile

            print(
                typer.style(f"\nWriting output to {outfile.resolve().relative_to(Path.cwd())}... ", fg="cyan"),
                end=""
            )
            outfile.write_text(outdata.file)  # typer.unstyle(outdata) also works
            typer.secho("Done", fg="green")
            # typer.launch doesn't appear to work on wsl tries to use ps to launch
            # typer.echo("Opening config directory")
            # typer.launch(str(outfile), locate=True)

    # else:
    #     typer.echo("No Data Returned")


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
                cache = Cache(session)
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
def do(what: DoArgs = typer.Argument(...),
       args1: str = typer.Argument(..., metavar="Identifying Attributes: [serial #|name|ip address|mac address]"),
       args2: str = typer.Argument(None, metavar="identifying attribute i.e. port #, required for some actions."),
       yes: bool = typer.Option(False, "-Y", metavar="Bypass confirmation prompts - Assume Yes"),
       debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                                  callback=debug_callback),
       account: str = typer.Option("central_info",
                                   envvar="ARUBACLI_ACCOUNT",
                                   help="The Aruba Central Account to use (must be defined in the config)",
                                   callback=account_name_callback),
       ) -> None:

    if not args1:
        typer.secho("Operation Requires additional Argument: [serial #|name|ip address|mac address]", fg="red")
        typer.echo("Examples:")
        typer.echo(f"> do {what} nash-idf21-sw1 {'2' if what.startswith('bounce') else ''}")
        typer.echo(f"> do {what} 10.0.30.5 {'2' if what.startswith('bounce') else ''}")
        typer.echo(f"> do {what} f40343-a0b1c2 {'2' if what.startswith('bounce') else ''}")
        typer.echo(f"> do {what} f4:03:43:a0:b1:c2 {'2' if what.startswith('bounce') else ''}")
        typer.echo("\nWhen Identifying device by Mac Address most commmon MAC formats are accepted.\n")
        raise typer.Exit(1)
    else:
        if what.startswith("bounce") and not args2:
            typer.secho("Operation Requires additional Argument: <port #>", fg="red")
            typer.echo("Example:")
            typer.echo(f"> do {what} {args1} 2")
            raise typer.Exit(1)

        cache = Cache(session)
        serial = cache.get_dev_identifier(args1)
        kwargs = {
            "serial_num": serial,
        }

    # -- // do the Command \\ --
    if yes or typer.confirm(typer.style(f"Please Confirm {what} {args1} {args2}", fg="cyan")):
        resp = getattr(session, what.replace("-", "_"))(args2, **kwargs)
        typer.echo(resp)
        if resp.ok:
            typer.echo(f"{typer.style('Success', fg='green')} command Queued.")
            # always returns queued on success even if the task is done
            resp = session.get_task_status(resp.task_id)
            typer.secho(f"Task Status: {resp.get('reason', '')}, State: {resp.state}", fg="green" if resp.ok else "red")

    else:
        raise typer.Abort()


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

    typer.secho(f"session.{method}({(args)}, {kwargs})", fg="green")
    resp = getattr(session, method)(*args, **kwargs)
    for k, v in resp.__dict__.items():
        typer.echo(f"{k}: {v}")


@app.callback()
def callback():
    """
    Aruba Central API CLI
    """


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()
