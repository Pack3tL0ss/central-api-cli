#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import sys
import time
from typing import Dict, List, Literal, Union
from pathlib import Path
from rich.console import Console


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
FormatType = Literal["json", "yaml", "csv", "rich", "simple"]
MsgType = Literal["initial", "previous", "forgot", "will_forget", "previous_will_forget"]
console = Console()


class CLICommon:
    def __init__(self, account: str = "default", cache: Cache = None, central: CentralApi = None):
        self.account = account
        self.cache = cache
        self.central = central

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
                        f"'central_info' is not defined in the config.  This is the default when not overriden by\n"
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
    def debug_callback(ctx: typer.Context, debug: bool):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return False

        if debug:
            log.DEBUG = config.debug = debug
            return debug

    # not used at the moment but could be used to allow unambiguous partial tokens
    @staticmethod
    def normalize_tokens(token: str) -> str:
        return token.lower() if token not in CASE_SENSITIVE_TOKENS else token

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
    ) -> FormatType:
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
    def _display_results(
        data: Union[List[dict], List[str], None] = None,
        tablefmt: str = "rich",
        title: str = None,
        caption: str = None,
        pager: bool = True,
        outfile: Path = None,
        sort_by: str = None,
        reverse: bool = False,
        pad: int = None,
        cleaner: callable = None,
        **cleaner_kwargs,
    ):
        if data:
            data = utils.listify(data)

            if cleaner:
                data = cleaner(data, **cleaner_kwargs)

            if sort_by and all(isinstance(d, dict) for d in data):
                if not all([True if sort_by in d else False for d in data]):
                    typer.echo(f"Invalid dataset for {sort_by} not all entries contain a {sort_by} key")
                    typer.secho("sort by is not implemented for all commands yet", fg="red")
                else:
                    data = sorted(data, key=lambda d: d[sort_by])

            if reverse:
                data = data[::-1]

            outdata = utils.output(
                data,
                tablefmt,
                title=title,
                caption=caption,
                account=None if config.account in ["central_info", "account"] else config.account,
                config=config,
            )
            typer.echo_via_pager(outdata) if pager and tty and len(outdata) > tty.rows else typer.echo(outdata)

            # -- // Output to file \\ --
            if outfile and outdata:
                if Path().cwd() != Path.joinpath(config.outdir / outfile):
                    if Path.joinpath(outfile.parent.resolve() / ".git").is_dir():
                        typer.secho(
                            "It looks like you are in the root of a git repo dir.\n"
                            "Exporting to out subdir."
                            )
                    config.outdir.mkdir(exist_ok=True)
                    outfile = config.outdir / outfile

                print(typer.style(f"\nWriting output to {outfile}... ", fg="cyan"), end="")
                outfile.write_text(outdata.file)  # typer.unstyle(outdata) also works
                typer.secho("Done", fg="green")

    def display_results(
        self,
        resp: Union[Response, List[Response]] = None,
        data: Union[List[dict], List[str], None] = None,
        tablefmt: str = "rich",
        title: str = None,
        caption: str = None,
        pager: bool = True,
        outfile: Path = None,
        sort_by: str = None,
        reverse: bool = None,
        pad: int = None,
        exit_on_fail: bool = False,
        ok_status: Union[int, List[int], Dict[int, str]] = None,
        cleaner: callable = None,
        **cleaner_kwargs,
    ) -> None:
        """Output Formatted API Response to display and optionally to file

        one of resp or data attribute is required

        Args:
            resp (Union[Response, List[Response], None], optional): API Response objects.
            data (Union[List[dict], List[str], None], optional): API Response output data.
            tablefmt (str, optional): Format of output. Defaults to "rich" (tabular).
            title: (str, optional): Title of output table.
                Only applies to "rich" tablefmt. Defaults to None.
            caption: (str, optional): Caption displayed at bottome of table.
                Only applies to "rich" tablefmt. Defaults to None.
            pager (bool, optional): Page Output / or not. Defaults to True.
            outfile (Path, optional): path/file of output file. Defaults to None.
            sort_by (Union[str, List[str], None] optional): column or columns to sort output on.
            reverse (bool, optional): reverse the output.
            ok_status (Union[int, List[int], Tuple[int, str], List[Tuple[int, str]]], optional): By default
                responses with status_code 2xx are considered OK and are rendered as green by
                Output class.  provide int or list of int to override additional status_codes that
                should also be rendered as success/green.  provide a dict with {int: str, ...}
                where string can be any color supported by Output class or "neutral" "success" "fail"
                where neutral is no formatting, and success / fail will use the default green / red respectively.
            cleaner (callable, optional): The Cleaner function to use.
        """
        # TODO remove ok_status, and handle in CentralAPI method (set resp.ok = True)
        if pad:
            log.warning("Depricated pad parameter referenced in display_results")

        pager = False if config.no_pager else pager

        if resp is not None:
            resp = utils.listify(resp)

            # update caption with rate limit
            if resp[-1].rl:
                rl_str = f"[italic dark_olive_green2]{resp[-1].rl}".lstrip()
                caption = f"{caption} {rl_str}" if caption else rl_str

            for idx, r in enumerate(resp):
                # Multi request resuest url line
                if len(resp) > 1:
                    _url = r.url if not hasattr(r.url, "path") else r.url.path
                    typer.secho(f"Request {idx + 1} [{r.method}: {_url}] Response:", fg="cyan")

                if not r or tablefmt == "action":
                    fg = "green" if r else "red"

                    typer.secho(str(r), fg=fg)

                    if idx + 1 == len(resp):
                        console.print(f"\n{rl_str}")

                    if not r and exit_on_fail:
                        raise typer.Exit(1)
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
                        cleaner=cleaner,
                        **cleaner_kwargs
                    )

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
                cleaner=cleaner,
                **cleaner_kwargs
            )


if __name__ == "__main__":
    pass
