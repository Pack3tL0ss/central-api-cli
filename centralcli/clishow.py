import typer
import time
import asyncio
import sys
import json
from typing import List, Union, Any
from pathlib import Path
# from centralcli import config, log, Cache, Response, utils


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi
from centralcli.constants import ClientArgs, StatusOptions, SortOptions

app = typer.Typer()


tty = utils.tty
show_help = ["all (devices)", "device[s] (same as 'all' unless followed by device identifier)", "switch[es]", "ap[s]",
             "gateway[s]", "group[s]", "site[s]", "clients", "template[s]", "variables", "certs"]
args_metavar_dev = "[name|ip|mac-address|serial]"
args_metavar_site = "[name|site_id|address|city|state|zip]"
args_metavar = f"""Optional Identifying Attribute: {args_metavar_dev}"""


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
        return typer.style(
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


def default_callback(ctx: typer.Context, default: bool):
    if ctx.resilient_parsing:  # tab completion, return without validating
        return

    if default and config.sticky_account_file.is_file():
        typer.secho('Using default central account', fg="cyan")
        config.sticky_account_file.unlink()


def debug_callback(debug: bool):
    if debug:
        log.DEBUG = config.debug = debug


def get_format(
    do_json: bool = False,
    do_yaml: bool = False,
    do_csv: bool = False,
    do_rich: bool = False,
    default: str = "simple"
) -> str:
    if do_json:
        return "json"
    elif do_yaml:
        return "yaml"
    elif do_csv:
        return "csv"
    elif do_rich:
        return "rich"
    else:
        return default


def eval_resp(resp: Response, pad: int = 0, sort_by: str = None) -> Any:
    if not resp.ok:
        msg = f"{' ' * pad}{typer.style('ERROR:', fg=typer.colors.RED)} "
        if isinstance(resp.output, dict):
            _msg = resp.output.get('description', resp.output.get('detail', '')).replace('Error: ', '')
            if _msg:
                msg += _msg
            else:
                msg += json.dumps(resp.output)
        else:
            msg += str(resp.output)

        typer.echo(msg)
    else:
        # TODO sort output
        if sort_by is not None:
            typer.secho("sort option not implemented yet", fg="red")

        return resp.output


# TODO combine eval_resp and display_results
# TODO cleaner moves here (for now), then eventually to an output object (in utils now)
#   prep for breaking API into separate package.
def display_results(data: Union[List[dict], List[str], None], tablefmt: str = "simple",
                    pager=True, outfile: Path = None, cleaner: callable = None, cleaner_kwargs: dict = {}) -> Union[list, dict]:
    if data:
        if cleaner:
            data = cleaner(data, **cleaner_kwargs)

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


def show_devices(
    dev_type: str, *args, outfile: Path = None, update_cache: bool = False, group: str = None, status: str = None,
    state: str = None, label: Union[str, List[str]] = None, pub_ip: str = None, do_clients: bool = False,
    do_stats: bool = False, sort_by: str = None, no_pager: bool = False, do_json: bool = False, do_csv: bool = False,
    do_yaml: bool = False, do_rich: bool = False
) -> None:
    cache(refresh=update_cache)

    if group:
        group = cache.get_group_identifier(group)
        if not group:
            raise typer.Exit(1)

    # -- // Peform GET Call \\ --
    resp = None
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

    if dev_type == "device":
        if args:
            dev_type, serial = cache.get_dev_identifier(args, ret_field="type-serial")

            if dev_type and serial:
                resp = session.request(session.get_dev_details, dev_type, serial, **params)
        else:  # show devices ... equiv to show all
            resp = session.request(session.get_all_devicesv2, **params)

    elif dev_type == "all":
        # if no params (expected result may differ) update cache if not updated this session and return results from there
        if len(params) == 2 and list(params.values()).count(False) == 2:
            if session.get_all_devicesv2 not in cache.updated:
                asyncio.run(cache.update_dev_db())

            resp = Response(output=cache.devices)
        else:  # will only run if user specifies params (filters)
            resp = session.request(session.get_all_devicesv2, **params)

    # aps, switches, gateways, ...
    elif args:
        serial = cache.get_dev_identifier(args)
        resp = session.request(session.get_dev_details, dev_type, serial)
        # device details is a lot of data default to yaml output, default horizontal would typically overrun tty
        if True not in [do_csv, do_json]:
            do_yaml = True
    else:
        resp = session.request(session.get_devices, dev_type, **params)

    data = eval_resp(resp)

    if data:
        tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)
        display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show APs/details")
