#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import environ as env
import subprocess
import sys
from pathlib import Path
from time import sleep
from typing import List

import typer
from rich import print
from rich.console import Console
from rich.markup import escape

try:
    import psutil
    hook_enabled = True
except (ImportError, ModuleNotFoundError):
    hook_enabled = False

err_console = Console(stderr=True)
clean_console = Console(emoji=False)
clean_err_console = Console(emoji=False, stderr=True)

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import (
        BatchRequest, cli, cliadd, cliassign, clibatch, clicaas, clicancel,
        clicheck, cliclone, clidel, clidev, cliexport, clikick, clirefresh,
        clirename, cliset, clishow, clitest, clitshoot, cliunassign,
        cliupdate, cliupgrade, cliconvert, config, log, utils,
    )
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import (
            BatchRequest, cli, cliadd, cliassign, clibatch, clicaas, clicancel,
            clicheck, cliclone, clidel, clidev, cliexport, clikick, clirefresh,
            clirename, cliset, clishow, clitest, clitshoot, cliunassign,
            cliupdate, cliupgrade, cliconvert, config, log, utils,
        )
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.cache import CentralObject  # noqa
from centralcli.constants import (BlinkArgs, BounceArgs, IdenMetaVars, StartArgs, ResetArgs, EnableDisableArgs,)  #noqa
from centralcli.environment import env_var, env  #noqa

iden = IdenMetaVars()

CONTEXT_SETTINGS = {
    # "token_normalize_func": lambda x: cli.normalize_tokens(x),
    "help_option_names": ["?", "--help"]
}

app = typer.Typer(context_settings=CONTEXT_SETTINGS, rich_markup_mode="rich")
app.add_typer(clishow.app, name="show",)
app.add_typer(clidel.app, name="delete",)
app.add_typer(cliadd.app, name="add",)
app.add_typer(cliassign.app, name="assign",)
app.add_typer(cliunassign.app, name="unassign",)
app.add_typer(cliclone.app, name="clone",)
app.add_typer(cliupdate.app, name="update",)
app.add_typer(cliupgrade.app, name="upgrade",)
app.add_typer(clibatch.app, name="batch",)
app.add_typer(clicaas.app, name="caas", hidden=True,)
app.add_typer(clirefresh.app, name="refresh",)
app.add_typer(clitest.app, name="test",)
app.add_typer(clitshoot.app, name="ts",)
app.add_typer(clirename.app, name="rename",)
app.add_typer(clikick.app, name="kick",)
app.add_typer(cliset.app, name="set",)
app.add_typer(cliexport.app, name="export",)
app.add_typer(clicheck.app, name="check",)
app.add_typer(clicancel.app, name="cancel",)
app.add_typer(cliconvert.app, name="convert",)
app.add_typer(clidev.app, name="dev", hidden=True)


