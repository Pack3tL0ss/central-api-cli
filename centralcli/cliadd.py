#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from enum import Enum
from pathlib import Path
import sys
from typing import List, Tuple
import typer
import yaml
from rich import print
from rich.console import Console


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import cli, utils, cleaner
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import cli, utils, cleaner
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.constants import DevTypes, GatewayRole, state_abbrev_to_pretty, IdenMetaVars, NotifyToArgs
from centralcli.strings import LongHelp
help_text = LongHelp()


app = typer.Typer()
color = utils.color
iden = IdenMetaVars()

class AddWlanArgs(str, Enum):
    type = "type"
    psk = "psk"
    vlan = "vlan"
    zone = "zone"
    ssid = "ssid"
    bw_limit_up = "bw_limit_up"
    bw_limit_down = "bw_limit_down"
    bw_limit_user_up = "bw_limit_user_up"
    bw_limit_user_down = "bw_limit_user_down"
    portal_profile = "portal_profile"


class AddGroupArgs(str, Enum):
    serial = "serial"
    group = "group"
    mac = "mac"


# TODO update completion with mac oui, serial prefix
# TODO mac with colons breaks arg completion that follows unless enclosed in single quotes
# FIXME Not all flows work on 2.5.5  I think license may be broken
@app.command()
def device(
    kw1: AddGroupArgs = typer.Argument(..., hidden=True, metavar="serial", show_default=False,),
    serial: str = typer.Argument(..., metavar="<SERIAL NUM>", hidden=False, autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    kw2: str = typer.Argument(..., hidden=True, metavar="mac", autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    mac: str = typer.Argument(..., metavar="<MAC ADDRESS>", hidden=False, autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    kw3: str = typer.Argument(None, metavar="group", hidden=True, autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    group: str = typer.Argument(None, metavar="[GROUP]", help="pre-assign device to group",
                               autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    # kw4: str = typer.Argument(None, metavar="", hidden=True, autocompletion=cli.cache.smg_kw_completion),
    # site: str = typer.Argument(None, metavar="site [SITE]", help="assign device to site",
                            #    autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    _group: str = typer.Option(None, "--group", autocompletion=cli.cache.group_completion, hidden=True),
    # _site: str = typer.Option(None, autocompletion=cli.cache.site_completion, hidden=False),
    license: List[cli.cache.LicenseTypes] = typer.Option(None, "--license", help="Assign license subscription(s) to device", show_default=False),  # type: ignore
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options"),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", rich_help_panel="Common Options", show_default=False,),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
        autocompletion=cli.cache.account_completion,
        rich_help_panel="Common Options",
    ),
) -> None:
    """Add a Device to Aruba Central.

    Serial Number and MAC are required, group is opional.
    """
    kwd_vars = [kw1, kw2, kw3]
    vals = [serial, mac, group]
    kwargs = {
        "mac": None,
        "serial": None,
        "group": None,
        # "site": None,
        "license": license
    }

    for name, value in zip(kwd_vars, vals):
        if name and name not in kwargs:
            dev = cli.cache.get_dev_identifier(name, silent=True)
            if dev:  # allow user to put dev name for rare case where dev is in cache but not in inventory  # TESTME
                kwargs["serial"] = dev.serial
                kwargs["mac"] = dev.mac
            else:
                print(f"[bright_red]Error[/]: {name} is invalid")
                raise typer.Exit(1)
        else:
            kwargs[name] = value

    kwargs["group"] = kwargs["group"] or _group
    # kwargs["site"] = kwargs["site"] or _site

    # Error if both serial and mac are not provided
    if not kwargs["mac"] or not kwargs["serial"]:
        cli.exit("[bright_red]Error[/]: both serial number and mac address are required.")

    api_kwd = {"serial": "serial_num", "mac": "mac_address"}
    kwargs = {api_kwd.get(k, k): v for k, v in kwargs.items() if v}

    _msg = [f"Add device: [bright_green]{kwargs['serial_num']}|{kwargs['mac_address']}[/bright_green]"]
    if "group" in kwargs and kwargs["group"]:
        _group = cli.cache.get_group_identifier(kwargs["group"])
        kwargs["group"] = _group.name
        _msg += [f"\n  Pre-Assign to Group: [bright_green]{kwargs['group']}[/bright_green]"]
    # if "site" in kwargs and kwargs["site"]:
    #     _site = cli.cache.get_site_identifier(kwargs["site"])
    #     kwargs["site"] = _site.id
    #     _msg += [f"\n  Assign to Site: [bright_green]{_site.name}[/bright_green]"]
    if "license" in kwargs and kwargs["license"]:
        _lic_msg = [lic._value_ for lic in kwargs["license"]]
        _lic_msg = _lic_msg if len(kwargs["license"]) > 1 else _lic_msg[0]
        _msg += [
            f"\n  Assign License{'s' if len(kwargs['license']) > 1 else ''}: [bright_green]{_lic_msg}[/bright_green]"
        ]
        kwargs["license"] = [lic.replace("-", "_") for lic in kwargs["license"]]

    console = Console(emoji=False)
    console.print("".join(_msg))

    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.add_devices, **kwargs)
        cli.display_results(resp, tablefmt="action")
        # TODO need to update inventory cache after device add


@app.command(short_help="Add a group", help="Add a group")
def group(
    group: str = typer.Argument(..., metavar="[GROUP NAME]", autocompletion=cli.cache.group_completion, show_default=False,),
    # group_password: str = typer.Argument(
    #     None,
    #     show_default=False,
    #     help="Group password is required. You will be prompted for password if not provided.",
    #     autocompletion=lambda incomplete: incomplete
    # ),
    wired_tg: bool = typer.Option(False, "--wired-tg", help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(False, "--wlan-tg", help="Manage AP configurations via templates"),
    gw_role: GatewayRole = typer.Option(None, help="Configure Gateway Role [grey42]\[default: branch][/]", show_default=False,),
    aos10: bool = typer.Option(None, "--aos10", is_flag=True, help="Create AOS10 Group [grey42]\[default: AOS8 IAP][/]", show_default=False),
    microbranch: bool = typer.Option(
        None,
        "--mb",
        is_flag=True,
        help="Configure Group for MicroBranch APs (AOS10 only)",
        show_default=False,
    ),
    ap: bool = typer.Option(None, "--ap", help="Allow APs in group"),
    sw: bool = typer.Option(None, "--sw", help="Allow ArubaOS-SW switches in group."),
    cx: bool = typer.Option(None, "--cx", help="Allow ArubaOS-CX switches in group."),
    gw: bool = typer.Option(None, "--gw", help="Allow gateways in group."),
    mon_only_sw: bool = typer.Option(False, "--mon-only-sw", help="Monitor Only for ArubaOS-SW"),
    mon_only_cx: bool = typer.Option(False, "--mon-only-cx", help="Monitor Only for ArubaOS-CX"),
    # ap_user: str = typer.Option("admin", help="Provide user for AP group"),  # TODO build func to update group pass
    # ap_passwd: str = typer.Option(None, help="Provide password for AP group (use single quotes)"),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    debugv: bool = typer.Option(
        False, "--debugv",
        envvar="ARUBACLI_VERBOSE_DEBUG",
        help="Enable verbose Debug Logging",
        callback=cli.verbose_debug_callback,
        hidden=True,
    ),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account", show_default=False,),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    # if not group_password:
    #     group_password = typer.prompt("Group Password", confirmation_prompt=True, hide_input=True,)

    # else:
    #     _msg = f'{_msg}{typer.style(f"?", fg="cyan")}'

    allowed_types = []
    if ap:
        allowed_types += ["ap"]
    if sw:
        allowed_types += ["sw"]
    if cx:
        allowed_types += ["cx"]
    if gw:
        allowed_types += ["gw"]
    if not allowed_types:
        allowed_types = ["ap", "gw", "cx", "sw"]
    _arch = "Instant" if not aos10 else "AOS10"

    # -- // Error on combinations that are not allowed by API \\ --
    if not aos10 and microbranch:
        print(
            f":x: [bright_red]Microbranch is only valid if group is configured as AOS10 group ({color('--aos10')})."
        )
        raise typer.Exit(1)
    if (mon_only_sw or mon_only_cx) and wired_tg:
        print(":x: [bright_red]Error: Monitor only is not valid for template group.")
        raise typer.Exit(1)
    if mon_only_sw and "sw" not in allowed_types or mon_only_cx and "cx" not in allowed_types:
        print(":x: [bright_red]Error: Monitor only is not valid without '--sw' or '--cx' (Allowed Device Types)")
        raise typer.Exit(1)
    if gw_role and gw_role == "wlan" and not aos10:
        print(":x: [bright_red]WLAN role for Gateways requires the group be configured as AOS10 via --aos10 option.")
        raise typer.Exit(1)
    if all([x is None for x in [ap, sw, cx, gw]]):
        print("[green]No Allowed devices provided. Allowing all device types.")
        print("[reset]  NOTE: Device Types can be added after group is created, but not removed.\n")

    _arch_msg = f"[bright_green]{_arch} "
    _msg = f"[cyan]Create {'' if aos10 is None else _arch_msg}[cyan]group [bright_green]{group}[/bright_green]"
    _msg = f"{_msg}\n    [cyan]Allowed Device Types[/cyan]: [bright_green]{allowed_types}[/bright_green]"

    if wired_tg:
        _msg = f"{_msg}\n    [cyan]switches[/cyan]: [bright_green]Template Group[/bright_green]"
    if wlan_tg:
        _msg = f"{_msg}\n    [cyan]APs[/cyan]: [bright_green]Template Group[/bright_green]"
    if gw_role:
        _msg = f"{_msg}\n    [cyan]Gateway Role[/cyan]: [bright_green]{gw_role}[/bright_green]"
    if microbranch:
        _msg = f"{_msg}\n    [cyan]AP Role[/cyan]: [bright_green]Microbranch[/bright_green]"
    if mon_only_sw:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-SW: [bright_green]True[/bright_green]"
    if mon_only_cx:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-CX: [bright_green]True[/bright_green]"
    print(f"{_msg}\n")

    if yes or typer.confirm("Proceed?"):
        resp = cli.central.request(
            cli.central.create_group,
            group,
            wired_tg=wired_tg,
            wlan_tg=wlan_tg,
            allowed_types=allowed_types,
            aos10=aos10,
            microbranch=microbranch,
            gw_role=gw_role,
            monitor_only_sw=mon_only_sw,
        )
        cli.display_results(resp, tablefmt="action")
        if resp:
            asyncio.run(
                cli.cache.update_group_db({'name': group, 'template group': {'Wired': wired_tg, 'Wireless': wlan_tg}})
            )
        else:
            raise typer.Exit(1)


# TODO autocompletion
@app.command(short_help="Add WLAN (SSID)")
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]", autocompletion=cli.cache.group_completion),
    name: str = typer.Argument(..., ),
    kw1: Tuple[AddWlanArgs, str] = typer.Argument(("psk", None), metavar="psk [WPA PASSPHRASE]",),
    kw2: Tuple[AddWlanArgs, str] = typer.Argument(("type", "employee"), metavar="type ['employee'|'guest']",),
    kw3: Tuple[AddWlanArgs, str] = typer.Argument(("vlan", ""), metavar="vlan [VLAN]",),
    kw4: Tuple[AddWlanArgs, str] = typer.Argument(("zone", ""), metavar="zone [ZONE]",),
    kw5: Tuple[AddWlanArgs, str] = typer.Argument(("ssid", None), metavar="ssid [SSID]",),
    kw6: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_up", ""), metavar="bw-limit-up [LIMIT]",),
    kw7: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_down", ""), metavar="bw-limit-down [LIMIT]",),
    kw8: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_user_up", ""), metavar="bw-limit-user-up [LIMIT]",),
    kw9: Tuple[AddWlanArgs, str] = typer.Argument(
        ("bw_limit_user_down", ""),
        metavar="bw-limit-user-down [LIMIT]",
    ),
    kw10: Tuple[AddWlanArgs, str] = typer.Argument(
        ("portal_profile", ""),
        metavar="portal-profile [PORTAL PROFILE]",
    ),
    hidden: bool = typer.Option(False, "--hidden", help="Make WLAN hidden"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes
    group = cli.cache.get_group_identifier(group)
    kwarg_list = [kw1, kw2, kw3, kw4, kw5, kw6, kw7, kw8, kw9, kw10]
    _to_name = {
        "psk": "wpa_passphrase",
        "ssid": "essid",
        "bw_limit_up": "bandwidth_limit_up",
        "bw_limit_down": "bandwidth_limit_down",
        "bw_limit_user_up": "bandwidth_limit_peruser_up",
        "bw_limit_user_down": "bandwidth_limit_peruser_down",
        "portal_profile": "captive_profile_name",
    }
    kwargs = {_to_name.get(kw[0], kw[0]): kw[1] for kw in kwarg_list}
    if hidden:
        kwargs["hide_ssid"] = True

    if not kwargs["wpa_passphrase"]:
        typer.secho("psk/passphrase is currently required for this command")
        raise typer.Exit(1)

    if yes or typer.confirm(typer.style(f"Please Confirm Add wlan {name} to {group.name}", fg="cyan")):
        resp = cli.central.request(cli.central.create_wlan, group.name, name, **kwargs)
        typer.secho(str(resp), fg="green" if resp else "red")
    else:
        raise typer.Abort()


@app.command(short_help="Add a site.", help=help_text.add_site)
def site(
    site_name: str = typer.Argument(...),
    address: str = typer.Argument(None, help="street address, (enclose in quotes)"),
    city: str = typer.Argument(None,),
    state: str = typer.Argument(
        None,
        autocompletion=lambda incomplete: [
        s for s in [
            *list(state_abbrev_to_pretty.keys()),
            *list(state_abbrev_to_pretty.values())
            ]
            if s.lower().startswith(incomplete.lower())
        ]
    ),
    zipcode: int = typer.Argument(None,),
    country: str = typer.Argument(None,),
    lat: str = typer.Option(None, metavar="LATITUDE"),
    lon: str = typer.Option(None, metavar="LONGITUDE"),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    # These conversions just make the fields match what is used if done via GUI
    if state and len(state) == 2:
        state = state_abbrev_to_pretty.get(state, state)
    if country and country.upper() in ["US", "USA"]:
        country = "United States"

    kwargs = {
        "address": address,
        "city": city,
        "state": state,
        "zipcode": zipcode if zipcode is None else str(zipcode),
        "country": country,
        "latitude": lat,
        "longitude": lon
    }
    address_fields = {k: v for k, v in kwargs.items() if v}

    print(f"Add Site: [cyan]{site_name}[reset]:")
    _ = [print(f"  {k}: {v}") for k, v in address_fields.items()]
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.create_site, site_name, **address_fields)
        cli.display_results(resp)
        if resp:
            asyncio.run(cli.cache.update_site_db(resp.raw))
        else:
            raise typer.Exit(1)


# TODO allow more than one label and use batch_request
@app.command(help="Create a new label")
def label(
    name: str = typer.Argument(..., ),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    _msg = "Creating" if yes else "Create"
    print(f"{_msg} new label [cyan]{name}[/]")
    if yes or typer.confirm("Proceed?"):
        resp = cli.central.request(cli.central.create_label, name)
        cli.display_results(resp, cleaner=cleaner.get_labels)
        if resp.ok:  # TODO pass data to cli.cache.update_label_db to update vs doing a subsequenct call
            asyncio.run(cli.cache.update_label_db(cleaner.get_labels(resp.output)))


# FIXME # API-FLAW The cert_upload endpoint does not appear to be functional
# "Missing Required Query Parameter: Error while uploading certificate, invalid arguments"
# This worked: cencli add certificate lejun23 securelogin.kabrew.com.all.pem -pem -svr  (no passphrase, entering passphrase caused error above)
# TODO options should prob be --pem to be consistent with other commands
@app.command(hidden=False)
def certificate(
    cert_name: str = typer.Argument(..., show_default=False),
    cert_file: Path = typer.Argument(None, exists=True, readable=True, show_default=False,),
    passphrase: str = typer.Option(None, help="optional passphrase"),
    # cert_type: CertTypes = typer.Argument(...),
    # cert_format: CertFormat = typer.Argument(None,),
    pem: bool = typer.Option(False, "-pem", help="upload certificate in PEM format", show_default=False,),
    der: bool = typer.Option(False, "-der", help="upload certificate in DER format", show_default=False,),
    pkcs12: bool = typer.Option(False, "-pkcs12", help="upload certificate in pkcs12 format", show_default=False,),
    server_cert: bool = typer.Option(False, "-svr", help="Type: Server Certificate", show_default=False,),
    ca_cert: bool = typer.Option(False, "-ca", help="Type: CA", show_default=False,),
    crl: bool = typer.Option(False, "-crl", help="Type: CRL", show_default=False,),
    int_ca_cert: bool = typer.Option(False, "-int-ca", help="Type: Intermediate CA", show_default=False,),
    ocsp_resp_cert: bool = typer.Option(False, "-ocsp-resp", help="Type: OCSP responder", show_default=False,),
    ocsp_signer_cert: bool = typer.Option(False, "-ocsp-signer", help="Type: OCSP signer", show_default=False,),
    ssh_pub_key: bool = typer.Option(False, "-public", help="Type: SSH Public cert", show_default=False, hidden=True,),
    yes: bool = typer.Option(False, "-Y", "-y", help="Bypass confirmation prompts - Assume Yes"),
    default: bool = typer.Option(
        False, "-d", is_flag=True, help="Use default central account", show_default=False
    ),
    debug: bool = typer.Option(
        False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",
    ),
    account: str = typer.Option(
        "central_info",
        envvar="ARUBACLI_ACCOUNT",
        help="The Aruba Central Account to use (must be defined in the config)",
    ),
) -> None:
    """Upload a Certificate to Aruba Central
    """
    passphrase = "" if passphrase is None else passphrase
    cert_format_params = [pem, der, pkcs12]
    cert_formats = ["PEM", "DER", "PKCS12"]
    cert_format = None

    if not any([server_cert, ca_cert, crl, int_ca_cert, ocsp_resp_cert, ocsp_signer_cert, ssh_pub_key]):
        print("Error: Certificate Type must be provided using one of the options i.e. -svr")
        raise typer.Exit(1)
    elif not any(cert_format_params):
        if cert_file is None:
            print("Error: Cert format must be provided use one of '-pem'. '-der', or '-pkcs12'")
            raise typer.Exit(1)
    else:
        cert_format = cert_formats[cert_format_params.index(True)]

    kwargs = {
        "passphrase": passphrase,
        "cert_name": cert_name,
        "cert_format": cert_format,
        "server_cert": server_cert,
        "ca_cert": ca_cert,
        "crl": crl,
        "int_ca_cert": int_ca_cert,
        "ocsp_resp_cert": ocsp_resp_cert,
        "ocsp_signer_cert": ocsp_signer_cert,
        "ssh_pub_key": ssh_pub_key
    }

    kwargs = {k: v for k, v in kwargs.items() if v}

    if not cert_file:
        print("\n[bright_green]No Cert file specified[/]")
        print("Provide certificate content encoded in base64 format.")
        cert_file = utils.get_multiline_input(return_type="str")
        kwargs["cert_data"] = cert_file
    elif cert_file.exists():
        kwargs["cert_file"] = cert_file
    else:
        print(f"ERROR: The specified certificate file [cyan]{cert_file.name}[/] not found.")
        raise typer.Exit(1)

    print("[bright_green]Upload Certificate:")
    _ = [
        print(f"   {k}: [cyan]{v}[/]") for k, v in kwargs.items()
        if k not in  ["passphrase", "cert_data"]
        ]
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.upload_certificate, **kwargs)
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Add a WebHook")
def webhook(
    name: str = typer.Argument(..., ),
    urls: List[str] = typer.Argument(..., help="webhook urls",),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes

    print("Adding WebHook: [cyan]{}[/cyan] with urls:\n  {}".format(name, '\n  '.join(urls)))
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.add_webhook, name, urls)

        cli.display_results(resp, tablefmt="action")
        if not resp:
            raise typer.Exit(1)


# TODO ?? add support for converting j2 template to central template
@app.command(short_help="Add/Upload a new template", help="Add/Upload a new template to a template group")
def template(
    name: str = typer.Argument(..., ),
    group: str = typer.Argument(..., help="Group to upload template to",),
    template: Path = typer.Argument(None, exists=True),
    dev_type: DevTypes = typer.Option("ap"),
    model: str = typer.Option("ALL"),
    version: str = typer.Option("ALL", "--ver"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    yes = yes_ if yes_ else yes

    group = cli.cache.get_group_identifier(group)
    if not template:
        print("[bright_green]No Template file provided[/].  Template content is required.")
        print("Provide Template Content:")
        template = utils.get_multiline_input()
        template = template.encode("utf-8")

    print(f"\n[bright_green]Add{'ing' if yes else ''} Template[/] [cyan]{name}[/] to group [cyan]{group.name}[/]")
    print("[bright_green]Template will apply to[/]:")
    print(f"    Device Types: [cyan]{dev_type}[/]")
    print(f"    Model: [cyan]{model}[/]")
    print(f"    Version: [cyan]{version}[/]")
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.add_template, name, group=group.name, template=template, device_type=dev_type, version=version, model=model)
        cli.display_results(resp, tablefmt="action")
    # TODO update cache


# TODO cache for portal name/id
# TODO config option for different random pass formats
@app.command()
def guest(
    portal_id: str = typer.Argument(..., ),
    name: str = typer.Argument(..., ),
    password: str = typer.Option(None,),  #  hide_input=True, prompt=True, confirmation_prompt=True),
    company: str = typer.Option(None, help="Company Name",),
    phone: str = typer.Option(None, help="Phone # of guest; Format [+CountryCode][PhoneNumber]"),
    email: str = typer.Option(None, help="email of guest"),
    notify_to: NotifyToArgs = typer.Option(None, help="Notify to 'phone' or 'email'"),
    disable: bool = typer.Option(False, "--disable", is_flag=True, show_default=False, help="add account, but set to disabled"),
    yes: bool = typer.Option(False, "-Y", help="Bypass confirmation prompts - Assume Yes"),
    yes_: bool = typer.Option(False, "-y", hidden=True),
    debug: bool = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    default: bool = typer.Option(False, "-d", is_flag=True, help="Use default central account",),
    account: str = typer.Option("central_info",
                                envvar="ARUBACLI_ACCOUNT",
                                help="The Aruba Central Account to use (must be defined in the config)",),
) -> None:
    """Add a guest user to a configured portal"""
    yes = yes_ if yes_ else yes
    notify = True if notify_to is not None else None
    is_enabled = True if not disable else False

    _phone_strip = list("()-. ")
    if phone:
        phone_orig = phone
        phone = "".join([p for p in phone if p not in _phone_strip])
        if not phone.startswith("+"):
            if not len(phone) == 10:
                print(f"phone number provided {phone_orig} appears to be [bright_red]invalid[/]")
                raise typer.Exit(1)
            phone = f"+1{phone}"

    # TODO Add options for expire after / valid forever
    payload = {
        "portal_id": portal_id,
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


    # portal_id = cli.cache.get_portal_identifier(portal_id)
    _msg = f"[bright_green]Add[/] Guest: [cyan]{name}[/] with the following options:\n"
    _msg += f"  {options}\n"
    _msg += "\n[italic dark_olive_green2]Password (if provided) not displayed[/]\n"
    print(_msg)
    if yes or typer.confirm("\nProceed?", abort=True):
        resp = cli.central.request(cli.central.add_visitor, **payload)
        cli.display_results(resp, tablefmt="action")


@app.callback()
def callback():
    """
    Add devices / objects
    """
    pass


if __name__ == "__main__":
    print("hit")
    app()