def aps(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    show_devices(
        'aps', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show switches/details")
def switches(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    show_devices(
        'switches', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show interfaces/details")
def interfaces(
    device: str = typer.Argument(..., metavar=args_metavar_dev, hidden=False),
    slot: str = typer.Argument(None, help="Slot name of the ports to query (chassis only)",),
    # port: List[int] = typer.Argument(None, help="Optional list of interfaces to filter on"),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    cache(refresh=update_cache)
    dev_type, serial = cache.get_dev_identifier(device, ret_field="type-serial")

    resp = session.request(session.get_switch_ports, serial, cx=dev_type == "CX")
    data = eval_resp(resp)
    if data:
        tablefmt = get_format(do_json=None, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

        display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show All Devices")
def all(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    show_devices(
        'all', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show devices [identifier]")
def devices(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    type_to_link = {
        'ap': 'aps',
        'SW': 'switches',
        'CX': 'switches',
        'gateway': 'gateways'
    }
    if args[0] == 'all':
        dev_type = 'all'
        args = () if len(args) == 1 else args[1:]

    if args:
        dev_type, args = cache.get_dev_identifier(args, ret_field="type-serial")
        args = utils.listify(args)
        dev_type = type_to_link.get(dev_type, dev_type)
    else:  # show devices ... equiv to show all
        dev_type = 'all'

    show_devices(
        dev_type, *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show gateways/details")
def gateways(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    show_devices(
        'gateways', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show controllers/details")
def controllers(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),  # TODO cache group names
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    status: StatusOptions = typer.Option(None, metavar="[up|down]", help="Filter by device status"),
    state: StatusOptions = typer.Option(None, hidden=True),  # alias for status
    pub_ip: str = typer.Option(None, metavar="<Public IP Address>", help="Filter by Public IP"),
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
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    show_devices(
        'mobility_controllers', *args, outfile=outfile, update_cache=update_cache, group=group, status=status,
        state=state, label=label, pub_ip=pub_ip, do_clients=do_clients, do_stats=do_stats,
        sort_by=sort_by, no_pager=no_pager, do_json=do_json, do_csv=do_csv, do_yaml=do_yaml,
        do_rich=do_rich)


@app.command(short_help="Show contents of Identifier Cache.")
def cache(
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Alpha Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    cache(refresh=update_cache)
    resp = Response(output=cache.all)
    data = eval_resp(resp)
    if data:
        tablefmt = get_format(do_json=None, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command(short_help="Show groups/details")
def groups(
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    if session.get_all_groups not in cache.updated:
        asyncio.run(cache.update_group_db())

        resp = Response(output=cache.groups)
        data = eval_resp(resp)
        display_results(data, tablefmt='rich', pager=not no_pager, outfile=outfile)


@app.command(short_help="Show sites/details")
def sites(
    args: List[str] = typer.Argument(None, metavar=args_metavar_site, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
    cache(refresh=update_cache)
    site_id = None
    if args:
        site_id = cache.get_site_identifier(args)

    if site_id is None:
        if session.get_all_sites not in cache.updated:
            asyncio.run(cache.update_site_db())
        resp = Response(output=cache.sites)
    else:
        resp = session.request(session.get_site_details, site_id)

    data = eval_resp(resp)
    if data:
        tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)

        display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def templates(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    group: str = typer.Option(None, "--group", help="Get Templates for Group"),
    name: str = typer.Option(None, metavar="<Template Name>", help="[Templates] Filter by Template Name"),
    device_type: str = typer.Option(None, "--dev-type", metavar="[IAP|ArubaSwitch|MobilityController|CX]>",
                                    help="[Templates] Filter by Device Type"),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by dev version Template is assigned to"),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model"),
    #  variablised: str = typer.Option(False, "--with-vars",
    #                                  help="[Templates] Show Template with variable place-holders and vars."),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback),
):
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
            if session.get_all_templates not in cache.updated:
                asyncio.run(cache.update_template_db())

            # TODO using cache breaks filtering params
            resp = Response(output=cache.templates)
        else:  # show templates --group <group name>
            resp = session.request(session.get_all_templates_in_group, group, **params)
    elif group:  # show template <arg> --group <group_name>
        _args = cache.get_template_identifier(args)
        if _args:  # name of template
            resp = session.request(session.get_template, group, args)
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
                resp = session.request(session.get_variablised_template, _args)
    else:  # provided args but no group
        _args = cache.get_dev_identifier(args, retry=False)
        if _args:  # assume arg is device identifier 1st
            resp = session.request(session.get_variablised_template, _args)
        else:  # next try template names
            _args = cache.get_template_identifier(args, ret_field="group-name")
            if _args:
                group, tmplt_name = _args[0], _args[1]
                resp = session.request(session.get_template, group, tmplt_name)
            else:
                # typer.secho(f"No Match Found for {args} in Cachce")
                raise typer.Exit(1)

    data = eval_resp(resp)
    if data:
        tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich)

        display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def variables(
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback)
):
    cache(refresh=update_cache)

    if args and args != "all":
        args = cache.get_dev_identifier(args)

    resp = session.request(session.get_variables, args)
    data = eval_resp(resp)
    tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def lldp(
    device: List[str] = typer.Argument(..., metavar=args_metavar_dev, hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback)
):
    cache(refresh=update_cache)

    device = cache.get_dev_identifier(device[-1])  # take last arg from list so they can type "neighbor" if they want.
    resp = session.request(session.get_ap_lldp_neighbor, device)
    data = eval_resp(resp)
    tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile, cleaner=cleaner.get_lldp_neighbor)


@app.command()
def certs(
    name: str = typer.Argument(None, metavar='[certificate name|certificate hash]', hidden=False),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    sort_by: SortOptions = typer.Option(None, "--sort"),
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",
                                 callback=default_callback),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
                               callback=debug_callback),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",
                                callback=account_name_callback)
):
    resp = session.request(session.get_certificates, name, callback=cleaner.get_certificates)
    data = eval_resp(resp)
    tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

    display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def clients(
    filter: ClientArgs = typer.Argument('all', case_sensitive=False, ),
    args: List[str] = typer.Argument(None, metavar=args_metavar_dev, help="Show clients for a specific device"),
    # os_type:
    # band:
    group: str = typer.Option(None, metavar="<Device Group>", help="Filter by Group", ),
    label: str = typer.Option(None, metavar="<Device Label>", help="Filter by Label", ),
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    sort_by: SortOptions = typer.Option(None, "--sort", hidden=True,),  # TODO Unhide after implemented
    reverse: SortOptions = typer.Option(None, "-r", hidden=True,),  # TODO Unhide after implemented
    verbose: bool = typer.Option(False, "-v", hidden=True,),  # TODO Unhide after implemented
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        callback=default_callback,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        callback=debug_callback,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        callback=account_name_callback,
    ),
):
    # TODO quick and dirty, make less dirty (the way I passed cache all the way through **kwargs to cleanerq)
    resp = session.request(session.get_clients, filter, *args, callback_kwargs={'cache': cache})
    data = eval_resp(resp)
    tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="json")

    display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.command()
def logs(
    # args: List[str] = typer.Argument(None, metavar=args_metavar_dev, help="Show clients for a specific device"),
    # os_type:
    # band:
    do_json: bool = typer.Option(False, "--json", is_flag=True, help="Output in JSON"),
    do_yaml: bool = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML"),
    do_csv: bool = typer.Option(False, "--csv", is_flag=True, help="Output in CSV"),
    do_rich: bool = typer.Option(False, "--rich", is_flag=True, help="Beta Testing rich formatter"),
    outfile: Path = typer.Option(None, help="Output to file (and terminal)", writable=True),
    update_cache: bool = typer.Option(False, "-U", hidden=True),  # Force Update of cache for testing
    sort_by: SortOptions = typer.Option(None, "--sort", hidden=True,),  # TODO Unhide after implemented
    reverse: SortOptions = typer.Option(None, "-r", hidden=True,),  # TODO Unhide after implemented
    verbose: bool = typer.Option(False, "-v", hidden=True,),  # TODO Unhide after implemented
    no_pager: bool = typer.Option(False, "--no-pager", help="Disable Paged Output"),
    default: bool = typer.Option(
        False, "-d",
        is_flag=True,
        help="Use default central account",
        callback=default_callback,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        envvar="ARUBACLI_DEBUG",
        help="Enable Additional Debug Logging",
        callback=debug_callback,
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        callback=account_name_callback,
    ),
):
    # TODO start_time typer.Option pendumlum.... 3H 5h 20m etc. add other filter options
    resp = session.request(session.get_audit_logs, start_time=int(time.time() - 172800),)
    data = eval_resp(resp)
    tablefmt = get_format(do_json=do_json, do_yaml=do_yaml, do_csv=do_csv, do_rich=do_rich, default="rich")

    display_results(data, tablefmt=tablefmt, pager=not no_pager, outfile=outfile)


@app.callback()
def callback():
    """
    Show Details about Aruba Central Objects
    """
    pass


if __name__ == "__main__":
    app()
