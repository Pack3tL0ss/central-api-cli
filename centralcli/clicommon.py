#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import typer
import time
import sys
# import json
from typing import List, Literal, Union
from pathlib import Path


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
FormatType = Literal["json", "yaml", "csv", "rich", "simple"]
MsgType = Literal["initial", "previous", "forgot", "will_forget", "previous_will_forget"]


class CLICommon:
    def __init__(self, account: str = "default"):
        self.account = account
        self.cache = None
        self.central = None

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

        # -- // sticky last account caching and messaging \\ --
        if account == "central_info":
            if config.sticky_account_file.is_file():
                last_account, last_cmd_ts = config.sticky_account_file.read_text().split("\n")
                last_cmd_ts = float(last_cmd_ts)

                # delete last_account file if they've configured forget_account_after
                if config.forget_account_after:
                    if time.time() > last_cmd_ts + (config.forget_account_after * 60):
                        config.sticky_account_file.unlink(missing_ok=True)
                        typer.echo(self.AcctMsg(msg="forgot"))
                    else:
                        account = last_account
                        typer.echo(self.AcctMsg(account, msg="previous_will_forget"))
                else:
                    account = last_account
                    typer.echo(self.AcctMsg(account, msg="previous"))
        else:
            if account in config.data:
                config.sticky_account_file.parent.mkdir(exist_ok=True)
                config.sticky_account_file.write_text(f"{account}\n{round(time.time(), 2)}")
                typer.echo(self.AcctMsg(account))

        if account in config.data:
            config.account = self.account = account
            self.central = CentralApi(account)
            self.cache = Cache(self.central)
            return account
        else:
            strip_keys = ["central_info", "ssl_verify", "token_store", "forget_account_after", "debug", "debugv", "limit"]
            typer.echo(
                f"{typer.style('ERROR:', fg=typer.colors.RED)} "
                f"The specified account: '{account}' is not defined in the config @\n"
                f"{config.file}\n\n"
            )

            _accounts = [k for k in config.data.keys() if k not in strip_keys]
            if _accounts:
                typer.echo(
                    f"The following accounts are defined {_accounts}\n"
                    f"The default account 'central_info' is used if no account is specified via --account flag.\n"
                    f"or the ARUBACLI_ACCOUNT environment variable.\n"
                )
            else:
                if not config.data:
                    # TODO prompt user for details
                    typer.secho("Configuration doesn't exist", fg="red")
                else:
                    typer.secho("No accounts defined in config", fg="red")

            if account != "central_info" and "central_info" not in config.data:
                typer.echo(
                    f"{typer.style('WARNING:', fg='yellow')} "
                    f"'central_info' is not defined in the config.  This is the default when not overriden by\n"
                    f"--account parameter or ARUBACLI_ACCOUNT environment variable."
                )

            raise typer.Exit(code=1)

    def default_callback(self, ctx: typer.Context, default: bool):
        if ctx.resilient_parsing:  # tab completion, return without validating
            return

        if default and config.sticky_account_file.is_file():
            typer.secho("Using default central account", fg="cyan")
            config.sticky_account_file.unlink()

    @staticmethod
    def debug_callback(debug: bool):
        if debug:
            log.DEBUG = config.debug = debug

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
                    typer.secho(f"Invalid dataset for {sort_by} not all entries contain a {sort_by} key")
                else:
                    data = sorted(data, key=lambda d: d[sort_by])

            if reverse:
                data = data[::-1]

            outdata = utils.output(data, tablefmt, title=title, caption=caption, config=config)
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
        cleaner: callable = None,
        exit_on_fail: bool = False,
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
            cleaner (callable, optional): The Cleaner function to use.
        """
        if pad:
            log.warning("Depricated pad parameter referenced in display_results")

        pager = False if config.no_pager else pager

        if resp is not None:
            resp = utils.listify(resp)

            data = []
            for idx, r in enumerate(resp):
                if len(resp) > 1:
                    typer.secho(f"Request {idx + 1} [{r.method}: {r.url.path}] Response:", fg="cyan")
                if not r or tablefmt == "action":
                    typer.secho(str(r), fg="green" if r else "red")
                    if not r and exit_on_fail:
                        raise typer.Exit(1)
                else:
                    # TODO add sort and reverse funcs
                    if sort_by is not None:
                        typer.secho("sort by is not implemented for all commands yet", fg="red")

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
