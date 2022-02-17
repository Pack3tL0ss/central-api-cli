#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
import time
from typing import Dict, List, Literal, Union, Tuple
from pathlib import Path
from rich.console import Console
from rich import print
import json


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, utils, Cache, Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, utils, Cache, Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi


tty = utils.tty
CASE_SENSITIVE_TOKENS = ["R", "U"]
TableFormat = Literal["json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action"]
MsgType = Literal["initial", "previous", "forgot", "will_forget", "previous_will_forget"]
console = Console(emoji=False)


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
            return str(self)

        def __str__(self) -> str:
            if self.msg and hasattr(self, self.msg):
                return getattr(self, self.msg)
            else:
                return self.initial

        @property
        def initial(self):
            acct_clr = f"{typer.style(self.account, fg='cyan')}"
            return (
                f"{typer.style(f'Using Account: {acct_clr}.', fg='magenta')}  "
                f"{typer.style(f'Account setting is sticky.  ', fg='red', blink=True)}"
                f"\n  {acct_clr} {typer.style(f'will be used for subsequent commands until', fg='magenta')}"
                f"\n  {typer.style('--account <account name> or `-d` (revert to default). is used.', fg='magenta')}"
            )

        @property
        def previous(self):
            return (
                f"{typer.style(f'Using previously specified account: ', fg='magenta')}"
                f"{typer.style(self.account, fg='cyan', blink=True)}.  "
                f"\n{typer.style('Use `--account <account name>` to switch to another account.', fg='magenta')}"
                f"\n{typer.style('    or `-d` flag to revert to default account.', fg='magenta')}"
            )

        @property
        def forgot(self):
            return typer.style(
                "Forget option set for account, and expiration has passed.  reverting to default account", fg="magenta"
            )

        @property
        def will_forget(self):
            return typer.style(
                f"Forget options is configured, will revert to default account "
                f'{typer.style(f"{config.forget_account_after} mins", fg="cyan")}'
                f'{typer.style(" after last command.", fg="magenta")}',
                fg="magenta",
            )

        @property
        def previous_will_forget(self):
            return f"{self.previous}\n\n{self.will_forget}"

    def account_name_callback(self, ctx: typer.Context, account: str):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return account

        # -- // sticky last account messaging account is loaded in __init__ \\ --
        if account in ["central_info", "default"]:
            if config.sticky_account_file.is_file():
                last_account, last_cmd_ts = config.sticky_account_file.read_text().split("\n")
                last_cmd_ts = float(last_cmd_ts)

                # last account messaging
                if config.forget:
                    if time.time() > last_cmd_ts + (config.forget * 60):
                        # config.sticky_account_file.unlink(missing_ok=True)
                        typer.echo(self.AcctMsg(msg="forgot"))
                    else:
                        account = last_account
                        typer.echo(self.AcctMsg(account, msg="previous_will_forget"))
                else:
                    account = last_account
                    typer.echo(self.AcctMsg(account, msg="previous"))
        else:
            if account in config.data:
                # config.sticky_account_file.parent.mkdir(exist_ok=True)
                # config.sticky_account_file.write_text(f"{account}\n{round(time.time(), 2)}")
                typer.echo(self.AcctMsg(account))

        if config.valid:
            # config.account = self.account = account
            # self.central = CentralApi(account)
            # self.cache = Cache(self.central)
            return account
        else:
            typer.echo(
                f"{typer.style('ERROR:', fg=typer.colors.RED)} "
                f"The specified account: '{config.account}' is not defined in the config @\n"
                f"{config.file}\n\n"
            )

            if config.defined_accounts:
                typer.echo(
                    f"The following accounts are defined {', '.join(config.defined_accounts)}\n"
                    f"The default account 'central_info' is used if no account is specified via --account flag.\n"
                    f"or the ARUBACLI_ACCOUNT environment variable.\n"
                )
            else:
                if not config.data:
                    # TODO prompt user for details
                    typer.secho("Configuration doesn't exist", fg="red")
                else:
                    typer.secho("No accounts defined in config", fg="red")

            if account not in ["central_info", "default"]:
                if "central_info" not in config.data and "default" not in config.data:
                    typer.echo(
                        f"{typer.style('WARNING:', fg='yellow')} "
                        f"'central_info' is not defined in the config.  This is the default when not overridden by\n"
                        f"--account parameter or ARUBACLI_ACCOUNT environment variable."
                    )

            raise typer.Exit(code=1)

    @staticmethod
    def default_callback(ctx: typer.Context, default: bool):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return

        if default and config.sticky_account_file.is_file():
            typer.secho("Using default central account", fg="bright_green")
            config.sticky_account_file.unlink()
            return default

    @staticmethod
    def send_cmds_node_callback(ctx: typer.Context, commands: Union[str, Tuple[str]]):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return

        # utils.json_print(ctx.__dict__)
        # utils.json_print(ctx.parent.__dict__)
        # utils.json_print(locals())
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

    # not used at the moment but could be used to allow unambiguous partial tokens
    @staticmethod
    def normalize_tokens(token: str) -> str:
        return token.lower() if token not in CASE_SENSITIVE_TOKENS else token

    # DEPRECATED
    def dev_completion(
        self,
        ctx: typer.Context,
        args: List[str],
        incomplete: str,
    ) -> str:
        # devs = cli.cache.devices
        # _completion = [dev["name"] for dev in devs if incomplete.lower() in dev["name"].lower()]
        # _completion += [dev["serial"] for dev in devs if incomplete.lower() in dev["serial"].lower()]
        # _completion += [dev["mac"] for dev in devs if utils.Mac(incomplete).cols.lower() in dev["mac"].lower()]
        # print(args)
        # ["site", "group"]
        # return [k for k in [*_completion, "site", "group"] if incomplete in k]
        return self.cache.completion(incomplete, cache="dev")

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
            if Path().cwd() != Path.joinpath(config.outdir / outfile):
                if Path.joinpath(outfile.parent.resolve() / ".git").is_dir():
                    typer.secho(
                        "It looks like you are in the root of a git repo dir.\n"
                        "Exporting to out subdir."
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
        pad: int = None,
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

            if sort_by and all(isinstance(d, dict) for d in data):
                if sort_by not in data[0] and sort_by.replace("_", " ") in data[0]:
                    sort_by = sort_by.replace("_", " ")

                if not all([True if sort_by in d else False for d in data]):
                    print(f"[dark_orange3]Warning: [cyan]{sort_by}[reset] does not appear to be a valid field")
                    print("Valid Fields:\n----------\n{}\n----------".format("\n".join(data[0].keys())))
                else:
                    try:
                        data = sorted(data, key=lambda d: d[sort_by])
                    except TypeError as e:
                        print(
                            f"[dark_orange3]Warning:[reset] Unable to sort by [cyan]{sort_by}.\n{e} "
                        )

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
                "set_width_cols": set_width_cols,
                "full_cols": full_cols,
                "fold_cols": fold_cols,
            }
            outdata = utils.output(**kwargs)

            if stash:
                config.last_command_file.write_text(
                    json.dumps({k: v for k, v in kwargs.items() if k != "config"})
                )

            typer.echo_via_pager(outdata) if pager and tty and len(outdata) > tty.rows else typer.echo(outdata)

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
        pad: int = None,
        exit_on_fail: bool = False,
        ok_status: Union[int, List[int], Dict[int, str]] = None,
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
                Valid Values: "json", "yaml", "csv", "rich", "simple", "tabulate", "raw", "action"
                Where "raw" is unformatted raw response and "action" is formatted for POST|PATCH etc.
                where the result is a simple success/error.
            title: (str, optional): Title of output table.
                Only applies to "rich" tablefmt. Defaults to None.
            caption: (str, optional): Caption displayed at bottome of table.
                Only applies to "rich" tablefmt. Defaults to None.
            pager (bool, optional): Page Output / or not. Defaults to True.
            outfile (Path, optional): path/file of output file. Defaults to None.
            sort_by (Union[str, List[str], None] optional): column or columns to sort output on.
            reverse (bool, optional): reverse the output.
            stash (bool, optional): stash (cache) the output of the command.  The CLI can re-display with
                show last.  Default: True
            ok_status (Union[int, List[int], Tuple[int, str], List[Tuple[int, str]]], optional): By default
                responses with status_code 2xx are considered OK and are rendered as green by
                Output class.  provide int or list of int to override additional status_codes that
                should also be rendered as success/green.  provide a dict with {int: str, ...}
                where string can be any color supported by Output class or "neutral" "success" "fail"
                where neutral is no formatting, and success / fail will use the default green / red respectively.
            set_width_cols (Dict[str: Dict[str, int]]): Passed to output function defines cols with min/max width
                example: {'details': {'min': 10, 'max': 30}, 'device': {'min': 5, 'max': 15}}
            full_cols (list): columns to ensure are displayed at full length (no wrap no truncate)
            cleaner (callable, optional): The Cleaner function to use.
        """
        # TODO remove ok_status, and handle in CentralAPI method (set resp.ok = True)
        if pad:
            log.error("Deprecated pad parameter referenced in display_results", show=True)

        if resp is not None:
            resp = utils.listify(resp)

            # update caption with rate limit
            if resp[-1].rl:
                rl_str = f"[italic dark_olive_green2]{resp[-1].rl}".lstrip()
                caption = f"{caption} {rl_str}" if caption else rl_str

            for idx, r in enumerate(resp):
                # Multi request url line
                m_colors = {
                    "DELETE": "red",
                    "GET": "bright_green",
                    "PATH": "dark_orange3",
                }
                fg = "bright_green" if r else "red"
                if len(resp) > 1:
                    _url = r.url if not hasattr(r.url, "raw_path_qs") else r.url.path
                    # typer.secho(f"Request {idx + 1} [{r.method}: {_url}] Response:", fg="cyan")
                    m_color = m_colors.get(r.method, "reset")
                    print(
                        f"Request {idx + 1} [[{m_color}]{r.method}[reset]: "
                        f"[cyan]{_url}[/cyan]]\n [fg]Response[reset]:"
                    )
                if self.raw_out:
                    tablefmt = "raw"

                if not r or tablefmt in ["action", "raw"]:

                    if tablefmt == "raw":
                        # dots = f"[{fg}]{'.' * 16}[/{fg}]"
                        status_code = f"[{fg}]status code: {r.status}[/{fg}]"
                        print(r.url)
                        print(status_code)
                        if not r.ok:
                            print(r.error)
                        # print(f"{dots}\n{status_code}\n{dots}")
                        print("[bold cyan]Unformatted response from Aruba Central API GW[/bold cyan]")
                        print(r.raw)

                        if outfile:
                            self.write_file(outfile, r.raw)

                    else:
                        # typer.secho(str(r), fg=fg)
                        print(f"[{fg}]{r}")

                    if idx + 1 == len(resp):
                        console.print(f"\n{rl_str}")

                else:
                    self._display_results(
                        r.output,
                        tablefmt=tablefmt,
                        title=title,
                        caption=caption,
                        pager=pager,
                        outfile=outfile,
                        sort_by=sort_by,
                        reverse=reverse,
                        pad=pad,
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
                print("DEBUG error code return")
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
                pad=pad,
                set_width_cols=set_width_cols,
                full_cols=full_cols,
                fold_cols=fold_cols,
                cleaner=cleaner,
                **cleaner_kwargs
            )


if __name__ == "__main__":
    pass
