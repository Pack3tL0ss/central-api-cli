#!/usr/bin/env python3
#
# Author: Wade Wells github/Pack3tL0ss
from typing import Optional

import json
import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any, List, Union
from rich import print
from rich.prompt import Prompt, Confirm
from rich.console import Console

import tablib
import yaml

try:
    import readline  # noqa
except Exception:
    pass

clear = Console().clear
class ClusterName(str, Enum):
    internal = "internal"
    prod1 = "prod1"
    prod2 = "prod2"
    prod4 = "prod4"

CLUSTER_URLS = {
    "internal": "https://internal-apigw.central.arubanetworks.com",
    "us1": "https://app1-apigw.central.arubanetworks.com",
    "us2": "https://apigw-prod2.central.arubanetworks.com",
    "us4": "https://apigw-uswest4.central.arubanetworks.com",
    "cn1": "https://app1-apigw.central.arubanetworks.com.cn",

}

def get_cluster_url(cluster: ClusterName) -> str:
    return CLUSTER_URLS.get(cluster)

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
    "webclient_info",
]

def abort():
    print("Aborted")
    sys.exit()

def ask(
    prompt: str = "",
    *,
    console: Optional[Console] = None,
    password: bool = False,
    choices: Optional[List[str]] = None,
    show_default: bool = True,
    show_choices: bool = True,
) -> str:
    """wrapper function for rich.Prompt().ask()

    Handles KeyBoardInterrupt, EoFError, and exits if user inputs "abort"

    """
    if choices:
        choices += ["abort"]
    try:
        choice = Prompt.ask(
            prompt,
            console=console,
            password=password,
            choices=choices,
            show_default=show_default,
            show_choices=show_choices
        )
    except (KeyboardInterrupt, EOFError):
        abort()

    if choice.lower() == "abort":
        abort()

    return choice


def _get_config_file(dirs: List[Path]) -> Path:
    dirs = [dirs] if not isinstance(dirs, list) else dirs
    for _dir in dirs:
        for f in list(Path.glob(_dir, "config.*")):
            if f.suffix in valid_ext and 'base_url' in f.read_text():
                return f

def _get_user_input(valid: list) -> str:
    choice = ""
    try:
        while choice.lower() not in valid:
            choice = input(" >> ")
            if choice.lower() == "abort":
                print("Aborted")
                sys.exit()
            elif choice.lower() not in valid:
                print(
                    f"[red]Invalid input.[/red] {choice}.\n"
                    f"  Select from: {', '.join(valid)}"
                )
        return choice
    except (KeyboardInterrupt, EOFError):
        print("Aborted")
        sys.exit()


