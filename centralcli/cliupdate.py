#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys
from typing import TYPE_CHECKING, List, Union
# from typing import List
import typer
from rich import print
from rich.console import Console
from rich.text import Text
from rich.markup import escape
from jinja2 import FileSystemLoader, Environment
import yaml

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import utils, cli, cleaner, BatchRequest, log
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import utils, cli, cleaner, BatchRequest, log
    else:
        print(pkg_dir.parts)
        raise e

from .constants import IdenMetaVars, DevTypes, GatewayRole, NotifyToArgs, state_abbrev_to_pretty, RadioBandOptions, DynamicAntMode, flex_dual_models
from . import render
from .cache import CacheTemplate
from .caas import CaasAPI

if TYPE_CHECKING:
    from .cache import CacheDevice, CacheGroup, CachePortal


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
        help=f"Template: {escape(f'[name] or Device: {iden_meta.dev}')}",
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
    else:
        cache_template = obj

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
        # will exit above if call failed.
        cache_template.data["template_hash"] = cli.central.request(cli.get_file_hash, file=template, string=payload)
        _ = cli.central.request(cli.cache.update_template_db, data=cache_template.data)


@app.command(help="Update existing or add new Variables for a device/template")
def variables(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=cli.cache.dev_completion, show_default=False,),
    var_value: List[str] = typer.Argument(..., help="comma seperated list 'variable = value, variable2 = value2'", show_default=False,),
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
        cli.exit("Something went wrong parsing variables.  Unequal length for Variables vs Values")

    var_dict = {k: v for k, v in zip(vars, vals)}

    con = Console(emoji=False)
    msg = "Sending Update" if yes else "Please Confirm: [bright_green]Update[/]"
    con.print(f"{msg} {dev.rich_help_text}")
    _ = [con.print(f'    {k}: [bright_green]{v}[/]') for k, v in var_dict.items()]
    if cli.confirm(yes):
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
    group_dev: CacheDevice | CacheGroup = cli.cache.get_identifier(group_dev, qry_funcs=["group", "dev"], device_type=["ap", "gw"])
    config_out = utils.generate_template(cli_file, var_file=var_file)
    cli_cmds = utils.validate_config(config_out)

    output = render.output(cli_cmds)
    output = Text.from_ansi(output.tty)

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
        caasapi = CaasAPI(central=cli.central)
        node_iden = group_dev.name if group_dev.is_group else group_dev.mac
    elif do_ap or (device and device.generic_type == "ap"):
        if device and device.generic_type != "ap":
            cli.exit(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
        use_caas = False
        node_iden = group_dev.name if group_dev.is_group else group_dev.serial

    cli.console.rule("Configuration to be sent")
    cli.console.print(output, emoji=False)
    cli.console.rule()
    cli.console.print(f"\nUpdating {'group' if group_dev.is_group else group_dev.generic_type.upper()} [cyan]{group_dev.name}[/]")
    if cli.confirm(yes):
        if use_caas:
            resp = cli.central.request(caasapi.send_commands, node_iden, cli_cmds)
            cli.display_results(resp, cleaner=cleaner.parse_caas_response)
        else:
            # FIXME this is OK for group level ap config , for AP this method is not valid
            if group_dev.is_dev:
                cli.exit("Not Implemented yet for AP device level updates")
            resp = cli.central.request(cli.central.replace_ap_config, node_iden, cli_cmds)
            cli.display_results(resp, tablefmt="action")

# TODO Add access spectrum monitor mode support, move logic to clicommon, and build batch update
@app.command()
def ap(
    aps: List[str] = typer.Argument(..., metavar=iden_meta.dev_many, autocompletion=cli.cache.dev_ap_completion, show_default=False,),
    hostname: str = typer.Option(None, help="Rename/Set AP hostname", show_default=False),
    ip: str = typer.Option(None, help=f"Configure Static IP [grey62]{escape('[mask, gateway, and dns must be provided]')}[/]", show_default=False,),
    mask: str = typer.Option(None, help="Subnet mask in format 255.255.255.0 [grey62 italic]Required/Applies when --ip is provided[/]", show_default=False,),
    gateway: str = typer.Option(None, help="Default Gateway [grey62 italic]Required/Applies when --ip is provided[/]", show_default=False,),
    dns: List[str] = typer.Option(None, help="Space seperated list of dns servers. [grey62 italic]Required/Applies when --ip is provided[/]", show_default=False,),
    domain: str = typer.Option(None, help="DNS domain name.  [grey62 italic]Optional/Applies when --ip is provided[/]", show_default=False,),
    disable_radios: List[RadioBandOptions] = typer.Option(None, "-D", "--disable-radios", help="List of radio(s) to disable.", show_default=False,),
    enable_radios: List[RadioBandOptions] = typer.Option(None, "-E", "--enable-radios", help="List of radio(s) to enable.", show_default=False,),
    flex_dual_exclude: RadioBandOptions = typer.Option(
        None,
        "-e",
        "--flex-exclude",
        help="The radio to be excluded on flex dual band APs.  i.e. [cyan]--flex-exclude 2.4[/] means the 5Ghz and 6Ghz radios will be used.",
        show_default=False
    ),
    access_mode: List[RadioBandOptions] = typer.Option(None, "-A", "--access", help="Space seperated list of radio(s) to set to [cyan]access mode[/]", show_default=False, hidden=True),
    spectrum_mode: List[RadioBandOptions] = typer.Option(None, "-S", "--spectrum", help="Space seperated list of radio(s) to set to [cyan]spectrum mode[/]", show_default=False, hidden=True),
    monitor_mode: List[RadioBandOptions] = typer.Option(None, "-M", "--monitor", help="Space seperated list of radio(s) to set to [cyan]air monitor mode[/]", show_default=False, hidden=True),
    antenna_width: DynamicAntMode = typer.Option(None, "-W", "--antenna-width", help="Dynamic Antenna Width [grey62 italic]Only applies to AP 679[/]", show_default=False,),
    tagged_uplink_vlan: int = typer.Option(None, "-u", "--tagged-uplink-pvid", help="Configure Uplink VLAN (tagged).", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Update per-ap-settings (ap env)"""
    aps: List[CacheDevice] = [cli.cache.get_dev_identifier(ap, dev_type="ap") for ap in aps]

    disable_radios = None if not disable_radios else [r.value for r in disable_radios]
    enable_radios = None if not enable_radios else [r.value for r in enable_radios]
    flex_dual_exclude = None if not flex_dual_exclude else flex_dual_exclude.value
    antenna_width = None if not antenna_width else antenna_width.value

    radio_24_disable = None if not enable_radios or "2.4" not in enable_radios else False
    radio_5_disable = None if not enable_radios or "5" not in enable_radios else False
    radio_6_disable = None if not enable_radios or "6" not in enable_radios else False
    if disable_radios:
        for radio, var in zip(["2.4", "5", "6"], [radio_24_disable, radio_5_disable, radio_6_disable]):
            if radio in disable_radios and var is not None:
                cli.exit(f"Invalid combination you tried to enable and disable the {radio}Ghz radio")
            # var = None if radio not in disable_radios else True  # doesn't work
        radio_24_disable = None if "2.4" not in disable_radios else True
        radio_5_disable = None if "5" not in disable_radios else True
        radio_6_disable = None if "6" not in disable_radios else True


    kwargs = {
        "hostname": hostname,
        "ip": ip,
        "mask": mask,
        "gateway": gateway,
        "dns": dns,
        "domain": domain,
        "radio_24_disable": radio_24_disable,
        "radio_5_disable": radio_5_disable,
        "radio_6_disable": radio_6_disable,
        "uplink_vlan": tagged_uplink_vlan,
        "flex_dual_exclude": flex_dual_exclude,
        "dynamic_ant_mode": antenna_width,
    }
    if ip and not all([mask, gateway, dns]):
        cli.exit("[cyan]mask[/], [cyan]gateway[/], and [cyan]--dns[/] are required when [cyan]--ip[/] is provided.")
    if len(aps) > 1 and hostname or ip:
        cli.exit("Setting hostname/ip on multiple APs doesn't make sesnse")

    print(f"[bright_green]Updating[/]: {utils.summarize_list([ap.summary_text for ap in aps], color=None, pad=10).lstrip()}")
    print("\n[green italic]With the following per-ap-settings[/]:")
    _ = [print(f"  {k}: {v}") for k, v in kwargs.items() if v is not None]
    skip_flex = [ap for ap in aps if ap.model not in flex_dual_models]
    skip_width = [ap for ap in aps if ap.model not in ["679"]]

    warnings = []
    if flex_dual_exclude is not None and skip_flex:
        warnings += [f"[yellow]:information:[/]  Flexible dual radio [red]will be ignored[/] for {len(skip_flex)} AP, as the setting doesn't apply to those models."]
    if antenna_width is not None and skip_width:
        warnings += [f"[yellow]:information:[/]  Dynamic antenna width [red]will be ignored[/] for {len(skip_width)} AP, as the setting doesn't apply to those models."]
    if warnings:
        warn_text = '\n'.join(warnings)
        print(f"\n{warn_text}")

    # determine if any effective changes after skips for settings on invalid AP models
    changes = 2
    if not list(filter(None, list(kwargs.values())[0:-2])):
        if not flex_dual_exclude or (flex_dual_exclude and not [ap for ap in aps if ap not in skip_flex]):
            changes -= 1
        if not antenna_width or (antenna_width and not [ap for ap in aps if ap not in skip_width]):
            changes -= 1
    if not changes:
        cli.exit("No valid updates provided for the selected AP models... Nothing to do.")

    cli.confirm(yes)  # exits here if they abort
    batch_resp = cli.central.batch_request(
        [
            BatchRequest(
                cli.central.update_per_ap_settings,
                ap.serial,
                hostname=hostname,
                ip=ip,
                mask=mask,
                gateway=gateway,
                dns=dns,
                domain=domain,
                radio_24_disable=radio_24_disable,
                radio_5_disable=radio_5_disable,
                radio_6_disable=radio_6_disable,
                uplink_vlan=tagged_uplink_vlan,
                flex_dual_exclude=None if ap.model not in flex_dual_models else flex_dual_exclude,
                dynamic_ant_mode=None if ap.model != "679" else antenna_width,
            ) for ap in aps
        ]
    )

    cli.display_results(batch_resp, tablefmt="action")

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
        help=f"Group(s) to update (SSID must be defined in each group) [grey42]{escape('[default: All Groups that contain specified SSIDs will be updated]')}[/]",
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

def get_guest_id(portal_id: str, name: str) -> str:
    guest_resp = cli.central.request(cli.central.get_guests, portal_id)
    if not guest_resp:
        log.error(f"Unable to Update details for {name}, request to fetch visitor_id failed.", caption=True, log=True)
        cli.display_results(guest_resp, tablefmt="action", exit_on_fail=True)

    guests = [g for g in guest_resp.output if g["name"] == name]
    if not guests:
        cli.exit(f"Unable to update details for {name}, no match found while fetching visitor_id.")
    elif len(guests) > 1:
        guest_resp.output = guests
        cli.display_results(guest_resp, caption=f"Guests matching user {name}", tablefmt="yaml")
        cli.exit(f"Too many matches for {name} while fetching visitor_id.")
    else:
        return guests[0]["id"]

@app.command()
def guest(
    portal: str = typer.Argument(..., metavar=iden_meta.portal, autocompletion=cli.cache.portal_completion, show_default=False,),
    name: str = typer.Argument(..., show_default=False,),
    password: str = typer.Option(None,),  #  hide_input=True, prompt=True, confirmation_prompt=True),
    company: str = typer.Option(None, help="Company Name", show_default=False,),
    phone: str = typer.Option(None, help="Phone # of guest; Format: +[CountryCode][PhoneNumber]", show_default=False,),
    email: str = typer.Option(None, help="email of guest", show_default=False,),
    notify_to: NotifyToArgs = typer.Option(None, help="Notify to 'phone' or 'email'", show_default=False,),
    disable: bool = typer.Option(None, "-D", "--disable", help="disable the account", show_default=False,),
    enable: bool = typer.Option(None, "-E", "--enable", help="enable the account", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.account,
) -> None:
    """Update a previously created guest account"""
    if disable and enable:
        cli.exit("Invalid combination of options.  Using both [cyan]-E[/]|[cyan]--enable[/] and [cyan]-D[/]|[cyan]--disable[/] does not make sense.")
    elif disable:
        is_enabled = False
    elif enable:
        is_enabled = True
    else:
        is_enabled = None
    notify = True if notify_to is not None else None

    portal: CachePortal = cli.cache.get_name_id_identifier("portal", portal)
    visitor_id = get_guest_id(portal.id, name)

    # TODO move to utils used by add and update.
    _phone_strip = list("()-. ")
    if phone:
        phone_orig = phone
        phone = "".join([p for p in list(phone) if p not in _phone_strip])
        if not phone.startswith("+"):
            if not len(phone) == 10:
                cli.exit(f"phone number provided {phone_orig} appears to be [bright_red]invalid[/]")
            phone = f"+1{phone}"

    # TODO Add options for expire after / valid forever
    payload = {
        "portal_id": portal.id,
        "visitor_id": visitor_id,
        "name": name,
        "company_name": company,
        "phone": phone,
        "email": email,
        "notify": notify,
        "notify_to": None if not notify_to else notify_to.value,
        "is_enabled": is_enabled,
    }
    payload = utils.strip_none(payload)
    options = "\n  ".join(yaml.safe_dump(payload).splitlines())
    if password:
        payload["password"] = password

    _msg = f"[bright_green]Update[/] Guest: [cyan]{name}[/] with the following options:\n  {options}\n"
    if password:
        _msg += "\n[italic dark_olive_green2]Password not displayed[/]\n"
    print(_msg)
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.add_guest, **payload)
        password = None
        payload = None
        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Update existing Aruba Central objects
    """
    pass


if __name__ == "__main__":
    app()
