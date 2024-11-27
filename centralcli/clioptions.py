# -*- coding: utf-8 -*-
from centralcli.cache import Cache
from centralcli.constants import iden_meta
from rich.markup import escape

import typer


class CLIArgs:
    def __init__(self, cache: Cache):
        self.cache = cache
        self.name = typer.Argument(..., show_default=False,)
        self.device = typer.Argument(..., metavar=iden_meta.dev, show_default=False, autocompletion=cache.dev_completion)
        self.devices = typer.Argument(..., metavar=iden_meta.dev_many, autocompletion=cache.dev_completion, show_default=False,)
        self.what = typer.Argument(..., show_default=False,)
        self.group: str = typer.Argument(..., metavar=iden_meta.group, autocompletion=cache.group_completion, show_default=False,)
        self.group_dev: str = typer.Argument(..., metavar="[GROUP|DEVICE]", help="Group or device", autocompletion=cache.group_dev_ap_gw_completion, show_default=False,)
        self.import_file = typer.Argument(None, exists=True, show_default=False,)

class CLIOptions:
    def __init__(self, cache: Cache, timerange: str = "3h", include_mins: bool = None):
        self.cache = cache
        self.timerange: str = timerange
        self.include_mins: bool = include_mins if include_mins is not None else True
        self.group = typer.Option(None, help="Filter by Group", metavar=iden_meta.group, autocompletion=cache.group_completion, show_default=False,)
        self.group_many = typer.Option(None, help="Filter by Group(s)", metavar=iden_meta.group_many, autocompletion=cache.group_completion, show_default=False,)
        self.site = typer.Option(None, help="Filter by Site", metavar=iden_meta.site, autocompletion=cache.site_completion, show_default=False,)
        self.site_many = typer.Option(None, help="Filter by Site(s)", metavar=iden_meta.site_many, autocompletion=cache.site_completion, show_default=False,)
        self.label = typer.Option(None, help="Filter by Label", metavar=iden_meta.label, autocompletion=cache.label_completion,show_default=False,)
        self.label_many = typer.Option(None, help="Filter by Label(s)", metavar=iden_meta.label_many, autocompletion=cache.label_completion,show_default=False,)
        self.debug = typer.Option(False, "--debug", envvar="ARUBACLI_DEBUG", help="Enable Additional Debug Logging", rich_help_panel="Common Options",)
        self.debugv: bool = typer.Option(False, "--debugv", help="Enable Verbose Debug Logging", rich_help_panel="Common Options",)
        self.do_json = typer.Option(False, "--json", is_flag=True, help="Output in JSON", show_default=False, rich_help_panel="Formatting",)
        self.do_yaml = typer.Option(False, "--yaml", is_flag=True, help="Output in YAML", show_default=False, rich_help_panel="Formatting",)
        self.do_csv = typer.Option(False, "--csv", is_flag=True, help="Output in CSV", show_default=False, rich_help_panel="Formatting",)
        self.do_table = typer.Option(False, "--table", help="Output in table format", show_default=False, rich_help_panel="Formatting",)
        self.outfile = typer.Option(None, "--out", help="Output to file (and terminal)", writable=True, show_default=False, rich_help_panel="Common Options",)
        self.reverse = typer.Option(False, "-r", help="Reverse output order", show_default=False, rich_help_panel="Formatting",)
        self.pager = typer.Option(False, "--pager", help="Enable Paged Output", rich_help_panel="Common Options",)
        self.yes = typer.Option(False, "-Y", "-y", "--yes", help="Bypass confirmation prompts - Assume Yes",)
        self.device_many = typer.Option(None, "--dev", metavar=iden_meta.dev_many, help="Filter by device", autocompletion=cache.dev_completion, show_default=False,)
        self.device = typer.Option(None, "--dev", metavar=iden_meta.dev, help="Filter by device", autocompletion=cache.dev_completion, show_default=False,)
        self.swarm_device = typer.Option(None, "-s", "--swarm", metavar=iden_meta.dev, help="Filter by the swarm associated with specified AOS8 IAP", autocompletion=cache.dev_ap_completion, show_default=False,)
        self.sort_by = typer.Option(
            None,
            "--sort",
            help="Field to sort by [grey42 italic](Some fields may require -v (verbose) option where supported)[/]",
            show_default=False,
            rich_help_panel="Formatting",
        )
        self.default = typer.Option(False, "-d", help="Use default central account", show_default=False, rich_help_panel="Common Options",)
        self.account = typer.Option(
            "central_info",
            envvar="ARUBACLI_ACCOUNT",
            help="The Aruba Central Account to use (must be defined in the config)",
            rich_help_panel="Common Options",
            autocompletion=cache.account_completion,
        )
        self.verbose = typer.Option(
            0,
            "-v",
            count=True,
            metavar="",
            help="Verbosity: Show more details, Accepts -vv -vvv etc. for increasing verbosity where supported",
            rich_help_panel="Formatting",
            show_default=False,
        )
        self.raw = typer.Option(
            False,
            "--raw",
            help="Show raw unformatted response from Central API Gateway",
            rich_help_panel="Formatting",
            show_default=False,
        )
        self.end = typer.Option(
            None,
            "-e", "--end",
            help=f"End of time-range (24hr notation) [grey42]{escape('[default: Now]')}[/]",
            formats=["%m/%d/%Y-%H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y", "%Y-%m-%d"],
            # rich_help_panel="Time Range Options",
            show_default=False,
        )
        self.update_cache = typer.Option(False, "-U", hidden=True)
        self.show_example = typer.Option(False, "--example", help="Show Example import file format.", show_default=False)
        self.at = typer.Option(
            None,
            help=f"Perform operation at specified date/time (24hr notation) [grey42]{escape('[default: Now]')}[/]",
            formats=["%m/%d/%Y-%H:%M", "%Y-%m-%dT%H:%M"],
            # rich_help_panel="Time Range Options",
            show_default=False,
        )

    @property
    def start(self):
        return typer.Option(
            None,
            "-s", "--start",
            help=f"Start of time-range (24hr notation) [grey42]{escape(f'[default: {self.timerange_to_start}]')}[/]",
            formats=["%m/%d/%Y-%H:%M", "%Y-%m-%dT%H:%M", "%m/%d/%Y", "%Y-%m-%d"],
            # rich_help_panel="Time Range Options",
            show_default=False,
        )

    @property
    def past(self):
        return typer.Option(
            None,
            "-p",
            "--past",
            help=f"Collect data for last... M=months, w=weeks, d=days, h=hours{', m=mins' if self.include_mins else ''} i.e.: 3h [grey42]{escape(f'[default: {self.timerange}]')}[/]",
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

    def __call__(self, timerange: str = None, include_mins: bool = None):
        if timerange:
            self.timerange = timerange
        if include_mins is not None:
            self.include_mins = include_mins
        return self
