#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import List, Union
# from typing import List
import typer
from rich import print
from rich.console import Console
from jinja2 import FileSystemLoader, Environment
import yaml

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, cli, caas, cleaner, BatchRequest, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, cli, caas, cleaner, BatchRequest, log
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import IdenMetaVars, DevTypes, GatewayRole, state_abbrev_to_pretty
from centralcli import CentralObject
from .cache import CacheTemplate


SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."
tty = utils.tty
iden_meta = IdenMetaVars()

app = typer.Typer()


# TODO add support for j2 / variable conversion as with cencli update config
@app.command(help="Update an existing template")
def template(
    name: str = typer.Argument(
        ...,
        metavar="IDENTIFIER",
        help=f"Template: \[name] or Device: \{iden_meta.dev}",
        autocompletion=cli.cache.dev_template_completion,
        show_default=False,
    ),
    template: Path = typer.Argument(
        None,
        help="Path to file containing new template",
        exists=True,
        autocompletion=lambda incomplete: [],
        show_default=False,
    ),
    group: str = typer.Option(
        None,
        help="[Templates] The template group the template belongs to",
        autocompletion=cli.cache.group_completion,
        show_default=False,
    ),
    device_type: DevTypes = typer.Option(
        None, "--dev-type",
        help="[Templates] Filter by Device Type",
        show_default=False,
    ),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by version", show_default=False,),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    if group:
        group = cli.cache.get_group_identifier(group).name

    obj = cli.cache.get_identifier(
        name, ("template", "dev"), device_type=device_type, group=group
    )
    if obj.is_dev:
        _tmplt = [t for t in cli.cache.templates if t["group"] == obj.group and t["model"] in obj.model]

        if _tmplt and version:
            _tmplt = [t for t in _tmplt if t["version"] in ["ALL", version]]

        if len(_tmplt) != 1:
            cli.exit(f"Failed to determine template for {obj.name}.  Found: {len(_tmplt)}")

        cache_template = CacheTemplate(_tmplt[0])

    kwargs = {
        "name": cache_template.name,
        "group": group or cache_template.group,
        "device_type": device_type or cache_template.device_type,
        "version": version or cache_template.version,
        "model": model or cache_template.model
    }

    payload = None
    if not template:
        payload = utils.get_multiline_input(prompt="Paste in new template contents.")
        payload = payload.encode("utf-8")

    print(f"\n[bright_green]Updat{'ing' if yes else 'e'} Template[/] [cyan]{cache_template.name}[/] in group [cyan]{kwargs['group']}[/]")
    print(f"    Device Type: [cyan]{kwargs['device_type']}[/]")
    print(f"    Model: [cyan]{kwargs['model']}[/]")
    print(f"    Version: [cyan]{kwargs['version']}[/]")
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.update_existing_template, **kwargs, template=template, payload=payload)
        cli.display_results(resp, tablefmt="action", exit_on_fail=True)
        cache_template.data["template_hash"] = cli.central.request(cli.get_file_hash, file=template, string=payload)
        _ = cli.central.request(cli.cache.update_template_db, data=cache_template)