# TODO see if can change kw1 to "group" kw2 to "site" and unhide
@app.command()
def move(
    device: List[str, ] = typer.Argument(None, metavar=iden.dev_many, autocompletion=cli.cache.dev_kwarg_completion, show_default=False,),
    kw1: str = typer.Argument(
        None,
        metavar="",
        show_default=False,
        hidden=True,
    ),
    kw1_val: str = typer.Argument(
        None,
        metavar="[site <SITE>]",
        show_default=False,
        help="[cyan]site[/] keyword followed by the site name.",
        hidden=False,
    ),
    kw2: str = typer.Argument(
        None,
        metavar="",
        show_default=False,
        hidden=True,
    ),
    kw2_val: str = typer.Argument(
        None,
        metavar="[group <GROUP>]",
        show_default=False,
        help=f"[cyan]group[/] keyword followed by the group name.  [grey42 italic]{escape('[site and/or group required]')}[/]",
        hidden=False,
    ),
    _group: str = typer.Option(
        None,
        "--group",
        help="Group to Move device(s) to",
        hidden=True,
        autocompletion=cli.cache.group_completion,
    ),
    _site: str = typer.Option(
        None, "--site",
        help="Site to move device(s) to",
        hidden=True,
        autocompletion=cli.cache.site_completion,
    ),
    reset_group: bool = typer.Option(
        False,
        "--reset-group",
        show_default=False,
        help="Reset group membership.  (move to the defined default group)",
    ),
    cx_retain_config: bool = typer.Option(False, "-k", help="Keep config intact for CX switches during move"),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Move device(s) to a defined group and/or site.
    """
    group, site, = None, None
    device = device or ()
    for a, b in zip([kw1, kw2], [kw1_val, kw2_val]):
        if a == "group":
            group = b
        elif a == "site":
            site = b
        else:
            device += tuple([aa for aa in [a, b] if aa and aa not in ["group", "site", "device", "devices"]])  # Allow unnecessary keyword device(s) 'cencli batch move devices ...'

    group = group or _group

    if reset_group and not group:
        default_group_resp = cli.central.request(cli.central.get_default_group)
        default_group = default_group_resp.output
        group = default_group
    elif reset_group and group:
        err_console.print(f":warning: [cyan italic]--reset-group[/] flag ignored as destination group {group} was provided")

    site = site or _site

    if not group and not site:
        cli.exit("Missing Required Argument, group and/or site is required.")

    data = [{"serial": d, "group": group, "site": site, "retain_config": cx_retain_config} for d in device]
    move_resp = cli.batch_move_devices(data=data, yes=yes)
    cli.display_results(move_resp, tablefmt="action")


@app.command()
def bounce(
    what: BounceArgs = typer.Argument(..., show_default=False),
    device: str = typer.Argument(..., metavar=iden.dev, show_default=False, autocompletion=cli.cache.dev_switch_completion),
    ports: List[str] = typer.Argument(..., autocompletion=lambda incomplete: [], show_default=False),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Bounce interface(s) or PoE on interface(s) (Valid on switches)

    Ranges are supported:
    [cyan]cencli bounce interface edge3 1/1/1-1/1/4 2/1/1-2/1/4[/] will bounce the 8 interfaces in those ranges
    [cyan]cencli bounce interface edge3 1/1/1-1/1/4,2/1/1-2/1/4[/] comma seperated similar to swich CLI is also valid

    [italic dark_olive_green2]Results in 1 API call per interface[/]
    """
    dev = cli.cache.get_dev_identifier(device, conductor_only=True)
    command = 'bounce_poe_port' if what == 'poe' else 'bounce_interface'
    ports = utils.get_interfaces_from_range(ports)

    print(f"Bounce [cyan]{what.value}[/] on [cyan]{dev.name}[/]: interface{'s' if len(ports) > 1 else ''} [cyan]{', '.join(ports)}[/]")
    if len(ports) > 1:
        print(f"[italic dark_olive_green2]{len(ports)} API calls will be performed.[/]\n")
    if cli.confirm(yes):
        resp = cli.central.batch_request([cli.central.BatchRequest(cli.central.send_bounce_command_to_device, dev.serial, command, p) for p in ports])
        cli.display_results(resp, tablefmt="action")
        # We don't check the task status because central seems to show the state as QUEUED even after execution appears complete


@app.command()
def remove(
    devices: List[str] = cli.arguments.devices,
    site: str = typer.Argument(
        ...,
        metavar="[site <SITE>]",
        show_default=False,
        autocompletion=cli.cache.remove_completion
    ),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Remove a device from a site
    """
    devices = (d for d in devices if d != "site")
    devices = [cli.cache.get_dev_identifier(dev, conductor_only=True) for dev in devices]
    site = cli.cache.get_site_identifier(site)

    print(
        f"Remove {', '.join([f'[bright_green]{dev.name}[/bright_green]' for dev in devices])} from site [bright_green]{site.name}"
    )
    if cli.confirm(yes):
        devs_by_type = {}
        for d in devices:
            if d.generic_type not in devs_by_type:
                devs_by_type[d.generic_type] = [d.serial]
            else:
                devs_by_type[d.generic_type] += [d.serial]
        reqs = [
            cli.central.BatchRequest(
                cli.central.remove_devices_from_site,
                site.id,
                serials=serials,
                device_type=dev_type,
            ) for dev_type, serials in devs_by_type.items()
        ]
        resp = cli.central.batch_request(reqs)
        cli.display_results(resp, tablefmt="action", exit_on_fail=True, cache_update_pending=True)
        # central will show the stack_id and all member serials in the success output.  So we strip the stack id
        swack_ids = utils.strip_none([d.get("swack_id") for d in devices if d.get("swack_id", "") != d.get("serial", "")])
        update_data = [{**dict(cli.cache.get_dev_identifier(s["device_id"])), "site": None} for r in resp for s in r.raw["success"] if s["device_id"] not in swack_ids]
        cli.central.request(cli.cache.update_dev_db, data=update_data)




@app.command()
def reboot(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion, show_default=False,),
    swarm: bool = typer.Option(False, "-s", "--swarm", help="Reboot the swarm [grey42 italic](IAP cluster)[/] associated with the provided device (AP)."),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Reboot devices or swarms

    Use --swarm to reboot the swarm associated with the specified device (The device can be any AP in the swarm)
    """
    devs: List[CentralObject] = [cli.cache.get_dev_identifier(dev, conductor_only=True) for dev in devices]

    batch_reqs, confirm_msgs = [], []
    _confirm_pfx = "Reboot:" if not yes else "Rebooting:"
    for dev in devs:
        conf_msg = dev.rich_help_text
        func = cli.central.send_command_to_device
        arg = dev.serial

        if swarm:  # TODO reboot swarm has not been tested
            if dev.type != "ap":
                print(f":warning:  Ignoring [green]-s[/]|[cyan]--swarm[/], as it only applies to APs not {dev.type}\n")
            elif dev.version.startswith("10."):
                print(":warning:  Ignoring [green]-s[/]|[cyan]--swarm[/] option, as it only applies to [cyan]AOS8[/] IAP\n")
            else:
                func = cli.central.send_command_to_swarm
                arg = dev.swack_id
                conf_msg = f'the [cyan]swarm {dev.name}[/] belongs to'

        batch_reqs += [BatchRequest(func, arg, 'reboot')]
        confirm_msgs += [conf_msg]

    confirm_msgs_str = "\n  ".join(confirm_msgs)
    clean_console.print(f'\u26a0  [bold bright_green]{_confirm_pfx}[/]\n  {confirm_msgs_str}')  # use unicode chars here as confirm message could have mac looks like emoji markup :cd:
    if len(batch_reqs) > 1:
        print(f"  [italic dark_olive_green2]Will result in {len(batch_reqs)} API Calls.")

    if cli.confirm(yes):
        batch_resp = cli.central.batch_request(batch_reqs)
        cli.display_results(batch_resp, tablefmt="action")


@app.command()
def reset(
    what: ResetArgs = typer.Argument("overlay", help="overlay is the only option currently"),
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_ap_gw_completion, show_default=False),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Reset overlay control connection (OTO/ORO)
    """
    # Not sure this works on APs/MB AP
    dev = cli.cache.get_dev_identifier(device, dev_type=("gw", "ap",))

    console = Console(emoji=False)
    _msg = "Reset" if not yes else "Resetting"
    _msg = f"{_msg} ORO connection for [cyan]{dev.rich_help_text}[/]"
    console.print(_msg)

    if cli.confirm(yes):
        resp = cli.central.request(cli.central.reset_overlay_connection, dev.serial)
        cli.display_results(resp, tablefmt="action")


@app.command(help="Blink LED")
def blink(
    device: str = typer.Argument(..., show_default=False, metavar=iden.dev, autocompletion=cli.cache.dev_switch_ap_completion),
    action: BlinkArgs = typer.Argument(..., show_default=False),  # metavar="Device: [on|off|<# of secs to blink>]"),
    secs: int = typer.Argument(None, metavar="SECONDS", help="Blink for {secs} seconds.", show_default=False,),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    command = f'blink_led_{action.value}'
    dev = cli.cache.get_dev_identifier(device, dev_type=["switch", "ap"])
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, command, duration=secs)
    cli.display_results(resp, tablefmt="action")


@app.command()
def nuke(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_switch_ap_completion),
    swarm: bool = typer.Option(False, "-s", "--swarm", help="Factory Default the swarm [grey42 italic](IAP cluster)[/] associated with the provided device (AP)."),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Reset a device to factory default, erase all configuration (Valid on ArubaOS-SW or IAP Clusters)

    :warning:  For AOS8 IAP this command is only valid for entire cluster, not individual APs [cyan]-s[/]|[cyan]--swarm[/] option is required.
    """
    dev = cli.cache.get_dev_identifier(device, dev_type=["ap", "switch"])
    if dev.type == "cx":
        cli.exit("This command only applies to [cyan]AOS-SW[/] switches, not [cyan]CX[/]")

    conf_msg = dev.rich_help_text
    if dev.type == "cx":
        func = cli.central.send_command_to_device
        arg = dev.serial
        if swarm:
            print(f"[dark_orange3]:warning:[/]  Ignoring [cyan]-s[/]|[cyan]--swarm[/] option, as it only applies to APs not {dev.type}\n")
    else:  # AP all others will error in get_dev_identifier
        func = cli.central.send_command_to_swarm
        arg = dev.swack_id
        if dev.is_aos10:
            cli.exit("This command is only valid for [cyan]AOS8[/] IAP clusters not [cyan]AOS10[/] APs")
        elif not swarm:
            cli.exit("This command is only valid for the entire swarm in AOS8, not individual APs.  Use [cyan]-s[/]|[cyan]--swarm[/] to default the entire IAP cluster associated with the provided AP")
        else:
            conf_msg = f'the [cyan]swarm {dev.name}[/] belongs to'

    console = Console(emoji=False)
    _msg = "Factory Default" if not yes else "Factory Defaulting"
    _msg = f"[bright_red blink]{_msg}[/] {conf_msg}"
    console.print(_msg)
    if cli.confirm(yes):
        resp = cli.central.request(func, arg, 'erase_configuration')
        cli.display_results(resp, tablefmt="action")


@app.command(short_help="Save Device Running Config to Startup")
def save(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_completion),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    dev = cli.cache.get_dev_identifier(device)
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'save_configuration')
    cli.display_results(resp, tablefmt="action")


@app.command(short_help="Sync/Refresh device config with Aruba Central")
def sync(
    device: str = typer.Argument(..., metavar=iden.dev, autocompletion=cli.cache.dev_gw_completion, show_default=False),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Sync/Refresh device config with Aruba Central

    Only valid for gateways (aka controllers)
    """
    dev = cli.cache.get_dev_identifier(device, dev_type="gw")
    resp = cli.central.request(cli.central.send_command_to_device, dev.serial, 'config_sync')
    cli.display_results(resp, tablefmt="action")


# TODO get the account, port and process details (start_time, pid) cache
# add cache.RunDB or InfoDB to use to store this kind of stuff
start_help = f"""Start WebHook Proxy Service on this system in the background

    Currently 2 webhook automations:
    For Both automations the URL to configure as the webhook destination is [cyan]http://localhost/api/webhook[/] (currently http)

    [cyan]hook-proxy[/]:
      - Gathers status of all branch tunnels at launch, and utilizes webhooks to keep a local DB up to date.
      - Presents it's own REST API that can be polled for branch/tunnel status:
        See [cyan]http://localhost:port/api/docs[/] (after starting proxy) for available endpoints / schema details.

    [cyan]hook2snow[/]:
      - [bright_red]!!![/] This integration is incomplete, as the customer that requested it ended up going a different route with the webhooks.
      - Queries alerts API at launch to gather any "Open" items.
      - Receives webhooks from Aruba Central, and creates or resolves incidents in Service-Now via SNOW REST API

    [italic]Requires optional hook-proxy component '[bright_green]pip3 install -U centralcli{escape("[hook-proxy]")}[reset]'
    """
@app.command(help=start_help, short_help="Start WebHook Proxy", hidden=not hook_enabled)
def start(
    what: StartArgs = typer.Argument(
        "hook-proxy",
        help="See documentation for info on what each webhook receiver does",
    ),
    port: int = typer.Option(config.webhook.port, help="Port to listen on (overrides config value if provided)", show_default=True),
    collect: bool = typer.Option(False, "--collect", "-c", help="Store raw webhooks in local json file", hidden=True),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    if config.deprecation_warning:  # TODO remove at 2.0.0+
        print(config.deprecation_warning)
    svc = "wh_proxy" if what == "hook-proxy" else "wh2snow"
    yes_both = True if yes > 1 else False
    yes = True if yes else False
    def terminate_process(pid):
        p = psutil.Process(pid)
        for _ in range(2):
            p.terminate()
            if p.status() != 'Terminated':
                p.kill()
            else:
                break

    def get_pid():
        for p in psutil.process_iter(attrs=["name", "cmdline"]):
            if p.info["cmdline"] and True in [svc in x for x in p.info["cmdline"][1:]]:
                return p.pid # if p.ppid() == 1 else p.ppid()

    pid = get_pid()
    if pid:
        _abort = True if not port or port == int(config.webhook.port) else False
        print(f"Webhook proxy is currently running (process id {pid}).")
        print(f"Terminat{'e' if not yes_both else 'ing'} existing process{'?' if not yes_both else '.'}")
        if cli.confirm(yes_both, abort=_abort):
            terminate_process(pid)
            print("[cyan]Process Terminated")

    # ["nohup", sys.executable, "-m", "centralcli.wh_proxy", "--port", str(port), "--account", config.account],
    config_port = 9143 if not config.webhook else config.webhook.port
    print(f"Webhook Proxy will listen on port {port or config_port}")
    if cli.confirm(yes):
        port = port or config.webhook.port
        cmd = ["nohup", sys.executable, "-m", f"centralcli.{svc}", str(port)]
        if collect:
             cmd += ["-c"]
        with cli.console.status("Starting Webhook Proxy..."):
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            sleep(2)

        with cli.console.status("Ensuring startup success...", spinner="dots2"):
            sleep(8)

        proc = psutil.Process(p.pid)
        if not psutil.pid_exists(p.pid) or proc.status() not in ["running", "sleeping"]:
            output = [line.decode("utf-8").rstrip() for line in p.stdout if not line.decode("utf-8").startswith("nohup")]
            print("\n".join(output))
            print("\nWebHook Proxy Startup [red]Failed[/].")
        else:
            print(f"[{p.pid}] WebHook Proxy [bright_green]Started[/].")


@app.command(short_help="Stop WebHook Proxy", hidden=not hook_enabled)
def stop(
    what: StartArgs = typer.Argument(
        ...,
        # metavar=f"hook-proxy",
    ),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Stop WebHook Proxy (background process).
    """
    svc = "wh_proxy" if what == "hook-proxy" else "wh2snow"
    # TODO move these out of this function and just call them from both start/stop
    def terminate_process(pid):
        console = Console(emoji=False)
        with console.status("Terminating Webhook Proxy..."):
            p = psutil.Process(pid)
            for _ in range(2):
                p.terminate()
                sleep(2)

                if p.is_running():
                    p.kill()
                else:
                    return True

        with console.status("Waiting for WebHook Proxy to die..."):
            _pass = 0
            while p.is_running() or _pass < 8:
                sleep(1)
                if not p.is_running():
                    return True
                _pass += 1

        return False

    def _get_process_info():
        for p in psutil.process_iter(attrs=["name", "cmdline"]):
            if svc in str(p.cmdline()[1:]):
                for flag in p.cmdline()[::-1]:
                    if flag.startswith("-"):
                        continue
                    elif flag.isdigit():
                        port = flag
                        break
                return p.pid, port

    proc = _get_process_info()
    if proc:
        print(f"[{proc[0]}] WebHook Proxy is listening on port: {proc[1]}")
        print(f"Terminat{'e' if not yes else 'ing'} existing process{'?' if not yes else '.'}")
        if cli.confirm(yes):
            dead = terminate_process(proc[0])
            cli.exit("[cyan]WebHook process terminated" if dead else "Terminate may have [bright_red]failed[/] verify process.", code=0 if dead else 1)
    else:
        cli.exit("WebHook Proxy is not running.", code=0)

@app.command(short_help="Archive devices", hidden=False)
def archive(
    devices: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Archive devices.  This has less meaning/usefulness with the transition to GreenLake.

    cencli archive <devices>, followed by cencli unarchive <devices> removes any subscriptions
    and the devices assignment to the Aruba Central App in GreenLake.

    Archive removes the GreenLake assignment, but the device can't be added to a different account
    until it's unarchived.

    Just use cencli deleve device ... or cencli batch delete devices
    """
    _emsg = ""
    _msg = "[bright_green]Archive devices[/]:"
    serials = []
    cache_devs: List[CentralObject] = [cli.cache.get_dev_identifier(dev, silent=True, include_inventory=True, exit_on_fail=False) for dev in devices]
    for dev_in, cache_dev in zip(devices, cache_devs):
        if cache_dev:
            _msg = f"{_msg}\n    {cache_dev.rich_help_text}"
            serials += [cache_dev.serial]
        elif cache_dev is None and not utils.is_serial(dev_in):
            _emsg = f"{_emsg}\n    [dark_orange3]\u26a0[/]  [red]Skipping[/] [cyan]{dev_in}[/].  Not found in Cache and does not appear to be a serial number."
        else:
            _msg = f"{_msg}\n    {dev_in}"
            serials += [dev_in]

    console = Console(emoji=False)
    console.print(_msg, _emsg, sep="\n")
    if cli.confirm(yes):
        resp = cli.central.request(cli.central.archive_devices, serials)
        cli.display_results(resp, tablefmt="action")



@app.command()
def unarchive(
    serials: List[str] = typer.Argument(..., metavar=iden.dev_many, autocompletion=cli.cache.dev_completion),
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Unacrchive devices

    Remove previously archived devices from archive.

    Specify device by serial.  (archived devices will not be in Inventory cache for name lookup)
    """
    serials: List[CentralObject] = [cli.cache.get_dev_identifier(dev, silent=True, retry=False, include_inventory=True, exit_on_fail=False) or dev for dev in serials]

    _msg = "[bright_green]Unarchive devices[/]:"
    if serials and any([isinstance(d, CentralObject) for d in serials]):
        if len(serials) > 1:
            _dev_msg = '\n    '.join([dev if not isinstance(dev, CentralObject) else dev.rich_help_text for dev in serials])
            _msg = f"{_msg}\n    {_dev_msg}\n"
        else:
            dev = serials[0]
            _msg = f"{_msg} {dev if not isinstance(dev, CentralObject) else dev.rich_help_text}"
        serials: List[str] = [d if not isinstance(d, CentralObject) else d.serial for d in serials]
    else:
        _dev_msg = '\n    '.join(serials)
        _msg = f"{_msg}\n    {_dev_msg}\n"
    cli.console.print(_msg, emoji=False)

    resp = cli.central.request(cli.central.unarchive_devices, serials)
    cli.display_results(resp, tablefmt="action")


@app.command(hidden=True)
def enable(
    what: EnableDisableArgs = typer.Argument("auto-sub"),
    services: List[cli.cache.LicenseTypes] = typer.Argument(..., show_default=False),  # type: ignore
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Enable auto subscribe for service.

    Enabling auto subscribe sets the level (i.e. foundation/advanced) for all devices of the same type as the subscription provided.
    i.e. `enable auto-sub advanced-switch-6300` will enable auto subscribe for all switch tiers (6100, 6200, etc)
    """

    _msg = "[bright_green]Enable[/] auto-subscribe for license"
    if len(services) > 1:
        _svc_msg = '\n    '.join([s.name for s in services])
        _msg = f'{_msg}s:\n    {_svc_msg}\n'
    else:
        svc = services[0]
        _msg = f'{_msg} {svc.name}'
    print(_msg)
    print('\n[dark_orange]!![/] Enabling auto-subscribe applies the specified tier (i.e. foundation/advanced) for [green bold]all[/] devices of the same type.')
    print('[cyan]enable auto-sub advanced-switch-6300[/] will result in [green bold]all[/] switch models being set to auto-subscribe the advanced license appropriate for that model.')
    print('Not just the 6300 models.')
    if cli.confirm(yes):
        services = [s.name for s in services]

        resp = cli.central.request(cli.central.enable_auto_subscribe, services=services)
        cli.display_results(resp, tablefmt="action")


@app.command(hidden=True)
def disable(
    what: EnableDisableArgs = typer.Argument("auto-sub"),
    services: List[cli.cache.LicenseTypes] = typer.Argument(..., show_default=False),  # type: ignore
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Disable auto subscribe for service.

    Disabling auto subscribe removes auto-subscribe for all models of the same type.
    i.e. `disable auto-sub advanced-switch-6300` will disable auto subscribe for all switch tiers (6100, 6200, etc)
    """

    _msg = "[bright_green]Disable[/] auto-subscribe for license"
    if len(services) > 1:
        _svc_msg = '\n    '.join([s.name for s in services])
        _msg = f'{_msg}s:\n    {_svc_msg}\n'
    else:
        svc = services[0]
        _msg = f'{_msg} {svc.name}'
    print(_msg)
    print('\n[dark_orange]!![/] Disabling auto subscribe removes auto-subscribe for all models of the same type.')
    print('[cyan]disable auto-sub advanced-switch-6300[/] will result in auto-subscribe being disabled for [green bold]all[/] switch models.')
    print('Not just the 6300.')
    if cli.confirm(yes):
        services = [s.name for s in services]

        resp = cli.central.request(cli.central.disable_auto_subscribe, services=services)
        cli.display_results(resp, tablefmt="action")

@app.command(hidden=True)
def renew_license(
    device: List[str] = cli.arguments.devices,
    yes: bool = cli.options.yes,
    debug: bool = cli.options.debug,
    default: bool = cli.options.default,
    account: str = cli.options.workspace,
) -> None:
    """Renew-Licenses on devices.

    :warning: Device may go offline briefly.
    This command will unnassign then reassign the subscription currently applied to the device,

    [italic]This is useful when the subscription currently applied is approaching expiration, and other subscription
    keys exist with expiration further out.  When reassigned central will use the subscription with the longest
    duration remianing.[/]
    """
    def normalize_sub(subscription: str) -> str:
        return subscription.lower().replace(" ", "_").replace("/", "_")

    raise NotImplementedError()
    from centralcli.cache import CacheInvDevice
    devices = [cli.cache.get_dev_identifier(d) for d in device]
    inv_data = [CacheInvDevice(cli.cache.inventory_by_serial[s]) for s in [s.serial for s in devices]]
    calls_by_sub = {}
    dev_types = []
    for idx, dev in enumerate(set(inv_data)):
        if not dev.services:
            skipped = inv_data.pop(idx)
            cli.econsole.print(f":warning: Skipping {skipped} as it does not have any subscriptions assigned.  Use [cyan]cencli assign license <device(s)>[/] to assign licenses.")
            continue
        dev_types += ["switch" if dev.type in ["cx", "sw"] else dev.type]
        for sub in dev.services:
            calls_by_sub = utils.update_dict(calls_by_sub, normalize_sub(sub), dev.serial)
    # subs_resp = cli.central.request(cli.central.get_subscriptions, device_type=None if len(dev_types) > 1 else dev_types[0])
    # subs_by_name = {f'{normalize_sub(sub["license_type"])}_{sub["subscription_key"]}': sub["end_date"] / 1000 for sub in subs_resp.output if sub["available"] and sub["status"] != "EXPIRED"}
    # Gave up on this for now, the names from the inventory don't map well with the names from get_subscriptions.  Would need to build a map
    # i.e. Foundation-90/70xx vs foundation_70xx


def all_commands_callback(ctx: typer.Context, update_cache: bool):
    # --raw and --debug-limit are honored and stripped out in init
    if ctx.resilient_parsing:
        config.is_completion = True
        return

    # if not ctx.resilient_parsing:
    version, workspace, debug, debugv, default, update_cache = None, None, None, None, None, None
    for idx, arg in enumerate(sys.argv[1:]):
        if idx == 0 and arg in ["-v", "-V", "--version"]:
            version = True
        if arg == "--debug":
            debug = True
        if arg == "--debugv":
            debugv = True
        elif arg == "-d":
            default = True
        elif arg in ["--ws", "--workspace"] and "-d" not in sys.argv:
            workspace = sys.argv[idx + 2]  # sys.argv enumeration is starting at index 1 so need to adjust idx by 2 for next arg
        elif arg == "-U":
            update_cache = True
        elif arg.startswith("-") and not arg.startswith("--"):  # -dU is allowed
            if "d" in arg:
                default = True
            if "U" in arg:
                update_cache = True

    workspace = workspace or env.workspace
    debug = debug or env.debug

    if version:
        cli.version_callback(ctx)
        cli.exit(code=0)
    if default:
        if ("--ws" in sys.argv or "--workspace" in sys.argv) and workspace != config.default_workspace:
            ws_flag = "--ws" if "--ws" in sys.argv else "--workspace"
            cli.econsole.print(f":warning:  Both [cyan]-d[/] and [cyan]{ws_flag}[/] flag used.  Honoring [cyan]-d[/], ignoring workspace [cyan]{workspace}[/]")
            workspace = config.default_workspace
        cli.workspace_name_callback(ctx, workspace=config.default_workspace, default=True)
    else:
        cli.workspace_name_callback(ctx, workspace=workspace)

    if debug:
        cli.debug_callback(ctx, debug=debug)
    if debugv:
        log.DEBUG = config.debug = log.verbose = config.debugv = debugv
        _ = sys.argv.pop(sys.argv.index("--debugv"))
    if update_cache:
        cli.econsole.print("Pretend I'm updating the cache...")
        # cli.cache(refresh=True)
        # _ = sys.argv.pop(sys.argv.index("-U"))
        # TODO ensure cache update is removed from all commands as we are doing it here now


@app.callback()
def callback(
    # ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", "-v", case_sensitive=False, is_flag=True, help="Show current cencli version, and latest available version.",),
    # debug: bool = typer.Option(False, "--debug", is_flag=True, envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging",),
    #                         #    callback=all_commands_callback),
    # debugv: bool = typer.Option(False, "--debugv", is_flag=True, help="Enable Verbose Debug Logging", hidden=True,),
                            #    callback=all_commands_callback),
    # default: bool = typer.Option(
    #     False,
    #     "-d",
    #     is_flag=True,
    #     help="Use default central account",
    #     show_default=False,
    # ),
    debug: bool = cli.options.get("debug", rich_help_panel="Options"),
    debugv: bool = cli.options.get("debugv", hidden=True),
    default: bool = cli.options.get("default", rich_help_panel="Options"),
    # account: str = typer.Option(
    #     "default",
    #     envvar="ARUBACLI_ACCOUNT",
    #     help="The Aruba Central Account to use (must be defined in the config)",
    #     autocompletion=cli.cache.account_completion,
    #     hidden=True
    # ),
    # workspace: str = typer.Option(
    #     "default",
    #     "-ws", "--workspace",
    #     envvar="CENCLI_WORKSPACE",
    #     help="The Aruba Central [dim italic]([green]GreenLake[/green])[/] WorkSpace to use (must be defined in the config)",
    #     autocompletion=cli.cache.account_completion,
    # ),
    workspace: str = cli.options.get("workspace", rich_help_panel="Options"),
    # update_cache: bool = typer.Option(False, "-U", hidden=True, lazy=True, callback=all_commands_callback),
    update_cache: bool = cli.options.get("update_cache", lazy=True, callback=all_commands_callback)
) -> None:
    """
    Aruba Central API CLI.  A CLI for interacting with Aruba Central APIs.

    Use [cyan]--raw[/] which is supported globally, to see the raw unformatted response from Aruba Central.
    Append [cyan]--again[/] to any command to re-display the output of the [bright_green]last[/] command from local cache.
       - This is intended for use with up arrow. It's the equivalent of [cyan]cencli show last[/].
       - Ignores the command on the command line and converts it to [cyan]cencli show last[/]
       - Only retains options valid for [cyan]cencli show last[/] i.e. --json -r ...
       - Useful if you want to see the same output in a different format or you want to output to file (--out <FILE>)
       - :warning:  [cyan]--raw[/] output is not cached for re-display.
    """
    ...
    # if account != "default":
    #     workspace = account if workspace == "default" else workspace


log.debug(f'{__name__} called with Arguments: {" ".join(sys.argv)}')

if __name__ == "__main__":
    app()
