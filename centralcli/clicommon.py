#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
from typing import List, Literal, Union, Tuple, Dict, Any, TYPE_CHECKING
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.progress import track
from rich.markup import escape
from rich import print
import json
from importlib.metadata import version
import os
import pendulum
from datetime import datetime
import time
import ipaddress

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response, render, BatchRequest, cleaner as clean
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response, render, BatchRequest, cleaner as clean
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi
from centralcli.objects import DateTime, Encoder
from centralcli.utils import ToBool
from centralcli.clioptions import CLIOptions, CLIArgs

if TYPE_CHECKING:
    from centralcli.cache import CentralObject, CacheGroup, CacheLabel, CacheDevice, CacheInvDevice
    from .typedefs import CacheTableName


tty = utils.tty
CASE_SENSITIVE_TOKENS = ["R", "U"]
TableFormat = Literal["json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action", "clean"]
MsgType = Literal["initial", "previous", "forgot", "will_forget", "previous_will_forget"]
clean_console = Console(emoji=False)
clean_err_console = Console(emoji=False, stderr=True)
err_console = Console(emoji=True, stderr=True)


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
                confirm_msg = f'\u2139  [dark_olive_green2]{len(v_list)}[/] {dev_word} will be {action_words} {move_type} [cyan]{k}[/]'  # \u2139 = :information:
                if retain_config:
                    confirm_msg = f"{confirm_msg} [italic dark_olive_green2]CX config will be preserved[/]."
                confirm_msgs += [confirm_msg]
                if len(v_list) > 6:
                    v_list = [*v_list[0:3], "...", *v_list[-3:]]
                confirm_msgs = [*confirm_msgs, *[f'  {dev}' for dev in v_list]]

        return confirm_msgs

    @property
    def serials_by_move_type(self) -> Dict[str, List[str]]:
        out = {}
        for req in self.reqs:
            move_type = "group" if self._move_type == "group" else f"{self._move_type}_id"
            key = req.kwargs.get(move_type)
            if not key and move_type == "group":
                key = req.kwargs["group"]

            serials = req.kwargs["serials"]
            out = utils.update_dict(out, key=key, value=serials)

        return out
