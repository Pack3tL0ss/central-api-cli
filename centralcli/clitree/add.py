#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

import pendulum
import typer
import yaml
from rich.console import Console

from centralcli import common, config, log, render, utils
from centralcli.client import BatchRequest
from centralcli.constants import DevTypes, GatewayRole, NotifyToArgs, iden_meta, state_abbrev_to_pretty
from centralcli.render import econsole
from centralcli.response import Response

if TYPE_CHECKING:
    from ..cache import CacheGroup, CacheMpskNetwork, CachePortal

from ..clicommon import APIClients

api_clients = APIClients()
api = api_clients.classic


app = typer.Typer()
color = utils.color

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

err_console = Console(stderr=True)


def _update_inv_cache_after_dev_add(resp: Response | List[Response], serial: str = None, mac: str = None, license: str | List[str] = None) -> None:
    if license:
        try:
            license = utils.unlistify(license)
            license: str = license.lower().replace("_", "-").replace(" ", "-"),
        except Exception as e:  # pragma: no cover
            log.exception(f"{e.__class__.__name__} Exception in _update_inv_cache_after_dev_add\n{e}", caption=True)  # This isn't imperative given it's the inv cache.  It's not used for much.

    inv_data = {
        'type': "-",
        'model': "-",
        'sku': "-",
        'mac': mac,
        'serial': serial,
        'services': license,
    }
    resp = utils.listify(resp)
    for r in resp:
        if r.url.path == '/platform/device_inventory/v1/devices':
            if not r.ok:  # pragma: no cover
                return
            try:
                inv_data["sku"] = r.raw["extra"]["message"]["available_device"][0]["part_number"]
            except Exception as e:  # pragma: no cover
                log.warning(f"Unable to extract sku after inventory update ({e.__class__.__name__}), value will be omitted from inv cache.\n{e}")

    api.session.request(common.cache.update_inv_db, data=inv_data)


