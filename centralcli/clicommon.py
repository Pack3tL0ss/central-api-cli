#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Tuple, Union

import pendulum
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.markup import escape
from rich.progress import track

from centralcli import config, log, render, utils
from centralcli.clioptions import CLIArgs, CLIOptions
from centralcli.constants import dynamic_antenna_models, flex_dual_models
from centralcli.models.cache import Groups, Inventory, Labels
from centralcli.models.imports import ImportSites
from centralcli.objects import DateTime
from centralcli.utils import ToBool

from .classic.api import ClassicAPI
from .cleaner import strip_no_value
from .client import BatchRequest, Session
from .cnx.api import GreenLakeAPI
from .environment import env, env_var
from .models.common import APUpdate, APUpdates
from .models.imports import ImportSubDevices
from .response import Response
from .ws_client import follow_logs

if TYPE_CHECKING:  # pragma: no cover
    from centralcli.cache import Cache, CacheDevice, CacheGroup, CacheInvDevice, CacheLabel, CacheSub, CentralObject
    from centralcli.typedefs import CacheTableName, LogType, SendConfigTypes


TableFormat = Literal["json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action", "clean"]
MsgType = Literal["initial", "previous", "forgot", "will_forget", "previous_will_forget"]

api = ClassicAPI()


class MoveData:
    def __init__(
            self,
            *,
            mv_reqs: List[BatchRequest],
            mv_msgs: Dict[str, List[str]],
            action_word: Literal["pre-provisioned", "moved", "removed", "assigned"],
            move_type: Literal["group", "site", "label"],
            retain_config: bool = False,
            cache_devs: List[CentralObject] = None,
        ) -> None:
        self._move_type = move_type
        self.cache_devs = cache_devs
        self.reqs: Tuple[BatchRequest] = mv_reqs or []
        self.msgs: List[str] = self._build_msg_list(mv_msgs=mv_msgs, action_word=action_word, move_type=move_type, retain_config=retain_config)

    def __bool__(self) -> bool:
        return True if self.reqs else False

    def __str__(self) -> str:
        return "\n".join(self.msgs)

    def __len__(self) -> int:
        return len(self.reqs)

    def _build_msg_list(self, mv_msgs: Dict[str, List[str]], action_word: Literal["pre-provisioned", "moved", "removed", "assigned"], move_type: Literal["group", "site", "label"], retain_config: bool = False,) -> List[str]:
        confirm_msgs = []
        if mv_msgs:
            for k, v_list in mv_msgs.items():
                dev_word = "devices" if len(v_list) > 1 else "device"
                action_words = f"[bright_green]{action_word}[/] to" if action_word != "removed" else f"[red]{action_word}[/] from"
                confirm_msg = f'[deep_sky_blue1]\u2139[/]  [dark_olive_green2]{len(v_list)}[/] {dev_word} will be {action_words} {move_type} [cyan]{k}[/]'  # \u2139 = :information:
                if retain_config:
                    confirm_msg = f"{confirm_msg} [italic dark_olive_green2]CX config will be preserved[/]."
                confirm_msgs += [confirm_msg]
                if len(v_list) > 6:
                    v_list = [*v_list[0:3], "...", *v_list[-3:]]
                confirm_msgs = [*confirm_msgs, *[f'  {dev}' for dev in v_list]]

        return confirm_msgs


@dataclass
class Skipped:
    iden: str
    reason: str

    def __str__(self):
        return f"{self.iden}: {self.reason}"

    def __rich__(self):
        return f"[bright_green]{self.iden}[/]: [dim red1]{self.reason}[/]"


@dataclass
class APRequestInfo:
    reqs: List[BatchRequest] | None
    ap_data: APUpdates
    skipped: Dict[str, Skipped] | None = None
    requires_reboot: Dict[str, CacheDevice] | None = None
    env_update_aps: int | None = None
    gps_update_aps: int | None = None

    @property
    def skipped_summary(self) -> str:
        return utils.summarize_list([s.__rich__() for s in self.skipped.values()], max=12, color=None, italic=True)


@dataclass
class PreConfig:
    name: str
    dev_type: Literal["ap", "gw"]
    config: str
    request: BatchRequest


class APIClients:  # TODO play with cached property vs setting in init to see how it impacts import performance across the numerous files that need this

    @cached_property
    def classic(self):
        return ClassicAPI(config.classic.base_url)

    @cached_property
    def glp(self):
        return None if not config.glp.ok else GreenLakeAPI(config.glp.base_url)