class CLICommon:
    def __init__(self, account: str = "default", cache: Cache = None, central: CentralApi = None, raw_out: bool = False):
        self.account = account
        self.cache = cache
        self.central = central
        self.raw_out = raw_out
        self.options = CLIOptions(cache)
        self.arguments = CLIArgs(cache)
        self.econsole = Console(stderr=True)
        self.console = Console()

    def confirm(self, yes: bool = False, *, prompt: str = "\nProceed?", abort: bool = True,) -> bool:
        confirm = Confirm(prompt=prompt, console=self.econsole,)
        result = yes or confirm()
        if not result and abort:
            self.econsole.print("[red]Aborted[/]")
            self.exit(code=0)

        return result

    def pause(self, prompt="Press Enter to Continue", *, console: Console = None) -> None:
        console = console or self.econsole
        ask = Prompt(prompt, console=console, password=True, show_default=False, show_choices=False)
        _ = ask()

    class AcctMsg:
        def __init__(self, account: str = None, msg: MsgType = None) -> None:
            self.account = account
            self.msg = msg

        def __repr__(self) -> str:
            return f"<{self.__module__}.{type(self).__name__} ({self.cache}|{self.get('name', bool(self))}) object at {hex(id(self))}>"

        def __str__(self) -> str:
            if self.msg and hasattr(self, self.msg):
                return getattr(self, self.msg)
            else:
                return self.initial if not os.environ.get("ARUBACLI_ACCOUNT") else self.envvar

        def __call__(self) -> str:
            return self.__str__()

        @property
        def envvar(self):
            return f'[magenta]Using Account[/]: [cyan]{self.account}[/] [italic]based on env var[/] [dark_green]ARUBACLI_ACCOUNT[/]'

        @property
        def initial(self):
            msg = (
                f'[magenta]Using Account[/]: [cyan]{self.account}[/].\n'
                f'[bright_red blink]Account setting is sticky.[/]  '
                f'[cyan]{self.account}[/] [magenta]will be used for subsequent commands until[/]\n'
                f'[cyan]--account <account name>[/] or [cyan]-d[/] (revert to default). is used.\n'
            )
            return msg

        @property
        def previous(self):
            return (
                f'[magenta]Using previously specified account[/]: [cyan blink]{self.account}[/]'
                f'\n[magenta]Use[/] [cyan]--account <account name>[/] [magenta]to switch to another account.[/]'
                f'\n    or [cyan]-d[/] [magenta]flag to revert to default account[/].'
            )

        @property
        def forgot(self):
                return ":information:  Forget option set for account, and expiration has passed.  [bright_green]reverting to default account\n[/]"

        @property
        def will_forget(self):
            will_forget_msg = "[magenta]Forget options is configured, will revert to default account[/]\n"
            will_forget_msg = f"{will_forget_msg}[cyan]{config.forget}[/][magenta] mins after last command[/]\n"
            return will_forget_msg

        @property
        def previous_will_forget(self):
            return f"{self.previous}\n\n{self.will_forget}"

        @property
        def previous_short(self):
            return f":information:  Using previously specified account: [bright_green]{self.account}[/].\n"

    def account_name_callback(self, ctx: typer.Context, account: str, default: bool = False) -> str:
        """Responsible for account messaging.  Actual account is determined in config.

        Account has to be collected prior to CLI for completion to work specific to the account.

        Args:
            ctx (typer.Context): Typer context
            account (str): account name.  Will only have value if --account flag was used.
                Otherwise we use the default account, or envvar, or the last account (if forget timer not expired.)
            default (bool, optional): If default flag was used to call this func. Defaults to False.

        Raises:
            typer.Exit: Exits if account is not found.

        Returns:
            str: account name
        """
        if ctx.resilient_parsing:  # tab completion, return without validating, so does use of "test method" command
            return account

        emoji_console = Console()

        # cencli test method requires --account when using non default, we do not honor forget_account_after
        if " ".join(sys.argv[1:]).startswith("test method"):
            if account:
                emoji_console.print(f":information:  Using account [bright_green]{account}[/]\n",)
                return account
            else:
                return "default" if "default" in config.data else "central_info"

        account = account or config.default_account  # account only has value if --account flag is used.

        if default:  # They used the -d flag
            emoji_console.print(":information:  [bright_green]Using default central account[/]\n",)
            if config.sticky_account_file.is_file():
                config.sticky_account_file.unlink()
            if account in config.data:
                return account
            elif "default" in config.data:
                return "default"

        # -- // sticky last account messaging account is loaded in config.py \\ --
        elif account in ["central_info", "default"]:
            if config.last_account:
                # last account messaging.
                if config.forget is not None:
                    if config.last_account_expired:
                        msg = self.AcctMsg(account)
                        emoji_console.print(msg.forgot)
                        if config.sticky_account_file.is_file():
                            config.sticky_account_file.unlink()

                    else:
                        account = config.last_account
                        msg = self.AcctMsg(account)
                        if not config.last_account_msg_shown:
                            clean_console.print(msg.previous_will_forget)
                            config.update_last_account_file(account, config.last_cmd_ts, True)
                        else:
                            emoji_console.print(msg.previous_short)

                else:
                    account = config.last_account
                    msg = self.AcctMsg(account)
                    if not config.last_account_msg_shown:
                        clean_console.print(msg.previous)
                        config.update_last_account_file(account, config.last_cmd_ts, True)
                    else:
                        emoji_console.print(msg.previous_short)

        elif account in config.data:
            if account == os.environ.get("ARUBACLI_ACCOUNT", ""):
                msg = self.AcctMsg(account)
                clean_console.print(msg.envvar)
            elif config.forget is not None and config.forget > 0:
                clean_console.print(self.AcctMsg(account).initial)
            # No need to print account msg if forget is set to zero



        if config.valid:
            return account
        else:  # -- Error messages config invalid or account not found in config --
            _def_msg = False
            emoji_console.print(
                f":warning:  [bright_red]Error:[/] The specified account: [cyan]{config.account}[/] is not defined in the config @\n"
                f"  {config.file}\n"
            )

            if "central_info" not in config.data and "default" not in config.data:
                _def_msg = True
                emoji_console.print(
                    ":warning:  [cyan]central_info[/] is not defined in the config.  This is the default when not overridden by\n"
                    "--account flag or [cyan]ARUBACLI_ACCOUNT[/] environment variable.\n"
                )

            if account not in ["central_info", "default"]:
                if config.defined_accounts:
                    clean_console.print(f"[bright_green]The following accounts are defined[/] [cyan]{'[/], [cyan]'.join(config.defined_accounts)}[reset]\n")
                    if not _def_msg:
                        clean_console.print(
                            f"The default account [cyan]{config.default_account}[/] is used if no account is specified via [cyan]--account[/] flag.\n"
                            "or the [cyan]ARUBACLI_ACCOUNT[/] environment variable.\n"
                        )

            raise typer.Exit(code=1)

    def version_callback(self, ctx: typer.Context | None = None,):
        if ctx is not None and ctx.resilient_parsing:  # tab completion, return without validating
            return

        current = version("centralcli")
        resp = self.central.request(self.central.get, "https://pypi.org/pypi/centralcli/json")
        if not resp:
            print(current)
        else:
            major = max([int(str(k).split(".")[0]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2])
            minor = max([int(str(k).split(".")[1]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2 and int(str(k).split(".")[0]) == major])
            patch = max([int(str(k).split(".")[2]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2 and int(str(k).split(".")[0]) == major and int(str(k).split(".")[1]) == minor])
            latest = f'{major}.{minor}.{patch}'
            msg = "[bold bright_green]centralcli[/] "
            msg += 'A CLI app for interacting with Aruba Central Cloud Management Platform.\n'
            msg += f'Brought to you by [cyan]{resp.output["info"]["author"]}[/]\n\n'
            msg += "\n".join([f'  {k}: [cyan]{v}[/]' for k, v in resp.output["info"]["project_urls"].items()])
            msg += f'\n\nVersion: {current}'
            if current == latest:
                msg += " [italic green3]You are on the latest version.[reset]"
            else:
                msg += f'\nLatest Available Version: {latest}'

            print(msg)

    @staticmethod
    def default_callback(ctx: typer.Context, default: bool):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return

        if default and config.sticky_account_file.is_file():
            emoji_console = Console()
            emoji_console.print(":information:  [bright_green]Using default central account[/]\n",)
            config.sticky_account_file.unlink()
            return default

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
    def verbose_debug_callback(ctx: typer.Context, debugv: bool):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return False

        if debugv:
            log.DEBUG = log.verbose = config.debug = config.debugv = debugv
            return debugv

    # TODO not used at the moment but could be used to allow unambiguous partial tokens
    @staticmethod
    def normalize_tokens(token: str) -> str:
        return token.lower() if token not in CASE_SENSITIVE_TOKENS else token

    @staticmethod
    def get_format(
        do_json: bool = False, do_yaml: bool = False, do_csv: bool = False, do_table: bool = False, default: str = "rich"
    ) -> TableFormat:
        """Simple helper method to return the selected output format type (str)"""
        if do_json:
            return "json"
        elif do_yaml:
            return "yaml"
        elif do_csv:
            return "csv"
        elif do_table:
            return "rich" if default != "rich" else "tabulate"
        else:
            return default

    def write_file(self, outfile: Path, outdata: str) -> None:
        """Output data to file

        Args:
            outfile (Path): The file to write to.
            outdata (str): The text to write.
        """
        if outfile and outdata:
            if config.cwd != config.outdir:
                if (
                    outfile.parent.resolve().name == "central-api-cli" and
                    Path.joinpath(outfile.parent.resolve() / ".git").is_dir()
                ):
                    # outdir = Path.home() / 'cencli-out'
                    print(
                        "\n[bright_green]You appear to be in the development git dir.\n"
                        f"Exporting to[/] [cyan]{config.outdir.relative_to(config.cwd)}[/] directory."
                    )
                    config.outdir.mkdir(exist_ok=True)
                    outfile = config.outdir / outfile

            print(f"[cyan]Writing output to {outfile}... ", end="")

            if not outfile.parent.is_dir():
                self.econsole.print(f"[red]Directory Not Found[/]\n[dark_orange3]:warning:[/]  Unable to write output to [cyan]{outfile.name}[/].\nDirectory [cyan]{str(outfile.parent.absolute())}[/] [red]does not exist[/].")
            else:
                out_msg = None
                try:
                    if isinstance(outdata, (dict, list)):
                        outdata = json.dumps(outdata, indent=4)
                    # ensure LF at EoF
                    outdata = f"{outdata.rstrip()}\n"
                    outfile.write_text(outdata)  # typer.unstyle(outdata) also works
                except Exception as e:
                    outfile.write_text(f"{outdata}")
                    out_msg = f"Error ({e.__class__.__name__}) occurred during attempt to output to file.  " \
                        "Used simple string conversion"

                print("[italic green]Done")
                if out_msg:
                    log.warning(out_msg, show=True)

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
        console = Console(emoji=emoji)
        if code != 0:
            msg = f"[dark_orange3]\u26a0[/]  {msg}" if msg else msg  # \u26a0 = ⚠ / :warning:

        # Display any log captions when exiting
        if log.caption:
            console.print(log.caption.lstrip().replace("\n  ", "\n"))

        if msg:
            console.print(msg)
        raise typer.Exit(code=code)

    def _sort_results(
            self,
            data: List[dict] | List[str] | dict | None,
            *,
            sort_by: str,
            reverse: bool,
            tablefmt: TableFormat,
            caption: str = None,
    ) -> Tuple:
        if sort_by and all(isinstance(d, dict) for d in data):
            possible_sort_keys = [sort_by, sort_by.replace("_", " ").replace("-", " "), f'{sort_by.replace("_", " ").replace("-", " ")} %', f'{sort_by.replace("_", " ").replace("-", " ")}%']
            matched_key = [k for k in possible_sort_keys if k in data[0]]
            sort_by = sort_by if not matched_key else matched_key[0]

            sort_msg = None
            if not all([sort_by in d for d in data]):
                sort_msg = [
                        f":warning:  [dark_orange3]Sort Error: [cyan]{sort_by}[reset] does not appear to be a valid field",
                        "Valid Fields: {}".format(", ".join(f'{k.replace(" ", "-")}' for k in data[0].keys()))
                ]
            else:
                try:
                    if sort_by in ["ip", "destination"] or sort_by.endswith(" ip"):
                        data = sorted(data, key=lambda d: ipaddress.IPv4Address("0.0.0.0") if not d[sort_by] or d[sort_by] == "-" else ipaddress.ip_address(d[sort_by].split("/")[0]))
                    else:
                        type_ = str
                        for d in data:
                            if d[sort_by] is not None:
                                type_ = type(d[sort_by])
                                break
                        data = sorted(data, key=lambda d: d[sort_by] if d[sort_by] is not None and d[sort_by] != "-" else 0 if type_ in [int, DateTime] else "")
                except TypeError as e:
                    sort_msg = [f":warning:  Unable to sort by [cyan]{sort_by}.\n   {e.__class__.__name__}: {e} "]

            if sort_msg:
                _caption = "\n".join([f" {m}" for m in sort_msg])
                _caption = _caption if tablefmt != "rich" else render.rich_capture(_caption, emoji=True)
                if caption:
                    c = caption.splitlines()
                    c.insert(-1, _caption)
                    caption = "\n".join(c)
                else:
                    caption = _caption

        return data if not reverse else data[::-1], caption

    @staticmethod
    def _add_captions_from_cleaner(caption: str) -> str:
        """Need to append any captions added from cleaners.

        TODO make more elegant.  Redesign to remove the need for this.
        """
        caption = caption.splitlines()
        new_captions = [f" {c.lstrip()}" for c in log._caption if c.strip() not in [cap.strip() for cap in caption]]
        rl_str = [] if not caption else [caption.pop(-1)]
        caption = [*caption, *new_captions, *rl_str]
        return "\n".join(caption)

    def _display_results(
        self,
        data: Union[List[dict], List[str], dict, None] = None,
        tablefmt: str = "rich",
        title: str = None,
        caption: str = None,
        pager: bool = False,
        outfile: Path = None,
        sort_by: str = None,
        reverse: bool = False,
        stash: bool = True,
        output_by_key: str | List[str] = "name",
        group_by: str = None,
        set_width_cols: dict = None,
        full_cols: Union[List[str], str] = [],
        fold_cols: Union[List[str], str] = [],
        cleaner: callable = None,
        **cleaner_kwargs,
    ):
        if not data:
            log.warning(f"No data passed to _display_output {typer.unstyle(render.rich_capture(title))} {typer.unstyle(render.rich_capture(caption))}")
            return
        cap_console = Console(stderr=True)
        data = utils.listify(data)

        if cleaner and not self.raw_out:
            with clean_console.status("Cleaning Output..."):
                _start = time.perf_counter()
                data = cleaner(data, **cleaner_kwargs)
                caption = self._add_captions_from_cleaner(caption)
                data = utils.listify(data)
                _duration = time.perf_counter() - _start
                log.debug(f"{cleaner.__name__} took {_duration:.2f} to clean {len(data)} records")

        data, caption = self._sort_results(data, sort_by=sort_by, reverse=reverse, tablefmt=tablefmt, caption=caption)

        if self.raw_out and tablefmt in ["simple", "rich"]:
            tablefmt = "json"

        kwargs = {
            "outdata": data,
            "tablefmt": tablefmt,
            "title": title,
            "caption": caption,
            "account": None if config.account in ["central_info", "default"] else config.account,
            "config": config,
            "output_by_key": output_by_key,
            "group_by": group_by,
            "set_width_cols": set_width_cols,
            "full_cols": full_cols,
            "fold_cols": fold_cols,
        }
        with clean_console.status("Rendering Output..."):
            outdata = render.output(**kwargs)

        if stash:
            config.last_command_file.write_text(
                json.dumps({k: v if not isinstance(v, DateTime) else v.ts for k, v in kwargs.items() if k != "config"}, cls=Encoder)
            )

        typer.echo_via_pager(outdata) if pager and tty and len(outdata) > tty.rows else typer.echo(outdata)

        # if "Limit:" not in outdata and caption is not None and cleaner is not None and cleaner.__name__ != "parse_caas_response":
        #     print(caption)
        if caption and tablefmt != "rich":
            cap_console.print("".join([line.lstrip() for line in caption.splitlines(keepends=True)]))

        if outfile and outdata:
            print()
            self.write_file(outfile, outdata.file)


    def display_results(
        self,
        resp: Union[Response, List[Response]] = None,
        data: Union[List[dict], List[str], dict, None] = None,
        tablefmt: TableFormat = "rich",
        title: str | List[str] = None,
        caption: str | List[str] = None,
        pager: bool = False,
        outfile: Path = None,
        sort_by: str = None,
        reverse: bool = False,
        stash: bool = True,
        output_by_key: str | List[str] = "name",
        group_by: str = None,
        exit_on_fail: bool = False,  # TODO make default True so failed calls return a failed return code to the shell.  Need to validate everywhere it needs to be set to False
        cache_update_pending: bool = False,
        set_width_cols: dict = None,
        full_cols: Union[List[str], str] = [],
        fold_cols: Union[List[str], str] = [],
        cleaner: callable = None,
        **cleaner_kwargs,
    ) -> None:
        """Output Formatted API Response to display and optionally to file

        one of resp or data attribute is required

        Args:
            resp (Union[Response, List[Response], None], optional): API Response objects.
            data (Union[List[dict], List[str], None], optional): API Response output data.
            tablefmt (str, optional): Format of output. Defaults to "rich" (tabular).
                Valid Values: "json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action", "clean"
                Where "raw" is unformatted raw response and "action" is formatted for POST|PATCH etc.
                where the result is a simple success/error.
                clean bypasses all formatters.
            title: (str | List[str], optional): Title of output table.
                List[str] is allowed if tablefmt is not rich, list should match the # of Responses
                Defaults to None.
            caption: (str | List[str], optional): Caption displayed at bottom of table.
                Only applies to "rich" tablefmt. Defaults to None.
            pager (bool, optional): Page Output / or not. Defaults to True.
            outfile (Path, optional): path/file of output file. Defaults to None.
            sort_by (Union[str, List[str], None] optional): column or columns to sort output on.
            reverse (bool, optional): reverse the output.
            stash (bool, optional): stash (cache) the output of the command.  The CLI can re-display with
                show last.  Default: True
            output_by_key: For json or yaml output, if any of the provided keys are foound in the List of dicts
                the List will be converted to a Dict[value of provided key, original_inner_dict].  Defaults to name.
            group_by: When provided output will be grouped by this key.  For outputs where multiple entries relate to a common device, and multiple devices exist in the output.
                i.e. interfaces for a device when the output contains multiple devices.  Results in special formatting.  Defaults to None
            exit_on_fail: (bool, optional): If provided resp indicates a failure exit after display.  Defaults to False
            cache_update_pending: (bool, optional): If a cache update is to be performed if resp is success.
                Results in a warning before exit if failure. Defaults to False
            set_width_cols (Dict[str: Dict[str, int]]): Passed to output function defines cols with min/max width
                example: {'details': {'min': 10, 'max': 30}, 'device': {'min': 5, 'max': 15}}.  Applies to tablefmt=rich.
            full_cols (list): columns to ensure are displayed at full length (no wrap no truncate). Applies to tablfmt=rich. Defaults to [].
            fold_cols (Union[List[str], str], optional): columns that will be folded (wrapped within the same column). Applies to tablfmt=rich. Defaults to [].
            cleaner (callable, optional): The Cleaner function to use.
        """
        if isinstance(caption, list):
            caption = "\n ".join(caption)
        if resp is not None:
            resp = utils.listify(resp)

            if self.raw_out:
                tablefmt = "raw"

            # update caption with rate limit
            try:
                last_rl = sorted(resp, key=lambda r: r.rl.remain_day)
                if last_rl:
                    rl_str = f"[reset][italic dark_olive_green2]{last_rl[0].rl}[/]".lstrip()
                    caption = f"{caption}\n {rl_str}" if caption else f" {rl_str}"
            except Exception as e:
                rl_str = ""
                log.error(f"Exception when trying to determine last rate-limit str for caption {e.__class__.__name__}")

            caption = caption or ""
            if log.caption:  # rich table is printed with emoji=False need to manually swap the emoji
                # TODO see if table has option to only do emoji in caption
                _log_caption = log.caption.replace(":warning:", "\u26a0").replace(":information:", "\u2139")  # warning ⚠, information: ℹ
                if len(resp) > 1 and ":warning:" in log.caption:
                    caption = f'{caption}\n[bright_red]  !!! Partial command failure !!!\n{_log_caption}[/]'
                else:
                    caption = f'{caption}\n{_log_caption}'

            for idx, r in enumerate(resp):
                try:
                    if config.capture_raw and r.method == "GET":
                        with clean_console.status("Capturing raw response"):
                            raw = r.raw if r.url.path in r.raw else {r.url.path: r.raw}
                            with config.capture_file.open("a") as f:
                                f.write(json.dumps(raw))
                except Exception as e:
                    log.error(f"Exception whilte attempting to capture raw output {repr(e)}")

                # Multi request url line (example below)
                # Request 1 [POST: /platform/device_inventory/v1/devices]
                #  Response:
                m_colors = {
                    "GET": "bright_green",
                    "DELETE": "red",
                    "PATCH": "dark_orange3",
                    "PUT": "dark_orange3",
                    "POST": "dark_orange3"
                }
                fg = "bright_green" if r else "red"

                conditions = [len(resp) > 1, tablefmt in ["action", "raw", "clean"], r.ok and not r.output, not r.ok]
                if any(conditions):
                    if isinstance(title, list) and len(title) == len(resp):
                        print(title[idx])
                    else:
                        _url = r.url if not hasattr(r.url, "path") else r.url.path
                        m_color = m_colors.get(r.method, "reset")
                        print(f"Request {idx + 1} [[{m_color}]{r.method}[reset]: [cyan]{_url}[/cyan]]")
                        print(f" [{fg}]Response[reset]:")


                conditions = [tablefmt in ["action", "raw", "clean"], r.ok and not r.output, not r.ok]
                if any(conditions):
                    # raw output (unformatted response from Aruba Central API GW)
                    if tablefmt in ["raw", "clean"]:
                        status_code = f"[{fg}]status code: {r.status}[/{fg}]"
                        print(r.url)
                        print(status_code)
                        if not r.ok:
                            print(r.error)

                        if tablefmt == "clean":
                            typer.echo_via_pager(r.output) if pager else typer.echo(r.output)
                        else:
                            print("[bold cyan]Unformatted response from Aruba Central API GW[/bold cyan]")
                            plain_console = Console(color_system=None, emoji=False)
                            if config.sanitize:
                                r.raw = json.loads(render.Output().sanitize_strings(json.dumps(r.raw), config=config))
                            if pager:
                                with plain_console.pager:
                                    plain_console.print(r.raw)
                            else:
                                plain_console.print(r.raw)

                        if outfile:
                            print()
                            self.write_file(outfile, r.raw if tablefmt != "clean" else r.output)

                    # prints the Response objects __str__ method which includes status_code
                    # and formatted contents of any payload. example below
                    # status code: 201
                    # Success
                    else:
                        if not r.url.path == "/caasapi/v1/exec/cmd":
                            clean_console.print(r)
                        else:
                            clean_console.print(Text.from_ansi(clean.parse_caas_response(r.output)))  # TODO still need to covert everything from cleaners to rich MarkUp so we can use rich print consistently vs typer.echo
                            # TODO make __rich__ renderable method in Response object with markups

                    if idx + 1 == len(resp):
                        if caption.replace(rl_str, "").lstrip():
                            _caption = caption.replace(rl_str, "") if r.output else f'  {render.unstyle(caption.replace(rl_str, "")).strip()}'
                            if not r.output:  # Formats any caption directly under Empty Response msg
                                _caption = "\n  ".join(f"{'  ' if idx == 0 else ''}[grey42 italic]{line.strip()}[/]" for idx, line in enumerate(_caption.splitlines()))
                            self.econsole.print(_caption)
                        self.econsole.print(f"\n{rl_str}")

                # response to single request are sent to _display_results for full output formatting. (rich, json, yaml, csv)
                else:
                    self._display_results(
                        r.output,
                        tablefmt=tablefmt,
                        title=title,
                        caption=caption if idx == len(resp) - 1 else None,
                        pager=pager,
                        outfile=outfile,
                        sort_by=sort_by,
                        reverse=reverse,
                        stash=stash,
                        output_by_key=output_by_key,
                        group_by=group_by,
                        set_width_cols=set_width_cols,
                        full_cols=full_cols,
                        fold_cols=fold_cols,
                        cleaner=cleaner,
                        **cleaner_kwargs
                    )

            if exit_on_fail and not all([r.ok for r in resp]):
                if cache_update_pending:
                    self.econsole.print(":warning:  [italic]Cache update skipped due to failed API response(s)[/].")
                raise typer.Exit(1)

        elif data:
            self._display_results(
                data,
                tablefmt=tablefmt,
                title=title,
                caption=caption,
                pager=pager,
                outfile=outfile,
                sort_by=sort_by,
                reverse=reverse,
                stash=stash,
                output_by_key=output_by_key,
                set_width_cols=set_width_cols,
                full_cols=full_cols,
                fold_cols=fold_cols,
                cleaner=cleaner,
                **cleaner_kwargs
            )

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

    def verify_time_range(self, start: datetime | pendulum.DateTime | None, end: datetime | pendulum.DateTime = None, past: str = None, max_days: int = 90) -> pendulum.DateTime | None:
        if end and past:
            log.warning("[cyan]--end[/] flag ignored, providing [cyan]--past[/] implies end is now.", caption=True,)
            end = None

        if start and past:
            log.warning(f"[cyan]--start[/] flag ignored, providing [cyan]--past[/] implies end is now - {past}", caption=True,)

        if past:
            start = self.delta_to_start(delta=past)

        if start is None:
            return start, end

        if not hasattr(start, "timezone"):
            start = pendulum.from_timestamp(start.timestamp(), tz="UTC")
        if end is None:
            _end = pendulum.now(tz=start.timezone)
        else:
            _end = end if hasattr(end, "timezone") else pendulum.from_timestamp(end.timestamp(), tz="UTC")

        delta = _end - start

        if delta.days > max_days:
            if end:
                self.exit(f"[cyan]--start[/] and [cyan]--end[/] provided span {delta.days} days.  Max allowed is 90 days.")
            else:
                log.info(f"[cyan]--past[/] option spans {delta.days} days.  Max allowed is 90 days.  Output constrained to 90 days.", caption=True)
                return self.delta_to_start("2_159h"), end  # 89 days and 23 hours to avoid timing issue with API endpoint

        return start, _end

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

    def _get_import_file(self, import_file: Path = None, import_type: CacheTableName = None, text_ok: bool = False,) -> List[Dict[str, Any]]:
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


        if isinstance(data, dict) and all([isinstance(v, dict) for v in data.values()]):
            if import_type in ["groups", "sites"]:  # accept yaml/json keyed by name for groups and sites
                data = [{"name": k, **v} for k, v in data.items()]
            elif utils.is_serial(list(data.keys())[0]):  # accept yaml/json keyed by serial for devices
                data = [{"serial": k, **v} for k, v in data.items()]
        elif text_ok and isinstance(data, list) and all([isinstance(d, str) for d in data]):
            if import_type == "devices" and utils.is_serial(data[0].keys()[-1]):  # spot check the last key to ensure it looks like a serial
                data = [{"serial": s} for s in data if not s.lower().startswith("serial")]
            if import_type == "labels":
                data = [{"name": label} for label in data if not label.lower().startswith("label")]

        data = clean.strip_no_value(data, aggressive=True)  # We need to strip empty strings as csv import will include the field with empty string and fail validation
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
            _ = self.central.request(self.cache.refresh_dev_db, dev_type=device.type)
            device = self.cache.get_dev_identifier(device.serial, include_inventory=True, dev_type=device.type)

        return device

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
                            clean_console.print(f"\u2139  [dark_orange3]Ignoring[/] group move for {cache_dev.summary_text}. [italic grey42](already in group [magenta]{to_group}[/magenta])[reset].")
                            _skip = True

                    # Determine if device is in inventory only determines use of pre-provision group vs move to group
                    if not has_connected:
                        req_dict = pregroup_mv_reqs
                        msg_dict = pregroup_mv_msgs
                        if retain_config:
                            err_console.print(f'[bright_red]\u26a0[/]  {cache_dev.summary_text} Group assignment is being ignored.')  # \u26a0 is :warning: need clean_console to prevent MAC from being evaluated as :cd: emoji
                            err_console.print(f'  [italic]Device has not connected to Aruba Central, it must be "pre-provisioned to group [magenta]{to_group}[/]".  [cyan]retain_config[/] is only valid on group move not group pre-provision.[/]')
                            err_console.print('  [italic]To onboard and keep the config, allow it to onboard to the default unprovisioned group (default behavior without pre-provision), then move it once it appears in Central, with retain-config option.')
                            _skip = True
                    else:
                        req_dict = group_mv_reqs if not retain_config else group_mv_cx_retain_reqs
                        msg_dict = group_mv_msgs if not retain_config else group_mv_cx_retain_msgs

            if not _skip:
                req_dict = utils.update_dict(req_dict, key=to_group, value=cache_dev.serial)
                msg_dict = utils.update_dict(msg_dict, key=to_group, value=cache_dev.rich_help_text)

        mv_reqs, pre_reqs, mv_retain_reqs = [], [], []
        if pregroup_mv_reqs:
            pre_reqs = [self.central.BatchRequest(self.central.preprovision_device_to_group, group=k, serials=v) for k, v in pregroup_mv_reqs.items()]
        if group_mv_reqs:
            mv_reqs = [self.central.BatchRequest(self.central.move_devices_to_group, group=k, serials=v) for k, v in group_mv_reqs.items()]
        if group_mv_cx_retain_reqs:
            mv_retain_reqs = [self.central.BatchRequest(self.central.move_devices_to_group, group=k, serials=v, cx_retain_config=True) for k, v in group_mv_cx_retain_reqs.items()]

        return self.GroupMoves(
            pregroup_mv_reqs=pre_reqs,
            pregroup_mv_msgs=pregroup_mv_msgs,
            group_mv_reqs=mv_reqs,
            group_mv_msgs=group_mv_msgs,
            group_mv_cx_retain_reqs=mv_retain_reqs,
            group_mv_cx_retain_msgs=group_mv_cx_retain_msgs,
            cache_devs=cache_devs
        )


    def _check_site(self, cache_devs: List[CacheDevice | CacheInvDevice], import_data: dict) -> SiteMoves:
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
                            clean_console.print(f"\u2139  [dark_orange3]Ignoring[/] site move for {cache_dev.summary_text}. [italic grey42](already in site [magenta]{to_site.name}[/magenta])[reset]")
                    elif not has_connected:
                        if idx == 0:
                            cache_dev = self._check_update_dev_db(cache_dev)
                        else:
                            clean_console.print(f"\u2139  [dark_orange3]Ignoring[/] site move for {cache_dev.summary_text}. [italic grey42](Device must connect to Central before site can be assigned)[reset]")
                    elif idx != 0:
                        site_mv_reqs = utils.update_dict(site_mv_reqs, key=f'{to_site.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                        site_mv_msgs = utils.update_dict(site_mv_msgs, key=to_site.name, value=cache_dev.rich_help_text)

                    if now_site:
                        now_site = self.cache.get_site_identifier(now_site)
                        if idx != 0 and now_site.name != to_site.name:  # need to remove from current site
                            clean_console.print(f'{cache_dev.summary_text} will be removed from site [red]{now_site.name}[/] to facilitate move to site [bright_green]{to_site.name}[/]')
                            site_rm_reqs = utils.update_dict(site_rm_reqs, key=f'{now_site.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                            site_rm_msgs = utils.update_dict(site_rm_msgs, key=now_site.name, value=cache_dev.rich_help_text)

        rm_reqs = []
        if site_rm_reqs:
            for k, v in site_rm_reqs.items():
                site_id, dev_type = k.split("~|~")
                rm_reqs += [BatchRequest(self.central.remove_devices_from_site, site_id=int(site_id), serials=v, device_type=dev_type)]

        mv_reqs = []
        if site_mv_reqs:
            for k, v in site_mv_reqs.items():
                site_id, dev_type = k.split("~|~")
                mv_reqs += [BatchRequest(self.central.move_devices_to_site, site_id=int(site_id), serials=v, device_type=dev_type)]

        return self.SiteMoves(
            cache_devs=cache_devs,
            site_mv_reqs=mv_reqs,
            site_mv_msgs=site_mv_msgs,
            site_rm_reqs=rm_reqs,
            site_rm_msgs=site_rm_msgs
        )

    def _check_label(self, cache_devs: List[CentralObject], import_data: dict,) -> MoveData:
        label_ass_reqs, label_ass_msgs = {}, {}
        for cache_dev, mv_data in zip(cache_devs, import_data):
            to_label = mv_data.get("label", mv_data.get("labels"))
            if to_label:
                to_label = utils.listify(to_label)
                for label in to_label:
                    clabel = self.cache.get_label_identifier(to_label)
                    if clabel.name in cache_dev.get("labels"):
                        clean_console.print(f'{cache_dev.rich_help_text}, already assigned label [magenta]{label.name}[/]. Ingoring.')
                    else:
                        label_ass_reqs = utils.update_dict(label_ass_reqs, key=f'{clabel.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                        label_ass_msgs = utils.update_dict(label_ass_msgs, key=clabel.name, value=cache_dev.rich_help_text)

        batch_reqs = []
        if label_ass_reqs:
            for k, v in label_ass_reqs.items():
                label_id, dev_type = k.split("~|~")
                batch_reqs += [self.central.BatchRequest(self.central.assign_label_to_devices, label_id=int(label_id), serials=v, device_type=dev_type)]

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
                    site_success_serials = [s["device_id"] for s in r.raw["success"] if s["device_id"] in serials]  # if .... in serials stips out stack_id, success will have all member serials + the stack_id
                    cache_by_serial = {serial: {**cache_by_serial[serial], "site": name} for serial in serials if serial in site_success_serials}
                if move_type == "group":  # All or none here as far as the rresponse.
                    cache_by_serial = {serial: {**cache_by_serial[serial], "group": name} for serial in serials}

        self.central.request(
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
        if len(set(dev_idens)) < len(dev_idens):  # Detect and filter out any duplicate entries
            filtered_count = len(dev_idens) - len(set(dev_idens))
            dev_idens = set(dev_idens)
            err_console.print(f"[dark_orange3]:warning:[/]  Filtering [cyan]{filtered_count}[/] duplicate device{'s' if filtered_count > 1 else ''} from update.")

        # conductor_only option, as group move will move all associated devices when device is part of a swarm or stack
        cache_devs: List[CentralObject] = [self.cache.get_dev_identifier(d, include_inventory=True, conductor_only=True, silent=True, exit_on_fail=False) for d in dev_idens]
        not_found_devs: List[str] = [s for s, c in zip(dev_idens, cache_devs) if c is None]
        cache_devs: List[CacheDevice | CacheInvDevice] = [d for d in cache_devs if d]

        if not_found_devs:
            not_in_inv_msg = utils.color(not_found_devs, color_str="cyan", pad_len=4, sep="\n")
            self.econsole.print(f"\n[dark_orange3]\u26a0[/]  The following provided devices were not found in the inventory.\n{not_in_inv_msg}", emoji=False)
            self.econsole.print("[grey42 italic]They will be skipped[/]\n")
            if not cache_devs:
                self.exit("No devices found")


        site_rm_reqs, batch_reqs, confirm_msgs = [], [], [""]
        if do_site:
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

        clean_console.print("\n".join(confirm_msgs))
        if self.confirm(yes):
            site_rm_res = []
            if site_rm_reqs:
                site_rm_res = self.central.batch_request(site_rm_reqs)
                if not all([r.ok for r in site_rm_res]):
                    err_console.print("[bright_red]\u26a0[/]  Some site remove requests failed, Aborting...")  # \u26a0 is :warning: need clean_console to prevent MAC from being evaluated as :cd: emoji
                    return site_rm_res
            batch_res = self.central.batch_request(batch_reqs)
            self.device_move_cache_update(batch_res, serials_by_site=serials_by_site, serials_by_group=serials_by_group)  # We don't store device labels in cache.  AP response does not include labels

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
            self.econsole.print(f"[dark_orange3]:warning:[/]  Import includes {len(not_in_cache)} group{'s' if len(not_in_cache) > 1 else ''} that do [red bold]not exist[/] according to local group cache.\n:arrows_clockwise: [bright_green]Updating[/] local [cyan]group[/] cache.")
            _ = self.central.request(self.cache.refresh_group_db)  # This updates cli.cache.groups_by_name

        # notify and remove any groups that don't exist after cache update
        cache_by_name: Dict[str, CacheGroup] = {name: self.cache.groups_by_name.get(name) for name in names_from_import}
        not_in_central = [name for name, data in cache_by_name.items() if data is None]
        if not_in_central:
            self.econsole.print(f"[dark_orange3]:warning:[/]  [red]Skipping[/] {utils.color(not_in_central, 'red')} [italic]group{'s do' if len(not_in_central) > 1 else ' does'} not exist in Central.[/]")

        groups: List[CacheGroup] = [g for g in cache_by_name.values() if g is not None]
        reqs = [self.central.BatchRequest(self.central.delete_group, g.name) for g in groups]

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
        print(_msg)

        if len(reqs) > 1 and not yes:
            print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

        if self.confirm(yes):
            resp = self.central.batch_request(reqs)
            self.display_results(resp, tablefmt="action")
            doc_ids = [g.doc_id for g, r in zip(groups, resp) if r.ok]
            if doc_ids:
                self.central.request(self.cache.update_group_db, data=doc_ids, remove=True)

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
            self.econsole.print(f"[dark_orange3]:warning:[/]  Import includes {utils.color(not_in_cache, 'red')}... {'do' if len(not_in_cache) > 1 else 'does'} [red bold]not exist[/] according to local label cache.  :arrows_clockwise: [bright_green]Updating local label cache[/].")
            _ = self.central.request(self.cache.refresh_label_db)  # This updates cli.cache.labels

        # notify and remove any labels that don't exist after cache update
        cache_by_name: Dict[str, CacheLabel] = {name: self.cache.labels_by_name.get(name) for name in names_from_import}
        not_in_central = [name for name, data in cache_by_name.items() if data is None]
        if not_in_central:
            self.econsole.print(f"[dark_orange3]:warning:[/]  [red]Skipping[/] {utils.color(not_in_central, 'red')} [italic]label{'s do' if len(not_in_central) > 1 else ' does'} not exist in Central.[/]")

        labels: List[CacheLabel] = [label for label in cache_by_name.values() if label is not None]
        reqs = [self.central.BatchRequest(self.central.delete_label, g.id) for g in labels]

        if len(labels) == 1:
            pre = ''
            pad = 0
            sep = ", "
        else:
            pre = sep = '\n'
            pad = 4

        label_msg = f'{pre}{utils.color([g.name for g in labels], "cyan", pad_len=pad, sep=sep)}'
        _msg = f"[bright_red]Delet{'e' if not yes else 'ing'}[/] {'label ' if len(labels) == 1 else f'{len(reqs)} labels:'}{label_msg}"
        print(_msg)

        if len(reqs) > 1 and not yes:
            print(f"\n[italic dark_olive_green2]{len(reqs)} API calls will be performed[/]")

        if self.confirm(yes):
            resp = self.central.batch_request(reqs)
            self.display_results(resp, tablefmt="action")
            doc_ids = [g.doc_id for g, r in zip(labels, resp) if r.ok]
            if doc_ids:
                self.central.request(self.cache.update_label_db, data=doc_ids, remove=True)

    def show_archive_results(self, arch_resp: List[Response]) -> None:
        def summarize_arch_res(arch_resp: List[Response]) -> None:
            for res in arch_resp:
                caption = res.output.get("message")
                action = res.url.name
                if res.get("succeeded_devices"):
                    title = f"Devices successfully {action}d."
                    data = [utils.strip_none(d) for d in res.get("succeeded_devices", [])]
                    self.display_results(data=data, title=title, caption=caption)
                if res.get("failed_devices"):
                    title = f"Devices that [bright_red]failed[/] to {action}."
                    data = [utils.strip_none(d) for d in res.get("failed_devices", [])]
                    self.display_results(data=data, title=title, caption=caption)

        if all([r.ok for r in arch_resp[0:2]]) and all([not r.get("failed_devices") for r in arch_resp[0:2]]):
            arch_resp[0].output = arch_resp[0].output.get("message")
            arch_resp[1].output =  f'  {arch_resp[1].output.get("message", "")}\n  Subscriptions successfully removed for {len(arch_resp[1].output.get("succeeded_devices", []))} devices.\n  \u2139  archive/unarchive flushes all subscriptions for a device.'
            self.display_results(arch_resp[0:2], tablefmt="action")
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
                cache_update_reqs += [br(self.cache.refresh_inv_db)]
        # Update cache remove deleted items
        if cache_update_reqs:
            _ = self.central.batch_request(cache_update_reqs)

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

            func = getattr(self.central, f"delete_{dev_type}")
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

            _del_resp: List[Response] = self.central.batch_request(del_reqs_try, continue_on_fail=True)

            if _try == 3:
                if not all([r.ok for r in _del_resp]):
                    self.econsole.print("\n[dark_orange]:warning:[/]  Retries exceeded. Devices still remain [bright_green]Up[/] in central and cannot be deleted.  This command can be re-ran once they have disconnected.")
                del_resp += _del_resp
            else:
                del_resp += [r for r in _del_resp if r.ok or isinstance(r.output, dict) and r.output.get("error_code", "") != "0007"]

            del_reqs_try = [del_reqs_try[idx] for idx, r in enumerate(_del_resp) if not r.ok and isinstance(r.output, dict) and r.output.get("error_code", "") == "0007"]
            if del_reqs_try:
                print(f"{len(del_reqs_try)} device{'s are' if len(del_reqs_try) > 1 else ' is'} still [bright_green]Up[/] in Central")
            else:
                break

        return del_resp

    def _get_inv_doc_ids(self, batch_resp: List[Response]) -> List[int] | None:
        if not batch_resp[1].url.name == "unarchive":
            return

        if isinstance(batch_resp[1].raw, dict) and "succeeded_devices" in batch_resp[1].raw:
            try:
                cache_inv_to_del = [self.cache.inventory_by_serial.get(d["serial_number"]) for d in batch_resp[1].raw["succeeded_devices"]]
                inv_doc_ids = [dev.doc_id for dev in cache_inv_to_del]
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

    def batch_delete_devices(self, data: List[Dict[str, Any]] | Dict[str, Any], *, ui_only: bool = False, cop_inv_only: bool = False, yes: bool = False, force: bool = False,) -> List[Response]:
        BR = BatchRequest
        confirm_msg = []

        try:
            serials_in = [dev["serial"] for dev in data]
            # serials_in = [dev["serial"].upper() for dev in data]
        except KeyError:
            self.exit("Missing required field: [cyan]serial[/].")

        # cache_devs: List[CacheDevice | CacheInvDevice | None] = [self.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False, retry=not cop_inv_only) for idx, d in enumerate(serials_in)]  # returns None if device not found in cache after update
        cache_devs: List[CacheDevice | CacheInvDevice | None] = []
        serial_updates: Dict[int, str] = {}
        for idx, d in enumerate(serials_in):
            this_dev = self.cache.get_dev_identifier(d, silent=True, include_inventory=True, exit_on_fail=False, retry=not cop_inv_only)
            if this_dev:
                serial_updates[idx] = this_dev.serial
            cache_devs += [this_dev]

        not_found_devs: List[str] = [s for s, c in zip(serials_in, cache_devs) if c is None]
        cache_found_devs: List[CacheDevice | CacheInvDevice] = [d for d in cache_devs if d is not None]
        cache_mon_devs: List[CacheDevice] = [d for d in cache_found_devs if d.db.name == "devices"]
        cache_inv_devs: List[CacheInvDevice] = [d for d in cache_found_devs if d.db.name == "inventory"]

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
            BR(self.central.archive_devices, valid_serials),
            BR(self.central.unarchive_devices, valid_serials),
        ]

        # build reqs to remove devs from monit views.  Down devs now, Up devs delayed to allow time to disc.
        mon_del_reqs = delayed_mon_del_reqs = []
        if not cop_inv_only:
            mon_del_reqs, delayed_mon_del_reqs = self._build_mon_del_reqs(cache_mon_devs)

        # cop only delete devices from GreenLake inventory
        cop_del_reqs = [] if not config.is_cop or not cache_inv_devs else [
            BR(self.central.cop_delete_device_from_inventory, [dev.serial for dev in cache_inv_devs])
        ]

        # warn about devices that were not found
        if (mon_del_reqs or delayed_mon_del_reqs or cop_del_reqs) and not_found_devs:
            not_in_inv_msg = utils.color(not_found_devs, color_str="cyan", pad_len=4, sep="\n")
            self.econsole.print(f"\n[dark_orange3]\u26a0[/]  The following provided devices were not found in the inventory.\n{not_in_inv_msg}", emoji=False)
            self.econsole.print("[grey42 italic]They will be skipped[/]\n")

        if ui_only:
            _total_reqs = len(mon_del_reqs)
        elif cop_inv_only:
            _total_reqs = len([*arch_reqs, *cop_del_reqs])
        else:
            _total_reqs = len([*arch_reqs, *cop_del_reqs, *mon_del_reqs, *delayed_mon_del_reqs])

        if not _total_reqs:
            if ui_only and delayed_mon_del_reqs:  # they select ui only, but devices are online
                self.exit(f"[cyan]--ui-only[/] provided, but only applies to devices that are offline, {len(delayed_mon_del_reqs)} device{'s are' if len(delayed_mon_del_reqs) > 1 else ' is'} online.  Nothing to do. Exiting...")
            self.exit("[italic]Everything is as it should be, nothing to do.  Exiting...[/]", code=0)

        sin_plural = f"[cyan]{len(cache_found_devs)}[/] devices" if len(cache_found_devs) > 1 else "device"
        confirm_msg += [f"\n[dark_orange3]\u26a0[/]  [red]Delet{'ing' if yes else 'e'}[/] the following {sin_plural}{'' if not ui_only else ' [grey42 italic]monitoring UI only[/]'}:"]
        if ui_only:
            confirmation_devs = utils.summarize_list([c.summary_text for c in cache_mon_devs if c.status.lower() == 'down'], max=40, color=None)
            if delayed_mon_del_reqs:  # using delayed_mon_reqs can be inaccurate re count when stacks are involved, as they could provide 4 switches, but if it's a stack that's 1 delete call.  hence the list comp below.
                self.econsole.print(
                    f"[cyan]{len([c for c in cache_mon_devs if c.status.lower() == 'up'])}[/] of the [cyan]{len(cache_mon_devs)}[/] found devices are currently [bright_green]online[/]. [grey42 italic]They will be skipped.[/]\n"
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
        self.console.print("\n".join(confirm_msg), emoji=False)
        batch_resp = []
        mon_doc_ids = []
        inv_doc_ids = []
        if self.confirm(yes):
            ...  # We abort if they don't confirm.

        # archive / unarchive (removes all subscriptions disassociates with Central in GLCP)
        # Also monitoring UI delete for any devices currently offline.
        batch_resp = self.central.batch_request([*arch_reqs, *mon_del_reqs])  # mon_del_reqs will be empty list if cop_inv_only
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
            batch_resp += self.central.batch_request(cop_del_reqs)

        if batch_resp:
            self.display_results(batch_resp, tablefmt="action")

        # Cache Updates
        if mon_doc_ids:
            self.central.request(self.cache.update_dev_db, mon_doc_ids, remove=True)
        if inv_doc_ids:
            self.central.request(self.cache.update_inv_db, inv_doc_ids, remove=True)

# Header rows used by CAS
#DEVICE NAME,SERIAL,MAC,GROUP,SITE,LABELS,LICENSE,ZONE,SWARM MODE,RF PROFILE,INSTALLATION TYPE,RADIO 0 MODE,RADIO 1 MODE,RADIO 2 MODE,DUAL 5GHZ MODE,SPLIT 5GHZ MODE,FLEX DUAL BAND,ANTENNA WIDTH,ALTITUDE,IP ADDRESS,SUBNET MASK,DEFAULT GATEWAY,DNS SERVER,DOMAIN NAME,TIMEZONE,AP1X USERNAME,AP1X PASSWORD

    # def batch_update_aps(self, data: List[dict]) -> List[Response]:
    #         data: List[CacheDevice] = [self.cache.get_dev_identifier(ap, dev_type="ap") for ap in data]

    #         disable_radios = None if not disable_radios else [r.value for r in disable_radios]
    #         enable_radios = None if not enable_radios else [r.value for r in enable_radios]
    #         flex_dual_exclude = None if not flex_dual_exclude else flex_dual_exclude.value
    #         antenna_width = None if not antenna_width else antenna_width.value

    #         radio_24_disable = None if not enable_radios or "2.4" not in enable_radios else False
    #         radio_5_disable = None if not enable_radios or "5" not in enable_radios else False
    #         radio_6_disable = None if not enable_radios or "6" not in enable_radios else False
    #         if disable_radios:
    #             for radio, var in zip(["2.4", "5", "6"], [radio_24_disable, radio_5_disable, radio_6_disable]):
    #                 if radio in disable_radios and var is not None:
    #                     cli.exit(f"Invalid combination you tried to enable and disable the {radio}Ghz radio")
    #                 # var = None if radio not in disable_radios else True  # doesn't work
    #             radio_24_disable = None if "2.4" not in disable_radios else True
    #             radio_5_disable = None if "5" not in disable_radios else True
    #             radio_6_disable = None if "6" not in disable_radios else True


    #         kwargs = {
    #             "hostname": hostname,
    #             "ip": ip,
    #             "mask": mask,
    #             "gateway": gateway,
    #             "dns": dns,
    #             "domain": domain,
    #             "radio_24_disable": radio_24_disable,
    #             "radio_5_disable": radio_5_disable,
    #             "radio_6_disable": radio_6_disable,
    #             "uplink_vlan": tagged_uplink_vlan,
    #             "flex_dual_exclude": flex_dual_exclude,
    #             "dynamic_ant_mode": antenna_width,
    #         }
    #         if ip and not all([mask, gateway, dns]):
    #             cli.exit("[cyan]mask[/], [cyan]gateway[/], and [cyan]--dns[/] are required when [cyan]--ip[/] is provided.")
    #         if len(data) > 1 and hostname or ip:
    #             cli.exit("Setting hostname/ip on multiple APs doesn't make sesnse")

    #         print(f"[bright_green]Updating[/]: {utils.summarize_list([ap.summary_text for ap in data], color=None, pad=10).lstrip()}")
    #         print("\n[green italic]With the following per-ap-settings[/]:")
    #         _ = [print(f"  {k}: {v}") for k, v in kwargs.items() if v is not None]
    #         skip_flex = [ap for ap in data if ap.model not in flex_dual_models]
    #         skip_width = [ap for ap in data if ap.model not in ["679"]]

    #         warnings = []
    #         if flex_dual_exclude is not None and skip_flex:
    #             warnings += [f"[yellow]:information:[/]  Flexible dual radio [red]will be ignored[/] for {len(skip_flex)} AP, as the setting doesn't apply to those models."]
    #         if antenna_width is not None and skip_width:
    #             warnings += [f"[yellow]:information:[/]  Dynamic antenna width [red]will be ignored[/] for {len(skip_width)} AP, as the setting doesn't apply to those models."]
    #         if warnings:
    #             warn_text = '\n'.join(warnings)
    #             print(f"\n{warn_text}")

    #         # determine if any effective changes after skips for settings on invalid AP models
    #         changes = 2
    #         if not list(filter(None, list(kwargs.values())[0:-2])):
    #             if not flex_dual_exclude or (flex_dual_exclude and not [ap for ap in data if ap not in skip_flex]):
    #                 changes -= 1
    #             if not antenna_width or (antenna_width and not [ap for ap in data if ap not in skip_width]):
    #                 changes -= 1
    #         if not changes:
    #             cli.exit("No valid updates provided for the selected AP models... Nothing to do.")

    #         self.confirm(yes)  # exits here if they abort
    #         batch_resp = cli.central.batch_request(
    #             [
    #                 BatchRequest(
    #                     cli.central.update_per_ap_settings,
    #                     ap.serial,
    #                     hostname=hostname,
    #                     ip=ip,
    #                     mask=mask,
    #                     gateway=gateway,
    #                     dns=dns,
    #                     domain=domain,
    #                     radio_24_disable=radio_24_disable,
    #                     radio_5_disable=radio_5_disable,
    #                     radio_6_disable=radio_6_disable,
    #                     uplink_vlan=tagged_uplink_vlan,
    #                     flex_dual_exclude=None if ap.model not in flex_dual_models else flex_dual_exclude,
    #                     dynamic_ant_mode=None if ap.model != "679" else antenna_width,
    #                 ) for ap in data
    #             ]
    #         )

    def help_default(self, default_txt: str) -> str:
        """Helper function that returns properly escaped default text, including rich color markup, for use in CLI help.

        Args:
            default_txt (str): The default value to display in the help text.  Do not include the word 'default: '

        Returns:
            str: Formatted default text.  i.e. [default: some value] (with color markups)
        """
        return f"[grey62]{escape(f'[default: {default_txt}]')}[/grey62]"

if __name__ == "__main__":
    pass
