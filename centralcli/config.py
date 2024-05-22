#!/usr/bin/env python3
#
# Author: Wade Wells github/Pack3tL0ss
from __future__ import annotations

import json
import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any, List, Dict, Union, TypeVar, TextIO, Tuple, Optional
from rich import print
from rich.prompt import Prompt, Confirm
from rich.console import Console
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from yarl import URL
# from pydantic import ConfigDict  # pydantic 2 not supported yet

import tablib
from tablib.exceptions import UnsupportedFormat
import yaml


try:
    import readline  # noqa
except Exception:
    pass

err_console = Console(stderr=True)

class Token(BaseModel):
    access: str = Field(..., alias="access_token")
    refresh : str = Field(..., alias="refresh_token")

class SnowTokens(BaseModel):
    config: Token
    cache: Optional[Token] = None

class WebHook(BaseModel):
    token: Optional[str] = None
    port: Optional[int] = 9443

class ServiceNow(BaseModel):
    # model_config = ConfigDict(arbitrary_types_allowed=True) pydantic 2 / not supported yet
    id: str
    base_url: HttpUrl = Field(..., alias="url")
    port: int = None
    incident_path: str
    refresh_path: str = "oauth_token.do"
    assignment_group: str
    client_id: str
    client_secret: str
    token: SnowTokens = None
    tok_file: Path = None

    @property
    def incident_url(self) -> URL:
        return URL(f"{self.base_url.rstrip('/')}:{self.port or self.base_url.port}/{self.incident_path.lstrip('/')}?sysparm_display_value=true")

    @property
    def refresh_url(self) -> URL:
        return URL(f"{self.base_url.rstrip('/')}:{self.port or self.base_url.port}/{self.refresh_path.lstrip('/')}")



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

valid_ext = ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf']
NOT_ACCOUNT_KEYS = [
    "central_info",
    "ssl_verify",
    "token_store",
    "forget_account_after",
    "debug",
    "debugv",
    "limit",
    "no_pager",  # deprecated key kept in for older configs that might be using it
    "sanitize",
    "webclient_info",
]

JSON_TYPE = Union[List, Dict, str]  # pylint: disable=invalid-name
DICT_T = TypeVar("DICT_T", bound=Dict)  # pylint: disable=invalid-name

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


class SafeLineLoader(yaml.SafeLoader):
    """Loader class that keeps track of line numbers."""

    def compose_node(self, parent: yaml.nodes.Node, index: int) -> yaml.nodes.Node:
        """Annotate a node with the first line it was seen."""
        last_line: int = self.line
        node: yaml.nodes.Node = super().compose_node(parent, index)
        node.__line__ = last_line + 1  # type: ignore
        return node


def load_yaml(fname: Path) -> JSON_TYPE:
    """Load a YAML file."""
    with fname.open(encoding="utf-8") as conf_file:
        return parse_yaml(conf_file)


def parse_yaml(content: Union[str, TextIO]) -> JSON_TYPE:
    """Load a YAML file."""
    # If configuration file is empty YAML returns None
    # We convert that to an empty dict
    return yaml.load(content, Loader=SafeLineLoader) or {}


def _include_yaml(loader: SafeLineLoader, node: yaml.nodes.Node) -> JSON_TYPE:
    """Load another YAML file and embeds it using the !include tag.

    Example:
        devices: !include devices.yaml
        groups: !include groups.yaml
        sites: !include sites.yaml

    """
    fname = Path(loader.name).parent / node.value
    try:
        if fname.suffix in ['.csv', '.tsv', '.dbf']:
            csv_data = "".join([line for line in fname.read_text(encoding="utf-8").splitlines(keepends=True) if line and not line.startswith("#")])
            try:
                ds = tablib.Dataset().load(csv_data)
            except UnsupportedFormat:
                print(f'Unable to import data from {fname.name} verify formatting commas/headers/etc.')
                sys.Exit(1)
            return yaml.load(ds.yaml, Loader=SafeLineLoader) or {}
        else:
            return load_yaml(fname)
    except FileNotFoundError as exc:
        print(f"{node.start_mark}: Unable to read file {fname}.")
        raise exc


