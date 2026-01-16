# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Callable
from typing import Any, List, Literal, Optional, Sequence, Type

import click
import typer
from rich.markup import escape
from typer.models import ArgumentInfo, OptionInfo

from centralcli.cache import Cache
from centralcli.constants import iden_meta
from centralcli.typedefs import UNSET

from .environment import env_var

ArgumentType = Literal["cache", "name", "device", "devices", "device_type", "what", "group", "groups", "group_dev", "site", "import_file", "wid", "version", "session_id", "ssid", "portal", "portals", "banner_file", "dest_workspace"]
OptionType = Literal[
    "client", "group", "group_many", "site", "site_many", "label", "label_many", "debug", "debugv", "device_type", "do_json", "do_yaml", "do_csv", "do_table",
    "outfile", "reverse", "pager", "ssid", "yes", "yes_int", "device_many", "device", "swarm_device", "swarm", "sort_by", "default", "workspace", "verbose",
    "raw", "end", "update_cache", "show_example", "at", "in", "reboot", "start", "past", "subscription", "version", "not_version", "band", "banner", "banner_file",
    "tags",
]

class CLIArgs:
    def __init__(self, cache: Cache):
        self.cache = cache
        self.name: ArgumentInfo = typer.Argument(..., show_default=False,)
        self.device: ArgumentInfo = typer.Argument(..., metavar=iden_meta.dev, show_default=False, autocompletion=cache.dev_completion)
        self.devices: ArgumentInfo = typer.Argument(..., metavar=iden_meta.dev_many, autocompletion=cache.dev_completion, show_default=False,)
        self.device_type: ArgumentInfo = typer.Argument(..., show_default=False,)
        self.what: ArgumentInfo = typer.Argument(..., show_default=False,)
        self.group: ArgumentInfo = typer.Argument(..., metavar=iden_meta.group, autocompletion=cache.group_completion, show_default=False,)
        self.groups: ArgumentInfo = typer.Argument(..., metavar=iden_meta.group_many, autocompletion=cache.group_completion, show_default=False,)
        self.group_dev: ArgumentInfo = typer.Argument(..., metavar="[GROUP|DEVICE]", help="Group or device", autocompletion=cache.group_dev_completion, show_default=False,)
        self.session_id: ArgumentInfo = typer.Argument(None, help="The session id of a previously run troubleshooting session", show_default=False,)
        self.site: ArgumentInfo = typer.Argument(..., metavar=iden_meta.site, autocompletion=cache.site_completion, show_default=False,)
        self.ssid: ArgumentInfo = typer.Argument(..., help="SSIDs are not cached.  Ensure text/case is accurate.", show_default=False,)
        self.import_file: ArgumentInfo = typer.Argument(None, exists=True, show_default=False,)
        self.banner_file: ArgumentInfo = typer.Argument(None, help="The file with the desired banner text.  [dim italic]supports .j2 (Jinja2) template[/]", exists=True, show_default=False)
        self.wid: ArgumentInfo = typer.Argument(..., help="Use [cyan]show webhooks[/] to get the wid", show_default=False,)
        self.portal: ArgumentInfo = typer.Argument(..., metavar=iden_meta.portal, autocompletion=cache.portal_completion, show_default=False,)
        self.portals: ArgumentInfo = typer.Argument(..., metavar=iden_meta.portal_many, autocompletion=cache.portal_completion, show_default=False,)
        self.dest_workspace: ArgumentInfo = typer.Argument(
            None,
            envvar=env_var.dest_workspace,
            help="The Aruba Central [dim italic]([green]GreenLake[/green])[/] Destination WorkSpace for migration operations",
            autocompletion=cache.workspace_completion,
            show_default=False,
        )
        self.version: ArgumentInfo = typer.Argument(
            None,
            help=f"Firmware Version [dim]{escape('[default: recommended version]')}",
            show_default=False,
            autocompletion=lambda incomplete: [
                m for m in [
                    ("<firmware version>", "The version of firmware to upgrade to."),
                    *[m for m in cache.null_completion(incomplete)]
                ]
            ],
        )

    def get(
        self,
        argument: ArgumentType,
        *param_decls: Optional[Sequence[str]],
        default: Optional[Any] = UNSET,
        callback: Optional[Callable[..., Any]] = UNSET,
        metavar: Optional[str] = UNSET,
        expose_value: bool = UNSET,
        is_eager: bool = UNSET,
        envvar: Optional[str | List[str]] = UNSET,
        shell_complete: Optional[
            Callable[
                [click.Context, click.Parameter, str],
                List["click.shell_completion.CompletionItem"] | List[str],
            ]
        ] = UNSET,
        autocompletion: Optional[Callable[..., Any]] = UNSET,
        default_factory: Optional[Callable[[], Any]] = UNSET,
        # Custom type
        parser: Optional[Callable[[str], Any]] = UNSET,
        click_type: Optional[click.ParamType] = UNSET,
        # TyperArgument
        show_default: bool | str = UNSET,
        show_choices: bool = UNSET,
        show_envvar: bool = UNSET,
        help: Optional[str] = UNSET,
        hidden: bool = UNSET,
        # Choice
        case_sensitive: bool = UNSET,
        # Numbers
        min: Optional[int | float] = UNSET,
        max: Optional[int | float] = UNSET,
        clamp: bool = UNSET,
        # DateTime
        formats: Optional[List[str]] = UNSET,
        # File
        mode: Optional[str] = UNSET,
        encoding: Optional[str] = UNSET,
        errors: Optional[str] = UNSET,
        lazy: Optional[bool] = UNSET,
        atomic: bool = UNSET,
        # Path
        exists: bool = UNSET,
        file_okay: bool = UNSET,
        dir_okay: bool = UNSET,
        writable: bool = UNSET,
        readable: bool = UNSET,
        resolve_path: bool = UNSET,
        allow_dash: bool = UNSET,
        path_type: None | Type[str] | Type[bytes] = UNSET,
        # Rich settings
        rich_help_panel: str | None = UNSET,
    ) -> ArgumentInfo:
        """Same fingerprint as typer.Argument

        set rich_help_panel="Arguments" to force the default panel
        """
        attr = getattr(self, argument)
        kwargs = {
            "default": default,
            "param_decls": param_decls,
            "callback": callback,
            "metavar": metavar,
            "expose_value": expose_value,
            "is_eager": is_eager,
            "envvar": envvar,
            "shell_complete": shell_complete,
            "autocompletion": autocompletion,
            "default_factory": default_factory,
            # Custom type
            "parser": parser,
            "click_type": click_type,
            # TyperArgument
            "show_default": show_default,
            "show_choices": show_choices,
            "show_envvar": show_envvar,
            "help": help,
            "hidden": hidden,
            # Choice
            "case_sensitive": case_sensitive,
            # Numbers
            "min": min,
            "max": max,
            "clamp": clamp,
            # DateTime
            "formats": formats,
            # File
            "mode": mode,
            "encoding": encoding,
            "errors": errors,
            "lazy": lazy,
            "atomic": atomic,
            # Path
            "exists": exists,
            "file_okay": file_okay,
            "dir_okay": dir_okay,
            "writable": writable,
            "readable": readable,
            "resolve_path": resolve_path,
            "allow_dash": allow_dash,
            "path_type": path_type,
            # Rich settings
            "rich_help_panel": rich_help_panel
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not UNSET}
        combined = {**attr.__dict__, **kwargs}
        param_decls = param_decls or combined["param_decls"]
        args = (combined["default"], *param_decls)
        kwargs_out = {k: v for k, v in combined.items() if k not in ["default", "param_decls"]}
        return typer.Argument(*args, **kwargs_out)


