#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import typer
import sys
from typing import List, Literal, Union, Tuple
from pathlib import Path
from rich.console import Console
from rich import print
import json
import pkg_resources
import os


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response, render, cleaner as clean
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response, render, cleaner as clean
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi
from centralcli.objects import DateTime, Encoder


tty = utils.tty
CASE_SENSITIVE_TOKENS = ["R", "U"]
TableFormat = Literal["json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action", "clean"]
MsgType = Literal["initial", "previous", "forgot", "will_forget", "previous_will_forget"]
console = Console(emoji=False)
err_console = Console(emoji=False, stderr=True)


class CLICommon:
    def __init__(self, account: str = "default", cache: Cache = None, central: CentralApi = None, raw_out: bool = False):
        self.account = account
        self.cache = cache
        self.central = central
        self.raw_out = raw_out

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
            return f'Using Account: [cyan]{self.account}[/] [italic]based on env var[/] [dark_green]ARUBACLI_ACCOUNT[/]'

        @property
        def initial(self):
            msg = (
                f'[magenta]Using Account:[/] [cyan]{self.account}[/].\n'
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
        if ctx.resilient_parsing:  # tab completion, return without validating
            return account

        account = account or config.default_account  # account only has value if --account flag is used.
        emoji_console = Console()

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
                            console.print(msg.previous_will_forget)
                            config.update_last_account_file(account, config.last_cmd_ts, True)
                        else:
                            emoji_console.print(msg.previous_short)

                else:
                    account = config.last_account
                    msg = self.AcctMsg(account)
                    if not config.last_account_msg_shown:
                        console.print(msg.previous)
                        config.update_last_account_file(account, config.last_cmd_ts, True)
                    else:
                        emoji_console.print(msg.previous_short)

        elif account in config.data:
            if account == os.environ.get("ARUBACLI_ACCOUNT", ""):
                msg = self.AcctMsg(account)
                console.print(msg.envvar)
            elif config.forget is not None and config.forget > 0:
                console.print(self.AcctMsg(account).initial)
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
                    console.print(f"[bright_green]The following accounts are defined[/] [cyan]{'[/], [cyan]'.join(config.defined_accounts)}[reset]\n")
                    if not _def_msg:
                        console.print(
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
    def exit(msg: str = None, code: int = 1) -> None:
        """Print msg text and exit.

        Prepends warning emoji to msg if code indicates an error.
        """
        if code != 0:
            msg = f":warning:  {msg}" if msg else msg

        if msg:
            print(msg)
        raise typer.Exit(code=code)

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
        if data:
            data = utils.listify(data)

            if cleaner and not self.raw_out:
                data = cleaner(data, **cleaner_kwargs)
                data = utils.listify(data)

            # TODO make separate function
            if sort_by and all(isinstance(d, dict) for d in data):
                if sort_by not in data[0] and sort_by.replace("_", " ") in data[0]:
                    sort_by = sort_by.replace("_", " ")

                sort_msg = None
                if not all([sort_by in d for d in data]):
                    sort_msg = [
                            f":warning:  [dark_orange3]Sort Error: [cyan]{sort_by}[reset] does not appear to be a valid field",
                            "Valid Fields: {}".format(", ".join(f'{k.replace(" ", "_")}' for k in data[0].keys()))
                    ]
                else:
                    try:
                        type_ = str
                        for d in data:
                            if d[sort_by] is not None:
                                type_ = type(d[sort_by])
                                break
                        data = sorted(data, key=lambda d: d[sort_by] if d[sort_by] != "-" else 0 or 0 if type_ == int else "")
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
            # End sort function

            if reverse:
                data = data[::-1]

            if self.raw_out and tablefmt in ["simple", "rich"]:
                tablefmt = "json"

            # TODO make sure "account" is not valid then remove from list below
            if config.account == "account":
                log.warning("DEV NOTE account is 'account'", show=True)

            kwargs = {
                "outdata": data,
                "tablefmt": tablefmt,
                "title": title,
                "caption": caption,
                "account": None if config.account in ["central_info", "default", "account"] else config.account,
                "config": config,
                "output_by_key": output_by_key,
                "set_width_cols": set_width_cols,
                "full_cols": full_cols,
                "fold_cols": fold_cols,
            }
            with console.status("Rendering Output..."):
                outdata = render.output(**kwargs)

            if stash:
                config.last_command_file.write_text(
                    json.dumps({k: v if not isinstance(v, DateTime) else v.epoch for k, v in kwargs.items() if k != "config"}, cls=Encoder)
                )

            typer.echo_via_pager(outdata) if pager and tty and len(outdata) > tty.rows else typer.echo(outdata)

            # TODO test speed of use normal console object.
            # rich pager may render faster, but need to modify render.output .. rich_output
            # if pager and tty and len(outdata) > tty.rows:
            #     with console.pager():
            #         console.print(outdata)
            # else:
            #     console.print(outdata)

            if "Limit:" not in outdata and caption is not None and cleaner and cleaner.__name__ != "parse_caas_response":
                print(caption)

            if outfile and outdata:
                self.write_file(outfile, outdata.file)
        else:
            log.warning(f"No data passed to _display_output {title} {caption}")

    def display_results(
        self,
        resp: Union[Response, List[Response]] = None,
        data: Union[List[dict], List[str], dict, None] = None,
        tablefmt: TableFormat = "rich",
        title: str = None,
        caption: str = None,
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
            title: (str, optional): Title of output table.
                Only applies to "rich" tablefmt. Defaults to None.
            caption: (str, optional): Caption displayed at bottom of table.
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
        if resp is not None:
            resp = utils.listify(resp)

            # update caption with rate limit
            try:
                last_rl = sorted(resp, key=lambda r: r.rl.remain_day)
                if last_rl:
                    rl_str = f"[reset][italic dark_olive_green2]{last_rl[0].rl}[/]".lstrip()
                    caption = f"{caption}\n  {rl_str}" if caption else f"  {rl_str}"
            except Exception as e:
                log.error(f"Exception when trying to determine last rate-limit str for caption {e.__class__.__name__}")

            caption = caption or ""
            if log.caption:  # TODO change caption to list of Tuples or dict or objects with loglevel so we can determine if :warning: should be prepended.  Or do it in the log
                if len(resp) > 1 and ":warning:" in log.caption:
                    caption = f'{caption}\n[bright_red]  !!! Partial command failure !!!\n{log.caption}[/]'
                else:
                    caption = f'{caption}\n{log.caption}'


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
                conditions = [len(resp) > 1, tablefmt in ["action", "raw", "clean"], r.ok and not r.output]
                if any(conditions):
                    _url = r.url if not hasattr(r.url, "path") else r.url.path
                    m_color = m_colors.get(r.method, "reset")
                    print(
                        f"Request {idx + 1} [[{m_color}]{r.method}[reset]: "
                        f"[cyan]{_url}[/cyan]]\n [fg]Response[reset]:"
                    )

                if self.raw_out:
                    tablefmt = "raw"

                # Nothing returned in response payload
                if not r.output:
                    print(f"  Status Code: [{fg}]{r.status}[/]")
                    print("  :warning: Empty Response.  This may be normal.")
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
                        console.print(f"[{fg}]{r}[/]")

                    if idx + 1 == len(resp):
                        if caption:
                            print(caption.replace(rl_str, ""))
                        console.print(f"\n{rl_str}")

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


if __name__ == "__main__":
    pass
