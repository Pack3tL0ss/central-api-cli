#!/usr/bin/env python3
#
# Author: Wade Wells github/Pack3tL0ss

from pathlib import Path
from typing import Any, List, Union
import yaml
import json
import tablib
import sys
import time

# try:
#     from icecream import ic
# except Exception:
#     def ic(*_, **__):
#         pass

valid_ext = ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf', '.xls', '.xlsx']
NOT_ACCOUNT_KEYS = [
    "central_info",
    "ssl_verify",
    "token_store",
    "forget_account_after",
    "debug",
    "debugv",
    "limit",
    "no_pager",
    "sanitize",
]


def _get_config_file(dirs: List[Path]) -> Path:
    dirs = [dirs] if not isinstance(dirs, list) else dirs
    for _dir in dirs:
        for f in list(Path.glob(_dir, "config.*")):
            if f.suffix in valid_ext and 'client_id' in f.read_text():
                return f


class Config:
    def __init__(self, base_dir: Path = None):
        if base_dir and isinstance(base_dir, str):
            base_dir = Path(base_dir)
        self.base_dir = base_dir or Path(__file__).parent.parent
        cwd = Path().cwd()
        self.file = _get_config_file(
            [
                Path().home() / ".config" / "centralcli",
                Path().home() / ".centralcli",
                cwd / "config",
                cwd,
                Path().home() / ".config" / "centralcli" / "config",
            ]
        )
        if self.file:
            self.dir = self.file.parent
            self.base_dir = self.dir.parent if self.dir.name != "centralcli" else self.dir
            if Path.joinpath(cwd, "out").is_dir():
                self.outdir = cwd / "out"
            else:
                self.outdir = cwd
        else:
            if str(Path('.config/centralcli')) in str(self.base_dir):
                self.dir = self.base_dir
                self.outdir = cwd / "out"
            else:
                if 'site-packages' in str(self.base_dir):
                    self.base_dir = self.dir = Path().home() / ".centralcli"
                else:
                    self.dir = self.base_dir / "config"
                self.outdir = self.base_dir / "out"
            self.file = self.dir / "config.yaml"

        for ext in ["yml", "json"]:
            if self.dir.joinpath(f"config.{ext}").exists():
                self.file = self.dir / f"config.{ext}"
                break
        self.bulk_edit_file = self.dir / "bulkedit.csv"
        self.stored_tasks_file = self.dir / "stored-tasks.yaml"
        self.cache_dir = self.dir / ".cache"
        self.default_cache_file = self.cache_dir / "db.json"
        self.sticky_account_file = self.cache_dir / "last_account"
        self.sanitize_file = self.dir / "redact.yaml"

        self.data = self.get_file_data(self.file) or {}
        self.forget: Union[int, None] = self.data.get("forget_account_after")
        self.debug = self.data.get("debug", False)
        self.debugv = self.data.get("debugv", False)
        self.account = self.get_account_from_args()
        self.defined_accounts: List[str] = [k for k in self.data if k not in NOT_ACCOUNT_KEYS]

    def __bool__(self):
        return len(self.data) > 0

    def __len__(self):
        return len(self.data)

    def __getattr__(self, item: str, default: Any = None) -> Any:
        if item in self.data:
            return self.data.get(item, default)
        elif self.data.get(self.account):
            return self.data[self.account].get(item, default)
        else:
            return self.data.get("central_info", {}).get(item, default)

    # not used but may be handy
    @property
    def tokens(self):
        return self.data.get(self.account, {}).get("token", {})

    @property
    def valid(self):
        return self.account in self.data

    @property
    def token_store(self):
        return self.data.get(
            "token_store",
            {"type": "local", "path": f"{self.dir.joinpath('.cache')}"}
        )

    @property
    def cache_file(self):
        return self.default_cache_file if self.account in ["central_info", "default"] else self.cache_dir / f"{self.account}.json"

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.data:
            return self.data.get(key, default)
        elif self.account and key in self.data[self.account]:
            return self.data[self.account].get(key, default)

    @staticmethod
    def get_file_data(import_file: Path) -> dict:
        '''Return dict from yaml/json/csv... file.'''
        if import_file.exists() and import_file.stat().st_size > 0:
            with import_file.open() as f:
                try:
                    if import_file.suffix == ".json":
                        return json.loads(f.read())
                    elif import_file.suffix in [".yaml", ".yml"]:
                        return yaml.load(f, Loader=yaml.SafeLoader)
                    elif import_file.suffix in ['.csv', '.tsv', '.dbf', '.xls', '.xlsx']:
                        with import_file.open('r') as fh:
                            return tablib.Dataset().load(fh)
                    else:
                        raise UserWarning(
                            "Provide valid file with format/extension [.json/.yaml/.yml/.csv]!"
                        )
                except Exception as e:
                    raise UserWarning(f'Unable to load configuration from {import_file}\n{e.__class__}\n\n{e}')

    def get_account_from_args(self) -> str:
        """Determine account to use based on arguments & last_account file.

        Method does no harm / triggers no errors.  Any errors are handled
        in account_name_callback after cli is loaded.  We need to determine the
        account during init to load the cache for auto completion.

        Returns:
            str: The account to use based on --account -d flags and last_account file.
        """
        if "--account" in sys.argv:
            account = sys.argv[sys.argv.index("--account") + 1]
        elif "--account" in str(sys.argv):  # vscode debug workaround
            args = [a.split(" ") for a in sys.argv if "--account " in a][0]
            account = args[args.index("--account") + 1]
        elif "-d" in sys.argv or " -d " in str(sys.argv) or str(sys.argv).endswith("-d"):
            return "central_info"
        else:
            account = "central_info"

        if account in ["central_info", "default"]:
            if self.sticky_account_file.is_file():
                last_account, last_cmd_ts = self.sticky_account_file.read_text().split("\n")
                last_cmd_ts = float(last_cmd_ts)

                # last account sticky file handling -- messaging is in cli callback --
                if self.forget:
                    if time.time() > last_cmd_ts + (self.forget * 60):
                        self.sticky_account_file.unlink(missing_ok=True)
                        # typer.echo(self.AcctMsg(msg="forgot"))
                    else:
                        account = last_account
                        # typer.echo(self.AcctMsg(account, msg="previous_will_forget"))
                else:
                    account = last_account
                    # typer.echo(self.AcctMsg(account, msg="previous"))
        else:
            if account in self.data:
                self.sticky_account_file.parent.mkdir(exist_ok=True)
                self.sticky_account_file.write_text(f"{account}\n{round(time.time(), 2)}")
                # typer.echo(self.AcctMsg(account))
        return account