# TODO update completion with mac serial partial completion
# TODO mac with colons breaks arg completion that follows unless enclosed in single quotes
# FIXME Not all flows work on 2.5.5  I think license may be broken
# TOGLP
@app.command()
def device(
    kw1: AddGroupArgs = typer.Argument(None, hidden=True, metavar="", show_default=False,),
    serial: str = typer.Argument(..., metavar="serial <SERIAL NUM>", hidden=False, autocompletion=common.cache.smg_kw_completion, show_default=False,),
    kw2: str = typer.Argument(None, hidden=True, metavar="", autocompletion=common.cache.smg_kw_completion, show_default=False,),
    mac: str = typer.Argument(..., metavar="mac <MAC ADDRESS>", hidden=False, autocompletion=common.cache.smg_kw_completion, show_default=False,),
    kw3: str = typer.Argument(None, metavar="", hidden=True, autocompletion=common.cache.smg_kw_completion, show_default=False,),
    group: str = typer.Argument(None, metavar="[group GROUP]", help="pre-assign device to group", autocompletion=common.cache.smg_kw_completion, show_default=False,),
    # kw4: str = typer.Argument(None, metavar="", hidden=True, autocompletion=cli.cache.smg_kw_completion),
    # site: str = typer.Argument(None, metavar="site [SITE]", help="assign device to site",
                            #    autocompletion=cli.cache.smg_kw_completion, show_default=False,),
    _group: str = typer.Option(None, "--group", autocompletion=common.cache.group_completion, hidden=True),
    # _site: str = typer.Option(None, autocompletion=cli.cache.site_completion, hidden=False),
    subscription: List[common.cache.LicenseTypes] = common.options.subscription,  # type: ignore
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add a Device to Aruba Central

    Serial Number and MAC are required, group is optional.

    [italic cyan]serial[/], [italic cyan]mac[/], and [italic cyan]group[/] can be provided in any order.

    [turquoise4]Example[/]:
    [cyan]cencli add device serial USABC1234 mac aa:bb:cc:dd:ee:ff [dim]group WadeLab --sub advanced-switch-6300[/dim][/]
    """
    kwd_vars = [kw1, kw2, kw3]
    vals = [serial, mac, group]
    kwargs = {
        "mac": None,
        "serial": None,
        "group": None,
        # "site": None,
        "license": subscription
    }

    for name, value in zip(kwd_vars, vals):
        if name is not None:
            kwargs[name if not hasattr(name, "value") else name.value] = value

    kwargs["group"] = kwargs["group"] or _group

    # Error if both serial and mac are not provided
    if not kwargs["mac"] or not kwargs["serial"]:
        common.exit("[bright_red]Error[/]: both serial number and mac address are required.")

    _msg = [f"Add device: [bright_green]{kwargs['serial']}|{kwargs['mac']}[/bright_green]"]
    if "group" in kwargs and kwargs["group"]:
        _group: CacheGroup = common.cache.get_group_identifier(kwargs["group"])
        kwargs["group"] = _group.name
        _msg += [f"\n  Pre-Assign to Group: [bright_green]{kwargs['group']}[/bright_green]"]
    if "license" in kwargs and kwargs["license"]:
        _lic_msg = [lic.value for lic in kwargs["license"]]
        _lic_msg = _lic_msg if len(kwargs["license"]) > 1 else _lic_msg[0]
        _msg += [
            f"\n  Assign License{'s' if len(kwargs['license']) > 1 else ''}: [bright_green]{_lic_msg}[/bright_green]"
        ]
        kwargs["license"] = [lic.replace("-", "_") for lic in kwargs["license"]]

    render.econsole.print("".join(_msg), emoji=False)

    if render.confirm(yes):
        resp = api.session.request(api.platform.add_devices, **kwargs)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)
        _update_inv_cache_after_dev_add(resp, serial=serial, mac=mac, license=subscription)

@app.command()
def group(
    group: str = common.arguments.group,
    wired_tg: bool = typer.Option(False, "--wired-tg", help="Manage switch configurations via templates"),
    wlan_tg: bool = typer.Option(False, "--wlan-tg", help="Manage AP configurations via templates"),
    gw_role: GatewayRole = typer.Option(None, help=f"Configure Gateway Role {render.help_block('vpnc if --sdwan branch if not')}", show_default=False,),
    aos10: bool = typer.Option(None, "--aos10", is_flag=True, help=f"Create AOS10 Group {render.help_block('AOS8 IAP')}", show_default=False),
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
    sdwan: bool = typer.Option(None, "--sdwan", help="Allow EdgeConnect SD-WAN GWs in group. [red italic]Must be the only type allowed[/]"),
    mon_only_sw: bool = typer.Option(False, "--mon-only-sw", help="Monitor Only for ArubaOS-SW"),
    mon_only_cx: bool = typer.Option(False, "--mon-only-cx", help="Monitor Only for ArubaOS-CX"),
    cnx: bool = typer.Option(False, "--cnx", help="Make Group compatible with New Central (cnx). :warning:  All configurations will be pushed from New Central configuration model."),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add a group to Aruba Central"""
    allowed_types = []
    if ap:
        allowed_types += ["ap"]
    if sw:
        allowed_types += ["sw"]
    if cx:
        allowed_types += ["cx"]
    if gw:
        allowed_types += ["gw"]
    if not sdwan:
        _arch = "Instant" if not aos10 else "AOS10"
        if not allowed_types:
            allowed_types = ["ap", "gw", "cx", "sw"]
    else:
        _arch = "SD_WAN_Gateway"
        allowed_types = ["sdwan"]
        if gw_role and gw_role != "vpnc":
            render.econsole.print(f"[dark_orange3]:warning:[/]  Ignoring Gateway Role: [red]{gw_role}[/].  As the group is configured for [cyan]--sdwan[/], Gateway role [bright_green]vpnc[/] is implied.")
        gw_role = "vpnc"

    # -- // Error on combinations that are not allowed by API \\ --
    if any([ap, sw, cx, gw]) and sdwan:
        common.exit("When allowing [cyan]sdwan[/] in the group it must be the [red]only[/] type allowed in the group")
    if not aos10 and microbranch:
        common.exit("[cyan]Microbranch[/] is only valid if group is configured as AOS10 group via [cyan]--aos10[/] option.")
    if (mon_only_sw or mon_only_cx) and wired_tg:
        common.exit("[cyan]Monitor only[/] [bright_red]is not valid[/] for [cyan]template[/] group.")
    if mon_only_sw and "sw" not in allowed_types or mon_only_cx and "cx" not in allowed_types:
        common.exit("Monitor only is not valid without '--sw' or '--cx' (Allowed Device Types)")
    if gw_role and gw_role == "wlan" and not aos10:
        common.exit("WLAN role for Gateways requires the group be configured as AOS10 via [cyan]--aos10[/] option.")
    if all([x is None for x in [ap, sw, cx, gw, sdwan]]):
        econsole.print(f"[green]No Allowed devices provided. Allowing default device types [{utils.color(['ap', 'gw', 'cx', 'sw'], 'cyan')}]")
        econsole.print("[reset]  NOTE: Device Types can be added after group is created, but not removed.\n")

    _arch_msg = f"[bright_green]{_arch} "
    _msg = f"[cyan]Create {'' if aos10 is None else _arch_msg}[cyan]group [bright_green]{group}[/bright_green]"
    _msg = f"{_msg}\n    [cyan]Allowed Device Types[/cyan]: [bright_green]{allowed_types}[/bright_green]"

    if wired_tg:
        _msg = f"{_msg}\n    [cyan]switches[/cyan]: [bright_green]Template Group[/bright_green]"
    if wlan_tg:
        _msg = f"{_msg}\n    [cyan]APs[/cyan]: [bright_green]Template Group[/bright_green]"
    if gw_role:
        _msg = f"{_msg}\n    [cyan]Gateway Role[/cyan]: [bright_green]{gw_role.value}[/bright_green]"
    if microbranch:
        _msg = f"{_msg}\n    [cyan]AP Role[/cyan]: [bright_green]Microbranch[/bright_green]"
    if mon_only_sw:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-SW[/cyan]: [bright_green]:white_check_mark:[/bright_green]"
    if mon_only_cx:
        _msg = f"{_msg}\n    [cyan]Monitor Only ArubaOS-CX[/cyan]: [bright_green]:white_check_mark:[/bright_green]"
    if cnx:
        _msg = f"{_msg}\n\n    [yellow]:information:[/]  [italic]Group will be configured as [bright_green]CNX[/] enabled.  All configuration must be done in CNX ([bright_green]C[/]entral [bright_green]N[/]ext Generation E[bright_green]x[/]perience)"
        _msg = f"{_msg}\n    [dark_orange3]:warning:[/]  [italic]CNX configuration is currently Select Availability, contant your HPE Aruba Networking Account Team for details.[/italic]"


    econsole.print(f"{_msg}")

    if render.confirm(yes):
        resp = api.session.request(
            api.configuration.create_group,
            group,
            wired_tg=wired_tg,
            wlan_tg=wlan_tg,
            allowed_types=allowed_types,
            aos10=aos10,
            microbranch=microbranch,
            gw_role=gw_role,
            monitor_only_sw=mon_only_sw,
            monitor_only_cx=mon_only_cx,
            cnx=cnx
        )
        if not resp.ok:  # pragma: no cover
            log.warning(f"Group {group} not added to local Cache due to failure response from API.", caption=True)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)
        # prep data for cache
        data={
            'name': group,
            "allowed_types": allowed_types,
            "gw_role": gw_role,
            'aos10': aos10,
            "microbranch": None if not aos10 else bool(microbranch),
            'wlan_tg': wlan_tg,
            'wired_tg': wired_tg,
            'monitor_only_sw': mon_only_sw,
            'monitor_only_cx': mon_only_cx,
            'cnx': cnx
        }
        api.session.request(
            common.cache.update_group_db,
            data=data
        )