class Config:
    def __init__(self, base_dir: Path = None):
        self.valid_suffix = valid_ext
        if base_dir and isinstance(base_dir, str):
            base_dir = Path(base_dir)
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.cwd = Path().cwd()
        self.file = _get_config_file(
            [
                Path().home() / ".config" / "centralcli",
                Path().home() / ".centralcli",
                self.cwd / "config",
                self.cwd,
                # Path().home() / ".config" / "centralcli" / "config",
            ]
        )
        if self.file:
            self.dir = self.file.parent
            self.base_dir = self.dir.parent if self.dir.name != "centralcli" else self.dir
            if Path.joinpath(self.cwd, "out").is_dir():
                self.outdir = self.cwd / "out"
            else:
                self.outdir = self.cwd
        else:
            if str(Path('.config/centralcli')) in str(self.base_dir):
                self.dir = self.base_dir
                self.outdir = self.cwd / "out"
            else:  # pypi installed but no config exists yet
                if 'site-packages' in str(self.base_dir):
                    if Path.joinpath(Path().home(), ".config").exists():
                        self.base_dir = self.dir = Path().home() / ".config" / "centralcli"
                    else:
                        self.base_dir = self.dir = Path().home() / ".centralcli"
                else:  # dev git repo
                    self.dir = self.base_dir / "config"
                self.outdir = self.base_dir / "out"
            self.file = self.dir / "config.yaml"

            for ext in ["yml", "json"]:
                if self.dir.joinpath(f"config.{ext}").exists():
                    self.file = self.dir / f"config.{ext}"
                    break

            # No config found trigger first run wizard
            if not self.file.exists() and sys.stdin.isatty():
                if "-completion" not in str(sys.argv):
                    self.first_run()
                else:
                    ...  # TODO add typer.confirm(No config found ...)

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
        return len(self.data) > 0 and self.account in self.data

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

    @property
    def last_command_file(self):
        return self.cache_dir / "last_command" if self.account in ["central_info", "default"] else self.cache_dir / f"{self.account}_last_command"

    @property
    def wh_port(self):
        return self.data.get("webclient_info", {}).get("port", "9443")

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.data:
            return self.data.get(key, default)
        elif self.account and key in self.data[self.account]:
            return self.data[self.account].get(key, default)

    @staticmethod
    def get_file_data(import_file: Path, text_ok: bool = False) -> Union[dict, list]:
        """Returns dict from yaml/json/csv or list of lines from file when text_ok=True.

        Args:
            import_file (Path): import file.
            text_ok (bool, optional): When file extension is not one of yaml/yml/json/csv/tsv...
                parse file as text and return list of lines. Defaults to False.

        Raises:
            UserWarning: Raises UserWarning when text_ok is False (default) and extension is
                not in ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf', '.xls', '.xlsx']
            UserWarning: Raises UserWarning when a failure occurs when parsing the file,
                passes on the underlying exception.

        Returns:
            Union[dict, list]: Normally dict, list when text_ok and file extension not in
                ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf', '.xls', '.xlsx'].
        """
        if import_file.exists() and import_file.stat().st_size > 0:
            with import_file.open() as f:
                try:
                    if import_file.suffix == ".json":
                        return json.loads(f.read())
                    elif import_file.suffix in [".yaml", ".yml"]:
                        return yaml.load(f, Loader=yaml.SafeLoader)
                    elif import_file.suffix in ['.csv', '.tsv', '.dbf', '.xls', '.xlsx']:
                        with import_file.open('r') as fh:
                            # TODO return consistent data type list/dict
                            # tough given csv etc dictates a flat structure
                            return tablib.Dataset().load(fh)
                    elif text_ok:
                        return [line.rstrip() for line in import_file.read_text().splitlines()]
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
        elif "-d" in sys.argv or " -d " in str(sys.argv) or str(sys.argv).rstrip("']").endswith("-d"):
            return "central_info"
        else:
            account = "central_info" if not os.environ.get("ARUBACLI_ACCOUNT") else os.environ.get("ARUBACLI_ACCOUNT")

        if account in ["central_info", "default"]:
            if self.sticky_account_file.is_file():
                last_account, last_cmd_ts = self.sticky_account_file.read_text().split("\n")
                last_cmd_ts = float(last_cmd_ts)

                # TODO can't print here with about breaking auto-complete - restore messaging to account_name_callback
                # last account sticky file handling -- messaging is in cli callback --
                console = Console()
                if self.forget:
                    if time.time() > last_cmd_ts + (self.forget * 60):
                        self.sticky_account_file.unlink(missing_ok=True)
                        _m = f":warning: Forget option set for [cyan]{last_account}[/], and expiration has passed.  [bright_green]reverting to default account[/]"
                        _m = f"{_m}\nUse [cyan]--account[/] option or set environment variable ARUBACLI_ACCOUNT to use alternate account"
                        # console.print(_m)
                        if not Confirm(f"Proceed using default account", console=console):
                            abort()
                    else:
                        account = last_account
                        # console.print(f":warning: [magenta]Using Account[/] [cyan]{account}[/]\n")
                else:
                    account = last_account
                    # console.print(f":warning: [magenta]Using Account[/] [cyan]{account}[/]\n")
        else:
            if account in self.data:
                self.sticky_account_file.parent.mkdir(exist_ok=True)
                self.sticky_account_file.write_text(f"{account}\n{round(time.time(), 2)}")
        return account

    def first_run(self) -> str:
        """Method to collect configuration from user when no config file exists.

        Returns:
            str|None: The contents of the config file (yaml.safe_dump) or None if
                user choses to bypass.
        """
        example_link = "https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example"
        # populate example config file
        config_comments = f"\n\n# See Example at link below for all options. \n# {example_link}\n"
        self.dir.mkdir(exist_ok=True)
        print(f"[red]Configuration [/red]{self.file}[red] not found.")
        print(f"[bold cyan]Central API CLI First Run Configuration Wizard.[reset]")
        _clusters = list(CLUSTER_URLS.keys())
        choice = ""
        while True:
            print(
                "\nEnter [cyan italic]abort[/cyan italic] at any prompt to exit this wizard and create the file manually.\n"
                f"\nRefer to the example @ \n{example_link}\n\n"
            )
            # print("Select Your Cluster?")
            # print(
            #     f"Please Enter {', '.join(_clusters)}\n"
            #     "or 'other'."
            # )
            valid_clusters = _clusters + ["other"]

            # get base_url
            # choice = _get_user_input(valid_clusters)
            choice = ask("Central Cluster", choices=valid_clusters)
            if choice.lower() == "other":
                print(f"Provide API gateway URL in the format [cyan]{CLUSTER_URLS['us4']}")
                choice = ask("API Gateway URL")
                base_url = choice.rstrip("/")
            else:
                base_url = CLUSTER_URLS[choice.lower()]

            # get common variables
            # TODO pycentral library tokeStoreUtil makes customer_id optional, but load and refresh don't  so we need it here just
            # so the file has the expected name.  Would be nice just to use the format tok_account_name.json
            print(f"\nYour [cyan]customer id[/cyan] can be found by clicking the user icon in the upper right of the Central UI")
            customer_id = ask("customer id")
            # customer_id = choice
            print(f"\n[cyan]Client ID[reset] and [cyan]Client Secret[reset] can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print(f"You can double click the field in the table to select then copy, it will copy the entire token even with the token truncated with ...")
            client_id = ask("client id")
            # client_id = choice
            client_secret = ask("client secret")
            # client_secret = choice

            config_data = {
                "central_info": {
                    "base_url": base_url,
                    "customer_id": customer_id,
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            }
            # TODO double check refresh token expiration period.  Add link to readthdocs once cron/task scheduler examples posted
            clear()
            print("\n\n[bold]Authentication can be handled a couple of ways:")
            print("1. Provide Access and Refresh Tokens.  cencli will automatically refresh the access token when it expires.")
            print("   However, if the refresh token expires (don't use the cli for > 2 weeks).  You would need to manually update the tokens.")
            print("   Refer to GitHub for example cron/task-scheduler files to automatically refresh the tokens weekly to prevent this.")
            print("2. Providing user/pass")
            print("   which will allow cencli to generate new tokens if they expire.\n")
            print("You can also provide both.  Which will use the tokens initially, but if they expire it will use the user/pass to ")
            print("generate new tokens.")
            print("\nYou will be prompted for all 4 just hit enter to skip, but you need to provide one of them (the tokens or user/pass")

            print(f"\n[cyan]Access and Refresh Tokens[reset] can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print(f"Click the [blue]View Tokens[/blue] link for the appropriate row in the System Apps and Tokens table.")
            print(f"then click the [blue]Download Tokens[/blue] link in the Token List.  (Tokens will be displayed in a popup)")
            access_token = ask("Access Token")
            refresh_token = ask("Refresh Token")
            username = ask("username")
            if username.endswith("@hpe.com"):
                print("\n[red]You need to use token Auth or configure a user with an external email")
                print("[red]The OAUTH Flow does not work with hpe.com users (SSO).")
                print(f"[red]ignoring username {username}.")
                password = None
            else:
                password = None if not username else ask("password", password=True)

            valid = False
            if access_token:
                config_data["central_info"]["token"] = {
                    "access_token": access_token
                }
                valid = True
                if refresh_token:
                    config_data["central_info"]["token"]["refresh_token"] = refresh_token
            if username and password:
                config_data["central_info"]["username"] = username
                config_data["central_info"]["password"] = password
                valid = True

            if not valid:
                print("[red]Either username and password OR access token needs to be provided.")
                continue
            else:
                config_data = f"{yaml.safe_dump(config_data)}{config_comments}"
                Console().rule("\n\n[bold cyan]Resulting Configuration File Content")
                print(config_data)
                Console().rule()
                if Confirm.ask("\nContinue?"):
                    print(f"\n\n[cyan]Writing to {self.file}")
                    self.file.write_text(config_data)
                    break
                else:
                    if not Confirm.ask("Retry Entries?"):
                        abort()