@app.command(help="Update existing or add new Variables for a device/template")
def variables(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion),
    var_value: List[str] = typer.Argument(..., help="comma seperated list 'variable = value, variable2 = value2'"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    serial = dev.serial

    vars, vals, get_next = [], [], False
    for var in var_value:
        var = var.rstrip(",")
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
            _ = var.replace(" = ", "=").replace("'", "").strip().split('=')
            vars += [_[0]]
            vals += [_[1]]
            get_next = False

    if len(vars) != len(vals):
        typer.secho("something went wrong parsing variables.  Unequal length for Variables vs Values")
        raise typer.Exit(1)

    var_dict = {k: v for k, v in zip(vars, vals)}

    con = Console(emoji=False)
    msg = "Sending Update" if yes else "Please Confirm: [bright_green]Update[/]"
    con.print(f"{msg} {dev.rich_help_text}")
    [con.print(f'    {k}: [bright_green]{v}[/]') for k, v in var_dict.items()]
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(
            cli.central.update_device_template_variables,
            serial,
            dev.mac,
            var_dict=var_dict
        )
        cli.display_results(resp, tablefmt="action")


@app.command(
    short_help="Update group properties.",
    help="Update group properties.",
)
def group(
    group: str = cli.arguments.group,
    wired_tg: bool = typer.Option(None, "--wired-tg", help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(None, "--wlan-tg", help="Manage AP configurations via templates"),
    gw_role: GatewayRole = typer.Option(None, help="Gateway Role", show_default=False,),
    aos10: bool = typer.Option(None, "--aos10", is_flag=True, help="Create AOS10 Group (default AOS8/IAP)", show_default=False),
    mb: bool = typer.Option(None, "--mb", help="Configure Group for MicroBranch APs (AOS10 only"),
    ap: bool = typer.Option(None, "--ap", help="Allow APs in group"),
    sw: bool = typer.Option(None, "--sw", help="Allow ArubaOS-SW switches in group."),
    cx: bool = typer.Option(None, "--cx", help="Allow ArubaOS-CX switches in group."),
    gw: bool = typer.Option(None, "--gw", help=f"Allow gateways in group.\n{' ':34}If No device types specified all are allowed."),
    mo_sw: bool = typer.Option(None, help="Monitor Only for ArubaOS-SW"),
    mo_cx: bool = typer.Option(None, help="Monitor Only for ArubaOS-CX"),
    # ap_user: str = typer.Option("admin", help="Provide user for AP group"),  # TODO build func to update group pass
    # ap_passwd: str = typer.Option(None, help="Provide password for AP group (use single quotes)"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    group = cli.cache.get_group_identifier(group)

    if all(x is None for x in [wired_tg, wlan_tg, gw_role, aos10, mb, ap, sw, cx, gw, mo_sw, mo_cx]):
        print(
            "[bright_red]Missing required options.[/bright_red] "
            "Use [italic bright_green]cencli update group ?[/italic bright_green] to see available options"
        )  # TODO is there a way to trigger help text
        raise typer.Exit(1)
    if not aos10 and mb:
        cli.exit("[bright_red]Error[/]: Microbranch is only valid if group is configured as [cyan]AOS10[/] group.")
    if (mo_sw or mo_cx) and wired_tg:
        cli.exit("[bright_red]Error[/]: Monitor only is not valid for template group.")
    if mo_sw is not None and not sw:
        print("Invalid combination --mo-sw not valid without --sw")
        print("[bright_red]Error: Monitor only can only be set when initially adding AOS-SW as allowed to group.")
        raise typer.Exit(1)
    if mo_cx is not None and not cx:
        print("Invalid combination --mo-cx not valid without --cx")
        print("[bright_red]Error: Monitor only can only be set when initially adding AOS-CX as allowed to group.")
        raise typer.Exit(1)

    allowed_types = []
    if ap:
        allowed_types += ["ap"]
    if sw:
        allowed_types += ["sw"]
    if cx:
        allowed_types += ["cx"]
    if gw:
        allowed_types += ["gw"]

    _msg = f"[cyan]Update [cyan]group [bright_green]{group.name}[/bright_green]"
    if aos10 is not None:
        _msg = f"{_msg}\n    [cyan]AOS10[/cyan]: [bright_green]{aos10 is True}[/bright_green]"
    if allowed_types:
        _msg = f"{_msg}\n    [cyan]Allowed Device Types[/cyan]: [bright_green]{allowed_types}[/bright_green]"
    if wired_tg is not None:
        _msg = f"{_msg}\n    [cyan]wired Template Group[/cyan]: [bright_green]{wired_tg is True}[/bright_green]"
    if wlan_tg is not None:
        _msg = f"{_msg}\n    [cyan]WLAN Template Group[/cyan]: [bright_green]{wlan_tg is True}[/bright_green]"
    if gw_role is not None:
        _msg = f"{_msg}\n    [cyan]Gateway Role[/cyan]: [bright_green]{gw_role or 'branch'}[/bright_green]"
    if mb is not None:
        _msg = f"{_msg}\n    [cyan]MicroBranch[/cyan]: [bright_green]{mb is True}[/bright_green]"
    if mo_sw is not None:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-SW: [bright_green]{mo_sw is True}[/bright_green]"
    if mo_cx is not None:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-CX: [bright_green]{mo_cx is True}[/bright_green]"
    print(f"{_msg}\n")

    kwargs = {
        "group": group.name,
        "wired_tg": wired_tg,
        "wlan_tg": wlan_tg,
        "allowed_types": allowed_types,
        "aos10": aos10,
        "microbranch": mb,
        "gw_role": gw_role,
        "monitor_only_sw": mo_sw,
    }

    if cli.confirm(yes):
        resp = cli.central.request(
            cli.central.update_group_properties,
            **kwargs
        )
        cli.display_results(resp, tablefmt="action")

def generate_template(template_file: Union[Path, str], var_file: Union[Path, str], group_dev: str):
    '''Generate configuration files based on j2 templates and provided variables
    '''
    template_file = Path(str(template_file)) if not isinstance(template_file, Path) else template_file
    var_file = Path(str(var_file)) if not isinstance(var_file, Path) else var_file

    config_data = yaml.load(var_file.read_text(), Loader=yaml.SafeLoader)

    env = Environment(loader=FileSystemLoader(str(template_file.parent)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_file.name)

    # TODO output to temp or out dir cwd could be non-writable
    group_dev = Path.cwd() / f"{group_dev}.cfg"
    group_dev.write_text(template.render(config_data))

    return group_dev



@app.command("config")
def config_(
    group_dev: str = cli.arguments.group_dev,
    # TODO collect multi-line input as option to paste in config
    cli_file: Path = typer.Argument(..., help="File containing desired config/template in CLI format.", exists=True, autocompletion=lambda incomplete: tuple(), show_default=False,),
    var_file: Path = typer.Argument(None, help="File containing variables for j2 config template.", exists=True, autocompletion=lambda incomplete: tuple(), show_default=False,),
    do_gw: bool = typer.Option(None, "--gw", help="Update group level config for gateways."),
    do_ap: bool = typer.Option(None, "--ap", help="Update group level config for APs."),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Update group or device level config (ap or gw).
    """
    group_dev: CentralObject = cli.cache.get_identifier(group_dev, qry_funcs=["group", "dev"], device_type=["ap", "gw"])
    config_out = utils.generate_template(cli_file, var_file=var_file)
    cli_cmds = utils.validate_config(config_out)

    # TODO render.py module with helper function to return styled rule/line
    console = Console(record=True, emoji=False)
    console.begin_capture()
    console.rule("Configuration to be sent")
    console.print("\n".join([f"[green]{line}[/green]" for line in cli_cmds]))
    console.rule()
    console.print(f"\nUpdating {'group' if group_dev.is_group else group_dev.generic_type.upper()} [cyan]{group_dev.name}[/]")
    _msg = console.end_capture()

    if group_dev.is_group:
        device = None
        if not do_ap and not do_gw:
            cli.exit("Invalid Input, --gw or --ap option must be supplied for group level config.")
    else:  # group_dev is a device iden
        device = group_dev

    if do_gw or (device and device.generic_type == "gw"):
        if device and device.generic_type != "gw":
            cli.exit(f"Invalid input: --gw option conflicts with {device.name} which is an {device.generic_type}")
        use_caas = True
        caasapi = caas.CaasAPI(central=cli.central)  # XXX Burried import
        node_iden = group_dev.name if group_dev.is_group else group_dev.mac
    elif do_ap or (device and device.generic_type == "ap"):
        if device and device.generic_type != "ap":
            cli.exit(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
        use_caas = False
        node_iden = group_dev.name if group_dev.is_group else group_dev.serial

    typer.echo(_msg)
    if cli.confirm(yes):
        if use_caas:
            resp = cli.central.request(caasapi.send_commands, node_iden, cli_cmds)
            cli.display_results(resp, cleaner=cleaner.parse_caas_response)
        else:
            # FIXME this is OK for group level ap config , for AP this method is not valid
            if group_dev.is_dev:
                print("Not Implemented yet for AP device level updates")
                raise typer.Exit(1)
            resp = cli.central.request(cli.central.replace_ap_config, node_iden, cli_cmds)
            cli.display_results(resp, tablefmt="action")


@app.command(
    short_help="Update webhook details",
    help="Update webhook details (name/urls)"
)
def webhook(
    wid: str = typer.Argument(..., help="Use show webhooks to get the wid"),  # TODO completion
    name: str = typer.Argument(...,),
    urls: List[str] = typer.Argument(..., help="webhook URLs"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    print("Updating WebHook: [cyan]{}[/cyan] with urls:\n  {}".format(name, '\n  '.join(urls)))
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.update_webhook, wid, name, urls)
        cli.display_results(resp, tablefmt="action")


@app.command()
def site(
    site_name: str = typer.Argument(..., show_default=False, autocompletion=cli.cache.site_completion, help="[green3]current[/] site name"),
    address: str = typer.Argument(None, help="street address, [italic green4](enclose in quotes)[/]", show_default=False),
    city: str = typer.Argument(None, show_default=False),
    state: str = typer.Argument(
        None,
        autocompletion=lambda incomplete: [
        s for s in [
            *list(state_abbrev_to_pretty.keys()),
            *list(state_abbrev_to_pretty.values())
            ]
            if s.lower().startswith(incomplete.lower())
        ],
        show_default=False
    ),
    zip: int = typer.Argument(None, help="zipcode", show_default=False),
    country: str = typer.Argument(None, show_default=False),
    new_name: str = typer.Option(None, show_default=False, help="Change Site Name"),
    lat: str = typer.Option(None, metavar="LATITUDE", show_default=False),
    lon: str = typer.Option(None, metavar="LONGITUDE", show_default=False),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """
    Update details for an existing site.

    Provide [cyan]geo-loc[/] or [cyan]address[/] details, not both.
    [italic]Google Maps "Plus Codes" are supported for address field.[/]

    If address is provided assoicated geo coordinates are automatically populated.
    If geo coordinates are provided, any address associated with the site is cleared.

    [italic green3]Wrap Arguments that contain spaces in quotes i.e. "5402 Champions Hill Dr"[/]
    """
    site_now = cli.cache.get_site_identifier(site_name)

    # These conversions just make the fields match what is used if done via GUI
    # We also populate Country for US if it's one of the US states/territories
    if state and len(state) == 2:
        state = state_abbrev_to_pretty.get(state, state)
        if not country and state in state_abbrev_to_pretty.values():
            country = "United States"
    if country and (country.upper() in ["US", "USA"] or "united states" in country.lower()):
        country = "United States"
    if city and city.endswith(","):
        city = city.rstrip(",")

    kwargs = {
        "address": address,
        "city": city,
        "state": state,
        "zipcode": zip if zip is None else str(zip),
        "country": country,
        "latitude": lat,
        "longitude": lon
    }
    address_fields = {k: v for k, v in kwargs.items() if v}

    if not address_fields and not new_name:
        cli.exit("[red]No Update data provided[/]\n[italic]Must provide address data and/or --new-name.")

    print(f"Updating Site: {site_now.summary_text}")
    print(f" [bright_green]Send{'ing' if yes else ''} the following updates:[reset]")
    rename_only = False
    if new_name and site_now.name != new_name:
        # Only provided new name send current address info to endpoint along with new name (name alone not allowed)
        if not address_fields:  # update requires either address fields or lon/lat even to change the name so send back existing data from cache with new name
            rename_only = True
            geo_keys = ["latitude", "longitude"]
            address_fields = {k: v for k, v in site_now.data.items() if k in kwargs.keys() and k not in geo_keys and v}
            if not address_fields:
                address_fields = {k: v for k, v in site_now.data.items() if k in geo_keys and v}

        print(f"  Change Name [red]{site_now.name}[/] --> [bright_green]{new_name}[/]")
    if rename_only:
        print("\n [italic green4]current address info being sent as it's required by API to change name[/]")
    _ = [print(f"  {k}: {v}") for k, v in address_fields.items()]
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.update_site, site_now.id, new_name or site_now.name, **address_fields)
        cli.display_results(resp, exit_on_fail=True)
        if resp:
            cli.central.request(cli.cache.update_site_db, data={"name": new_name or site_now.name, "id": site_now.id, **address_fields})


@app.command()
def wlan(
    wlan: str = typer.Argument(..., help="SSID to update", show_default=False,),
    groups: List[str] = typer.Argument(
        None,
        help="Group(s) to update (SSID must be defined in each group) [grey42]\[default: All Groups that contain specified SSIDs will be updated][/]",
        autocompletion=cli.cache.group_completion,
        show_default=False,
    ),
    ssid: str = typer.Option(None, help="Update SSID name", show_default=False,),
    hide: bool = typer.Option(None, show_default=False,),
    vlan: str = typer.Option(None, show_default=False,),
    zone: str = typer.Option(None, show_default=False,),
    psk: str = typer.Option(None, show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Update configuration options of an existing WLAN/SSID
    """
    if groups:
        _groups = [cli.cache.get_group_identifier(group) for group in groups]
        batch_req = [BatchRequest(cli.central.get_wlan, group=group.name, wlan_name=wlan) for group in _groups]
    else:  # TODO coppied from show wlans -v make common func
        group_res = cli.central.request(cli.central.get_groups_properties)
        if not group_res:
            log.error(f"Unable to determine Groups that contain SSID {wlan}", caption=True,)
            cli.display_results(group_res, exit_on_fail=True)

        groups = [g['group'] for g in group_res.output if 'AccessPoints' in g['properties']['AllowedDevTypes']]
        batch_req = [BatchRequest(cli.central.get_wlan, group=group, wlan_name=wlan) for group in groups]

    cli.central.silent = True
    batch_resp = cli.central.batch_request(batch_req)
    cli.central.silent = False

    failed, passed = [], []
    config_b4_dict = {}
    for group, res in zip(groups, batch_resp):
        if res.ok:
            passed += [res]
            config_b4_dict[group] = res.output.get("wlan", res.output)
        else:
            failed += [res]

    if failed:
        unexpected_failures = [
            f for f in failed
            if "cannot find" not in f.output.get("description").lower() and f.output.get("description") != "Invalid configuration ID"
        ]
        if unexpected_failures:
            print(f":warning:  Unexpected error while querying groups for existense of {wlan}")
            cli.display_results(unexpected_failures, exit_on_fail=False)

    if not config_b4_dict:
        cli.exit("Nothing to do", code=0)

    # TODO check if provided values differ from what's there already
    update_req = []
    for group in config_b4_dict:
        kwargs = {
            "scope": group,
            "wlan_name": wlan,
            "essid": ssid or config_b4_dict[group]["essid"],
            "type": config_b4_dict[group]["type"],
            "hide_ssid": hide if hide is not None else config_b4_dict[group]["hide_ssid"],
            "vlan": vlan or config_b4_dict[group]["vlan"],
            "zone": zone or config_b4_dict[group]["zone"],
            "wpa_passphrase": psk or config_b4_dict[group]["wpa_passphrase"],
            "captive_profile_name": config_b4_dict[group]["captive_profile_name"],
            "bandwidth_limit_up": config_b4_dict[group]["bandwidth_limit_up"],
            "bandwidth_limit_down": config_b4_dict[group]["bandwidth_limit_down"],
            "bandwidth_limit_peruser_up": config_b4_dict[group]["bandwidth_limit_peruser_up"],
            "bandwidth_limit_peruser_down": config_b4_dict[group]["bandwidth_limit_peruser_down"],
            "access_rules": config_b4_dict[group]["access_rules"],
        }
        update_req += [
            BatchRequest(cli.central.update_wlan, **kwargs)
        ]

    options = {
        "SSID name": ssid,
        "vlan": vlan,
        "zone": zone,
        "psk": psk,
    }
    print(f"Update WLAN Profile {wlan} in groups [cyan]{'[/], [cyan]'.join(list(config_b4_dict.keys()))}[/]")
    print('\n'.join([f"  [bright_green]-[/] Update [cyan]{k}[/] -> [bright_green]{v}[/]" for k, v in options.items() if v is not None]))
    if hide is not None:
        print(f"  [bright_green]-[/] Update [cyan]Visability[/] -> [bright_green]{'Visable (not hidden)' if not hide else 'hidden'}[/]")

    if yes or typer.confirm("\nProceed?", abort=True):
        update_res = cli.central.batch_request(update_req)
        cli.display_results(update_res)


@app.callback()
def callback():
    """
    Update existing Aruba Central objects
    """
    pass


if __name__ == "__main__":
    app()