class Config:
    def __init__(self, base_dir: Path = None):
        self.is_completion = False  # Updated in cli.py all_commands_callback if completion
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
            if not self.file.exists() and sys.stdin.isatty() and not self.is_completion:
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
        self.forget: int | None = self.data.get("forget_account_after")
        self.debug: bool = self.data.get("debug", False)
        self.debugv: bool = self.data.get("debugv", False)
        self.sanitize: bool = self.data.get("sanitize", False)
        self.default_account: str = "default" if "default" in self.data else "central_info"
        self.last_account, self.last_cmd_ts, self.last_account_msg_shown, self.last_account_expired = self.get_last_account()
        self.account = self.get_account_from_args()
        self.base_url = self.data.get(self.account, {}).get("base_url")
        self.limit: int | None = self.data.get("limit")  # Allows override of paging limit for pagination testing
        try:
            self.webhook = WebHook(**self.data.get(self.account, {}).get("webhook", {}))
        except ValidationError:
            self.webhook = WebHook()

        try:
            _snow_config = self.data.get(self.account, {}).get("snow", {})
            if _snow_config:
                if _snow_config.get("token", {}):
                    _config_token = _snow_config["token"]
                    # del _snow_config["token"]
                    _snow_config["token"] = {}
                    _snow_config["token"]["config"] = _config_token
                if self.snow_tok_file and self.snow_tok_file.exists():
                    _cache_token = json.loads(self.snow_tok_file.read_text())
                    _snow_config["token"]["cache"] = _cache_token
                _snow_config["tok_file"] = Path(self.cache_dir / f'snow_{self.tok_file.name}')
            self.snow = ServiceNow(**_snow_config)
        except ValidationError:
            self.snow = None

        self.defined_accounts: List[str] = [k for k in self.data if k not in NOT_ACCOUNT_KEYS]
        self.deprecation_warning = None  # TODO warning added 1.14.0

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

    @property
    def is_cop(self):
        return False if self.base_url.endswith("arubanetworks.com") else True

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
    def tok_file(self) -> Path:
        cust_id = self.data.get(self.account, {}).get("customer_id")
        client_id = self.data.get(self.account, {}).get("client_id")
        return Path(self.cache_dir / f'tok_{cust_id}_{client_id}.json') if cust_id and client_id else None

    @property
    def cache_file(self):
        return self.default_cache_file if self.account in ["central_info", "default"] else self.cache_dir / f"{self.account}.json"

    @property
    def last_command_file(self):
        return self.cache_dir / "last_command" if self.account in ["central_info", "default"] else self.cache_dir / f"{self.account}_last_command"

    @property
    def wh_port(self):
        _acct_specific = self.webhook.port if self.webhook.port != 9443 else None
        if self.data.get("webclient_info", {}).get("port"):
            self.deprecation_warning = (
                '[bright_red]Deprecation Warning[/]: The webhook config location has changed, and is now account specific. '
                'See https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example and update config.'
            )
        return _acct_specific or self.data.get("webclient_info", {}).get("port", 9443)

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.data:
            return self.data.get(key, default)
        elif self.account and key in self.data[self.account]:
            return self.data[self.account].get(key, default)

    def get_last_account(self) -> Tuple[str | None, float | None, bool | None]:
        """Gathers contents of last_account returns tuple with values.

        last_account file stores: name of last account, timestamp of last command, numeric bool if big (will forget) msg has been displayed.
            expiration is calculated based on the value of account_will_forget and delta between last_command timestamp and now.


        Returns:
            Tuple[None, str | None, float | bool | None, bool]:
                last_account, timestamp of last cmd using this account, if initial will_forget_msg has been displayed, if account is expired
        """
        if self.sticky_account_file.is_file():
            last_account_data = self.sticky_account_file.read_text().split("\n")
            if last_account_data:
                last_account = last_account_data[0]
                last_cmd_ts = float(last_account_data[1])
                big_msg_displayed = bool(int(last_account_data[2]))
                expired = True if self.forget is not None and time.time() > last_cmd_ts + (self.forget * 60) else False
                return last_account, last_cmd_ts, big_msg_displayed, expired
        return None, None, False, None

    def update_last_account_file(self, account: str, last_cmd_ts: int | float = round(time.time(), 2), msg_shown: bool = False):
        self.sticky_account_file.parent.mkdir(exist_ok=True)
        self.sticky_account_file.write_text(f"{account}\n{last_cmd_ts}\n{int(msg_shown)}")

    @staticmethod
    def get_file_data(import_file: Path, text_ok: bool = False, model: Any = None) -> Union[dict, list]:
        """Returns dict from yaml/json/csv or list of lines from file when text_ok=True.

        Args:
            import_file (Path): import file.
            text_ok (bool, optional): When file extension is not one of yaml/yml/json/csv/tsv...
                parse file as text and return list of lines. Defaults to False.
            model (Any, optional): Pydantic Model to return, dict from import is passed into model for validation.

        Raises:
            UserWarning: Raises UserWarning when text_ok is False (default) and extension is
                not in ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf']
            UserWarning: Raises UserWarning when a failure occurs when parsing the file,
                passes on the underlying exception.

        Returns:
            Union[dict, list]: Normally dict, list when text_ok and file extension not in
                ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf'].
        """
        if import_file.exists() and import_file.stat().st_size > 0:
            with import_file.open(encoding="utf-8-sig") as f:
                try:
                    if import_file.suffix == ".json":
                        return json.loads(f.read()) if not model else model(**json.loads(f.read()))
                    else:
                        yaml.SafeLoader.add_constructor("!include", _include_yaml)
                        if import_file.suffix in [".yaml", ".yml"]:
                            import_data = yaml.load(f, Loader=yaml.SafeLoader)
                            if not model:
                                return import_data
                            # return yaml.load(f, Loader=yaml.SafeLoader) if not model else model(*yaml.load(f, Loader=yaml.SafeLoader))
                        elif import_file.suffix in ['.csv', '.tsv', '.dbf']:
                            csv_data = "".join([line for line in f.read().splitlines(keepends=True) if line and not line.startswith("#")])
                            try:
                                ds = tablib.Dataset().load(csv_data)
                            except UnsupportedFormat:
                                try:
                                    # TODO if csv is single column maybe we should convert all to single list
                                    ds = tablib.Dataset().load(csv_data, format=import_file.suffix.lstrip("."))
                                except UnsupportedFormat:
                                    print(f'Unable to import data from {import_file.name} verify formatting commas/headers/etc.')
                                    sys.exit(1)
                            import_data = yaml.load(ds.json, Loader=yaml.SafeLoader)
                            if not model:
                                return import_data
                        elif text_ok:
                            if model:
                                raise UserWarning(f'text_ok=True, and model={model.__class__.__name__} are mutually exclusive.')
                            return [line.rstrip() for line in f.read().splitlines()]
                        else:
                            raise UserWarning(
                                "Provide valid file with format/extension [.json/.yaml/.yml/.csv]!"
                            )
                except Exception as e:
                    raise UserWarning(f'Unable to load configuration from {import_file}\n{e.__class__.__name__}\n\n{e}')

                if isinstance(import_data, list):
                    return model(**{list(model.__fields__.keys())[0]: import_data})
                elif isinstance(import_data, dict):
                    return model(**import_data)
                else:
                    raise TypeError(f'{model.__class__.__name__} model provided but data from import is unexpected type {type(import_data)}')

    def get_account_from_args(self) -> str:
        """Determine account to use based on arguments & last_account file.

        Method does no harm / triggers no errors.  Any errors are handled
        in account_name_callback after cli is loaded.  We need to determine the
        account during init to load the cache for auto completion.

        Returns:
            str: The account to use based on --account -d flags and last_account file.
        """
        # No printing, any printing messes with completion
        if "-d" in sys.argv or " -d " in str(sys.argv) or str(sys.argv).rstrip("']").endswith("-d"):
            return self.default_account
        elif [arg for arg in sys.argv if arg.startswith("-") and arg.count("-") == 1 and "d" in arg]:
            return self.default_account
        elif "--account" in sys.argv:
            account = sys.argv[sys.argv.index("--account") + 1]
        elif "--account " in str(sys.argv):  # vscode debug workaround
            args = [a.split(" ") for a in sys.argv if "--account " in a][0]
            account = args[args.index("--account") + 1]
        else:
            account = self.default_account if not os.environ.get("ARUBACLI_ACCOUNT") else os.environ.get("ARUBACLI_ACCOUNT")

        if account in ["central_info", "default"]:
            if self.forget and self.last_account_expired:
                pass  # all_commands_callback will handle messaging can't do here, along with last_account file reset.
            else:
                account = self.last_account or account
        elif account in self.data and account != os.environ.get("ARUBACLI_ACCOUNT", ""):
            if self.forget is not None and self.forget > 0:
                self.update_last_account_file(account)

        return account

    def first_run(self) -> str:
        """Method to collect configuration from user when no config file exists.

        Returns:
            str|None: The contents of the config file (yaml.safe_dump) or None if
                user chooses to bypass.
        """
        example_link = "https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example"
        # populate example config file
        config_comments = f"\n\n# See Example at link below for all options. \n# {example_link}\n"
        self.dir.mkdir(exist_ok=True)
        print(f"[red]Configuration [/red]{self.file}[red] not found.")
        print("[bold cyan]Central API CLI First Run Configuration Wizard.[reset]")
        _clusters = list(CLUSTER_URLS.keys())
        choice = ""
        while True:
            print(
                "\nEnter [cyan italic]abort[/cyan italic] at any prompt to exit this wizard and create the file manually.\n"
                f"\nRefer to the example @ \n{example_link}\n\n"
            )

            valid_clusters = _clusters + ["other"]
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
            print("\nYour [cyan]customer id[/cyan] can be found by clicking the user icon in the upper right of the Central UI")
            customer_id = ask("customer id")
            print("\n[cyan]Client ID[reset] and [cyan]Client Secret[reset] can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print("You can double click the field in the table to select then copy, it will copy the entire token even with the token truncated with ...")
            client_id = ask("client id")
            client_secret = ask("client secret")

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

            print("\n[cyan]Access and Refresh Tokens[reset] can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print("Click the [blue]View Tokens[/blue] link for the appropriate row in the System Apps and Tokens table.")
            print("then click the [blue]Download Tokens[/blue] link in the Token List.  (Tokens will be displayed in a popup)")
            access_token = ask("Access Token")
            refresh_token = ask("Refresh Token")
            username = ask("username")
            if username.endswith("@hpe.com"):
                print("\n[red]You need to use token Auth or configure a user with an external email")
                print("[red]The OAUTH Flow does not work with hpe.com users (SSO).")
                print(f"[red]ignoring username {username}.")
                password = None
            elif not username:
                username = None
                print()  # They did not enter a username.  CR is for correct format of config output
            else:
                password = ask("password", password=True)

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