class CLIOptions:
    def __init__(self, cache: Cache, timerange: str = "3h", include_mins: bool = None):
        self.cache = cache
        self.timerange: str = timerange
        self.include_mins: bool = include_mins if include_mins is not None else True
        self.client: OptionInfo = typer.Option(None, "--client", metavar=iden_meta.client, autocompletion=cache.client_completion, show_default=False,)
        self.do_gw: OptionInfo = typer.Option(None, "--gw", help="Update group level config for gateways.")
        self.do_ap: OptionInfo = typer.Option(None, "--ap", help="Update group level config for APs.")
        self.group: OptionInfo = typer.Option(None, help="Filter by Group", metavar=iden_meta.group, autocompletion=cache.group_completion, show_default=False,)
        self.group_many: OptionInfo = typer.Option(None, help="Filter by Group(s)", metavar=iden_meta.group_many, autocompletion=cache.group_completion, show_default=False,)
        self.site: OptionInfo = typer.Option(None, help="Filter by Site", metavar=iden_meta.site, autocompletion=cache.site_completion, show_default=False,)
        self.site_many: OptionInfo = typer.Option(None, help="Filter by Site(s)", metavar=iden_meta.site_many, autocompletion=cache.site_completion, show_default=False,)
        self.label: OptionInfo = typer.Option(None, help="Filter by Label", metavar=iden_meta.label, autocompletion=cache.label_completion,show_default=False,)
        self.label_many: OptionInfo = typer.Option(None, help="Filter by Label(s)", metavar=iden_meta.label_many, autocompletion=cache.label_completion,show_default=False,)
        self.debug: OptionInfo = typer.Option(False, "--debug", envvar=env_var.debug, help="Enable Additional Debug Logging", rich_help_panel="Common Options",)
        self.debugv: OptionInfo = typer.Option(False, "--debugv", help="Enable Verbose Debug Logging", rich_help_panel="Common Options",)
        self.do_json: OptionInfo = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting",)
        self.do_yaml: OptionInfo = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting",)
        self.do_csv: OptionInfo = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting",)
        self.do_table: OptionInfo = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting",)
        self.outfile: OptionInfo = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",)
        self.reverse: OptionInfo = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",)
        self.pager: OptionInfo = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",)
        self.ssid: OptionInfo = typer.Option(None, help="Filter/Apply command to a specific SSID", show_default=False)
        self.band: OptionInfo = typer.Option(None, help=f"Show Bandwidth for a specific band [dim]{escape('[ap must be provided]')}[/]", show_default=False)
        self.tags: OptionInfo = typer.Option(None, "-t", "--tags", help="Tags to be assigned to [bright_green]all[/] imported devices in format [cyan]tagname1 = tagvalue1, tagname2 = tagvalue2[/]")
        self.banner_file: OptionInfo = typer.Option(None, "--banner-file", help="The file with the desired banner text.  [dim italic]supports .j2 (Jinja2) template[/]", exists=True, show_default=False)
        self.banner: OptionInfo = typer.Option(False, "--banner", help="Update banner text.  This option will prompt for banner text (paste into terminal)", show_default=False)
        self.yes: OptionInfo = typer.Option(False, "-Y", "-y", "--yes", help="Bypass confirmation prompts - Assume Yes",)
        self.yes_int: OptionInfo = typer.Option(
            0,
            "-Y",
            "-y",
            "--yes",
            count=True,
            metavar="",
            help="Bypass confirmation prompts - Assume Yes, this command has potential for multiple confirmation prompts -yy to bypass all",
            rich_help_panel="Common Options",
            show_default=False,
        )
        self.version: OptionInfo = typer.Option(
            None,
            "-V",
            "--version",
            help="Filter by version (fuzzy match).  Prepend [cyan]-[/] to show devices not matching the version. [dim italic]i.e. -10.7.2.1[/]",
            show_default=False
        )
        self.device_many: OptionInfo = typer.Option(None, "--dev", metavar=iden_meta.dev_many, help="Filter by device", autocompletion=cache.dev_completion, show_default=False,)
        self.device: OptionInfo = typer.Option(None, "--dev", metavar=iden_meta.dev, help="Filter by device", autocompletion=cache.dev_completion, show_default=False,)
        self.device_type: OptionInfo = typer.Option(None, "--dev-type",help="Filter by Device Type",show_default=False,)
        self.swarm_device: OptionInfo = typer.Option(None, "-S", "--swarm", metavar=iden_meta.dev, help="Filter by the swarm associated with specified AOS8 IAP", autocompletion=cache.dev_ap_completion, show_default=False,)
        self.swarm: OptionInfo = typer.Option(False, "-S", "--swarm", help="Filter by the swarm associated with the ap specified. [dim italic](device/AP Argument must be provided)[/]", autocompletion=cache.dev_ap_completion, show_default=False,)
        self.sort_by: OptionInfo = typer.Option(
            None,
            "--sort",
            help="Field to sort by [dim italic](Some fields may require -v (verbose) option where supported)[/]",
            show_default=False,
            rich_help_panel="Formatting",
        )
        self.default: OptionInfo = typer.Option(False, "-d", help="Use default central workspace", show_default=False, rich_help_panel="Common Options",)
        self.workspace: OptionInfo = typer.Option(
            "default",
            "--ws", "--workspace",
            envvar=env_var.workspace,
            help="The Aruba Central [dim italic]([green]GreenLake[/green])[/] WorkSpace to use [dim italic](must be defined in the config)[/]",
            rich_help_panel="Common Options",
            autocompletion=cache.workspace_completion,
        )
        self.verbose: OptionInfo = typer.Option(
            0,
            "-v",
            count=True,
            metavar="",
            help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
            rich_help_panel="Formatting",
            show_default=False,
        )
        self.raw: OptionInfo = typer.Option(
            False,
            "--raw",
            help="Show raw unformatted response from Central API Gateway",
            rich_help_panel="Formatting",
            show_default=False,
        )
        self.end: OptionInfo = typer.Option(
            None,
            "-e", "--end",
            help=f"End of time-range (24hr notation) [dim]{escape('[default: Now]')}[/]",
            formats=["%m/%d/%Y-%H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y", "%Y-%m-%d"],
            # rich_help_panel="Time Range Options",
            show_default=False,
        )
        self.update_cache: OptionInfo = typer.Option(False, "-U", help="Update the local cache.", show_default=False)
        self.show_example: OptionInfo = typer.Option(False, "--example", help="Show Example import file format.", show_default=False)
        self.at: OptionInfo = typer.Option(
            None,
            help=f"Perform operation at specified date/time (24hr notation) [dim]{escape('[default: Now]')}[/]",
            formats=["%m/%d/%Y-%H:%M", "%Y-%m-%dT%H:%M"],
            # rich_help_panel="Time Range Options",
            show_default=False,
        )
        self.in_: OptionInfo = typer.Option(None, "--in", help=f"Upgrade device in <delta from now>, where d=days, h=hours, m=mins i.e.: [cyan]3h[/] [dim]{escape('[default: Now]')}[/]", show_default=False,)
        self.reboot: OptionInfo = typer.Option(False, "--reboot", "-R", help=f"Automatically reboot device after firmware download [dim]{escape('[default: No reboot if not AP')} [green](APs will reboot regardless)[/green]{escape(']')}[/]")
        self.subscription: OptionInfo = typer.Option(None, "-s", "--sub", help="Assign subscription(s) to device", show_default=False)


    @property
    def start(self) -> OptionInfo:
        return typer.Option(
            None,
            "-s", "--start",
            help=f"Start of time-range (24hr notation) [dim]{escape(f'[default: {self.timerange_to_start}]')}[/]",
            formats=["%m/%d/%Y-%H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y", "%Y-%m-%d"],
            # rich_help_panel="Time Range Options",
            show_default=False,
        )

    @property
    def past(self) -> OptionInfo:
        return typer.Option(
            None,
            "-p",
            "--past",
            help=f"Collect data for last... M=months, w=weeks, d=days, h=hours{', m=mins' if self.include_mins else ''} i.e.: 3h [dim]{escape(f'[default: {self.timerange}]')}[/]",
            # rich_help_panel="Time Range Options",
            show_default=False,
        )

    @property
    def timerange_to_start(self,) -> str:
        letter_to_word = {
            "M": "months",
            "w": "weeks",
            "d": "days",
            "h": "hours",
            "m": "minutes"
        }
        time_letter = self.timerange[-1]
        time_word = letter_to_word.get(time_letter, "ERR")
        if len(self.timerange) == 2 and self.timerange.startswith("1"):  # pragma: no cover
            time_word = time_word.rsplit("s")

        return f"{self.timerange[0:-1]} {time_word} ago"

    def get(
        self,
        option: OptionType,
        *param_decls: Optional[Sequence[str]],
        default: Optional[Any] = UNSET,
        callback: Optional[Callable[..., Any]] = UNSET,
        metavar: Optional[str] = UNSET,
        expose_value: bool = UNSET,
        is_eager: bool = UNSET,
        envvar: Optional[str | List[str]] = UNSET,
        shell_complete: Optional[
            Callable[
                [click.Context, click.Parameter, str],
                List["click.shell_completion.CompletionItem"] | List[str],
            ]
        ] = UNSET,
        autocompletion: Optional[Callable[..., Any]] = UNSET,
        default_factory: Optional[Callable[[], Any]] = UNSET,
        # Custom type
        parser: Optional[Callable[[str], Any]] = UNSET,
        click_type: Optional[click.ParamType] = UNSET,
        # Option
        show_default: bool | str = UNSET,
        prompt: bool |str = UNSET,
        confirmation_prompt: bool = UNSET,
        prompt_required: bool = UNSET,
        hide_input: bool = UNSET,
        is_flag: Optional[bool] = UNSET,
        flag_value: Optional[Any] = UNSET,
        count: bool = UNSET,
        allow_from_autoenv: bool = UNSET,
        help: Optional[str] = UNSET,
        hidden: bool = UNSET,
        show_choices: bool = UNSET,
        show_envvar: bool = UNSET,
        # Choice
        case_sensitive: bool = UNSET,
        # Numbers
        min: Optional[int | float] = UNSET,
        max: Optional[int | float] = UNSET,
        clamp: bool = UNSET,
        # DateTime
        formats: Optional[List[str]] = UNSET,
        # File
        mode: Optional[str] = UNSET,
        encoding: Optional[str] = UNSET,
        errors: Optional[str] = UNSET,
        lazy: Optional[bool] = UNSET,
        atomic: bool = UNSET,
        # Path
        exists: bool = UNSET,
        file_okay: bool = UNSET,
        dir_okay: bool = UNSET,
        writable: bool = UNSET,
        readable: bool = UNSET,
        resolve_path: bool = UNSET,
        allow_dash: bool = UNSET,
        path_type: None | Type[str] | Type[bytes] = UNSET,
        # Rich settings... set to False to disable
        rich_help_panel: str | bool = UNSET,

    ) -> OptionInfo:
        """Same fingerprint as typer.Option

        set rich_help_panel="Options" to force the default panel
        """
        if option == "in":  # pragma: no cover
            option = "in_"
        attr = getattr(self, option)
        kwargs = {
            "default": default,
            "callback": callback,
            "metavar": metavar,
            "expose_value": expose_value,
            "is_eager": is_eager,
            "envvar": envvar,
            "shell_complete": shell_complete,
            "autocompletion": autocompletion,
            "default_factory": default_factory,
            # Custom type
            "parser": parser,
            "click_type": click_type,
            # Option
            "show_default": show_default,
            "prompt": prompt,
            "confirmation_prompt": confirmation_prompt,
            "prompt_required": prompt_required,
            "hide_input": hide_input,
            "is_flag": is_flag,
            "flag_value": flag_value,
            "count": count,
            "allow_from_autoenv": allow_from_autoenv,
            "help": help,
            "hidden": hidden,
            "show_choices": show_choices,
            "show_envvar": show_envvar,
            # Choice
            "case_sensitive": case_sensitive,
            # Numbers
            "min": min,
            "max": max,
            "clamp": clamp,
            # DateTime
            "formats": formats,
            # File
            "mode": mode,
            "encoding": encoding,
            "errors": errors,
            "lazy": lazy,
            "atomic": atomic,
            # Path
            "exists": exists,
            "file_okay": file_okay,
            "dir_okay": dir_okay,
            "writable": writable,
            "readable": readable,
            "resolve_path": resolve_path,
            "allow_dash": allow_dash,
            "path_type": path_type,
            # Rich settings  ... Set to "Options" for the default panel
            "rich_help_panel": rich_help_panel,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not UNSET}
        combined = {**attr.__dict__, **kwargs}
        param_decls = param_decls or combined["param_decls"]
        args = (combined["default"], *param_decls)
        kwargs_out = {k: v for k, v in combined.items() if k not in ["default", "param_decls"]}
        return typer.Option(*args, **kwargs_out)


    def __call__(self, timerange: str, include_mins: bool = None):
        self.timerange = timerange
        if include_mins is not None:
            self.include_mins = include_mins
        return self