class CLICommon:
    def __init__(self, workspace: str = "default", cache: Cache = None, raw_out: bool = False):
        self.workspace = workspace
        self.cache = cache
        self.raw_out = raw_out
        self.options = CLIOptions(cache)
        self.arguments = CLIArgs(cache)

    class WorkSpaceMsg:
        def __init__(self, workspace: str = None, msg: MsgType = None) -> None:
            self.workspace = workspace
            self.msg = msg

        def __str__(self) -> str:
            if self.msg and hasattr(self, self.msg):
                return getattr(self, self.msg)
            else:
                return self.initial if not env.workspace else self.envvar

        def __call__(self) -> str:
            return self.__str__()

        @property
        def envvar(self):
            return f'[magenta]Using Workspace[/]: [cyan]{self.workspace}[/] [italic]based on env var[/] [dark_green]{env_var.workspace}[/]'

        @property
        def initial(self):
            msg = (
                f'[magenta]Using Workspace[/]: [cyan]{self.workspace}[/].\n'
                f'[bright_red blink]Workspace setting is sticky.[/]  '
                f'[cyan]{self.workspace}[/] [magenta]will be used for subsequent commands until[/]\n'
                f'[cyan]--ws[/]|[cyan]--workspace[/] [dark_olive_green2]<workspace name>[/] or [cyan]-d[/] (revert to default workspace). is used.\n'
            )
            return msg

        @property
        def previous(self):
            return (
                f'[magenta]Using previously specified workspace[/]: [cyan blink]{self.workspace}[/]'
                f'\n[magenta]Use[/] [cyan]--ws[/]|[cyan]--workspace[/] [dark_olive_green2]<workspace name>[/] [magenta]to switch to another workspace.[/]'
                f'\n    or [cyan]-d[/] [magenta]flag to revert to default workspace[/].'
            )

        @property
        def forgot(self):
                return ":information:  Forget option set for workspace, and expiration has passed.  [bright_green]reverting to default workspace\n[/]"

        @property
        def will_forget(self):
            will_forget_msg = "[magenta]Forget options is configured, will revert to default workspace[/]\n"
            will_forget_msg = f"{will_forget_msg}[cyan]{config.forget}[/][magenta] mins after last command[/]\n"
            return will_forget_msg

        @property
        def previous_will_forget(self):
            return f"{self.previous}\n\n{self.will_forget}"

        @property
        def previous_short(self):
            return f":information:  Using previously specified workspace: [bright_green]{self.workspace}[/].\n"

    def workspace_name_callback(self, ctx: typer.Context, workspace: str | None, default: bool = False) -> str:
        """Responsible for workspace messaging.  Actual workspace is determined in config.

        Workspace has to be collected prior to CLI for completion to work specific to the workspace.

        Args:
            ctx (typer.Context): Typer context
            workspace (str): workspace name.  Will only have value if --ws|--workspace flag was used.
                Otherwise we use the default workspace, or envvar, or the last workspace (if forget timer not expired.)
            default (bool, optional): If default flag was used to call this func. Defaults to False.

        Raises:
            typer.Exit: Exits if account is not found.

        Returns:
            str: account name
        """
        if ctx.resilient_parsing:  # tab completion, return without validating, so does use of "test method" command
            return workspace

        # dev commands that change files, we don't need to verify the workspace.
        if sys.argv[1:] and sys.argv[1] == "dev":
            return workspace

        # cencli test method requires --ws when using non default, we do not honor forget_account_after
        if " ".join(sys.argv[1:]).startswith("test method"):
            if workspace:
                render.econsole.print(f":information:  Using workspace [bright_green]{workspace}[/]\n",)
                return workspace
            else:
                return config.default_workspace

        workspace = workspace or config.default_workspace  # workspace only has value if --ws flag is used.

        if default:  # They used the -d flag
            render.econsole.print(":information:  [bright_green]Using default central workspace[/]\n",)
            if config.sticky_workspace_file.is_file():
                config.sticky_workspace_file.unlink()
            if workspace in config.defined_workspaces:
                return workspace
            return config.default_workspace

        # -- // sticky last account messaging account is loaded in config.py \\ --
        elif workspace == config.default_workspace:  # They didn't specify anything via cmd flags.  Honor last_account if set and not expired.
            if config.last_workspace:
                # last account messaging.
                if config.forget is not None:
                    if config.last_workspace_expired:
                        msg = self.WorkSpaceMsg(workspace)
                        render.econsole.print(msg.forgot)
                        if config.sticky_workspace_file.is_file():
                            config.sticky_workspace_file.unlink()

                    else:
                        workspace = config.last_workspace
                        msg = self.WorkSpaceMsg(workspace)
                        if not config.last_workspace_msg_shown:
                            render.econsole.print(msg.previous_will_forget)
                            config.update_last_workspace_file(workspace, config.last_cmd_ts, True)
                        else:
                            render.econsole.print(msg.previous_short)

                else:
                    workspace = config.last_workspace
                    msg = self.WorkSpaceMsg(workspace)
                    if not config.last_workspace_msg_shown:
                        render.econsole.print(msg.previous)
                        config.update_last_workspace_file(workspace, config.last_cmd_ts, True)
                    else:
                        render.econsole.print(msg.previous_short)

        elif workspace in config.defined_workspaces:
            if workspace == (env.workspace or ""):
                msg = self.WorkSpaceMsg(workspace)
                render.econsole.print(msg.envvar)
            elif config.forget is not None and config.forget > 0:
                render.econsole.print(self.WorkSpaceMsg(workspace).initial)
            # No need to print account msg if forget is set to zero

        if config.valid:
            return workspace
        else:  # -- Error messages config invalid or account not found in config --
            _def_msg = False
            render.econsole.print(
                f":warning:  [bright_red]Error:[/] The specified workspace: [cyan]{config.workspace}[/] is not defined in the config @\n"
                f"  {config.file}\n"
            )

            if "default" not in config.defined_workspaces:
                _def_msg = True
                render.econsole.print(
                    ":warning:  [cyan]default[/] workspace is not defined in the config.  This is the default when not overridden by\n"
                    f"--ws|--workspace flag or [cyan]{env_var.workspace}[/] environment variable.\n"
                )

            if workspace != "default":
                if config.defined_workspaces:
                    render.econsole.print(f"[bright_green]The following workspaces are defined[/] [cyan]{'[/], [cyan]'.join(config.defined_workspaces)}[reset]\n", emoji=False)
                    if not _def_msg:
                        render.econsole.print(
                            f"The default workspace [cyan]{config.default_workspace}[/] is used if no workspace is specified via [cyan]--ws[/]|[cyan]--workspace[/] flag.\n"
                            f"or the [cyan]{env_var.workspace}[/] environment variable.\n"
                        )

            self.exit()

    def version_callback(self, ctx: typer.Context | None = None,):
        if ctx is not None and ctx.resilient_parsing:  # tab completion, return without validating
            return

        try:
            current = version("centralcli")
        except PackageNotFoundError:
            # self.exit(str(e))
            current = "0.0.0"

        if current == "0.0.0":
            try:
                file = Path(__file__).parent / "pyproject.toml"
                data = file.read_text()
                current = [line for line in data.splitlines()[0:10] if line.startswith("version")][0].split()[2].replace('"', '')
            except Exception:
                ...

        msg = "[bold bright_green]HPE Aruba Central API CLI (cencli)[/]\n"
        msg += 'A CLI app for interacting with Aruba Central Cloud Management Platform.\n'
        msg += 'Brought to you by [cyan]Wade Wells [dim italic](Pack3tL0ss)[/dim italic][/]\n\n'

        session = Session()
        resp = session.request(session.get, "https://pypi.org/pypi/centralcli/json")
        if not resp:
            msg += "\n".join(
                [
                    "  Documentation: https://central-api-cli.readthedocs.org",
                    "  Homepage: https://github.com/Pack3tL0ss/central-api-cli",
                    "  Repository: https://github.com/Pack3tL0ss/central-api-cli",
                    "  issues: https://github.com/Pack3tL0ss/central-api-cli/issues"
                ]
            )
            msg += f'\n\nVersion: {current}'
        else:  # TODO there is a version key in the response.  should be resp.output["info"]["version"]
            major = max([int(str(k).split(".")[0]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2])
            minor = max([int(str(k).split(".")[1]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2 and int(str(k).split(".")[0]) == major])
            patch = max([int(str(k).split(".")[2]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2 and int(str(k).split(".")[0]) == major and int(str(k).split(".")[1]) == minor])
            latest = f'{major}.{minor}.{patch}'
            msg += "\n".join([f'  {k}: [cyan]{v}[/]' for k, v in resp.output["info"]["project_urls"].items()])
            msg += f'\n\nVersion: {current}'
            if current == latest:
                msg += " :sparkles: [italic green3]You are on the latest version.[reset] :sparkles:"
            else:
                msg += f'\nLatest Available Version: {latest}'

                try:
                    if "/uv/" in find_spec("centralcli").origin:
                        msg += "\n\nUse [cyan]uv tool upgrade centralcli[/] to upgrade"
                except Exception as e:
                    log.error(f"{e.__class__.__name__} cliself.version_callback Failed to find centralcli package path")

        render.econsole.print(msg)

    @staticmethod
    def send_cmds_node_callback(ctx: typer.Context, commands: Union[str, Tuple[str]]):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return

        if ctx.params["kw1"].lower() == "all" and ctx.params["nodes"].lower() == "commands":
            ctx.params["nodes"] = None
            return tuple([ctx.params["kw2"], *commands])
        else:
            return commands

    @staticmethod
    def debug_callback(ctx: typer.Context, debug: bool):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return False

        if debug:
            log.DEBUG = config.debug = debug
            return debug

    @staticmethod
    def get_format(
        do_json: bool = False, do_yaml: bool = False, do_csv: bool = False, do_table: bool = False, default: str = "rich"
    ) -> TableFormat:
        """Simple helper method to return the selected output format type (str)"""
        if do_yaml:
            return "yaml"
        if do_json:
            return "json"
        if do_csv:
            return "csv"
        if do_table:
            return "rich" if default != "rich" else "tabulate"

        return default

    @staticmethod
    def exit(msg: str = None, code: int = 1, emoji: bool = True) -> None:
        """Print msg text and exit.

        Prepends warning emoji to msg if code indicates an error.
            emoji arg has not impact on this behavior.
            Nothing is displayed if msg is not provided.

        Args:
            msg (str, optional): The msg to display (supports rich markup). Defaults to None.
            code (int, optional): The exit status. Defaults to 1 (indicating error).
            emoji (bool, optional): Set to false to disable emoji. Defaults to True.

        Raises:
            typer.Exit: Exit
        """
        console = Console(stderr=True, emoji=emoji)
        if code != 0:
            msg = f"[dark_orange3]\u26a0[/]  {msg}" if msg else msg  # \u26a0 = ⚠ / :warning:

        # Display any log captions when exiting
        if log.caption:
            console.print(log.caption.lstrip().replace("\n  ", "\n"))

        if msg:
            console.print(msg)
        raise typer.Exit(code=code)

    def delta_to_start(self, delta: str = None, past: bool = True) -> pendulum.DateTime | None:
        """Common helper to parse --past or --in option and return pendulum.DateTime object representing start time

        Args:
            delta (str, optional): Calculates start time from str like 3M where M=Months, w=weeks, d=days, h=hours, m=minutes. Defaults to None.
            past (bool, optional): by default returns time in the past (now - delta),
                if is_past=False will return future time (now + delta). Defaults to True.

        Returns:
            pendulum.DateTime | None: returns DateTime object in UTC or None if past argument was None.

        Raises:
            typer.Exit: If past str has value but is invalid.
        """
        if not delta:
            return

        delta = delta.replace(" ", "")
        now: pendulum.DateTime = pendulum.now(tz="UTC")
        delta_func = now.subtract if past else now.add
        try:
            if delta.endswith("d"):
                start = delta_func(days=int(delta.rstrip("d")))
            elif delta.endswith("h"):
                start = delta_func(hours=int(delta.rstrip("h")))
            elif delta.endswith("m"):
                start = delta_func(minutes=int(delta.rstrip("m")))
            elif delta.endswith("M"):
                start = delta_func(months=int(delta.rstrip("M")))
            elif delta.endswith("w"):
                start = delta_func(weeks=int(delta.rstrip("w")))
            else:
                self.exit(
                    '\n'.join(
                        [
                            f"[cyan]{'--past' if past else '--in'}[/] [bright_red]{delta}[/] Does not appear to be valid. Specifically timeframe suffix [bright_red]{list(delta)[-1]}[/] is not a recognized specifier.",
                            "Valid suffixes: [cyan]M[/]=Months, [cyan]w[/]=weeks, [cyan]d[/]=days, [cyan]h[/]=hours, [cyan]m[/]=minutes"
                        ]
                    )
                )
        except ValueError:
            self.exit(f"[cyan]{'--past' if past else '--in'}[/] [bright_red]{delta}[/] Does not appear to be valid")

        return start

    def verify_time_range(self, start: datetime | pendulum.DateTime | None, end: datetime | pendulum.DateTime = None, past: str = None, max_days: int = 90, end_offset: pendulum.Duration = None) -> Tuple[pendulum.DateTime | None, pendulum.DateTime | None]:
        if end and past:
            log.warning("[cyan]--end[/] flag ignored, providing [cyan]--past[/] implies end is now.", caption=True,)
            end = None

        if start and past:
            log.warning(f"[cyan]--start[/] flag ignored, providing [cyan]--past[/] implies end is now - {past}", caption=True,)

        if past:
            start = self.delta_to_start(delta=past)

        if end and end_offset and start is None:
            start = end - end_offset

        if start is None:
            return start, end

        if not hasattr(start, "timezone"):
            start = pendulum.from_timestamp(start.timestamp(), tz="UTC")
        if end is None:
            _end = pendulum.now(tz=start.timezone)
        else:
            _end = end if hasattr(end, "timezone") else pendulum.from_timestamp(end.timestamp(), tz="UTC")

        delta = _end - start

        if max_days is not None and delta.days > max_days:
            if end:
                self.exit(f"[cyan]--start[/] and [cyan]--end[/] provided span {delta.days} days.  Max allowed is 90 days.")
            else:
                log.info(f"[cyan]--past[/] option spans {delta.days} days.  Max allowed is 90 days.  Output constrained to 90 days.", caption=True)
                return self.delta_to_start("2_159h"), _end  # 89 days and 23 hours to avoid timing issue with API endpoint

        return start, _end

    @staticmethod
    def get_time_range_caption(start: datetime | pendulum.DateTime | None, end: datetime | pendulum.DateTime = None, default = "in past 3 hours.") -> str:
            if not end:
                return default if not start else f"in {DateTime(start.timestamp(), 'timediff-past')}"
            if start:
                return f"from {DateTime(start.timestamp(), 'mdyt')} to {DateTime(end.timestamp(), 'mdyt')}"

            raise ValueError("get_time_range_caption() requires start when end is provided.  Use verify_time_range with end_offset to set a default when not provided by user")


    @staticmethod
    async def get_file_hash(file: Path = None, string: str = None) -> str:
        import hashlib
        md5 = hashlib.md5()

        if file:
            with file.open("rb") as f:
                while chunk := f.read(4096):
                    md5.update(chunk)
        elif string:
            if isinstance(string, bytes):
                md5.update(string)
            else:
                md5.update(string.encode("utf-8"))
        else:
            raise ValueError("One of file or string argument is required")

        return md5.hexdigest()

    def _parse_subscription_data(self, data: dict[str, list | str] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            return data

        devices = []
        for idx, (sub, dev) in enumerate(data.items(), start=1):
            if not utils.is_resource_id(sub):
                sub_obj: CacheSub = self.cache.get_sub_identifier(sub)
                if not sub_obj:
                    self.exit(f"Unable to determine subscription id from subscription {sub} on line {idx} of import file.")

                sub = sub_obj.id
            inv_devs = [self.cache.get_combined_inv_dev_identifier(d) for d in utils.listify(dev)]
            devices += [{"serial": d.serial, "subscription": sub} for d in inv_devs]

        return devices

    def _get_import_file(self, import_file: Path = None, import_type: CacheTableName = None, subscriptions: bool = False, text_ok: bool = False,) -> list[dict[str, Any]]:
        data = None
        if import_file is not None:
            try:
                data = config.get_file_data(import_file, text_ok=text_ok)
            except UserWarning as e:
                log.exception(e)
                self.exit(e)

        if not data:
            self.exit(f"[bright_red]ERROR[/] {import_file.name} not found or empty.")

        if isinstance(data, dict) and import_type and import_type in data:
            data = data[import_type]

        if subscriptions:
            data = self._parse_subscription_data(data)


        import_type = import_type or ""
        if isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):
            if import_type in ["groups", "sites", "mpsk", "mac"]:  # accept yaml/json keyed by name for groups and sites
                data = [{"name": k, **v} for k, v in data.items()]
            elif utils.is_serial(list(data.keys())[0]):  # accept yaml/json keyed by serial for devices
                data = [{"serial": k, **v} for k, v in data.items()]
        elif text_ok and isinstance(data, list) and all([isinstance(d, str) for d in data]):
            if import_type == "devices" and utils.is_serial(data[0].keys()[-1]):  # spot check the last key to ensure it looks like a serial
                data = [{"serial": s} for s in data if not s.lower().startswith("serial")]
            if import_type == "labels":
                data = [{"name": label} for label in data if not label.lower().startswith("label")]

        data = strip_no_value(data, aggressive=True)  # We need to strip empty strings as csv import will include the field with empty string and fail validation
                                                            # We support yaml with csv as an !include so a conditional by import_file.suffix is not sufficient.

        # They can mark items as ignore or retired (True).  Those devices/items are filtered out.
        if isinstance(data, list) and all([isinstance(d, dict) for d in data]):
            data = [d for d in data if not d.get("retired", d.get("ignore"))]

        if not data:
            log.warning("No data after import from file.", caption=True)

        return data

    def _check_update_dev_db(self, device: CacheDevice) -> CacheDevice:
        if self.cache.responses.dev:  # TODO have check_fresh bypass API call if cli.cache.responses.dev has value  (move this check there)
            log.warning(f"_check_update_dev_db called for {device} devices have already been fetched this session. Skipping.")
        else:
            _ = api.session.request(self.cache.refresh_dev_db, dev_type=device.type)
            device = self.cache.get_dev_identifier(device.serial, include_inventory=True, dev_type=device.type)

        return device

    def _build_pre_config(self, node: str, dev_type: SendConfigTypes, cfg_file: Path, var_file: Path = None) -> PreConfig:
        """Build Configuration from raw config or jinja2 template/variable file.

        Args:
            node (str): The name of the central node (group name or device MAC for gw)
            dev_type (Literal["gw", "ap"]): Type of device being pre-provisioned.  One of 'gw' or 'ap'.
            cfg_file (Path): Path of the config file.
            var_file (Path, optional): Path of the variable file. Defaults to None.

        Raises:
            typer.Exit: If config is j2 template but no variable file is found.
            typer.Exit: If result of config generation yields no commands

        Returns:
            PreConfig: PreConfig object
        """
        if not cfg_file.exists():
            self.exit(f"[cyan]{node}[/] specified config: {cfg_file} [red]not found[/].  [red italic]Unable to generate config[/].")

        br = BatchRequest
        from centralcli.caas import CaasAPI  # TODO circular import if done at the top
        caasapi = CaasAPI()
        config_out = utils.generate_template(cfg_file, var_file=var_file)
        commands = utils.validate_config(config_out)

        this_req = br(caasapi.send_commands, node, cli_cmds=commands) if dev_type == "gw" else br(api.configuration.replace_ap_config, node, clis=commands)
        return PreConfig(name=node, config=config_out, dev_type=dev_type, request=this_req)

    def batch_add_groups(self, import_file: Path = None, data: dict = None, yes: bool = False) -> list[Response]:
        """Batch add groups to Aruba Central

        Args:
            import_file (Path, optional): import file containing group data. Defaults to None.
            data (dict, optional): data Used internally, when import_file is already parsed by batch_deploy. Defaults to None.
            yes (bool, optional): If True we bypass confirmation prompts. Defaults to False.

        Raises:
            typer.Exit: Exit if data is not in correct format.

        Returns:
            list[Response]: List of Response objects.
        """
        # TODO if multiple groups are being added and the first one fails, the remaining groups do not get added (due to logic in _batch_request)
        # either need to set continue_on_fail or strip any group actions for groups that fail (i.e. upload group config.)
        # TODO convert yes to int with count, allow -yy to skip config confirmation and main confirmation
        br = BatchRequest
        if import_file is not None:
            data = self._get_import_file(import_file, import_type="groups")
        elif not data:
            self.exit("No import file provided")

        reqs, gw_reqs, ap_reqs = [], [], []
        pre_cfgs = []
        confirm_msg = ""
        cache_data = []

        try:
            groups = Groups(data)
        except (ValidationError, KeyError) as e:
            self.exit(''.join(str(e).splitlines(keepends=True)[0:-1]))  # strip off the "for further information ... errors.pydantic.dev..."

        names_from_import = [g.name for g in groups]
        if any([name in self.cache.groups_by_name for name in names_from_import]):
            render.econsole.print("[dark_orange3]:warning:[/]  Import includes groups that already exist according to local cache.  Updating local group cache.")
            _ = api.session.request(self.cache.refresh_group_db)  # This updates cli.cache.groups_by_name
            # TODO maybe split batch_verify into the command and the function that does the validation, then send the data from import for groups that already exist to the validation func.

        skip = []
        for g in groups:
            for dev_type, cfg_file, var_file in zip(["gw", "ap"], [g.gw_config, g.ap_config], [g.gw_vars, g.ap_vars]):
                if cfg_file is not None:
                    pc = self._build_pre_config(g.name, dev_type=dev_type, cfg_file=cfg_file, var_file=var_file)
                    pre_cfgs += [pc]
                    confirm_msg += (
                        f"  [bright_green]{len(pre_cfgs)}[/]. [cyan]{g.name}[/] {'Gateway' if dev_type == 'gw' else 'AP'} "
                        f"group level will be configured based on [cyan]{cfg_file.name}[/]\n"
                    )
                    if dev_type == "gw":
                        gw_reqs += [pc.request]
                    else:
                        ap_reqs += [pc.request]

            if g.name in self.cache.groups_by_name:
                render.econsole.print(f"[dark_orange3]:warning:[/]  Group [cyan]{g.name}[/] already exists. [red]Skipping Group Add...[/]")
                skip += [g.name]
                continue

            reqs += [
                br(
                    api.configuration.create_group,
                    g.name,
                    allowed_types=g.allowed_types,
                    wired_tg=g.wired_tg,
                    wlan_tg=g.wlan_tg,
                    aos10=g.aos10,
                    microbranch=g.microbranch,
                    gw_role=g.gw_role,
                    monitor_only_sw=g.monitor_only_sw,
                    monitor_only_cx=g.monitor_only_cx,
                    cnx=g.cnx,
                )
            ]
            cache_data += [g.model_dump()]

        groups_cnt = len(groups) - len(skip)
        reqs_cnt = len(reqs) + len(gw_reqs) + len(ap_reqs)

        if pre_cfgs:
            confirm_msg = (
                "\n[bright_green]Group level configurations will be sent:[/]\n"
                f"{confirm_msg}"
            )

        if cache_data:
            _groups_text = utils.color([g.name for g in groups if g.name not in skip], "cyan", pad_len=4, sep="\n")
            confirm_msg = (
                f"[bright_green]The following {f'[cyan]{groups_cnt}[/] groups' if groups_cnt > 1 else 'group'} will be created[/]:\n{_groups_text}\n"
                f"{confirm_msg}"
            )

        if len(reqs) + len(gw_reqs) + len(ap_reqs) > 1:
            confirm_msg = f"{confirm_msg}\n[italic dark_olive_green2]{reqs_cnt} API calls will be performed.[/]\n"

        if not reqs_cnt:
            self.exit("No Updates to perform...", code=0)


        render.econsole.print(confirm_msg, emoji=False)
        if pre_cfgs:
            idx = 0
            while True:
                if idx > 0:
                    render.econsole.print(confirm_msg, emoji=False)
                render.econsole.print("Select [bright_green]#[/] to display config to be sent, [bright_green]go[/] to continue or [red]abort[/] to abort.")
                ch: str = render.ask(
                    ">",
                    console=render.econsole,
                    choices=[*[str(idx) for idx in range(1, len(pre_cfgs) + 1)], "abort", "go"],
                )
                if ch.lower() == "go":
                    yes = True
                    break
                else:
                    pc: PreConfig = pre_cfgs[int(ch) - 1]
                    pretty_type = 'Gateway' if pc.dev_type == 'gw' else pc.dev_type.upper()
                    render.econsole.rule(f"{pc.name} {pretty_type} config")
                    with render.econsole.pager():
                        render.econsole.print(pc.config, emoji=False)
                    render.econsole.rule(f"End {pc.name} {pretty_type} config")
                idx += 1

        resp = []
        if reqs and render.confirm(yes):
            resp = api.session.batch_request(reqs)

            # -- Update group cache --
            cache_update_data = [group_data for res, group_data in zip(resp, cache_data) if res.ok]
            api.session.request(self.cache.update_group_db, data=cache_update_data)

        if [*ap_reqs, *gw_reqs]:
            if not reqs:
                render.econsole.print("[dark_orange3]:warning:[/]  Updating Group level config for group(s) that [dark_olive_green2]already exists[/][red]![/]  [dark_orange3]:warning:[/]")
                render.confirm()  # render.confirm aborts

            config_reqs = []
            if gw_reqs:
                render.econsole.print("\n[bright_green]About to send group level gateway config (CLI commands)[/]")
                render.econsole.print("  [italic blink]This can take some time.[/]")
                config_reqs += gw_reqs
            if ap_reqs:
                render.econsole.print("\n[bright_green]About to send group level AP config (Replaces entire group level)[/]\n")
                config_reqs += ap_reqs
            if config_reqs:
                for _ in track(range(10), description="Delay to ensure groups are ready to accept configs."):
                    time.sleep(1)
                resp += api.session.batch_request(config_reqs, retry_failed=True)

        return resp or Response(error="No Groups were added")


    # TODO # FIXME incossistent return type. other batch_add... methods return a list[Response]  this returns a single combined response
    # for the sake of the output.  Probably best to do the combining elsewhere so the return is consistent
    # complicated further as this can return a list if there are any failures.
    def batch_add_sites(self, import_file: Path = None, data: dict = None, yes: bool = False) -> Response:
        if all([d is None for d in [import_file, data]]):
            raise ValueError("batch_add_sites requires import_file or data arguments, neither were provided")

        # We allow a list of flat dicts or a list of dicts where loc info is under
        # "site_address" or "geo_location"
        # can be keyed by name or flat.
        if import_file is not None:
            data = self._get_import_file(import_file, "sites")
        elif isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):  # Data keyed by site name
            data = [{"site_name": k, **data[k]} for k in data]  # deploy is the only one that passes raw data in.

        try:
            verified_sites = ImportSites(data)
        except Exception as e:
            self.exit(f"Import data failed validation, refer to [cyan]cencli batch add sites --example[/] for example formats.\n{e}")

        for idx in range(2):
            already_exists = [(s.site_name, idx) for idx, s in enumerate(verified_sites) if s.site_name in [s["name"] for s in self.cache.sites]]
            if already_exists:
                if idx == 0:
                    render.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{len(already_exists)}[/] sites from import already exist according to the cache, ensuring cache is current.")
                    _ = api.session.request(self.cache.refresh_site_db)
                else:
                    cache_exists = [self.cache.get_site_identifier(s[0]) for s in already_exists]
                    skip_txt = utils.summarize_list([s.summary_text for s in cache_exists], color=None)
                    render.econsole.print(f"[dark_orange3]:warning:[/]  The Following Sites will be [red]skipped[/] as they already exist in Central.\n{skip_txt}\n")
                    verified_sites = [site for idx, site in enumerate(verified_sites) if idx not in [s[1] for s in already_exists]]

        if not verified_sites:
            self.exit("[italic dark_olive_green2]No Sites remain after validation[/].")

        address_fields = {"site_name": "bright_green", "address": "bright_cyan", "city": "turquoise4", "state": "dark_olive_green3", "country": "magenta", "zipcode": "blue", "latitude": "medium_spring_green", "longitude": "spring_green3"}
        confirm_msg = utils.summarize_list(
            [
                "|".join([f'[{address_fields[k]}]{v}[/]' for k, v in site.model_dump().items() if v and k in address_fields]) for site in list(verified_sites)
            ],
            max=7
        )
        render.econsole.print(f"\n[bright_green]The Following [cyan]{len(verified_sites)}[/] Sites will be created:[/]")
        render.econsole.print(confirm_msg, emoji=False)

        render.confirm(yes)
        reqs = [
            BatchRequest(api.central.create_site, **site.model_dump())
            for site in verified_sites
        ]
        resp = api.session.batch_request(reqs)
        passed = list(sorted([r for r in resp if r.ok], key=lambda r: r.rl))
        failed = [r for r in resp if not r.ok]
        if passed:
            cache_data = [r.output for r in passed]
            api.session.request(self.cache.update_site_db, data=cache_data)  # TODO need an add function, this update combines old with new then truncates and re-writes all sites.
            # we combine the passing responses into 1.
            passed[0].output = cache_data
            resp = passed[0] if not failed else [passed[0], *failed]

        return resp

    def validate_license_type(self, data: List[Dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
        """validate device add import data for valid subscription name.

        Args:
            data (List[Dict[str, Any]]): The data from the import

        Returns:
            Tuple[List[Dict[str, Any]], bool]: Tuple with the data, and a bool indicating if a warning should occur indicating the license doesn't appear to be valid
                The data is the same as what was provided, with the key changed to 'license' if they used 'services' or 'subscription'
        """
        _final_sub_key = "subscription"
        sub_key = list(set([k for d in data for k in d.keys() if k in ["license", "services", "subscription"]]))
        sub_key = None if not sub_key else sub_key[0]
        warn = False
        if not sub_key:
            return data, warn

        already_warned = []
        for d in data:
            if d.get(sub_key):
                for idx in range(2):
                    try:
                        sub = self.cache.get_sub_identifier(d[sub_key], best_match=True)
                        d[sub_key] = sub.api_name
                        if sub_key != _final_sub_key:
                            del d[sub_key]
                        break
                    except ValueError:
                        if idx == 0 and self.cache.responses.license is None:
                            render.econsole.print(f'[dark_orange3]:warning:[/]  [cyan]{d[sub_key]}[/] [red]not found[/] in list of valid licenses.\n:arrows_clockwise: Refreshing subscription/license name cache.')
                            resp = api.session.request(self.cache.refresh_license_db)  # TOGLP
                            if not resp:
                                render.display_results(resp, exit_on_fail=True)
                        else:
                            warn = True
                            if d[sub_key] not in already_warned:
                                already_warned += [d[sub_key]]
                                render.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{d[sub_key]}[/] does not appear to be a valid license type.")
        return data, warn

    def verify_required_fields(self, data: List[Dict[str, Any]], required: List[str], optional: List[str] | None = None, example_text: str | None = None, exit_on_fail: bool = True):
        ok = True
        if not all([len(required) == len([k for k in d.keys() if k in required]) for d in data]):
            ok = False
            render.econsole.print("[bright_red]:warning:  !![/] Missing at least 1 required field")
            render.econsole.print("\nThe following fields are [bold]required[/]:")
            render.econsole.print(utils.color(required, pad_len=4, sep="\n"))
            if optional:
                render.econsole.print("\nThe following fields are optional:")
                render.econsole.print(utils.color(optional, color_str="cyan", pad_len=4, sep="\n"))
            if example_text:
                render.econsole.print(f"\nUse [cyan]{example_text}[/] to see valid import file formats.")
            # TODO finish full deploy workflow with config per-ap-settings variables etc allowed
            if exit_on_fail:
                self.exit()
        return ok

    # TOGLP
    def batch_add_devices(self, import_file: Path = None, data: list[dict[str, Any]] | None = None, yes: bool = False) -> List[Response]:
        # TODO build messaging similar to batch move.  build common func to build calls/msgs for these similar funcs
        data: List[Dict[str, Any]] = data or self._get_import_file(import_file, import_type="devices")
        if not data:
            self.exit("No data/import file")

        _reqd_cols = ["serial", "mac"]
        self.verify_required_fields(
            data, required=_reqd_cols, optional=['group', 'subscription'], example_text='cencli batch add devices --show-example'
        )
        data, warn = self.validate_license_type(data)
        word = "Adding" if not warn and yes else "Add"

        confirm_devices = ['|'.join([f'[bright_green]{k}[/]:[cyan]{v}[/]' for k, v in d.items() if v or isinstance(v, bool)]) for d in data]
        confirm_str = utils.summarize_list(confirm_devices, pad=2, color=None,)
        file_str = "import file" if not import_file else f"[cyan]{import_file.name}[/]"
        render.console.print(f'{len(data)} Devices found in {file_str}')
        render.console.print(confirm_str.lstrip("\n"), emoji=False)
        render.console.print(f'\n{word} {len(data)} devices found in {file_str}')
        if warn:
            msg = ":warning:  Warnings exist"
            msg = msg if not yes else f"{msg} [cyan]-y[/] flag ignored."
            render.econsole.print(msg)

        resp = None
        if render.confirm(yes=not warn and yes):
            resp: list[Response] = api.session.request(api.platform.add_devices, device_list=data)
            # if any failures occured don't pass data into update_inv_db.  Results in API call to get inv from Central
            _data = None if not all([r.ok for r in resp]) else data
            update_func = self.cache.refresh_inv_db
            kwargs = {}
            if _data:
                try:
                    _data = Inventory(_data).model_dump()
                    update_func = self.cache.update_inv_db
                    kwargs = {"data": _data}
                except ValidationError as e:
                    log.info(f"Performing full cache update after batch add devices as import_file data validation failed. {repr(e)}", show=True)
                    _data = None

            cache_res = [api.session.request(update_func, **kwargs)]  # This starts it's own spinner
            with render.Spinner("Allowing time for devices to populate before updating dev cache.") as spin:
                time.sleep(3)
                spin.update('Performing full device cache update after device edition.')
                time.sleep(2)

            # always perform full dev_db update as we don't know the other fields.
            cache_res += [api.session.request(self.cache.refresh_dev_db)]  # This starts it's own spinner

        return resp or Response(error="No Devices were added")

    # TODO this has not been tested validated at all
    # TODO adapt to add or delete based on param centralcli.delete_label needs the label_id from the cache.
    def batch_add_labels(self, import_file: Path = None, *, data: bool = None, yes: bool = False) -> List[Response]:
        if import_file is not None:
            data = self._get_import_file(import_file, "labels", text_ok=True)
        elif not data:
            self.exit("No import file provided")

        for idx in range(2):
            already_exists = [d["name"] for d in data if d["name"] in self.cache.label_names]
            if already_exists:
                if idx == 0:
                    render.econsole.print(f"[dark_orange3]:warning:[/]  [cyan]{len(already_exists)}[/] labels from import already exist according to the cache, ensuring cache is current.")
                    _ = api.session.request(self.cache.refresh_label_db)
                else:
                    skip_txt = utils.summarize_list(already_exists)
                    render.econsole.print(f"[dark_orange3]:warning:[/]  The Following Labels will be [red]skipped[/] as they already exist in Central.\n{skip_txt}\n")
                    data = [label for label in data if label["name"] not in self.cache.label_names]

        if not data:
            self.exit("[italic dark_olive_green2]No Labels remain after validation[/].")

        # TODO common func for this type of multi-element confirmation, we do this a lot.
        _msg = "\n".join([f"  [cyan]{inner['name']}[/]" for inner in data])
        _msg = _msg.lstrip() if len(data) == 1 else f"\n{_msg}"
        _msg = f"[bright_green]Create[/] {'label ' if len(data) == 1 else f'{len(data)} labels:'}{_msg}"
        render.console.print(_msg, emoji=False)

        render.confirm(yes)  # exits here if they don't confirm
        reqs = [BatchRequest(api.central.create_label, label_name=inner['name']) for inner in data]
        resp = api.session.batch_request(reqs)
        try:
            cache_data = Labels([r.output for r in resp if r.ok])
            _  = api.session.request(self.cache.update_label_db, data=cache_data.model_dump())
        except Exception as e:
            log.exception(f'Exception during label cache update in batch_add_labels]\n{e}')
            render.econsole.print(f'[dark_orange3]:warning:[/]  [bright_red]Cache Update Error[/]: {e.__class__.__name__}.  See logs.\nUse [cyan]cencli show labels[/] to refresh label cache.')

        return resp

    class SiteMoves:
        def __init__(self, *, site_mv_reqs: List[BatchRequest], site_mv_msgs: Dict[str, list], site_rm_reqs: List[BatchRequest], site_rm_msgs: Dict[str, list], cache_devs: List[CentralObject],):
            self.cache_devs = cache_devs
            self.move: MoveData = MoveData(mv_reqs=site_mv_reqs, mv_msgs=site_mv_msgs, action_word="moved", move_type="site", cache_devs=cache_devs)
            self.remove: MoveData = MoveData(mv_reqs=site_rm_reqs, mv_msgs=site_rm_msgs, action_word="removed" , move_type="site", cache_devs=cache_devs)

        def __str__(self) -> str:
            return "\n".join([*self.remove.msgs, *self.move.msgs])

        def __bool__(self) -> bool:
            return bool(self.reqs)

        def __len__(self) -> int:
            return len(self.reqs)

        @property
        def reqs(self) -> List[BatchRequest]:
            return [*self.remove.reqs, *self.move.reqs]

        @property
        def serials_by_site_id(self) -> Dict[str, List[str]]:
            out = {}
            for req in self.move.reqs:
                site_id, serials = (req.kwargs["site_id"], req.kwargs["serials"].copy())
                out = utils.update_dict(out, key=site_id, value=serials)

            return out

    class GroupMoves:
        def __init__(
                self,
                *,
                pregroup_mv_reqs: List[BatchRequest],
                pregroup_mv_msgs: Dict[str, list],
                group_mv_reqs: List[BatchRequest],
                group_mv_msgs: Dict[str, list],
                group_mv_cx_retain_reqs: List[BatchRequest],
                group_mv_cx_retain_msgs: Dict[str, list],
                cache_devs: List[CentralObject],
            ):
            self.preprovision: MoveData = MoveData(mv_reqs=pregroup_mv_reqs, mv_msgs=pregroup_mv_msgs, action_word="pre-provisioned", move_type="group", cache_devs=cache_devs)
            self.move: MoveData = MoveData(mv_reqs=group_mv_reqs, mv_msgs=group_mv_msgs, action_word="moved", move_type="group", cache_devs=cache_devs)
            self.move_keep_config: MoveData = MoveData(mv_reqs=group_mv_cx_retain_reqs, mv_msgs=group_mv_cx_retain_msgs, action_word="moved", move_type="group", retain_config=True, cache_devs=cache_devs)

        def __str__(self) -> str:
            return "\n".join([*self.preprovision.msgs, *self.move.msgs, *self.move_keep_config.msgs])

        def __bool__(self) -> bool:
            return bool(self.reqs)

        def __len__(self) -> int:
            return len(self.reqs)

        @property
        def reqs(self) -> List[BatchRequest]:
            return [*self.preprovision.reqs, *self.move.reqs, *self.move_keep_config.reqs]

        @property
        def serials_by_group(self) -> Dict[str, List[str]]:
            out = {}
            for req in [*self.move.reqs, *self.move_keep_config.reqs]:
                group = req.kwargs["group"]
                serials = req.kwargs["serials"].copy()
                out = utils.update_dict(out, key=group, value=serials)

            return out

    def _check_group(self, cache_devs: List[CacheDevice | CacheInvDevice], import_data: dict, cx_retain_config: bool = False, cx_retain_force: bool = None) -> GroupMoves:
        pregroup_mv_reqs, pregroup_mv_msgs = {}, {}
        group_mv_reqs, group_mv_msgs = {}, {}
        req_dict, msg_dict = {}, {}
        group_mv_cx_retain_reqs, group_mv_cx_retain_msgs = {}, {}
        _skip = False
        for cache_dev, mv_data in zip(cache_devs, import_data):
            has_connected = True if cache_dev.db.name == "devices" else False
            for idx in range(0, 2):
                to_group = mv_data.get("group")
                if cx_retain_force is not None:
                    retain_config = cx_retain_force if cache_dev.type == "cx" else False
                else:
                    retain_config = mv_data.get("retain_config") or cx_retain_config  # key to use the 'or' here in case retain_config is in data but set to null or ''
                    _retain_config = ToBool(retain_config)
                    retain_config = _retain_config.value
                    if not _retain_config.ok:
                        self.exit(f'{cache_dev.summary_text} has an invalid value ({retain_config}) for "retain_config".  Value should be "true" or "false" (or blank which is evaluated as false).  Aborting...')
                    if retain_config and cache_dev.type != "cx":
                        self.exit(f'{cache_dev.summary_text} has [cyan]retain_config[/] = {retain_config}.  [cyan]retain_config[/] is only valid for [cyan]cx[/] not [red]{cache_dev.type}[/].  Aborting...')
                if to_group:
                    if to_group not in self.cache.group_names:
                        to_group = self.cache.get_group_identifier(to_group)  # will force cache update
                        to_group = to_group.name

                    if to_group == cache_dev.get("group"):
                        if idx == 0:
                            cache_dev = self._check_update_dev_db(cache_dev)
                        else:
                            render.econsole.print(f"\u2139  [dark_orange3]Ignoring[/] group move for {cache_dev.summary_text}. [italic grey42](already in group [magenta]{to_group}[/magenta])[reset].", emoji=False)
                            _skip = True

                    # Determine if device is in inventory only determines use of pre-provision group vs move to group
                    if not has_connected:
                        req_dict = pregroup_mv_reqs
                        msg_dict = pregroup_mv_msgs
                        if retain_config:
                            render.econsole.print(f'[bright_red]\u26a0[/]  {cache_dev.summary_text} Group assignment is being ignored.', emoji=False)  # \u26a0 is :warning: need clean_console to prevent MAC from being evaluated as :cd: emoji
                            render.econsole.print(f'  [italic]Device has not connected to Aruba Central, it must be "pre-provisioned to group [magenta]{to_group}[/]".  [cyan]retain_config[/] is only valid on group move not group pre-provision.[/]')
                            render.econsole.print('  [italic]To onboard and keep the config, allow it to onboard to the default unprovisioned group (default behavior without pre-provision), then move it once it appears in Central, with retain-config option.')
                            _skip = True
                    else:
                        req_dict = group_mv_reqs if not retain_config else group_mv_cx_retain_reqs
                        msg_dict = group_mv_msgs if not retain_config else group_mv_cx_retain_msgs

            if not _skip:
                req_dict = utils.update_dict(req_dict, key=to_group, value=cache_dev.serial)
                msg_dict = utils.update_dict(msg_dict, key=to_group, value=cache_dev.rich_help_text)

        mv_reqs, pre_reqs, mv_retain_reqs = [], [], []
        if pregroup_mv_reqs:
            pre_reqs = [BatchRequest(api.configuration.preprovision_device_to_group, group=k, serials=v) for k, v in pregroup_mv_reqs.items()]
        if group_mv_reqs:
            mv_reqs = [BatchRequest(api.configuration.move_devices_to_group, group=k, serials=v) for k, v in group_mv_reqs.items()]
        if group_mv_cx_retain_reqs:
            mv_retain_reqs = [BatchRequest(api.configuration.move_devices_to_group, group=k, serials=v, cx_retain_config=True) for k, v in group_mv_cx_retain_reqs.items()]

        return self.GroupMoves(
            pregroup_mv_reqs=pre_reqs,
            pregroup_mv_msgs=pregroup_mv_msgs,
            group_mv_reqs=mv_reqs,
            group_mv_msgs=group_mv_msgs,
            group_mv_cx_retain_reqs=mv_retain_reqs,
            group_mv_cx_retain_msgs=group_mv_cx_retain_msgs,
            cache_devs=cache_devs
        )


    def _check_site(self, cache_devs: list[CacheDevice | CacheInvDevice], import_data: list[dict[str, Any]]) -> SiteMoves:
        site_rm_reqs, site_rm_msgs = {}, {}
        site_mv_reqs, site_mv_msgs = {}, {}
        for cache_dev, mv_data in zip(cache_devs, import_data):
            has_connected = True if cache_dev.db.name == "devices" else False
            for idx in range(0, 2):
                to_site = mv_data.get("site")
                now_site = cache_dev.get("site")
                if not to_site:
                    continue
                else:
                    to_site = self.cache.get_site_identifier(to_site)
                    if now_site and now_site == to_site.name:
                        if idx == 0:
                            cache_dev = self._check_update_dev_db(cache_dev)
                        elif now_site == to_site.name:
                            render.econsole.print(f"[deep_sky_blue3]\u2139[/]  [dark_orange3]Ignoring[/] site move for {cache_dev.summary_text}. [italic grey42](already in site [magenta]{to_site.name}[/magenta])[reset]", emoji=False)
                    elif not has_connected:
                        if idx == 0:
                            cache_dev = self._check_update_dev_db(cache_dev)
                        else:
                            render.econsole.print(f"[deep_sky_blue3]\u2139[/]  [dark_orange3]Ignoring[/] site move for {cache_dev.summary_text}. [italic grey42](Device must connect to Central before site can be assigned)[reset]", emoji=False)
                    elif idx != 0:
                        site_mv_reqs = utils.update_dict(site_mv_reqs, key=f'{to_site.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                        site_mv_msgs = utils.update_dict(site_mv_msgs, key=to_site.name, value=cache_dev.rich_help_text)

                    if now_site:
                        now_site = self.cache.get_site_identifier(now_site)
                        if idx != 0 and now_site.name != to_site.name:  # need to remove from current site
                            render.econsole.print(f'{cache_dev.summary_text} will be removed from site [red]{now_site.name}[/] to facilitate move to site [bright_green]{to_site.name}[/]', emoji=False)
                            site_rm_reqs = utils.update_dict(site_rm_reqs, key=f'{now_site.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                            site_rm_msgs = utils.update_dict(site_rm_msgs, key=now_site.name, value=cache_dev.rich_help_text)

        rm_reqs = []
        if site_rm_reqs:
            for k, v in site_rm_reqs.items():
                site_id, dev_type = k.split("~|~")
                rm_reqs += [BatchRequest(api.central.remove_devices_from_site, site_id=int(site_id), serials=v, device_type=dev_type)]

        mv_reqs = []
        if site_mv_reqs:
            for k, v in site_mv_reqs.items():
                site_id, dev_type = k.split("~|~")
                mv_reqs += [BatchRequest(api.central.move_devices_to_site, site_id=int(site_id), serials=v, device_type=dev_type)]

        return self.SiteMoves(
            cache_devs=cache_devs,
            site_mv_reqs=mv_reqs,
            site_mv_msgs=site_mv_msgs,
            site_rm_reqs=rm_reqs,
            site_rm_msgs=site_rm_msgs
        )

    def _check_label(self, cache_devs: list[CacheDevice | CacheInvDevice], import_data: list[dict[str, Any]],) -> MoveData:
        label_ass_reqs, label_ass_msgs = {}, {}
        for cache_dev, mv_data in zip(cache_devs, import_data):
            to_label = mv_data.get("label", mv_data.get("labels"))
            if to_label:
                to_label = utils.listify(to_label)
                for label in to_label:
                    clabel = self.cache.get_label_identifier(label)
                    # We don't check if device is already assigned to label as we don't cache label assignments in device cache
                    label_ass_reqs = utils.update_dict(label_ass_reqs, key=f'{clabel.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                    label_ass_msgs = utils.update_dict(label_ass_msgs, key=clabel.name, value=cache_dev.rich_help_text)

        batch_reqs = []
        if label_ass_reqs:
            for k, v in label_ass_reqs.items():
                label_id, dev_type = k.split("~|~")
                batch_reqs += [BatchRequest(api.central.assign_label_to_devices, label_id=int(label_id), serials=v, device_type=dev_type)]

        return MoveData(mv_reqs=batch_reqs, mv_msgs=label_ass_msgs, action_word="assigned", move_type="label")

    def device_move_cache_update(
            self,
            mv_resp: List[Response],
            serials_by_site: Dict[str: List[str]] = None,
            serials_by_group: Dict[str: List[str]] = None,
        ) -> None:
        serials_by_site = serials_by_site or {}
        serials_by_group = serials_by_group or {}
        serials = set(
            [
                *([s for s_list in serials_by_site.values() for s in s_list]),
                *([g for g_list in serials_by_group.values() for g in g_list]),
            ]
        )
        moves_by_type = {
            "site": {self.cache.SiteDB.search(self.cache.Q.id == site)[0]["name"]: serials for site, serials in serials_by_site.items()},
            "group": serials_by_group or {}
        }
        cache_by_serial = {k: self.cache.devices_by_serial.get(k, self.cache.inventory_by_serial[k]) for k in [*self.cache.inventory_by_serial, *self.cache.devices_by_serial] if k in serials}
        for r, (move_type, name, serials) in zip(mv_resp, [(move_type, name, serials) for move_type, v in moves_by_type.items() for name, serials in v.items()]):
            if r.ok:
                if move_type == "site":
                    site_success_serials = [s["device_id"] for s in r.raw["success"] if utils.is_serial(s["device_id"])]  # if .... is_serial stips out stack_id, success will have all member serials + the stack_id
                    cache_by_serial = {serial: {**cache_by_serial[serial], "site": name} for serial in serials if serial in site_success_serials}
                if move_type == "group":  # All or none here as far as the rresponse.
                    cache_by_serial = {serial: {**cache_by_serial[serial], "group": name} for serial in serials}

        api.session.request(
            self.cache.update_dev_db,
            data=list(cache_by_serial.values())
        )

    def batch_move_devices(
            self,
            import_file: Path = None,
            *,
            data: List[Dict[str, Any]] = None,
            yes: bool = False,
            do_group: bool = False,
            do_site: bool = False,
            do_label: bool = False,
            cx_retain_config: bool = False,
            cx_retain_force: bool = None,
        ):
        """Batch move devices based on contents of import file

        Args:
            import_file (Path, optional): Import file. Defaults to None (one of import_file or data is required).
            data: (List[Dict[str, Any]]): Data with device identifier and group, site, and/or label keys representing desired move to
                locations for those keys.  Defaults to None (one of import_file or data is required).
            yes (bool, optional): Bypass confirmation prompts. Defaults to False.
            do_group (bool, optional): Process group moves based on import. Defaults to False.
            do_site (bool, optional): Process site moves based on import. Defaults to False.
            do_label (bool, optional): Process label assignment based on import. Defaults to False.
            cx_retain_config (bool, optional): Keep config intact for CX switches during move. 'retain_config' in import_file/data
                takes precedence.  This value is applied only if value is not set in the import_file/data. Defaults to False.
            cx_retain_config (bool, optional): Keep config intact for CX switches during move regardless of 'retain_config' value
                in import_file/data.

        Group/Site/Label are processed by default, unless one of more of do_group, do_site, do_label is specified.

        Raises:
            typer.Exit: Exits with error code if none of name/ip/mac are provided for each device.
        """
        if all([arg is False for arg in [do_site, do_label, do_group]]):
            do_site = do_label = do_group = True

        if not any([data, import_file]):
            self.exit("import_file or data is required")

        devices = data or self._get_import_file(import_file, import_type="devices")

        try:
            dev_idens = [d.get("serial", d.get("mac", d.get("name", "INVALID"))) for d in devices]
        except AttributeError as e:
            self.exit(f"Exception gathering devices from [cyan]{import_file.name}[/]\n[red]AttributeError:[/] {e.args[0]}\nUse [cyan]cencli batch move --example[/] for example import format.)")

        if "INVALID" in dev_idens:
            self.exit(f'missing required field ({utils.color(["serial", "mac", "name"])}) for {dev_idens.index("INVALID") + 1} device in import file.')

        if len(set(dev_idens)) < len(dev_idens):  # Detect and filter out any duplicate entries  # TODO make seperate function and leverage in all batch_xxx_devices
            filtered_count = len(dev_idens) - len(set(dev_idens))
            dev_idens = set(dev_idens)
            render.econsole.print(f"[dark_orange3]:warning:[/]  Filtering [cyan]{filtered_count}[/] duplicate device{'s' if filtered_count > 1 else ''} from update.")

        # conductor_only option, as group move will move all associated devices when device is part of a swarm or stack
        cache_devs: list[CacheDevice | CacheInvDevice | None] = [self.cache.get_dev_identifier(d, include_inventory=True, conductor_only=True, silent=True, exit_on_fail=False) for d in dev_idens]
        not_found_devs: List[str] = [s for s, c in zip(dev_idens, cache_devs) if c is None]
        cache_devs: list[CacheDevice | CacheInvDevice] = [d for d in cache_devs if d is not None]

        if not_found_devs:
            not_in_inv_msg = utils.color(not_found_devs, color_str="cyan", pad_len=4, sep="\n")
            render.econsole.print(f"\n[dark_orange3]\u26a0[/]  The following provided devices were not found in the inventory.\n{not_in_inv_msg}", emoji=False)
            render.econsole.print("[dim italic]They will be skipped[/]\n")
            if not cache_devs:
                self.exit("No devices found")


        site_rm_reqs, batch_reqs, confirm_msgs = [], [], []
        if do_site:  # TODO switch stack with multiple switches confirmation will show "1 device will be moved...", no doubt the same for swarms.  Better if confirm msg indicated the actual # of devices impacted by the move in these cases
            site_ops = self._check_site(cache_devs=cache_devs, import_data=devices)
            batch_reqs += site_ops.move.reqs
            site_rm_reqs += site_ops.remove.reqs
            confirm_msgs += [str(site_ops)]
        serials_by_site = None if not do_site else site_ops.serials_by_site_id
        if do_group:
            group_ops = self._check_group(cache_devs=cache_devs, import_data=devices, cx_retain_config=cx_retain_config, cx_retain_force=cx_retain_force)
            batch_reqs += group_ops.reqs
            confirm_msgs += [str(group_ops)]
        serials_by_group = None if not do_group else group_ops.serials_by_group
        if do_label:
            label_ops = self._check_label(cache_devs=cache_devs, import_data=devices)
            batch_reqs += label_ops.reqs
            confirm_msgs += [str(label_ops)]

        _tot_req = (0 if not do_site else len(site_ops.remove)) + len(batch_reqs)
        if not _tot_req:
            self.exit("[italic dark_olive_green2]Nothing to do[/]", code=0)
        if _tot_req > 1:
            confirm_msgs += [f"\n[italic dark_olive_green2]Will result in {_tot_req} additional API Calls."]

        render.econsole.print("\n".join(confirm_msgs).strip(), emoji=False)  # stripping as we have a \n before and after coming from somewhere.
        if render.confirm(yes):
            site_rm_res = []
            if site_rm_reqs:
                site_rm_res = api.session.batch_request(site_rm_reqs)
                if not all([r.ok for r in site_rm_res]):
                    render.econsole.print("[bright_red]:warning:[/]  Some site remove requests failed, Aborting...")
                    return site_rm_res
            batch_res = api.session.batch_request(batch_reqs)
            # FIXME when move stack only the serial for the conductor is in serials_by_site which mucks the logic in device_move_cache_update.  Need to get all switches with a matching stack_id.  Probably a get_swack_members() method in Cache
            self.device_move_cache_update(batch_res, serials_by_site=serials_by_site, serials_by_group=serials_by_group)  # We don't store device labels in cache.  AP response does not include labels
            # CACHE # FIXME verify cache update logic for stack site move (initially had not site assigned).  Cache after move did not reflect the site they weree moved to.

            return [*site_rm_res, *batch_res]

    def batch_delete_groups(
            self,
            data: list | dict,
            *,
            yes: bool = False,
        ) -> None:
        data = utils.listify(data)
        names_from_import = [g["name"] for g in data if "name" in g]
        if not names_from_import:
            self.exit("Unable to extract group names from import data.  Refer to [cyan]cencli batch delete groups --example[/] for import data format.")

        # If any groups appear to not exist according to local cache, update local cache
        not_in_cache = [name for name in names_from_import if name not in self.cache.groups_by_name]
        if not_in_cache:
            render.econsole.print(f"[dark_orange3]:warning:[/]  Import includes {len(not_in_cache)} group{'s' if len(not_in_cache) > 1 else ''} that do [red bold]not exist[/] according to local group cache.\n:arrows_clockwise: [bright_green]Updating[/] local [cyan]group[/] cache.")
            _ = api.session.request(self.cache.refresh_group_db)  # This updates cli.cache.groups_by_name

        # notify and remove any groups that don't exist after cache update
        cache_by_name: Dict[str, CacheGroup] = {name: self.cache.groups_by_name.get(name) for name in names_from_import}
        not_in_central = [name for name, data in cache_by_name.items() if data is None]
        if not_in_central:
            render.econsole.print(f"[dark_orange3]:warning:[/]  [red]Skipping[/] {utils.color(not_in_central, 'red')} [italic]group{'s do' if len(not_in_central) > 1 else ' does'} not exist in Central.[/]")

        groups: List[CacheGroup] = [g for g in cache_by_name.values() if g is not None]
        reqs = [BatchRequest(api.configuration.delete_group, g.name) for g in groups]

        if not reqs:
            self.exit("No groups remain to process after validation.")

        if len(groups) == 1:
            pre = ''
            pad = 0
            sep = ", "
        else:
            pre = sep = '\n'
            pad = 4

        group_msg = f'{pre}{utils.color([g.name for g in groups], "cyan", pad_len=pad, sep=sep)}'
        _msg = f"[bright_red]Delet{'e' if not yes else 'ing'}[/] {'group ' if len(groups) == 1 else f'{len(reqs)} groups:'}{group_msg}"
        render.econsole.print(_msg)

        if len(reqs) > 1 and not yes:
            render.econsole.print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

        if render.confirm(yes):
            resp = api.session.batch_request(reqs)
            render.display_results(resp, tablefmt="action")
            doc_ids = [g.doc_id for g, r in zip(groups, resp) if r.ok]
            if doc_ids:
                api.session.request(self.cache.update_group_db, data=doc_ids, remove=True)

    def batch_delete_labels(
            self,
            data: list | dict,
            *,
            yes: bool = False,
        ) -> None:
        names_from_import = [g["name"] for g in data if "name" in g]
        if not names_from_import:
            self.exit("Unable to extract label names from import data.  Refer to [cyan]cencli batch delete labels --example[/] for import data format.")

        # If any labels appear to not exist according to local cache, update local cache
        not_in_cache = [name for name in names_from_import if name not in self.cache.labels_by_name]
        if not_in_cache:
            render.econsole.print(f"[dark_orange3]:warning:[/]  Import includes {utils.color(not_in_cache, 'red')}... {'do' if len(not_in_cache) > 1 else 'does'} [red bold]not exist[/] according to local label cache.  :arrows_clockwise: [bright_green]Updating local label cache[/].")
            _ = api.session.request(self.cache.refresh_label_db)  # This updates cli.cache.labels

        # notify and remove any labels that don't exist after cache update
        cache_by_name: Dict[str, CacheLabel] = {name: self.cache.labels_by_name.get(name) for name in names_from_import}
        not_in_central = [name for name, data in cache_by_name.items() if data is None]
        if not_in_central:
            render.econsole.print(f"[dark_orange3]:warning:[/]  [red]Skipping[/] {utils.color(not_in_central, 'red')} [italic]label{'s do' if len(not_in_central) > 1 else ' does'} not exist in Central.[/]")

        labels: List[CacheLabel] = [label for label in cache_by_name.values() if label is not None]
        reqs = [BatchRequest(api.central.delete_label, g.id) for g in labels]

        if len(labels) == 1:
            pre = ''
            pad = 0
            sep = ", "
        else:
            pre = sep = '\n'
            pad = 4

        label_msg = f'{pre}{utils.color([g.name for g in labels], "cyan", pad_len=pad, sep=sep)}'
        _msg = f"[bright_red]Delet{'e' if not yes else 'ing'}[/] {'label ' if len(labels) == 1 else f'{len(reqs)} labels:'}{label_msg}"
        render.econsole.print(_msg)

        if len(reqs) > 1 and not yes:
            render.econsole.print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

        if render.confirm(yes):
            resp = api.session.batch_request(reqs)
            render.display_results(resp, tablefmt="action")
            doc_ids = [g.doc_id for g, r in zip(labels, resp) if r.ok]
            if doc_ids:
                api.session.request(self.cache.update_label_db, data=doc_ids, remove=True)

    def show_archive_results(self, arch_resp: List[Response]) -> None:
        def summarize_arch_res(arch_resp: List[Response]) -> None:
            for res in arch_resp:
                caption = res.output.get("message")
                action = res.url.name
                if res.get("succeeded_devices"):
                    title = f"Devices successfully {action}d."
                    data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
                    render.display_results(data=data, title=title, caption=caption)
                if res.get("failed_devices"):
                    title = f"Devices that [bright_red]failed[/] to {action}."
                    data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
                    render.display_results(data=data, title=title, caption=caption)

        if all([r.ok for r in arch_resp[0:2]]) and all([not r.get("failed_devices") for r in arch_resp[0:2]]):
            arch_resp[0].output = arch_resp[0].output.get("message")
            _success_cnt = len(arch_resp[1].output.get("succeeded_devices", []))
            arch_resp[1].output =  (
                f'  {arch_resp[1].output.get("message", "")}\n'
                f'  Subscriptions successfully removed for {_success_cnt} device{utils.singular_plural_sfx(_success_cnt)}.\n'
                '  \u2139  archive/unarchive flushes all subscriptions and disassociates the Central service.'
            )
            render.display_results(arch_resp[0:2], tablefmt="action")
        else:
            summarize_arch_res(arch_resp[0:2])

    def update_dev_inv_cache(self, batch_resp: List[Response], cache_devs: List[CacheDevice], devs_in_monitoring: List[CacheDevice], inv_del_serials: List[str], ui_only: bool = False) -> None:
        br = BatchRequest
        all_ok = True if batch_resp and all(r.ok for r in batch_resp) else False
        inventory_devs = [d for d in cache_devs if d.db.name == "inventory"]
        cache_update_reqs = []
        if cache_devs and all_ok:
            cache_update_reqs += [br(self.cache.update_dev_db, [d.doc_id for d in devs_in_monitoring], remove=True)]
        else:
            cache_update_reqs += [br(self.cache.refresh_dev_db)]

        if cache_devs or inv_del_serials and not ui_only:
            if all_ok:  # TODO Update to pass Inv doc_ids
                cache_update_reqs += [
                    br(
                        self.cache.update_inv_db,
                        [d.doc_id for d in inventory_devs],
                        remove=True
                    )
                ]
            else:
                cache_update_reqs += [br(self.cache.refresh_inv_db_classic)]
        # Update cache remove deleted items
        if cache_update_reqs:
            _ = api.session.batch_request(cache_update_reqs)

    def _build_mon_del_reqs(self, cache_devs: List[CacheDevice]) -> Tuple[List[BatchRequest], List[BatchRequest]]:
        mon_del_reqs, delayed_mon_del_reqs, _stack_ids = [], [], []
        for dev in set(cache_devs):
            if dev.generic_type == "switch" and dev.swack_id is not None:
                dev_type = "stack"
                if dev.swack_id in _stack_ids:
                    continue
                else:
                    _stack_ids += [dev.swack_id]
            else:
                dev_type = dev.generic_type if dev.generic_type != "gw" else "gateway"

            func = getattr(api.monitoring, f"delete_{dev_type}")
            update_list = mon_del_reqs if dev.status.lower() == "down" else delayed_mon_del_reqs
            update_list += [BatchRequest(func, dev.serial if dev_type != "stack" else dev.swack_id)]

        return mon_del_reqs, delayed_mon_del_reqs

    def _process_delayed_mon_deletes(self, reqs: List[BatchRequest]) -> Tuple[List[Response], List[int]]:
        del_resp: List[Response] = []
        del_reqs_try = reqs.copy()

        _delay = 30
        for _try in range(4):
            _word = "more " if _try > 0 else ""
            _prefix = "" if _try == 0 else escape(f"[Attempt {_try + 1}] ")
            _delay -= (5 * _try) # reduce delay by 5 secs for each loop
            for _ in track(range(_delay), description=f"{_prefix}[green]Allowing {_word}time for devices to disconnect."):
                time.sleep(1)

            _del_resp: List[Response] = api.session.batch_request(del_reqs_try, continue_on_fail=True)

            if _try == 3:
                if not all([r.ok for r in _del_resp]):
                    render.econsole.print("\n[dark_orange]:warning:[/]  Retries exceeded. Devices still remain [bright_green]Up[/] in central and cannot be deleted.  This command can be re-ran once they have disconnected.")
                del_resp += _del_resp
            else:
                del_resp += [r for r in _del_resp if r.ok or isinstance(r.output, dict) and r.output.get("error_code", "") != "0007"]

            del_reqs_try = [del_reqs_try[idx] for idx, r in enumerate(_del_resp) if not r.ok and isinstance(r.output, dict) and r.output.get("error_code", "") == "0007"]
            if del_reqs_try:
                render.econsole.print(f"{len(del_reqs_try)} device{'s are' if len(del_reqs_try) > 1 else ' is'} still [bright_green]Up[/] in Central")
            else:
                break

        return del_resp

    def _get_inv_doc_ids(self, batch_resp: List[Response]) -> List[int] | None:
        if not batch_resp[1].url.name == "unarchive":
            return

        if isinstance(batch_resp[1].raw, dict) and "succeeded_devices" in batch_resp[1].raw:
            try:  # Normal circumstances serial should be in inventory, but for test runs the unarchive response may be a different mock response with different serial numbers not in inventory.
                cache_inv_to_del = [inv_dev for inv_dev in [self.cache.inventory_by_serial.get(d["serial_number"]) for d in batch_resp[1].raw["succeeded_devices"]] if inv_dev is not None]
                inv_doc_ids = [dev.doc_id for dev in cache_inv_to_del] or None
            except Exception as e:
                log.exception(f"Exception while attempting to extract unarchive results for Inv Cache Update.\n{e}")
                return
            return inv_doc_ids

    def _get_mon_doc_ids(self, del_resp: List[Response]) -> List[int]:
        doc_ids = []
        try:
            doc_ids = [self.cache.devices_by_serial[r.url.name].doc_id for r in del_resp if r.ok and "switch_stacks" not in r.url.parts]
            stack_ids = [r.url.name for r in del_resp if r.ok and "switch_stacks" in r.url.parts]
            for stack_id in stack_ids:
                doc_ids += [d.doc_id for d in self.cache.DevDB.search(self.cache.Q.swack_id == stack_id) if d is not None]
        except Exception as e:
            log.error(f"Error: {e.__class__.__name__} occured fetching doc_ids for local cache update after delete.  Use [cyan]cencli show all[/] to ensure device cache is current.", caption=True, log=True)

        return doc_ids

    # TOGLP
    def batch_delete_devices(self, data: List[Dict[str, Any]] | Dict[str, Any], *, ui_only: bool = False, cop_inv_only: bool = False, yes: bool = False, force: bool = False,) -> List[Response]:
        BR = BatchRequest
        confirm_msg = []

        try:
            serials_in = [dev["serial"] for dev in data]
        except KeyError:  # pragma: no cover
            self.exit("Missing required field: [cyan]serial[/].")

        cache_devs: List[CacheDevice | CacheInvDevice | None] = []
        # cache_devs: List[CacheInvMonDevice | None] = []
        serial_updates: Dict[int, str] = {}
        for idx, d in enumerate(serials_in):
            this_dev = self.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False, retry=not cop_inv_only,)  # dev_type=dev_type)
            # TODO implement this logic as it won't update dev cache once we add timestamp to cache update.  Logic will be to assume mon/dev cache is current if updated within last x hours, updated it otherwise to ensure mon deletion is not necessary.
            # This would be for scenario where device is found in inv cache but not in dev cache.  commented cache_mon_devs/cache_inv_devs also part of this logic.
            # For now given dev cache could be stale sticking with existing logci that will update dev cache proactively if found in inv but not dev to ensure dev is current.
            # this_dev = self.cache.get_combined_inv_dev_identifier(d, silent=True, retry_dev=False, exit_on_fail=False,)  # retry_inv=not cop_inv_only,)  # dev_type=dev_type)
            if this_dev is not None:
                serial_updates[idx] = this_dev.serial
            cache_devs += [this_dev]

        # if dev_type:
        #     dev_type = utils.listify(dev_type)
        #     cache_devs = [c for c in cache_devs if c is not None and c.type and c.type in dev_type]

        not_found_devs: List[str] = [s for s, c in zip(serials_in, cache_devs) if c is None]
        cache_found_devs: List[CacheDevice | CacheInvDevice] = [d for d in cache_devs if d is not None]
        cache_mon_devs: List[CacheDevice] = [d for d in cache_found_devs if d.db.name == "devices"]
        cache_inv_devs: List[CacheInvDevice] = [d for d in cache_found_devs if d.db.name == "inventory"]
        # cache_mon_devs: List[CacheDevice] = [d.mon for d in cache_found_devs if d.mon is not None]
        # cache_inv_devs: List[CacheInvDevice] = [d.inv for d in cache_found_devs if d.mon is None and d.inv is not None]

        serials_in = [s.upper() if idx not in serial_updates else serial_updates[idx] for idx, s in enumerate(serials_in)]
        invalid_serials = [s for s in serials_in if not utils.is_serial(s)]
        valid_serials = [s for s in serials_in if s not in invalid_serials]
        _not_valid_msg = "does not appear to be a valid serial"
        _not_found_msg = "was not found, does not exist in inventory"

        _ = [log.warning(f"Ignoring [cyan]{s}[/] as it {_not_valid_msg if s not in [s.upper() for s in not_found_devs] else _not_found_msg}", caption=True) for s in invalid_serials]

        # archive / unarchive removes any subscriptions (less calls than determining the subscriptions for each then unsubscribing)
        # It's OK to send both despite unarchive depending on archive completing first, as the first call is always done solo to check if tokens need refreshed.
        # We always use serials with import without validation for arch/unarchive as device will not show in inventory if it's already archved
        arch_reqs = [] if ui_only or not valid_serials else [
            BR(api.platform.archive_devices, valid_serials),
            BR(asyncio.sleep, 3),  # Had to add delay between archive/unarchive as GWs would remain archived despite returning 200 to the unarchive call.
            BR(api.platform.unarchive_devices, valid_serials),
        ]

        # build reqs to remove devs from monit views.  Down devs now, Up devs delayed to allow time to disc.
        mon_del_reqs = delayed_mon_del_reqs = []
        if not cop_inv_only:
            mon_del_reqs, delayed_mon_del_reqs = self._build_mon_del_reqs(cache_mon_devs)

        # cop only delete devices from GreenLake inventory
        cop_del_reqs = [] if not config.is_cop or not cache_inv_devs else [
            BR(api.platform.cop_delete_device_from_inventory, [dev.serial for dev in cache_inv_devs])
        ]

        # warn about devices that were not found
        if (mon_del_reqs or delayed_mon_del_reqs or cop_del_reqs) and not_found_devs:
            not_in_inv_msg = utils.color(not_found_devs, color_str="cyan", pad_len=4, sep="\n")
            render.econsole.print(f"\n[dark_orange3]\u26a0[/]  The following provided devices were not found in the inventory.\n{not_in_inv_msg}", emoji=False)
            render.econsole.print("[grey42 italic]They will be skipped[/]\n")

        if ui_only:
            _total_reqs = len(mon_del_reqs)
        elif cop_inv_only:
            _total_reqs = len([*[req for req in arch_reqs if req.func != asyncio.sleep], *cop_del_reqs])
        else:
            _total_reqs = len([*[req for req in arch_reqs if req.func != asyncio.sleep], *cop_del_reqs, *mon_del_reqs, *delayed_mon_del_reqs])

        if not _total_reqs:
            if ui_only and delayed_mon_del_reqs:  # they select ui only, but devices are online
                self.exit(f"[cyan]--ui-only[/] provided, but only applies to devices that are offline, {len(delayed_mon_del_reqs)} device{'s are' if len(delayed_mon_del_reqs) > 1 else ' is'} online.  Nothing to do. Exiting...")
            self.exit("[italic]Everything is as it should be, nothing to do.  Exiting...[/]", code=0)

        sin_plural = f"[cyan]{len(cache_found_devs)}[/] devices" if len(cache_found_devs) > 1 else "device"
        confirm_msg += [f"\n[dark_orange3]\u26a0[/]  [red]Delet{'ing' if yes else 'e'}[/] the following {sin_plural}{'' if not ui_only else ' [dim italic]monitoring UI only[/]'}:"]
        if ui_only:
            confirmation_devs = utils.summarize_list([c.summary_text for c in cache_mon_devs if c.status.lower() == 'down'], max=40, color=None)
            if delayed_mon_del_reqs:  # using delayed_mon_reqs can be inaccurate re count when stacks are involved, as they could provide 4 switches, but if it's a stack that's 1 delete call.  hence the list comp below.
                render.econsole.print(
                    f"[cyan]{len([c for c in cache_mon_devs if c.status.lower() == 'up'])}[/] of the [cyan]{len(cache_mon_devs)}[/] found devices are currently [bright_green]online[/]. [dim italic]They will be skipped.[/]\n"
                    "Devices can only be removed from UI if they are [red]offline[/]."
                )
                delayed_mon_del_reqs = []
            if not mon_del_reqs:
                self.exit("No devices found to remove from UI. [red]Exiting[/]...")
            else:
                confirm_msg += [confirmation_devs, f"\n[cyan][italic]{len([c for c in cache_mon_devs if c.status.lower() == 'down'])}[/cyan] devices will be removed from UI [bold]only[/].  They Will appear again once they connect to Central[/italic]."]
        else:
            confirmation_list = valid_serials if force or cop_inv_only else [d.summary_text for d in cache_found_devs]
            confirm_msg += [utils.summarize_list(confirmation_list, max=40, color=None if not force else 'cyan')]

        if _total_reqs > 1:
            confirm_msg += [f"\n[italic dark_olive_green2]Will result in {_total_reqs} additional API Calls."]

        # Perfrom initial delete actions (Any devs in inventory and any down devs in monitoring)
        render.console.print("\n".join(confirm_msg), emoji=False)
        batch_resp = []
        mon_doc_ids = []
        inv_doc_ids = []
        render.confirm(yes) # We abort if they don't confirm.

        # archive / unarchive (removes all subscriptions disassociates with Central in GLCP)
        # Also monitoring UI delete for any devices currently offline.
        batch_resp = api.session.batch_request([*arch_reqs, *mon_del_reqs])  # mon_del_reqs will be empty list if cop_inv_only
        if arch_reqs and len(batch_resp) >= 2:
            inv_doc_ids = self._get_inv_doc_ids(batch_resp)
            self.show_archive_results(batch_resp[:2])
            batch_resp = batch_resp[2:]

        if batch_resp:  # Now represents responses associated with mon_del_reqs, will be empty if cop_inv_only
            mon_doc_ids += self._get_mon_doc_ids(batch_resp)
            # Any that failed with device currently online error, append to back of delayed_mon_reqs (possible if dev status in cache was stale)
            delayed_mon_del_reqs += [req for req, resp in zip(mon_del_reqs, batch_resp) if not resp.ok and isinstance(resp.output, dict) and resp.output.get("error_code", "") == "0007"]

        if delayed_mon_del_reqs:
            delayed_mon_resp = self._process_delayed_mon_deletes(delayed_mon_del_reqs)
            batch_resp += delayed_mon_resp
            mon_doc_ids += self._get_mon_doc_ids(delayed_mon_resp)

        if cop_del_reqs:
            batch_resp += api.session.batch_request(cop_del_reqs)

        if batch_resp:
            render.display_results(batch_resp, tablefmt="action")

        # Cache Updates
        if mon_doc_ids:
            api.session.request(self.cache.update_dev_db, mon_doc_ids, remove=True)
        if inv_doc_ids:
            api.session.request(self.cache.update_inv_db, inv_doc_ids, remove=True)

    def batch_assign_subscriptions(self, data: list[dict[str, Any]] | dict[str, Any], *, tags: dict[str, str] = None, subscription: str = None, yes: bool = False,) -> List[Response]:
        # tags = None if not tags else {k: v if v.lower() not in ["none", "null"] else None for k, v in tags.items()}
        if subscription:
            sub_keys = ["subscription", "license", "services"]
            sub_key = [k for k in sub_keys if k.lower() in map(str.lower, data[0].keys())]
            sub_key = "subscription" if not sub_key else sub_key[0]
            _sub: CacheSub = self.cache.get_sub_identifier(subscription, best_match=True)
            data = [{**{k: v for k, v in inner.items() if k != sub_key}, "subscription": _sub.id} for inner in data]

        glp_api = GreenLakeAPI()
        try:
            _data = ImportSubDevices(self.cache, data)
        except ValidationError as e:
            self.exit(utils.clean_validation_errors(e))

        devs_by_sub_id = _data.serials_by_subscription_id(assigned=True)
        confirm_msg = []
        batch_reqs = []
        for sub_id, res in devs_by_sub_id.items():
            if not res.devices:
                continue

            csub: CacheSub = res.cache_sub
            # confirm_msg += [res.get_confirm_msg()]
            confirm_msg += [f"\n[deep_sky_blue1]\u2139[/]  [dark_olive_green2]Assigning[/] {csub.summary_text}... [magenta]To[/magenta] [cyan]{len(res)}[/] [magenta]devices found in import[/magenta]"]
            if len(res.devices) > csub.available:
                confirm_msg[-1] = confirm_msg[-1].rstrip()
                confirm_msg += [f"[dark_orange3]\u26a0[/]  # of devices provided ({len(res)}) exceeds remaining qty available ({csub.available}) for {csub.name} subscription."]
            batch_reqs += [BatchRequest(glp_api.devices.update_devices, device_ids=res.ids, subscription_ids=sub_id, tags=tags)]

        if tags:
            _tag_msg = '\n'.join([f'  [magenta]{k}[/]: {v}' for k, v in tags.items()])
            confirm_msg += [f"\n[bright_green]The following tags will be assigned to[/] [cyan]{len(_data)}[/] [bright_green]devices [dim italic]from import[/][/bright_green]:\n{_tag_msg}"]

        if _data.has_tags:
            for _tags, _ids in _data.ids_by_tags():
                _tag_msg = '\n'.join([f'  [magenta]{k}[/]: {v}' for k, v in _tags.items()])
                confirm_msg += [f"\n[bright_green]The following {'additional ' if tags else ''}tags will be assigned to[/] [cyan]{len(_ids)}[/] [bright_green]devices [dim italic]based on data defined in import[/][/bright_green]:\n{_tag_msg}"]
                batch_reqs += [BatchRequest(glp_api.devices.update_devices, device_ids=_ids, tags=_tags)]

        if _data.not_assigned_devs:
            confirm_msg += [
                "\n[dark_orange3]\u26a0[/]  Some devices have been skipped as they don't exist or are not associated with Aruba Central app in [green]GreenLake[/]",
                _data.warning_skip_not_assigned,
                "\n[deep_sky_blue1]\u2139[/]  Use [cyan]cencli batch add devices ...[/] to add devices to Aruba Central."
            ]  # \u26a0 == :warning:, \u2139 = :information:

        if not self.cache.responses.sub:
            confirm_msg += ["\n[italic dark_olive_green2 dim]Qty Available reflects qty as of last subscription cache refresh.  [cyan]cencli show subscriptions[/] and [cyan]cencli show inventory[/] both result in a subscription cache refresh.[/]"]

        render.econsole.print("\n".join(confirm_msg), emoji=False)
        if not batch_reqs:
            self.exit("All Devices were skipped.  Nothing to do.  Aborting...")
        render.confirm(yes) # aborts here if they don't confirm
        batch_res = glp_api.session.batch_request(batch_reqs)

        return batch_res


    def _build_update_ap_reqs(self, data: List[Dict[str, Any]]) -> APRequestInfo:
        altitude_by_serial, ap_env_by_serial, batch_reqs, requires_reboot = {}, {}, [], {}
        skipped: Dict[str, Skipped] = {}

        try:
            data: List[APUpdate] = APUpdates(data)
        except ValidationError as e:
            self.exit(utils.clean_validation_errors(e))

        for ap in data:
            cache_ap: CacheDevice = self.cache.get_dev_identifier(ap.serial)  # , dev_type="ap")
            ap_iden = utils.color([cache_ap.name, cache_ap.serial], color_str="cyan", sep="|")

            # Allow import to contain other device types, we skip them.
            if cache_ap.type != "ap":
                skipped[cache_ap.serial] = Skipped(ap_iden, f"[dark_orange3]:warning:[/]  Device is [red]{cache_ap.type}[/], Command is only valid for [green]APs[/].")
                continue

            if ap.gps_altitude:
                altitude_by_serial[cache_ap.swack_id] = ap.gps_altitude  # swack_id is serial for aos10, swarm_id for AOS8

            if ap.flex_dual_exclude and cache_ap.model not in flex_dual_models:
                log.error(f"Ignored [cyan]flex_dual_exclude[/] option for {ap_iden}. AP{cache_ap.model} is not a flex_dual radio AP", caption=True)
                ap.flex_dual_exclude = None
            if ap.dynamic_ant_mode and cache_ap.model not in dynamic_antenna_models:
                log.error(f"Ignored [cyan]antenna_width[/] option for {ap_iden}. AP{cache_ap.model} is not a dyanamic antenna AP", caption=True)
                ap.dynamic_ant_mode = None
            if (ap.ip and ap.ip != cache_ap.ip) or any([ap.mask, ap.gateway, ap.dns, ap.domain]) or ap.uplink_vlan:
                requires_reboot[ap.serial] = [cache_ap]

            kwargs = ap.api_params
            if {k: v for k, v in kwargs.items() if k != "serial" and v is not None}:
                ap_env_by_serial[ap.serial] = kwargs
            elif not ap.gps_altitude:
                skipped[ap.serial] = Skipped(ap_iden, f"[dark_orange3]:warning:[/]  [red]No updates found[/] in import file that apply to [cyan]AP{cache_ap.model}[/].")

        if ap_env_by_serial:
            batch_reqs += [BatchRequest(api.configuration.update_per_ap_settings, as_dict=ap_env_by_serial)]
        if altitude_by_serial:
            batch_reqs += [BatchRequest(api.configuration.update_ap_altitude, as_dict=altitude_by_serial)]

        return APRequestInfo(
            batch_reqs,
            ap_data=[ap for ap in data if ap.serial not in skipped],
            skipped=skipped,
            requires_reboot=requires_reboot,
            env_update_aps=len(ap_env_by_serial),
            gps_update_aps=len(altitude_by_serial),
        )

    def _reboot_after_changes(self, req_info: APRequestInfo, batch_resp: list[Response]) -> list[Response] | None:
        reboot_reqs: List[BatchRequest] = []
        skipped_reboots: List[CacheDevice] = []
        for req, resp in zip(req_info.reqs, batch_resp):
            serial = req.kwargs["serial"]
            if req.func == api.configuration.update_per_ap_settings and serial in req_info.requires_reboot:
                if resp.ok:
                    reboot_reqs += [BatchRequest(api.device_management.send_command_to_device, serial=serial, command="reboot")]
                else:
                    skipped_reboots += [req_info.requires_reboot[serial]]

        if skipped_reboots:
            log.warning(f"Reboot was not performed on the following APs as the Update call returned an error\n{utils.summarize_list([ap.summary_text for ap in skipped_reboots])}", caption=True)

        if reboot_reqs:
            return api.session.batch_request(reboot_reqs)

    # Header rows used by CAS
    #DEVICE NAME,SERIAL,MAC,GROUP,SITE,LABELS,LICENSE,ZONE,SWARM MODE,RF PROFILE,INSTALLATION TYPE,RADIO 0 MODE,RADIO 1 MODE,RADIO 2 MODE,DUAL 5GHZ MODE,SPLIT 5GHZ MODE,FLEX DUAL BAND,ANTENNA WIDTH,ALTITUDE,IP ADDRESS,SUBNET MASK,DEFAULT GATEWAY,DNS SERVER,DOMAIN NAME,TIMEZONE,AP1X USERNAME,AP1X PASSWORD
    # TODO cache update if AP is renamed
    def batch_update_aps(self, data: list | dict, *, yes: bool = False, reboot: bool = False) -> None:
        """Update per-ap-settings (ap env) or set gps altitude by updating ap level config"""
        try:
            _ = [dev["serial"] for dev in data if dev["serial"]]
        except KeyError:
            self.exit("Missing required field: [cyan]serial[/].")

        req_info: APRequestInfo = self._build_update_ap_reqs(data)
        if not req_info.reqs:
            self.exit("No valid updates provided... Nothing to do.")

        reboot_msg, reboot_resp = None, []
        reboot_base = "\n:recycle:  [italic dark_olive_green2]indicates a reboot is required for changes to take effect.[/]"
        call_cnt = (req_info.env_update_aps + req_info.gps_update_aps) * 2
        if req_info.requires_reboot and reboot:
            call_cnt += len(req_info.requires_reboot)
            reboot_msg = (
                f"{reboot_base}\n"
                f"[cyan]--reboot[/]|[cyan]-R[/] Option provided: {len(req_info.requires_reboot)} AP{utils.singular_plural_sfx(req_info.requires_reboot)} will be [bright_red]rebooted[/] after successful update"
            )
        elif req_info.requires_reboot:
            reboot_msg = (
                f"{reboot_base}\n"
                f"[dark_orange3]:warning:[/]  {len(req_info.requires_reboot)} AP{utils.singular_plural_sfx(req_info.requires_reboot, singular=' has', plural='s have')} "
                "changes that require reboot to take effect, but [cyan]--reboot[/]|[cyan]-R[/] options was not provided so [bright_red]no reboot will be performed[/]"
            )

        ap_update_cnt = len(data) - len(req_info.skipped)
        render.econsole.print(f"[bright_green]Updat{'e' if not yes else 'ing'}[/] {ap_update_cnt} AP{utils.singular_plural_sfx({ap_update_cnt})}")
        if req_info.env_update_aps:
            render.econsole.print(f"    Updating [cyan]per AP settings[/] for {req_info.env_update_aps} AP{utils.singular_plural_sfx(req_info.env_update_aps)}")
        if req_info.gps_update_aps:
            render.econsole.print(f"    Adding/Updating [cyan]gps-altitude[/] to {req_info.gps_update_aps} AP{utils.singular_plural_sfx(req_info.gps_update_aps)}")

        render.econsole.print("\n[bold magenta]Summary of Changes to be Applied[/]")
        if len(req_info.ap_data) > 12:
            render.econsole.print(f"    [dim italic]Summary showing 12 of the {len(req_info.ap_data)} devices being updated.")
        render.econsole.print(utils.summarize_list([ap.__rich__() for ap in req_info.ap_data], color=None, max=12, pad=4), emoji=False)

        if req_info.skipped:
            _cnt = len(req_info.skipped)
            render.econsole.print(f"\nThe following {_cnt} APs were skipped as no updates applied to those models:")
            if _cnt > 12:
                render.econsole.print(f"    [dim italic]Summary showing 12 of the {_cnt} skipped devices.")
            render.econsole.print(req_info.skipped_summary)

        calls_word = utils.singular_plural_sfx(req_info.reqs, singular=" was", plural="s were")
        caption = f"[deep_sky_blue1]:information:[/]  [italic cyan]{req_info.env_update_aps + req_info.gps_update_aps}[/] [italic dark_olive_green2]API call{calls_word} performed to get current configuration/settings. These calls are only shown if there was a failure.[/]"

        if reboot_msg:
            render.econsole.print(reboot_msg)
        render.econsole.print(f"\n[deep_sky_blue1]:information:[/]  [italic dark_olive_green2]This operation will result in {call_cnt} API calls[/]")

        render.confirm(yes)  # exits here if they abort
        _batch_resp = api.session.batch_request(req_info.reqs)
        # Nested BatchResponse here update_per_ap_settings and update_ap_altitude both return List[Response]
        batch_resp = []
        for resp in _batch_resp:
            batch_resp += resp if isinstance(resp, list) else [resp]
        if reboot and req_info.requires_reboot:
            reboot_resp = self._reboot_after_changes(req_info, batch_resp=batch_resp) or []

        render.display_results([*batch_resp, *reboot_resp], tablefmt="action", caption=caption)

    def help_block(self, default_txt: str, help_type: Literal["default", "requires"] = "default") -> str:
        """Helper function that returns properly escaped default text, including rich color markup, for use in CLI help.

        Args:
            default_txt (str): The default value to display in the help text.  Do not include the word 'default: '
            help_type (Literal["default", "requires"], optional): Impacts the coloring/format of the help_block. Defaults to "default".

        Returns:
            str: Formatted default text.  i.e. [default: some value] (with color markups)
        """
        style = "dim" if help_type == "default" else "dim red"
        return f"[{style}]{escape(f'[{help_type}: {default_txt}]')}[/{style}]"

    def ws_follow_tail(self, title: str = None, log_type: LogType = "event") -> None:  # pragma: no cover
        title = title or "device event Logs"
        render.econsole.print(f"Following tail on {title} (Streaming API).  Use CTRL-C to stop.")
        if ("audit" not in sys.argv and len(sys.argv[1:]) > 3) or len(sys.argv[1:]) > 4:
            honored = ['show', 'audit', 'logs', '-f']
            ignored = [option for option in sys.argv[1:] if option not in honored]
            render.econsole.print(f"[dark_orange3]:warning:[/]  Provided options {','.join(ignored)} [bright_red]ignored[/].  Not valid with [cyan]-f[/]")
        try:
            api.session.request(follow_logs, config.classic.wss, log_type=log_type)
        except KeyboardInterrupt:
            self.exit(" ", code=0)  # The empty string is to advance a line so ^C is not displayed before the prompt
        except Exception as e:
            self.exit(str(e))

    def parse_var_value_list(self, var_value: list[str, str], *, error_name: str = "variables") -> dict[str, str]:
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
            self.exit(f"Something went wrong parsing {error_name}.  Unequal length for {error_name} vs values.")  # pragma: no cover

        return {k: v for k, v in zip(vars, vals)}


if __name__ == "__main__":
    pass
