# -*- coding: utf-8 -*-
from __future__ import annotations

from centralcli.cache import Cache
from centralcli.constants import iden_meta
from rich.markup import escape
from typing import Optional, Any, List, Type
from collections.abc import Callable
import click

import typer

from typer.models import ArgumentInfo, OptionInfo


class CLIArgs:
    def __init__(self, cache: Cache):
        self.cache = cache
        self.name: ArgumentInfo = typer.Argument(..., show_default=False,)
        self.device: ArgumentInfo = typer.Argument(..., metavar=iden_meta.dev, show_default=False, autocompletion=cache.dev_completion)
        self.devices: ArgumentInfo = typer.Argument(..., metavar=iden_meta.dev_many, autocompletion=cache.dev_completion, show_default=False,)
        self.what: ArgumentInfo = typer.Argument(..., show_default=False,)
        self.group: ArgumentInfo = typer.Argument(..., metavar=iden_meta.group, autocompletion=cache.group_completion, show_default=False,)
        self.group_dev: ArgumentInfo = typer.Argument(..., metavar="[GROUP|DEVICE]", help="Group or device", autocompletion=cache.group_dev_ap_gw_completion, show_default=False,)
        self.import_file: ArgumentInfo = typer.Argument(None, exists=True, show_default=False,)
        self.wid: ArgumentInfo = typer.Argument(..., help="Use [cyan]show webhooks[/] to get the wid", show_default=False,)
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

class CLIOptions:
    def __init__(self, cache: Cache, timerange: str = "3h", include_mins: bool = None):
        self.cache = cache
        self.timerange: str = timerange
        self.include_mins: bool = include_mins if include_mins is not None else True
        self.client: OptionInfo = typer.Option(None, "--client", metavar=iden_meta.client, autocompletion=cache.client_completion, show_default=False,)
        self.group: OptionInfo = typer.Option(None, help="Filter by Group", metavar=iden_meta.group, autocompletion=cache.group_completion, show_default=False,)
        self.group_many: OptionInfo = typer.Option(None, help="Filter by Group(s)", metavar=iden_meta.group_many, autocompletion=cache.group_completion, show_default=False,)
        self.site: OptionInfo = typer.Option(None, help="Filter by Site", metavar=iden_meta.site, autocompletion=cache.site_completion, show_default=False,)
        self.site_many: OptionInfo = typer.Option(None, help="Filter by Site(s)", metavar=iden_meta.site_many, autocompletion=cache.site_completion, show_default=False,)
        self.label: OptionInfo = typer.Option(None, help="Filter by Label", metavar=iden_meta.label, autocompletion=cache.label_completion,show_default=False,)
        self.label_many: OptionInfo = typer.Option(None, help="Filter by Label(s)", metavar=iden_meta.label_many, autocompletion=cache.label_completion,show_default=False,)
        self.debug: OptionInfo = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",)
        self.debugv: OptionInfo = typer.Option(False, "--debugv", help="Enable Verbose Debug Logging", rich_help_panel="Common Options",)
        self.do_json: OptionInfo = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting",)
        self.do_yaml: OptionInfo = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting",)
        self.do_csv: OptionInfo = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting",)
        self.do_table: OptionInfo = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting",)
        self.outfile: OptionInfo = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",)
        self.reverse: OptionInfo = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",)
        self.pager: OptionInfo = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",)
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
        self.device_many: OptionInfo = typer.Option(None, "--dev", metavar=iden_meta.dev_many, help="Filter by device", autocompletion=cache.dev_completion, show_default=False,)
        self.device: OptionInfo = typer.Option(None, "--dev", metavar=iden_meta.dev, help="Filter by device", autocompletion=cache.dev_completion, show_default=False,)
        self.swarm_device: OptionInfo = typer.Option(None, "-s", "--swarm", metavar=iden_meta.dev, help="Filter by the swarm associated with specified AOS8 IAP", autocompletion=cache.dev_ap_completion, show_default=False,)
        self.sort_by: OptionInfo = typer.Option(
            None,
            "--sort",
            help="Field to sort by [dim italic](Some fields may require -v (verbose) option where supported)[/]",
            show_default=False,
            rich_help_panel="Formatting",
        )
        self.default: OptionInfo = typer.Option(False, "-d", help="Use default central account", show_default=False, rich_help_panel="Common Options",)
        self.account: OptionInfo = typer.Option(
            "central_info",
            envvar="ARUBACLI_ACCOUNT",
            help="The Aruba Central Account to use (must be defined in the config)",
            rich_help_panel="Common Options",
            autocompletion=cache.account_completion,
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
        self.update_cache: OptionInfo = typer.Option(False, "-U", hidden=True)
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
    def timerange_to_start(self,):
        letter_to_word = {
            "M": "months",
            "w": "weeks",
            "d": "days",
            "h": "hours",
            "m": "minutes"
        }
        time_letter = self.timerange[-1]
        time_word = letter_to_word.get(time_letter, "ERR")
        if len(self.timerange) == 2 and self.timerange.startswith("1"):
            time_word = time_word.rsplit("s")

        return f"{self.timerange[0:-1]} {time_word} ago"

    def get(
        self,
        option: str,
        default: Optional[Any] = None,
        *,
        callback: Optional[Callable[..., Any]] = None,
        metavar: Optional[str] = None,
        expose_value: bool = None,
        is_eager: bool = None,
        envvar: Optional[str | List[str]] = None,
        shell_complete: Optional[
            Callable[
                [click.Context, click.Parameter, str],
                List["click.shell_completion.CompletionItem"] | List[str],
            ]
        ] = None,
        autocompletion: Optional[Callable[..., Any]] = None,
        default_factory: Optional[Callable[[], Any]] = None,
        # Custom type
        parser: Optional[Callable[[str], Any]] = None,
        click_type: Optional[click.ParamType] = None,
        # Option
        show_default: bool | str = None,
        prompt: bool |str = None,
        confirmation_prompt: bool = None,
        prompt_required: bool = None,
        hide_input: bool = None,
        is_flag: Optional[bool] = None,
        flag_value: Optional[Any] = None,
        count: bool = None,
        allow_from_autoenv: bool = None,
        help: Optional[str] = None,
        hidden: bool = None,
        show_choices: bool = None,
        show_envvar: bool = None,
        # Choice
        case_sensitive: bool = None,
        # Numbers
        min: Optional[int | float] = None,
        max: Optional[int | float] = None,
        clamp: bool = None,
        # DateTime
        formats: Optional[List[str]] = None,
        # File
        mode: Optional[str] = None,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        lazy: Optional[bool] = None,
        atomic: bool = None,
        # Path
        exists: bool = None,
        file_okay: bool = None,
        dir_okay: bool = None,
        writable: bool = None,
        readable: bool = None,
        resolve_path: bool = None,
        allow_dash: bool = None,
        path_type: None | Type[str] | Type[bytes] = None,
        # Rich settings
        rich_help_panel: str | None = None,

    ) -> OptionInfo:
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
            # Rich settings
            "rich_help_panel": rich_help_panel,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        combined = {**attr.__dict__, **kwargs}
        args = (combined["default"], *combined["param_decls"])
        kwargs_out = {k: v for k, v in combined.items() if k not in ["default", "param_decls"]}
        return typer.Option(*args, **kwargs_out)


    def __call__(self, timerange: str = None, include_mins: bool = None):
        if timerange:
            self.timerange = timerange
        if include_mins is not None:
            self.include_mins = include_mins
        return self
