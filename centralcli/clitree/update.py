#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.markup import escape
from rich.text import Text

from centralcli import cleaner, common, log, render, utils
from centralcli.caas import CaasAPI
from centralcli.cache import CacheCert, CacheDevice, CacheGroup, CachePortal, CacheTemplate, api
from centralcli.client import BatchRequest
from centralcli.config import VALID_EXT
from centralcli.constants import DevTypes, DynamicAntMode, GatewayRole, IAPTimeZoneNames, NotifyToArgs, RadioBandOptions, iden_meta, state_abbrev_to_pretty

SPIN_TXT_AUTH = "Establishing Session with Aruba Central API Gateway..."
SPIN_TXT_CMDS = "Sending Commands to Aruba Central API Gateway..."
SPIN_TXT_DATA = "Collecting Data from Aruba Central API Gateway..."


app = typer.Typer()


# TODO add support for j2 / variable conversion as with cencli update config
@app.command(help="Update an existing template")
def template(
    name: str = typer.Argument(
        ...,
        metavar="IDENTIFIER",
        help=f"Template: {escape(f'[name] or Device: {iden_meta.dev}')}",
        autocompletion=common.cache.dev_template_completion,
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
        autocompletion=common.cache.group_completion,
        show_default=False,
    ),
    device_type: DevTypes = typer.Option(
        None, "--dev-type",
        help="[Templates] Filter by Device Type",
        show_default=False,
    ),
    version: str = typer.Option(None, metavar="<version>", help="[Templates] Filter by version", show_default=False,),
    model: str = typer.Option(None, metavar="<model>", help="[Templates] Filter by model", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    if group:
        group = common.cache.get_group_identifier(group).name

    obj = common.cache.get_identifier(
        name, ("template", "dev"), device_type=device_type, group=group
    )
    if obj.is_dev:
        _tmplt = [t for t in common.cache.templates if t["group"] == obj.group and t["model"] in obj.model]

        if _tmplt and version:
            _tmplt = [t for t in _tmplt if t["version"] in ["ALL", version]]

        if len(_tmplt) != 1:
            common.exit(f"Failed to determine template for {obj.name}.  Found: {len(_tmplt)}")

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

    render.econsole.print(f"\n[bright_green]Updat{'ing' if yes else 'e'} Template[/] [cyan]{cache_template.name}[/] in group [cyan]{kwargs['group']}[/]")
    render.econsole.print(f"    Device Type: [cyan]{kwargs['device_type']}[/]")
    render.econsole.print(f"    Model: [cyan]{kwargs['model']}[/]")
    render.econsole.print(f"    Version: [cyan]{kwargs['version']}[/]")
    if render.confirm(yes):
        resp = api.session.request(api.configuration.update_existing_template, **kwargs, template=template, payload=payload)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)
        # will exit above if call failed.
        cache_template.data["template_hash"] = api.session.request(common.get_file_hash, file=template, string=payload)
        _ = api.session.request(common.cache.update_template_db, data=cache_template.data)


@app.command(help="Update existing or add new Variables for a device/template")
def variables(
    device: str = typer.Argument(..., metavar=iden_meta.dev, autocompletion=common.cache.dev_completion, show_default=False,),
    var_value: list[str] = typer.Argument(..., help="comma seperated list 'variable = value, variable2 = value2'", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    dev = common.cache.get_dev_identifier(device)
    serial = dev.serial

    var_dict = common.parse_var_value_list(var_value)

    msg = "Sending Update" if yes else "Please Confirm: [bright_green]Update[/]"
    render.econsole.print(f"{msg} {dev.rich_help_text}", emoji=False)
    _ = [render.econsole.print(f'    {k}: [bright_green]{v}[/]', emoji=False) for k, v in var_dict.items()]
    if render.confirm(yes):
        resp = api.session.request(
            api.configuration.update_device_template_variables,
            serial,
            dev.mac,
            var_dict=var_dict
        )
        render.display_results(resp, tablefmt="action")


@app.command()
def group(
    group: str = common.arguments.group,
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
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update group properties."""
    group: CacheGroup = common.cache.get_group_identifier(group)

    if all(x is None for x in [wired_tg, wlan_tg, gw_role, aos10, mb, ap, sw, cx, gw, mo_sw, mo_cx]):
        common.exit(
            "[bright_red]Missing required options.[/bright_red] "
            "Use [italic bright_green]cencli update group ?[/italic bright_green] to see available options"
        )
    if not aos10 and mb:
        common.exit("[bright_red]Error[/]: Microbranch is only valid if group is configured as [cyan]AOS10[/] group.")
    if (mo_sw or mo_cx) and wired_tg:
        common.exit("[bright_red]Error[/]: Monitor only is not valid for template group.")
    if mo_sw is not None and not sw:
        common.exit(
            "Invalid combination --mo-sw not valid without --sw\n"
            "[bright_red]Error: Monitor only can only be set when initially adding AOS-SW as allowed to group."
        )
    if mo_cx is not None and not cx:
        common.exit(
            "Invalid combination --mo-cx not valid without --cx\n"
            "[bright_red]Error: Monitor only can only be set when initially adding AOS-CX as allowed to group."
        )

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
    render.econsole.print(f"{_msg}\n")

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

    if render.confirm(yes):
        resp = api.session.request(
            api.configuration.update_group_properties,
            **kwargs
        )
        render.display_results(resp, tablefmt="action")

def generate_template(template_file: Path | str, var_file: Path | str, group_dev: str):
    '''Generate configuration files based on j2 templates and provided variables
    '''
    template_file = Path(str(template_file)) if not isinstance(template_file, Path) else template_file
    var_file = Path(str(var_file)) if not isinstance(var_file, Path) else var_file

    config_data = yaml.load(var_file.read_text(), Loader=yaml.SafeLoader)

    env = Environment(loader=FileSystemLoader(str(template_file.parent)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_file.name)

    # TODO output to temp or out dir cwd could be non-writable
    group_dev: Path = Path.cwd() / f"{group_dev}.cfg"
    group_dev.write_text(template.render(config_data))

    return group_dev

config_help = f"""Update group or device level config (ap or gw).

[cyan]cli_file[/] Can be raw CLI (no variables or conditional logic) or a jinja2 template.
[italic][deep_sky_blue]:information:[/]  If the cli_file is a [medium_spring_green].j2[/] file the template will be converted based on variables in [cyan]var_file[/] prior to sending.[/italic]

If providing a jinja2 template, this command will automatically look for a [cyan]var_file[/] with the same name and a valid suffix [italic]({utils.color(VALID_EXT, color_str="medium_spring_green")})[/].
[cyan]--var-file <PATH>[/] can be used to specify the variable file explicitly.

"""
@app.command("config", help=config_help)
def config_(
    group_dev: str = common.arguments.get("group_dev", autocompletion=common.cache.group_dev_ap_gw_completion),
    cli_file: Path = typer.Argument(..., help="File containing desired config/template in CLI format.", exists=True, show_default=False,),
    var_file: Path = typer.Argument(None, help="File containing variables for j2 config template.", exists=True, show_default=False,),
    do_gw: bool = common.options.do_gw,
    do_ap: bool = common.options.do_ap,
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    group_dev: CacheDevice | CacheGroup = common.cache.get_identifier(group_dev, qry_funcs=["group", "dev"], device_type=["ap", "gw"])
    config_out = utils.generate_template(cli_file, var_file=var_file)
    cli_cmds = utils.validate_config(config_out)

    output = render.output(cli_cmds)
    output = Text.from_ansi(output.tty)

    if group_dev.is_group:
        device = None
        if not do_ap and not do_gw:
            common.exit("Invalid Input, --gw or --ap option must be supplied for group level config.")
    else:  # group_dev is a device iden
        device = group_dev

    if do_gw or (device and device.generic_type == "gw"):
        if device and device.generic_type != "gw":
            common.exit(f"Invalid input: --gw option conflicts with {device.name} which is an {device.generic_type}")
        use_caas = True
        caasapi = CaasAPI()
        node_iden = group_dev.name if group_dev.is_group else group_dev.mac
    elif do_ap or (device and device.generic_type == "ap"):
        if device and device.generic_type != "ap":
            common.exit(f"Invalid input: --ap option conflicts with {device.name} which is a {device.generic_type}")
        use_caas = False
        node_iden = group_dev.name if group_dev.is_group else group_dev.swack_id  # cache is populated with serial for swack_id for aos_10 so this works for both aos8 and aos10

    render.console.rule("Configuration to be sent")
    render.console.print(output, emoji=False)
    render.console.rule()
    if not group_dev.is_group and not group_dev.is_aos10:
        render.console.print(f"\nUpdating Swarm associted with {group_dev.generic_type.upper()} [cyan]{group_dev.name}[/]")
    else:
        render.console.print(f"\nUpdating {'group' if group_dev.is_group else group_dev.generic_type.upper()} [cyan]{group_dev.name}[/]")
    if render.confirm(yes):
        if use_caas:
            resp = api.session.request(caasapi.send_commands, node_iden, cli_cmds)
            render.display_results(resp, cleaner=cleaner.parse_caas_response)
        else:
            resp = api.session.request(api.configuration.replace_ap_config, node_iden, cli_cmds)
            render.display_results(resp, tablefmt="action")


# FIXME typer is not handling list[str] as expected.  Change groups metevar back to iden_meta.group_many once sorted.
# TODO check... Default for group ATM-LOCAL had "wlan cert-assignment-profile" no sub-commands below it...  it did not have "cp-cert-checksum ..."
#   update cp-cert ... added cp-cert-checksum, which removed "wlan cert-assignment-profile".  Need to verify what that is, thought the default was cp-cert-checksum pointing to default aruba cert.
@app.command()
def cp_cert(
    certificate: str = typer.Argument(
        ...,
        help="The certificate name or md5 checksum to use for Captive Portal. [dim italic red]Certificate must exist[/]",
        autocompletion=common.cache.cert_completion,
        show_default=False,
    ),
    groups: list[str] = common.options.get(
        "group_many", "-G", "--group",
        default=...,
        metavar=iden_meta.group.replace("NAME]", "NAME|all]"),
        help="The Group [dim italic](AP Group)[/] to be updated to use the Captive Portal certificate. [dark_orange3]:warning:[/]  [cyan]all[/] Will push to all AP groups",
        autocompletion=common.cache.group_ap_completion
    ),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update the Captive Portal certificate for APs at the group level

    This will update the certificate usage (cp-cert-checksum) at the group level (for APs) to reference the specified certificate.
    The certificate must be uploaded to Aruba Central first.  Use [cyan]cencli add certificate[/] to upload the certificate.
    and [cyan]cencli show certs[/] to see the available certificates.

    [dark_orange3]:warning:[/]  "--group|-G [red]all[/]" Will update Captive Portal certificate usage for **all** AP groups.

    :information:  Not supported on Template Groups.  [dim italic](They are filtered out if [cyan]all[/] is specified)[/]
    """
    cert: CacheCert = common.cache.get_cert_identifier(certificate)
    if cert.expired:
        common.exit(f"Aborting as {cert.summary_text} - is [bright_red bold]Expired[/].")
    if groups != ["all"]:
        groups: list[CacheGroup] = [common.cache.get_group_identifier(g, dev_type="ap") for g in groups]
    else:
        groups: list[CacheGroup] = common.cache.ap_groups

    # filter out Template Groups and CNX managed groups.
    groups = [g for g in groups if g.cnx is not True and not g.wlan_tg]

    _confirm_msg = f"Updat{'ing' if yes else 'e'} Captive Portal Certificate to {cert.name}|checksum: {cert.md5_checksum}\n  "
    if len(groups) > 1:
        _groups_txt = utils.color([g.name for g in groups], pad_len=4, sep='\n')
        _confirm_msg += f"in the following {len(groups)} groups:\n{_groups_txt}"
        _confirm_msg += f"\n\n[italic dark_olive_green2]Operation will result in {len(groups) * 2} API Calls."
    else:
        _confirm_msg += f"in group [bright_green]{groups[0].name}[/]"
    render.console.print(_confirm_msg)

    render.confirm(yes)
    group_names = [g.name for g in groups]
    resp = api.session.request(api.configuration.update_group_cp_cert, group_names, cp_cert_md5=cert.md5_checksum)
    render.display_results(resp, tablefmt="action")


@app.command(hidden=True)
def swarm(
    ap: str = typer.Argument(..., metavar=iden_meta.dev, help="Update the virtual controller/swarm associated with this AP", autocompletion=common.cache.dev_ap_completion, show_default=False,),
    name: str = typer.Option(None, help="The name to assign to the Virtual Controller", show_default=False,),
    ip: str = typer.Option(None, help="Configure static IP to assign to the Virtual Controller", show_default=False,),
    no_ip: bool = typer.Option(False, "--no-ip", help="Remove static IP currently assigned to Virtual Controller", show_default=False,),
    timezone: IAPTimeZoneNames = typer.Option(None, "--tz", help='timezone name', show_default=False),
    utc_offset: str = typer.Option(None, "-o", "--offset", help="Timezone offset in format h:mm where h = hours and mm = minutes.", show_default=False),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update AOS8 IAP swarm settings

    :warning:  It is recommended to do TimeZone updates via the UI currently, as API endpoint does not automatically add the appropriate daylight saving time rule
    """
    dev = common.cache.get_dev_identifier(ap, dev_type="ap", swack=True)
    if dev.is_aos10:
        common.exit("Command is only valid for AOS8 APs")

    offset_hr, offset_min, need_current_settings = None, None, False
    if utc_offset:
        try:
            offset_hr, offset_min = map(int, utc_offset.split(":"))
        except Exception as e:
            common.exit(f"[red dim]{e.__class__.__name__}[/]\nInvalid format for utc offset [cyan]{utc_offset}[/].  Should be in the form h:mm where h = hour, m = minutes i.e. 6:00 or -6:00.")

    kwargs = {
        "name": name,
        "ip_address": ip,
        "timezone": timezone if not timezone else timezone.value,
        "utc_offset": utc_offset
    }

    if all([v is None for v in kwargs.values()]) and not no_ip:
        common.exit("Nothing to do, No update options provided.")

    render.econsole.print(f"Updat{'ing' if yes else 'e'} Virtual Controller/swarm associated with [cyan]{dev.name}[/] with the following:", emoji=False)  # TODO need short summary with name|serial|ip only in CacheDevice
    _ = [render.econsole.print(f"  {k}: {v}") for k, v in kwargs.items() if v is not None]
    if no_ip:
        render.econsole.print("  ip: [dim italic][red]Remove[/red] static IP[/]")

    if any([v is None for v in kwargs.values()]):
        need_current_settings = True
        render.econsole.print("\n[italic dark_olive_green2]Will result in 2 API Calls.")
    render.confirm(yes)

    if need_current_settings:
        cur_resp = api.session.request(api.configuration.get_swarm_config, dev.swack_id)
        if not cur_resp.ok:
            log.error("Unable to perform update due to error fetching current settings for swarm", caption=True)
            render.display_results(cur_resp, tablefmt="action", exit_on_fail=True)
        name = name or cur_resp.output["name"]
        ip = ip or cur_resp.output["ip_address"] if not no_ip else ""
        timezone = timezone or cur_resp.output["timezone_name"]
        offset_hr = offset_hr or cur_resp.output["timezone_hr"]
        offset_min = offset_min or cur_resp.output["timezone_min"]

    resp = api.session.request(api.configuration.replace_swarm_config, swarm_id=dev.swack_id, name=name, ip_address=ip, timezone=timezone, tz_offset_hr=offset_hr, tz_offset_min=offset_min)
    render.display_results(resp, tablefmt="action")


# FIXME entering more than one DNS results in the 2nd and beyond entry being evaluated as additional aps
# update ap lwr --dns 10.0.30.51 10.0.30.52 ... results in aps = ['lwr', '10.0.30.52']
# Any options below that are list[str] will have all items beyond the first evaluated as if it was aps
@app.command()
def ap(
    aps: list[str] = common.arguments.get("devices", autocompletion=common.cache.dev_ap_completion,),
    hostname: str = typer.Option(None, help="Rename/Set AP hostname", show_default=False),
    ip: str = typer.Option(None, metavar=iden_meta.ip_dhcp, help="Configure Static IP or reset AP to [cyan]dhcp[/] [dim italic][cyan]--mask[/], [cyan]--gateway[/], and [cyan]--dns[/] must be provided if configuring static IP[/]", show_default=False,),
    mask: str = typer.Option(None, help="Subnet mask in format 255.255.255.0 [dim italic]Required/Applies when --ip is provided[/]", show_default=False,),
    gateway: str = typer.Option(None, help="Default Gateway [dim italic]Required/Applies when --ip is provided[/]", show_default=False,),
    dns: str = typer.Option(None, help="Comma seperated list [bright_green](no spaces)[/] of dns servers. [dim italic]Required/Applies when --ip is provided[/]", show_default=False, is_eager=True,),
    domain: str = typer.Option(None, help="DNS domain name.  [dim italic]Optional/Applies when --ip is provided[/]", show_default=False,),
    disable_radios: str = typer.Option(None, "-D", "--disable-radios", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to disable.", show_default=False, is_eager=True,),
    enable_radios: str = typer.Option(None, "-E", "--enable-radios", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to enable.", show_default=False, is_eager=True,),
    access_radios: str = typer.Option(None, "-A", "--access", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to set to [cyan]access mode[/]", show_default=False, is_eager=True,),
    monitor_radios: str = typer.Option(None, "-M", "--monitor", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to set to [cyan]air monitor mode[/]", show_default=False, is_eager=True,),
    spectrum_radios: str = typer.Option(None, "-S", "--spectrum", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to set to [cyan]spectrum mode[/]", show_default=False, is_eager=True,),
    # TODO FIX This see FIXME above
    # dns: list[str] = typer.Option(None, help="Comma seperated list [bright_green](no spaces)[/] of dns servers. [dim italic]Required/Applies when --ip is provided[/]", show_default=False, is_eager=True,),
    # domain: str = typer.Option(None, help="DNS domain name.  [dim italic]Optional/Applies when --ip is provided[/]", show_default=False,),
    # disable_radios: list[str] = typer.Option(None, "-D", "--disable-radios", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to disable.", show_default=False, is_eager=True,),
    # enable_radios: list[str] = typer.Option(None, "-E", "--enable-radios", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to enable.", show_default=False, is_eager=True,),
    # access_radios: list[str] = typer.Option(None, "-A", "--access", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to set to [cyan]access mode[/]", show_default=False, is_eager=True,),
    # monitor_radios: list[str] = typer.Option(None, "-M", "--monitor", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to set to [cyan]air monitor mode[/]", show_default=False, is_eager=True,),
    # spectrum_radios: list[str] = typer.Option(None, "-S", "--spectrum", help="Comma seperated list [bright_green](no spaces)[/] of radio(s) to set to [cyan]spectrum mode[/]", show_default=False, is_eager=True,),
    flex_dual_exclude: RadioBandOptions = typer.Option(
        None,
        "-e",
        "--flex-exclude",
        help="The radio to be excluded on flex dual band APs.  i.e. [cyan]--flex-exclude 2.4[/] means the 5Ghz and 6Ghz radios will be used.",
        show_default=False
    ),
    antenna_width: DynamicAntMode = typer.Option(None, "-w", "--antenna-width", help="Dynamic Antenna Width [dim italic]Only applies to AP 679[/]", show_default=False,),
    uplink_vlan: int = typer.Option(None, "-u", "--uplink-vlan", help="Configure Uplink VLAN (tagged).", show_default=False,),
    gps_altitude: float = typer.Option(None, "-a", "--altitude", help="The mounting height from the ground in meters.  [dim italic]Must be set for 6Ghz SP[/]", show_default=False,),
    reboot: bool = typer.Option(False, "--reboot", "-R", help="Automatically reboot device if IP or VLAN is changed [dim italic]Reboot is required for changes to take effect when IP or VLAN settings are changed[/]"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update per-ap-settings (ap env) and/or add/update gps ap-altitude to ap level config.

    Multiple APs can be provided (same settings would apply).

    [dark_orange3]:warning:[/]  If providing more than one value for the options that support it
    You currently have to separate with a comma and ensure there are no spaces.
    [bright_green]i.e.[/]: [cyan]-E 2.4,5,6[/]
    You can also wrap the value in quotes and separate with a space
    [bright_green]i.e.[/]: [cyan]--dns '10.0.30.51 10.0.30.52'[/]

    The current setting is retained for any options that are not provided.

    Use [cyan]--ip dhcp[/] to reset an AP that was previously provisioned with a static address to use DHCP
        This will clear the ip, mask, gateway, dns, and domain if configured.

    [dark_sky_blue1]:information:[/]  See [cyan]cencli batch update aps --help[/] for details on updating APs in batch based on setting provided via import file.
    """
    if len(aps) > 1 and (hostname or (ip and ip.lower() != "dhcp")):
        common.exit("Setting hostname/ip on multiple APs doesn't make sesnse")

    kwargs = {
        "hostname": hostname,
        "ip": ip,
        "mask": mask,
        "gateway": gateway,
        "dns": dns,
        "domain": domain,
        "disable_radios": disable_radios,
        "enable_radios": enable_radios,
        "access_radios": access_radios,
        "monitor_radios": monitor_radios,
        "spectrum_radios": spectrum_radios,
        "flex_dual_exclude": flex_dual_exclude,
        "dynamic_ant_mode": antenna_width,
        "uplink_vlan": uplink_vlan,
        "gps_altitude": gps_altitude
    }
    kwargs = utils.strip_none(kwargs)
    if not kwargs:
        common.exit("[bright_red]No Changes provided[/]... Nothing to do.  Use [cyan]cencli update ap --help[/] to see available options.")

    aps: list[CacheDevice] = [common.cache.get_dev_identifier(ap, dev_type="ap") for ap in aps]
    data = [{"serial": ap.serial, **kwargs} for ap in aps]
    common.batch_update_aps(data, yes=yes, reboot=reboot)


# CACHE cache for webhook the API for update reuires the name and urls in the body even if they are not changing.
@app.command()
def webhook(
    wid: str = common.arguments.wid,
    name: str = typer.Argument(..., help="Update webhook name", show_default=False,),
    urls: list[str] = typer.Argument(..., help="Update webhook destination URLs", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update webhook details

    :information:  Use [cyan]show webhooks[/] to get the wid (webhook id)

    This command requires and overwrites the webhook name and destination urls.
    So include all urls, even those that are not changing.
    """
    conf_msg = f"[bright_green]Updat{'e' if not yes else 'ing'}[/] [cyan]WebHook[/] with the following:"
    _pfx = "\n    "
    updates = "\n".join([f"  [bright_green]{k}[/]: {v if k == 'name' else ''.join([f'{_pfx}{url}' for url in v])}" for k, v in {"name": name, "urls": urls}.items() if v is not None])
    conf_msg = f"{conf_msg}\n{updates}"
    render.console.print(conf_msg, overflow="ellipsis")
    if render.confirm():
        resp = api.session.request(api.central.update_webhook, wid, name, urls)
        render.display_results(resp, tablefmt="action")


@app.command()
def site(
    site_name: str = common.arguments.get("site", help="[green3]current[/] site name"),
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
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """
    Update details for an existing site.

    Provide [cyan]geo-loc[/] or [cyan]address[/] details, not both.
    [italic]Google Maps "Plus Codes" are supported for address field.[/]

    If address is provided assoicated geo coordinates are automatically populated.
    If geo coordinates are provided, any address associated with the site is cleared.

    [italic green3]Wrap Arguments that contain spaces in quotes i.e. "5402 Champions Hill Dr"[/]
    """
    site_now = common.cache.get_site_identifier(site_name)

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
        common.exit("[red]No Update data provided[/]\n[italic]Must provide address data and/or --new-name.")

    render.econsole.print(f"Updating Site: {site_now.summary_text}", emoji=False)
    render.econsole.print(f" [bright_green]Send{'ing' if yes else ''} the following updates:[reset]")
    rename_only = False
    if new_name and site_now.name != new_name:
        # Only provided new name send current address info to endpoint along with new name (name alone not allowed)
        if not address_fields:  # update requires either address fields or lon/lat even to change the name so send back existing data from cache with new name
            rename_only = True
            geo_keys = ["latitude", "longitude"]
            address_fields = {k: v for k, v in site_now.data.items() if k in kwargs.keys() and k not in geo_keys and v}
            if not address_fields:
                address_fields = {k: v for k, v in site_now.data.items() if k in geo_keys and v}

        render.econsole.print(f"  Chang{'e' if not yes else 'ing'} Name [red]{site_now.name}[/] --> [bright_green]{new_name}[/]")
    if rename_only:
        render.econsole.print("\n [italic green4]current address info being sent as it's required by API to change name[/]")
    _ = [render.econsole.print(f"  {k}: {v}", emoji=False) for k, v in address_fields.items()]
    if render.confirm(yes):
        resp = api.session.request(api.central.update_site, site_now.id, new_name or site_now.name, **address_fields)
        render.display_results(resp, exit_on_fail=True)
        if resp:
            api.session.request(common.cache.update_site_db, data={"name": new_name or site_now.name, "id": site_now.id, **address_fields})


@app.command()
def wlan(
    wlan: str = typer.Argument(..., help="SSID to update", show_default=False,),
    groups: list[str] = typer.Argument(
        None,
        help=f"Group(s) to update (SSID must be defined in each group) {common.help_block('All Groups that contain specified SSIDs will be updated')}",
        autocompletion=common.cache.group_completion,
        show_default=False,
    ),
    ssid: str = typer.Option(None, help="Update SSID name", show_default=False,),
    hide: bool = typer.Option(None, show_default=False,),
    vlan: str = typer.Option(None, show_default=False,),
    zone: str = typer.Option(None, show_default=False,),
    psk: str = typer.Option(None, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update configuration options of an existing WLAN/SSID
    """
    if groups:
        _groups = [common.cache.get_group_identifier(group) for group in groups]
        batch_req = [BatchRequest(api.configuration.get_wlan, group=group.name, wlan_name=wlan) for group in _groups]
    else:  # TODO coppied from show wlans -v make common func
        group_res = api.session.request(api.configuration.get_groups_properties)
        if not group_res:
            log.error(f"Unable to determine Groups that contain SSID {wlan}", caption=True,)
            render.display_results(group_res, exit_on_fail=True)

        groups = [g['group'] for g in group_res.output if 'AccessPoints' in g['properties']['AllowedDevTypes']]
        batch_req = [BatchRequest(api.configuration.get_wlan, group=group, wlan_name=wlan) for group in groups]

    api.session.silent = True
    batch_resp = api.session.batch_request(batch_req)
    api.session.silent = False

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
            render.econsole.print(f"[dark_orange3]:warning:[/]  Unexpected error while querying groups for existense of {wlan}")
            render.display_results(unexpected_failures, exit_on_fail=False)

    if not config_b4_dict:
        common.exit("Nothing to do", code=0)

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
            BatchRequest(api.configuration.update_wlan, **kwargs)
        ]

    options = {
        "SSID name": ssid,
        "vlan": vlan,
        "zone": zone,
        "psk": psk,
    }
    render.econsole.print(f"Update WLAN Profile {wlan} in groups [cyan]{'[/], [cyan]'.join(list(config_b4_dict.keys()))}[/]")
    render.econsole.print('\n'.join([f"  [bright_green]-[/] Update [cyan]{k}[/] -> [bright_green]{v}[/]" for k, v in options.items() if v is not None]))
    if hide is not None:
        render.econsole.print(f"  [bright_green]-[/] Update [cyan]Visability[/] -> [bright_green]{'Visable (not hidden)' if not hide else 'hidden'}[/]")

    if yes or typer.confirm("\nProceed?", abort=True):
        update_res = api.session.batch_request(update_req)
        render.display_results(update_res)

def get_guest_id(portal_id: str, name: str) -> str:
    guest_resp = api.session.request(api.guest.get_guests, portal_id)
    if not guest_resp:
        log.error(f"Unable to Update details for {name}, request to fetch visitor_id failed.", caption=True, log=True)
        render.display_results(guest_resp, tablefmt="action", exit_on_fail=True)

    guests = [g for g in guest_resp.output if g["name"] == name]
    if not guests:
        common.exit(f"Unable to update details for {name}, no match found while fetching visitor_id.")
    elif len(guests) > 1:
        guest_resp.output = guests
        render.display_results(guest_resp, caption=f"Guests matching user {name}", tablefmt="yaml")
        common.exit(f"Too many matches for {name} while fetching visitor_id.")
    else:
        return guests[0]["id"]

@app.command()
def guest(
    portal: str = typer.Argument(..., metavar=iden_meta.portal, autocompletion=common.cache.portal_completion, show_default=False,),
    name: str = typer.Argument(..., show_default=False,),
    password: str = typer.Option(None,),  #  hide_input=True, prompt=True, confirmation_prompt=True),
    company: str = typer.Option(None, help="Company Name", show_default=False,),
    phone: str = typer.Option(None, help="Phone # of guest; Format: +[CountryCode][PhoneNumber]", show_default=False,),
    email: str = typer.Option(None, help="email of guest", show_default=False,),
    notify_to: NotifyToArgs = typer.Option(None, help="Notify to 'phone' or 'email'", show_default=False,),
    disable: bool = typer.Option(None, "-D", "--disable", help="disable the account", show_default=False,),
    enable: bool = typer.Option(None, "-E", "--enable", help="enable the account", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Update a previously created guest account"""
    if disable and enable:
        common.exit("Invalid combination of options.  Using both [cyan]-E[/]|[cyan]--enable[/] and [cyan]-D[/]|[cyan]--disable[/] does not make sense.")
    elif disable:
        is_enabled = False
    elif enable:
        is_enabled = True
    else:
        is_enabled = None
    notify = True if notify_to is not None else None

    portal: CachePortal = common.cache.get_name_id_identifier("portal", portal)
    visitor_id = get_guest_id(portal.id, name)

    # TODO move to utils used by add and update.
    _phone_strip = list("()-. ")
    if phone:
        phone_orig = phone
        phone = "".join([p for p in list(phone) if p not in _phone_strip])
        if not phone.startswith("+"):
            if not len(phone) == 10:
                common.exit(f"phone number provided {phone_orig} appears to be [bright_red]invalid[/]")
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
    render.econsole.print(_msg)
    if render.confirm(yes):
        resp = api.session.request(api.guest.add_guest, **payload)
        password = None
        payload = None
        render.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Update existing Aruba Central objects/configs
    """
    pass


if __name__ == "__main__":
    app()