# TODO autocompletion
@app.command()
def wlan(
    group: str = typer.Argument(..., metavar="[GROUP NAME|SWARM ID]", autocompletion=common.cache.group_completion, show_default=False,),
    name: str = typer.Argument(..., show_default=False, help="The WLAN profile name.  Also the SSID if not provided."),
    psk: Tuple[AddWlanArgs, str] = typer.Argument(("psk", None), metavar="psk [WPA PASSPHRASE]", show_default=False, show_choices=False,),
    wlan_type: Tuple[AddWlanArgs, str] = typer.Argument(("type", "employee"), metavar="type ['employee'|'guest']", show_default=False,),
    vlan: Tuple[AddWlanArgs, str] = typer.Argument(("vlan", ""), metavar="vlan [VLAN]", show_default=False,),
    zone: Tuple[AddWlanArgs, str] = typer.Argument(("zone", ""), metavar="zone [ZONE]", show_default=False,),
    ssid: Tuple[AddWlanArgs, str] = typer.Argument(("ssid", None), metavar="ssid [SSID]", help="By default the SSID will match the WLAN profile name.", show_default=False,),
    bw_up: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_up", ""), metavar="bw-limit-up [LIMIT]", show_default=False,),
    bw_down: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_down", ""), metavar="bw-limit-down [LIMIT]", show_default=False,),
    bw_user_up: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_user_up", ""), metavar="bw-limit-user-up [LIMIT]", show_default=False,),
    bw_user_down: Tuple[AddWlanArgs, str] = typer.Argument(("bw_limit_user_down", ""), metavar="bw-limit-user-down [LIMIT]", show_default=False,),
    portal_profile: Tuple[AddWlanArgs, str] = typer.Argument(("portal_profile", ""), metavar="portal-profile [PORTAL PROFILE]", show_default=False,),
    hidden: bool = typer.Option(False, "--hidden", help="Make WLAN hidden"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add WLAN (SSID)"""
    group = common.cache.get_group_identifier(group)
    kwarg_list = [psk, wlan_type, vlan, zone, ssid, bw_up, bw_down, bw_user_up, bw_user_down, portal_profile]
    _to_name = {
        "psk": "wpa_passphrase",
        "ssid": "essid",
        "bw_limit_up": "bandwidth_limit_up",
        "bw_limit_down": "bandwidth_limit_down",
        "bw_limit_user_up": "bandwidth_limit_peruser_up",
        "bw_limit_user_down": "bandwidth_limit_peruser_down",
        "portal_profile": "captive_profile_name",
    }
    kwargs = {_to_name.get(kw[0].value, kw[0].value): kw[1] for kw in kwarg_list if kw[1]}
    if hidden:
        kwargs["hide_ssid"] = True

    if "wpa_passphrase" not in kwargs:
        common.exit("psk/passphrase is currently required for this command")

    econsole.print(f"Add{'ing' if yes else ''} wlan [cyan]{name}[/] to group [cyan]{group.name}[/]")
    if render.confirm(yes):
        resp = api.session.request(api.configuration.create_wlan, group.name, name, **kwargs)
        render.display_results(resp, tablefmt="action")



@app.command()
def site(
    site_name: str = typer.Argument(... , show_default=False,),
    address: str = typer.Argument(None, help="street address, (enclose in quotes)", show_default=False,),
    city: str = typer.Argument(None, show_default=False,),
    state: str = typer.Argument(
        None,
        autocompletion=lambda incomplete: [
        s for s in [
            *list(state_abbrev_to_pretty.keys()),
            *list(state_abbrev_to_pretty.values())
            ]
            if s.lower().startswith(incomplete.lower())
        ],
        show_default=False,
    ),
    zipcode: int = typer.Argument(None, show_default=False,),
    country: str = typer.Argument(None, show_default=False,),
    lat: str = typer.Option(None, metavar="LATITUDE", show_default=False,),
    lon: str = typer.Option(None, metavar="LONGITUDE", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add a site to Aruba Central

    Provide [cyan]geo-loc[/] or [cyan]address[/] details, [red1]not both[/].
    [italic]Google Maps "Plus Codes" are supported for address field.[/]

    If address is provided assoicated geo coordinates are automatically populated.
    If geo coordinates are provided, address is [red1]not[/] calculated.

    [italic green3]Wrap Arguments that contain spaces in quotes i.e. "5402 Champions Hill Dr"[/]
    """
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
    address_fields = {k: v.rstrip(",") for k, v in kwargs.items() if v}  # We allow them to put commas in during entry

    econsole.print(f"Add Site: [cyan]{site_name}[reset]:")
    _ = [print(f"  {k}: {v}") for k, v in address_fields.items()]
    if render.confirm(yes):
        resp = api.session.request(api.central.create_site, site_name, **address_fields)
        render.display_results(resp, exit_on_fail=True)
        api.session.request(common.cache.update_site_db, data=resp.raw)



# TODO label can't match any existing label names OR site names.  Add pre-check via cache / cache-update if label already exists with that name ... then error if cache_update confirms it's accurate
@app.command()
def label(
    labels: List[str] = typer.Argument(..., metavar=iden_meta.label_many, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add label(s) to Aruba Central

    Label can't have any devices associated with it to delete.
    """
    econsole.print(f'[bright_green]{"Creating" if yes else "Create"}[/] label{"s" if len(labels) > 1 else ""}:')
    econsole.print("\n".join([f"  [cyan]{label}[/]" for label in labels]))
    ...
    for idx in range(0, 2):
        duplicate_names = [name for name in [*[s["name"] for s in common.cache.sites], *common.cache.label_names] if name in labels]
        if duplicate_names:
            if idx == 0:
                err_console.print(f":warning:  Name{'s' if len(duplicate_names) > 1 else ''} ({utils.color(duplicate_names)}) already exists in site or label DB, refreshing cache to ensure data is current.")
                common.cache.check_fresh(site_db=True, label_db=True)
            else:
                common.exit(f"Name{'s' if len(duplicate_names) > 1 else ''} ({utils.color(duplicate_names)}) already exists in site or label DB, label/site names must be unique (sites included)")

    batch_reqs = [BatchRequest(api.central.create_label, label) for label in labels]
    if render.confirm(yes):
        batch_resp = api.session.batch_request(batch_reqs)
        render.display_results(batch_resp, tablefmt="action")
        update_data = [{"id": resp.raw["label_id"], "name": resp.raw["label_name"], "devices": 0} for resp in batch_resp if resp.ok]
        api.session.request(common.cache.update_label_db, data=update_data)


# FIXME # API-FLAW The cert_upload endpoint does not appear to be functional
# "Missing Required Query Parameter: Error while uploading certificate, invalid arguments"
# This worked: cencli add certificate lejun23 securelogin.kabrew.com.all.pem -pem -svr  (no passphrase, entering passphrase caused error above)
@app.command()
def cert(
    cert_name: str = typer.Argument(..., show_default=False),
    cert_file: Path = typer.Argument(None, help="If not provided you'll be prompted to paste in cert text", exists=True, readable=True, show_default=False,),
    passphrase: str = typer.Option(None, help="optional passphrase", show_default=False,),
    pem: bool = typer.Option(False, "--pem", help="upload certificate in PEM format", show_default=False,),
    der: bool = typer.Option(False, "--der", help="upload certificate in DER format", show_default=False,),
    pkcs12: bool = typer.Option(False, "--pkcs12", help="upload certificate in pkcs12 format", show_default=False,),
    server_cert: bool = typer.Option(False, "--svr", help="Type: Server Certificate", show_default=False,),
    ca_cert: bool = typer.Option(False, "--ca", help="Type: CA", show_default=False,),
    crl: bool = typer.Option(False, "--crl", help="Type: CRL", show_default=False,),
    int_ca_cert: bool = typer.Option(False, "--int-ca", help="Type: Intermediate CA", show_default=False,),
    ocsp_resp_cert: bool = typer.Option(False, "--ocsp-resp", help="Type: OCSP responder", show_default=False,),
    ocsp_signer_cert: bool = typer.Option(False, "--ocsp-signer", help="Type: OCSP signer", show_default=False,),
    ssh_pub_key: bool = typer.Option(False, "--public", help="Type: SSH Public cert", show_default=False, hidden=True,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add/Upload a Certificate to Aruba Central
    """
    cert_format_params = [pem, der, pkcs12]
    cert_formats = ["PEM", "DER", "PKCS12"]
    cert_format = None

    if not any([server_cert, ca_cert, crl, int_ca_cert, ocsp_resp_cert, ocsp_signer_cert, ssh_pub_key]):
        common.exit("[red1]Error[/]: Certificate Type must be provided using one of the options i.e. [cyan]--svr[/]")
    # elif cert_file is None:   # TODO determine cert format from file
    elif not any(cert_format_params):
        common.exit(f"[red1]Error[/]: Cert format must be provided use one of {utils.color(['--pem', '--der', '--pkcs12'], color_str='cyan', sep='|')}")
    else:
        cert_format = cert_formats[cert_format_params.index(True)]

    kwargs = {
        "passphrase": passphrase or "",
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

    if not cert_file:  # pragma: no cover
        econsole.print("[bright_green]No Cert file specified[/]")
        if not crl:
            econsole.print("Provide certificate content encoded in base64 format.")
        cert_file = utils.get_multiline_input(prompt=f"[cyan]Enter/Paste in {'certificate' if not crl else 'crl'} text[/].")
        kwargs["cert_data"] = cert_file
    else:
        kwargs["cert_file"] = cert_file

    econsole.print("[bright_green]Upload Certificate:")
    _ = [
        econsole.print(f"   {k}: [cyan]{v}[/]") for k, v in kwargs.items()
        if k not in  ["passphrase", "cert_data"]
    ]
    if render.confirm(yes):
        resp = api.session.request(api.configuration.upload_certificate, **kwargs)
        render.display_results(resp, tablefmt="action")
        if resp.ok:
            try:
                data = {"name": cert_name, "type": resp.output["cert_type"].upper(), "md5_checksum": resp.output["cert_md5_checksum"], "expired": False, "expiration": None}
                api.session.request(common.cache.update_db, common.cache.CertDB, data=data, truncate=False)
            except Exception as e:  # pragma: no cover
                log.exception(f"Exception during attempt to update CertDB {repr(e)}", show=True)


@app.command(help="Add a WebHook")
def webhook(
    name: str = typer.Argument(..., show_default=False,),
    urls: List[str] = typer.Argument(..., help="webhook urls", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    econsole.print("Adding WebHook: [cyan]{}[/cyan] with urls:\n  {}".format(name, '\n  '.join(urls)))
    if render.confirm(yes):
        resp = api.session.request(api.central.add_webhook, name, urls)
        render.display_results(resp, tablefmt="action", exit_on_fail=True)


# TODO ?? add support for converting j2 template to central template
@app.command(short_help="Add/Upload a new template", help="Add/Upload a new template to a template group")
def template(
    name: str = typer.Argument(..., help="Template name", show_default=False,),
    group: str = typer.Argument(..., help="Group to upload template to", autocompletion=common.cache.group_completion, show_default=False,),
    template: Path = typer.Argument(None, help="Path to file containing template", exists=True, show_default=False,),
    dev_type: DevTypes = typer.Option(DevTypes.cx, metavar="[ap|sw|cx]", help="Device Type Template applies to",),
    model: str = typer.Option("ALL", help="Constrain template to specific model",),
    version: str = typer.Option("ALL", "--ver", help="Constrain template to specific version"),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    group: CacheGroup = common.cache.get_group_identifier(group)
    if not template:  # pragma: no cover
        econsole.print("[bright_green]No Template file provided[/].  Template content is required.")
        econsole.print("Provide Template Content:")
        template = utils.get_multiline_input()
        template = template.encode("utf-8")

    econsole.print(f"\n[bright_green]Add{'ing' if yes else ''} Template[/] [cyan]{name}[/] to group [cyan]{group.name}[/]")
    econsole.print("[bright_green]Template will apply to[/]:")
    econsole.print(f"    Device Type: [cyan]{dev_type.value}[/]")
    econsole.print(f"    Model: [cyan]{model}[/]")
    econsole.print(f"    Version: [cyan]{version}[/]")
    render.confirm(yes)

    template_hash, resp = api.session.batch_request(
        [
            BatchRequest(common.get_file_hash, template),
            BatchRequest(api.configuration.add_template, name, group=group.name, template=template, device_type=dev_type, version=version, model=model)
        ]
    )

    render.display_results(resp, tablefmt="action")
    if resp.ok:
        api_to_cli_dev_type = {
            "ArubaSwitch": "sw",
            "CX": "cx",
            "IAP": "ap",
            "MobilityController": "gw"
        }
        _ = api.session.request(
            common.cache.update_template_db, data={
                "name": name,
                "device_type": api_to_cli_dev_type.get(dev_type, dev_type.lower()),
                "group": group.name,
                "model": model,
                "version": version,
                "template_hash": template_hash,
            },
            add=True
        )

def _get_variable_file(var_file: Path) -> dict[str, dict[str, str]]:
    var_data = config.get_file_data(var_file)

    try:
        if isinstance(var_data, list):
            var_data = {dev_vars["_sys_serial"]: dev_vars for dev_vars in var_data}
        elif "_sys_serial" in var_data:
            var_data = {var_data["_sys_serial"]: var_data}
    except KeyError as e:  # pragma: no cover
        log.exception(f"{repr(e)} While attempting to parse variables from {var_file.name}\n{e}")
        common.exit(f"{repr(e)} While attempting to parse variables from {var_file.name}")

    if not all("_sys_serial" in vars and "_sys_lan_mac" in vars for vars in var_data.values()):
        common.exit("Missing required variable [cyan]_sys_serial[/] and/or [cyan]_sys_lan_mac[/].")

    return var_data


@app.command()
def variables(
    variable_file: Path = typer.Argument(..., exists=True, show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Upload variables for a device from file

    Use this command to add/define variables for a device that does not have variables yet.
    [deep_sky_blue3]:information:[/] Use [cyan]cencli update variables[/] to update variables for a device with existing variables.

    Variables: _sys_serial, and _sys_lan_mac are required.
    """
    var_data = _get_variable_file(variable_file)

    econsole.print(f"[bright_green]{'Uploading' if yes else 'Upload'}[/] variables for {len(var_data)} device with variables defined in [cyan]{variable_file.name}[/]")
    render.confirm(yes)

    batch_reqs = [BatchRequest(api.configuration.create_device_template_variables, serial, dev_data["_sys_lan_mac"], var_dict=dev_data) for serial, dev_data in var_data.items()]
    batch_res = api.session.batch_request(batch_reqs)
    render.display_results(batch_res, tablefmt="action")


# TODO config option for different random pass formats
# TODO options for valid_till and valid_till_no_limit
@app.command()
def guest(
    portal: str = typer.Argument(..., metavar=iden_meta.portal, autocompletion=common.cache.portal_completion, show_default=False,),
    name: str = typer.Argument(..., show_default=False,),
    password: str = typer.Option(None, help="Should generally be provided, wrap in single quotes", show_default=False,),  #  hide_input=True, prompt=True, confirmation_prompt=True),
    company: str = typer.Option(None, help="Company Name", show_default=False,),
    phone: str = typer.Option(None, help="Phone # of guest; Format: +[CountryCode][PhoneNumber]", show_default=False,),
    email: str = typer.Option(None, help="email of guest", show_default=False,),
    notify_to: NotifyToArgs = typer.Option(None, help="Send password via 'phone' or 'email'", show_default=False,),
    disable: bool = typer.Option(False, "--disable", is_flag=True, help="add account, but set to disabled", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add a guest user to a configured portal"""
    portal: CachePortal = common.cache.get_name_id_identifier("portal", portal)
    notify = True if notify_to is not None else None
    is_enabled = True if not disable else False

    if notify and not password:
        common.exit(f"[cyan]--notify-to[/] {notify_to} sends a notification to the user with thier password.  This option is only valid when [cyan]--password[/] is provided.")
        # TODO API allows password not to be sent, but don't think there is any logical scenario where we wouldn't need it.  Don't think you can get any auto-generated password
        # and notify-to does not send pass to user if pass is not part of payload.

    _phone_strip = list("()-. ")
    if phone:
        phone_orig = phone
        phone = "".join([p for p in list(phone) if p not in _phone_strip])
        if not phone.startswith("+"):
            if not len(phone) == 10:
                common.exit(f"phone number provided {phone_orig} appears to be [bright_red]invalid[/]")
            phone = f"+1{phone}"

    # TODO Add options for expire after / valid forever
    kwargs = {
        "portal_id": portal.id,
        "name": name,
        "company_name": company,
        "phone": phone,
        "email": email,
        "notify": notify,
        "notify_to": None if not notify_to else notify_to.value,
        "is_enabled": is_enabled,
    }
    kwargs = utils.strip_none(kwargs)
    options = "\n  ".join(yaml.safe_dump(kwargs).splitlines())
    if password:
        kwargs["password"] = password

    _msg = f"[bright_green]Add[/] Guest: [cyan]{name}[/] with the following options:\n"
    _msg += f"  {options}\n"
    if password:
        _msg += "\n[italic dark_olive_green2]Password not displayed[/]\n"
    econsole.print(_msg)
    if render.confirm(yes):
        resp = api.session.request(api.guest.add_guest, **kwargs)
        password = kwargs = None
        render.display_results(resp, tablefmt="action", exit_on_fail=True)  # exits here if call failed
        # TODO calc expiration based on portal config Kabrew portal appears to be 3 days
        try:
            created = pendulum.now(tz="UTC")
            expires = created.add(days=3)
            cache_data = {"portal_id": portal.id, "name": name, "id": resp.output["id"], "email": email, "phone": phone, "company": company, "enabled": is_enabled, "status": "Active" if is_enabled else "Inactive", "created": created.int_timestamp, "expires": expires.int_timestamp}
            _ = api.session.request(common.cache.update_db, common.cache.GuestDB, cache_data, truncate=False)
        except Exception as e:  # pragma: no cover
            log.exception(f"Exception attempting to update Guest cache after adding guest {name}.\n{e}")
            render.econsole.print(f"[red]:warning:[/]  Exception ({e.__class__.__name__}) occured during attempt to update guest cache, refer to logs ([cyan]cencli show logs cencli[/]) for details.")


@app.command()
def mpsk(
    ssid: str = typer.Argument(..., help="The MPSK SSID to associate the MPSK with", autocompletion=common.cache.mpsk_network_completion, show_default=False,),
    email: str = typer.Argument(..., help=":email:  email address which is used as the name for the MPSK", show_default=False,),
    role: str = typer.Option(..., help="The user role to associate with devices using this PSK", show_default=False,),
    psk: str = typer.Option(None, help=":warning:  This currently has no impact, PSK is always randomly generated.", show_default=False,  hidden=True,),
    #  The PSK/Passphrase, [dim italic]Best to wrap in single quotes.[/] {cli.help_block('Generate Random PSK')}", show_default=False,),
    disable: bool = typer.Option(False, "-D", "--disable", is_flag=True, help="Add MPSK Configuration, but set to [red]disabled[/]", show_default=False,),
    yes: bool = common.options.yes,
    debug: bool = common.options.debug,
    default: bool = common.options.default,
    workspace: str = common.options.workspace,
) -> None:
    """Add Named MPSK Configuration"""
    ssid: CacheMpskNetwork = common.cache.get_name_id_identifier("mpsk_network", ssid)
    render.econsole.print(f"[bright_green]Add{'ing' if yes else ''}[/] MPSK [cyan]{email}[/] with the following:")
    render.econsole.print(f"  Associate with MPSK SSID: [cyan]{ssid.name}[/]")
    render.econsole.print(f"  Assign Role: [cyan]{role}[/]")
    if psk:
        render.econsole.print("  [dim italic]Configure PSK as specified, not shown[/]", "[dark_orange3]:warning:[/] [dim italic][cyan]--psk[/] [red]is hidden because the option has no impact, The API will always randomly generate the psk[/]")
    if disable:
        render.econsole.print("  Create MPSK, but set as [red]disabled[/]")

    render.confirm(yes)  # exits here if they don't confirm
    resp = api.session.request(api.cloudauth.add_named_mpsk, ssid.id, name=email, role=role, enabled=not disable)
    render.display_results(resp, tablefmt="action")
    # CACHE update


@app.callback()
def callback():
    """
    Add devices / objects
    """
    pass


if __name__ == "__main__":
    app()
