#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
from typing import List, Literal, Union, Tuple, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich import print
import json
import pkg_resources
import os
import pendulum
from datetime import datetime
import time

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
from centralcli.cache import CentralObject


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
        self.reqs: List[BatchRequest] = mv_reqs or []
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
                key = req.kwargs["group_name"]  # NEXT-MAJOR this needs to be changed to group once preprov method on central.py updated to be consistent

            serials = req.kwargs["serial_nums"]
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
        self._confirm = Confirm(prompt="\nProceed?", console=self.econsole,)

    def confirm(self, yes: bool = False, *, abort: bool = True) -> bool:
        result = yes or self._confirm()
        if not result and abort:
            self.econsole.print("[red]Aborted[/]")
            self.exit(code=0)

        return result

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

        try:
            current = pkg_resources.get_distribution('centralcli').version
        except pkg_resources.DistributionNotFound:
            current = "0.0.0  !! Unable to gather version"
        resp = self.central.request(self.central.get, "https://pypi.org/pypi/centralcli/json")
        if not resp:
            print(current)
        else:
            major = max([int(str(k).split(".")[0]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2])
            minor = max([int(str(k).split(".")[1]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2 and int(str(k).split(".")[0]) == major])
            patch = max([int(str(k).split(".")[2]) for k in resp.output["releases"].keys() if "a" not in k and k.count(".") == 2 and int(str(k).split(".")[0]) == major and int(str(k).split(".")[1]) == minor])
            latest = f'{major}.{minor}.{patch}'
            # latest = max(resp.output["releases"])
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

    @staticmethod
    def write_file(outfile: Path, outdata: str) -> None:
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

            print(f"\n[cyan]Writing output to {outfile}... ", end="")

            out_msg = None
            try:
                if isinstance(outdata, (dict, list)):
                    outdata = json.dumps(outdata, indent=4)
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
        """
        console = Console(emoji=emoji)
        if code != 0:
            msg = f"\u26a0  {msg}" if msg else msg  # \u26a0 = ⚠ / :warning:

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
                    type_ = str
                    for d in data:
                        if d[sort_by] is not None:
                            type_ = type(d[sort_by])
                            break
                    data = sorted(data, key=lambda d: d[sort_by] if d[sort_by] is not None and d[sort_by] != "-" else 0 if type_ in [int, DateTime] else "")
                except TypeError as e:
                    sort_msg = [f":warning:  Unable to sort by [cyan]{sort_by}.\n   {e.__class__.__name__}: {e} "]

            if sort_msg:
                _caption = "\n".join([f"  {m}" for m in sort_msg])
                _caption = _caption if tablefmt != "rich" else render.rich_capture(_caption, emoji=True)
                if caption:
                    c = caption.splitlines()
                    c.insert(-1, _caption)
                    caption = "\n".join(c)
                else:
                    caption = _caption

        return data if not reverse else data[::-1], caption

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
        exit_on_fail: bool = False,  # TODO make default True so failed calls return a failed return code to the shell.  Need to validate everywhere it needs to be set to False
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
            set_width_cols (Dict[str: Dict[str, int]]): Passed to output function defines cols with min/max width
                example: {'details': {'min': 10, 'max': 30}, 'device': {'min': 5, 'max': 15}}.  Applies to tablefmt=rich.
            full_cols (list): columns to ensure are displayed at full length (no wrap no truncate). Applies to tablfmt=rich. Defaults to [].
            fold_cols (Union[List[str], str], optional): columns that will be folded (wrapped within the same column). Applies to tablfmt=rich. Defaults to [].
            cleaner (callable, optional): The Cleaner function to use.
        """
        if isinstance(caption, list):
            caption = "\n  ".join(caption)
        if resp is not None:
            resp = utils.listify(resp)

            if self.raw_out:
                tablefmt = "raw"

            # update caption with rate limit
            try:
                last_rl = sorted(resp, key=lambda r: r.rl.remain_day)
                if last_rl:
                    rl_str = f"[reset][italic dark_olive_green2]{last_rl[0].rl}[/]".lstrip()
                    caption = f"{caption}\n  {rl_str}" if caption else f"  {rl_str}"
            except Exception as e:
                rl_str = ""
                log.error(f"Exception when trying to determine last rate-limit str for caption {e.__class__.__name__}")

            caption = caption or ""
            if log.caption:  # rich table is printed with emoji=False need to manually swap the emoji
                # TODO see if table has option to only do emoji in caption
                _log_caption = log.caption.replace(":warning:", "\u26a0").replace(":information:", "\u2139")
                if len(resp) > 1 and ":warning:" in log.caption:
                    caption = f'{caption}\n[bright_red]  !!! Partial command failure !!!\n{_log_caption}[/]'
                else:
                    caption = f'{caption}\n{_log_caption}'

            for idx, r in enumerate(resp):
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

                if config.capture_raw:
                    with clean_console.status("Capturing raw response"):
                        raw = r.raw if r.url.path in r.raw else {r.url.path: r.raw}
                        with config.capture_file.open("a") as f:
                            f.write(json.dumps(raw))

                # Nothing returned in response payload
                if not r.output:
                    print(f"  Status Code: [{fg}]{r.status}[/]")
                    print("  :warning: Empty Response.  This may be normal.")

                    if log.caption:
                        print(log.caption)  # TODO verify this doesn't cause duplicate print, clean up so caption is only printed for non rich in one place.
                elif not cleaner and r.url and r.url.path == "/caasapi/v1/exec/cmd":
                    cleaner = clean.parse_caas_response

                if not r or tablefmt in ["action", "raw", "clean"]:

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
                            if pager:
                                with plain_console.pager:
                                    plain_console.print(r.raw)
                            else:
                                plain_console.print(r.raw)

                        if outfile:
                            self.write_file(outfile, r.raw if tablefmt != "clean" else r.output)

                    # prints the Response objects __str__ method which includes status_code
                    # and formatted contents of any payload. example below
                    # status code: 201
                    # Success
                    else:
                        # TODO make __rich__ renderable method in Response object with markups
                        # clean_console.print(str(r).replace("failed:", "[red]failed[/]:").replace("success:", "[bright_green]success[/]:"))
                        clean_console.print(r)
                        # console.print(f"[{fg}]{r}[/]")

                    if idx + 1 == len(resp):
                        if caption:
                            print(caption.replace(rl_str, ""))
                        clean_console.print(f"\n{rl_str}")

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
                        set_width_cols=set_width_cols,
                        full_cols=full_cols,
                        fold_cols=fold_cols,
                        cleaner=cleaner,
                        **cleaner_kwargs
                    )

            # TODO make elegant caas send-cmds uses this logic
            if cleaner and cleaner.__name__ == "parse_caas_response":
                print(caption)

            if exit_on_fail and not all([r.ok for r in resp]):
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

    def past_to_start(self, past: str = None,) -> pendulum.DateTime | None:
        """Common helper to parse --past option and return pendulum.DateTime object representing start time

        Args:
            past (str, optional): Calculates start time from str like 3M where M=Months, w=weeks, d=days, h=hours, m=minutes. Defaults to None.

        Returns:
            pendulum.DateTime | None: returns DateTime object in UTC or None if past argument was None.

        Raises:
            typer.Exit: If past str has value but is invalid.
        """
        if not past:
            return

        past = past.replace(" ", "")
        now: pendulum.DateTime = pendulum.now(tz="UTC")
        try:
            if past.endswith("d"):
                start = now.subtract(days=int(past.rstrip("d")))
            elif past.endswith("h"):
                start = now.subtract(hours=int(past.rstrip("h")))
            elif past.endswith("m"):
                start = now.subtract(minutes=int(past.rstrip("m")))
            elif past.endswith("M"):
                start = now.subtract(months=int(past.rstrip("M")))
            elif past.endswith("w"):
                start = now.subtract(weeks=int(past.rstrip("w")))
            else:
                self.exit(
                    '\n'.join(
                        [
                            f"[cyan]--past[/] [bright_red]{past}[/] Does not appear to be valid. Specifically timeframe suffix [bright_red]{list(past)[-1]}[/] is not a recognized specifier.",
                            "Valid suffixes: [cyan]M[/]=Months, [cyan]w[/]=weeks, [cyan]d[/]=days, [cyan]h[/]=hours, [cyan]m[/]=minutes"
                        ]
                    )
                )
        except ValueError:
            self.exit(f"[cyan]--past[/] [bright_red]{past}[/] Does not appear to be valid")

        return start

    def verify_time_range(self, start: datetime | pendulum.DateTime | None, end: datetime | pendulum.DateTime = None, past: str = None, max_days: int = 90) -> pendulum.DateTime | None:
        if end and past:
            log.warning("[cyan]--end[/] flag ignored, providing [cyan]--past[/] implies end is now.", caption=True,)
            end = None

        if start and past:
            log.warning(f"[cyan]--start[/] flag ignored, providing [cyan]--past[/] implies end is now - {past}", caption=True,)

        if past:
            start = self.past_to_start(past=past)

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
                return self.past_to_start("2_159h"), end  # 89 days and 23 hours to avoid issue with API endpoint

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
            md5.update(string.encode("utf-8"))
        else:
            raise ValueError("One of file or string argument is required")

        return md5.hexdigest()


    def _get_import_file(self, import_file: Path, import_type: Literal["devices", "sites", "groups", "labels", "macs", "mpsk"] = None, text_ok: bool = False,) -> List[Dict[str, Any]]:
        data = None
        if import_file is not None:
            data = config.get_file_data(import_file, text_ok=text_ok)

        if not data:
            self.exit(f":warning:  [bright_red]ERROR[/] {import_file.name} not found or empty.")

        if import_type and import_type in data:
            data = data[import_type]

        if data:
            if isinstance(data, dict):  # accept yaml/json keyed by serial #
                if utils.is_serial(list(data.keys())[0]):
                    data = [{"serial": k, **v} for k, v in data.items()]
            if isinstance(data, list) and text_ok:
                if import_type == "devices" and all(utils.is_serial(s) for s in data):
                    data = [{"serial": s} for s in data]
                if import_type == "labels":
                    data = [{"name": label} for label in data]

        # They can mark items as ignore or retired (True).  Those devices/items are filtered out.
        data = [d for d in data if not d.get("retired", d.get("ignore"))]

        return data


    def _check_update_dev_db(self, device: CentralObject) -> CentralObject:
        if self.central.get_all_devices not in self.cache.updated:  # TODO Use cli.cache.responses.  have check_fresh bypass API call if cli.cache.responses.dev has value
            _ = self.central.request(self.cache.update_dev_db, dev_type=device.type)
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
                group = req.kwargs["site_id"]
                serials = req.kwargs["serial_nums"]
                out = utils.update_dict(out, key=group, value=serials)

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
                serials = req.kwargs["serial_nums"]
                out = utils.update_dict(out, key=group, value=serials)

            return out


    def _check_group(self, cache_devs: List[CentralObject], import_data: dict, cx_retain_config: bool = False, cx_retain_force: bool = None) -> GroupMoves:
        pregroup_mv_reqs, pregroup_mv_msgs = {}, {}
        group_mv_reqs, group_mv_msgs = {}, {}
        group_mv_cx_retain_reqs, group_mv_cx_retain_msgs = {}, {}
        _skip = False
        for cache_dev, mv_data in zip(cache_devs, import_data):
            has_connected = True if cache_dev.get("status") else False
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
                            clean_console.print(f"\u2139  [dark_orange3]Ignoring[/] group move for {cache_dev.rich_help_text}. [italic grey42](already in group [magenta]{to_group}[/magenta])[reset].")
                            _skip = True

                    # Determine if device is in inventory only determines use of pre-provision group vs move to group
                    if not has_connected:
                        req_dict = pregroup_mv_reqs
                        msg_dict = pregroup_mv_msgs
                        if retain_config:
                            err_console.print(f'[bright_red]\u26a0[/]  {cache_dev.rich_help_text} Group assignment is being ignored.')  # \u26a0 is :warning: need clean_console to prevent MAC from being evaluated as :cd: emoji
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
            pre_reqs = [self.central.BatchRequest(self.central.preprovision_device_to_group, group_name=k, serial_nums=v) for k, v in pregroup_mv_reqs.items()]
        if group_mv_reqs:
            mv_reqs = [self.central.BatchRequest(self.central.move_devices_to_group, group=k, serial_nums=v) for k, v in group_mv_reqs.items()]
        if group_mv_cx_retain_reqs:
            mv_retain_reqs = [self.central.BatchRequest(self.central.move_devices_to_group, group=k, serial_nums=v, cx_retain_config=True) for k, v in group_mv_cx_retain_reqs.items()]

        return self.GroupMoves(
            pregroup_mv_reqs=pre_reqs,
            pregroup_mv_msgs=pregroup_mv_msgs,
            group_mv_reqs=mv_reqs,
            group_mv_msgs=group_mv_msgs,
            group_mv_cx_retain_reqs=mv_retain_reqs,
            group_mv_cx_retain_msgs=group_mv_cx_retain_msgs,
            cache_devs=cache_devs
        )


    def _check_site(self, cache_devs: List[CentralObject], import_data: dict) -> SiteMoves:
        site_rm_reqs, site_rm_msgs = {}, {}
        site_mv_reqs, site_mv_msgs = {}, {}
        for cache_dev, mv_data in zip(cache_devs, import_data):
            has_connected = True if cache_dev.get("status") else False
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
                            clean_console.print(f"\u2139  [dark_orange3]Ignoring[/] site move for {cache_dev.rich_help_text}. [italic grey42](already in site [magenta]{to_site.name}[/magenta])[reset]")
                    elif not has_connected:
                        if idx == 0:
                            cache_dev = self._check_update_dev_db(cache_dev)
                        else:
                            clean_console.print(f"\u2139  [dark_orange3]Ignoring[/] site move for {cache_dev.rich_help_text}. [italic grey42](Device must connect to Central before site can be assigned)[reset]")
                    elif idx != 0:
                        site_mv_reqs = utils.update_dict(site_mv_reqs, key=f'{to_site.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                        site_mv_msgs = utils.update_dict(site_mv_msgs, key=to_site.name, value=cache_dev.rich_help_text)

                    if now_site:
                        now_site = self.cache.get_site_identifier(now_site)
                        if idx != 0 and now_site.name != to_site.name:  # need to remove from current site
                            clean_console.print(f'{cache_dev.rich_help_text} will be removed from site [red]{now_site.name}[/] to facilitate move to site [bright_green]{to_site.name}[/]')
                            site_rm_reqs = utils.update_dict(site_rm_reqs, key=f'{now_site.id}~|~{cache_dev.generic_type}', value=cache_dev.serial)
                            site_rm_msgs = utils.update_dict(site_rm_msgs, key=now_site.name, value=cache_dev.rich_help_text)

        rm_reqs = []
        if site_rm_reqs:
            for k, v in site_rm_reqs.items():
                site_id, dev_type = k.split("~|~")
                rm_reqs += [self.central.BatchRequest(self.central.remove_devices_from_site, site_id=int(site_id), serial_nums=v, device_type=dev_type)]

        mv_reqs = []
        if site_mv_reqs:
            for k, v in site_mv_reqs.items():
                site_id, dev_type = k.split("~|~")
                mv_reqs += [self.central.BatchRequest(self.central.move_devices_to_site, site_id=int(site_id), serial_nums=v, device_type=dev_type)]

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
                batch_reqs += [self.central.BatchRequest(self.central.assign_label_to_devices, label_id=int(label_id), device_type=dev_type, serial_nums=v)]

        return MoveData(mv_reqs=batch_reqs, mv_msgs=label_ass_msgs, action_word="assigned", move_type="label")

    def device_move_cache_update(
            self,
            mv_resp: List[Response],
            serials_by_site: Dict[str: List[str]] = None,
            serials_by_group: Dict[str: List[str]] = None,
        ) -> None:
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
            if move_type == "site":
                site_success_serials = [s["device_id"] for s in r.raw["success"] if s["device_id"] in serials]  # if .... in serials stips out stack_id, success will have all member serials + the stack_id
                cache_by_serial = {serial: {**cache_by_serial[serial], "site": name} for serial in serials if serial in site_success_serials}
            if move_type == "group":  # All or none here as far as the rresponse.
                if r.ok:
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

        dev_idens = [d.get("serial", d.get("mac", d.get("name", "INVALID"))) for d in devices]
        if "INVALID" in dev_idens:
            self.exit(f'missing required field ({utils.color(["serial", "mac", "name"])}) for {dev_idens.index("INVALID") + 1} device in import file.')
        if len(set(dev_idens)) < len(dev_idens):  # Detect and filter out any duplicate entries
            filtered_count = len(dev_idens) - len(set(dev_idens))
            dev_idens = set(dev_idens)
            err_console.print(f"[dark_orange3]:warning:[/]  Filtering [cyan]{filtered_count}[/] duplicate device{'s' if filtered_count > 1 else ''} from update.")

        # conductor_only option, as group move will move all associated devices when device is part of a swarm or stack
        cache_devs: List[CentralObject] = [self.cache.get_dev_identifier(d, include_inventory=True, conductor_only=True) for d in dev_idens]

        site_rm_reqs, batch_reqs, confirm_msgs = [], [], [""]
        if do_site:
            site_ops = self._check_site(cache_devs=cache_devs, import_data=devices)
            batch_reqs += site_ops.move.reqs
            site_rm_reqs += site_ops.remove.reqs
            confirm_msgs += [str(site_ops)]
        if do_group:
            group_ops = self._check_group(cache_devs=cache_devs, import_data=devices, cx_retain_config=cx_retain_config, cx_retain_force=cx_retain_force)
            batch_reqs += group_ops.reqs
            confirm_msgs += [str(group_ops)]
        if do_label:
            label_ops = self._check_label(cache_devs=cache_devs, import_data=devices)
            batch_reqs += label_ops.reqs
            confirm_msgs += [str(label_ops)]

        _tot_req = (0 if not do_site else len(site_ops.remove)) + len(batch_reqs)
        if not _tot_req:
            self.exit("[italic dark_olive_green2]Nothing to do[/]", code=0)
        if _tot_req > 1:
            confirm_msgs += [f'\n{_tot_req} API calls will be performed.']

        clean_console.print("\n".join(confirm_msgs))
        if yes or typer.confirm("\nProceed?", abort=True):
            site_rm_res = []
            if site_rm_reqs:
                site_rm_res = self.central.batch_request(site_rm_reqs)
                if not all([r.ok for r in site_rm_res]):
                    err_console.print("[bright_red]\u26a0[/]  Some site remove requests failed, Aborting...")  # \u26a0 is :warning: need clean_console to prevent MAC from being evaluated as :cd: emoji
                    return site_rm_res
            batch_res = self.central.batch_request(batch_reqs)
            self.device_move_cache_update(batch_res, serials_by_site=site_ops.serials_by_site_id, serials_by_group=group_ops.serials_by_group)  # We don't store device labels in cache.  AP response does not include labels

            return [*site_rm_res, *batch_res]

if __name__ == "__main__":
    pass
