#!/usr/bin/env python3
#
# Author: Wade Wells github/Pack3tL0ss
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, List, Dict, Union, TextIO, Tuple, Optional
from rich import print
from rich.prompt import Confirm
from rich.console import Console
from pydantic import BaseModel, Field, HttpUrl, ValidationError, AliasChoices, ConfigDict
from yarl import URL
from collections.abc import Mapping

import tablib
from tablib.exceptions import UnsupportedFormat
import yaml
from . import utils
from .typedefs import JSON_TYPE


try:
    import readline  # noqa
except Exception:
    pass

err_console = Console(stderr=True)
clear = Console().clear


class Defaults:
    def __init__(self):
        self.cache_client_days = 90

default = Defaults()

EXAMPLE_LINK = "https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example"
GLP_BASE_URL = "https://global.api.greenlake.hpe.com"
BYPASS_FIRST_RUN_FLAGS = [
    "--install-completion",
    "--show-completion",
    "restore-config",
    "-V",
    "-v",
    "--help",
    "?"
]

VALID_EXT = ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf']
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
    "webclient_info",  # Also depricated should be under webhook within the workspace config
    "capture_raw",
    "cache_client_days",
]


class Token(BaseModel):
    access: str = Field(..., alias="access_token")
    refresh: str = Field(..., alias="refresh_token")


class CentralToken(Token):
    wss_key: Optional[str] = None


class SnowTokens(BaseModel):
    config: Token
    cache: Optional[Token] = None

class WebHook(BaseModel):
    token: Optional[str] = None
    port: Optional[int] = 9443

class ServiceNow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str
    base_url: HttpUrl = Field(..., alias=AliasChoices("base_url", "url"))
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

class WorkSpaceConfig(BaseModel):
    client_id: str
    client_secret: str
    customer_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[CentralToken] = None
    base_url: Optional[str] = Field(None, alias=AliasChoices("base_url", "classic_base_url"))
    webhook: Optional[WebHook] = None
    snow: Optional[ServiceNow] = None


# We make everything optional here so config can instantiate even if the workspace detail is missing
class AccountModel(BaseModel):
    base_url: Optional[HttpUrl] = Field(None, alias=AliasChoices("base_url", "url"))
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    customer_id: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[Token] = None


CLUSTER_URLS = {
    "internal": {
        "cnx": "https://internal.api.central.arubanetworks.com",
        "classic": "https://internal-apigw.central.arubanetworks.com",
        "aka": None
    },
    "us1": {
        "cnx": "https://us1.api.central.arubanetworks.com",
        "classic": "https://app1-apigw.central.arubanetworks.com",
        "aka": "prod"
    },
    "us2": {
        "cnx": "https://us2.api.central.arubanetworks.com",
        "classic": "https://apigw-prod2.central.arubanetworks.com",
        "aka": "central-prod2"
    },
    "us4": {
        "cnx": "https://us4.api.central.arubanetworks.com",
        "classic": "https://apigw-uswest4.central.arubanetworks.com",
        "aka": "uswest4"
    },
    "us5": {
        "cnx": "https://us5.api.central.arubanetworks.com",
        "classic": "https://apigw-uswest5.central.arubanetworks.com",
        "aka": "uswest5"
    },
    "us6": {
        "cnx": "https://us6.api.central.arubanetworks.com",
        "classic": "https://apigw-us-east-1.central.arubanetworks.com",
        "aka": "us-east-1"
    },
    "eu1": {
        "cnx": "https://de1.api.central.arubanetworks.com",
        "classic": "https://eu-apigw.central.arubanetworks.com",
        "aka": "de1"
    },
    "eu2": {
        "cnx": "https://de2.api.central.arubanetworks.com",
        "classic": "https://apigw-eucentral2.central.arubanetworks.com",
        "aka": "de2"
    },
    "eu3": {
        "cnx": "https://de3.api.central.arubanetworks.com",
        "classic": "https://apigw-eucentral3.central.arubanetworks.com",
        "aka": "de3"
    },
    "ca1": {
        "cnx": "https://ca1.api.central.arubanetworks.com",
        "classic": "https://app1-apigw.central.arubanetworks.com.cn",
        "aka": "Canada-1 / starman"
    },
    "in1": {
        "cnx": "https://in.api.central.arubanetworks.com",
        "classic": "https://api-ap.central.arubanetworks.com",
        "aka": "apac1 / India"
    },
    "jp1": {
        "cnx": "https://jp1.api.central.arubanetworks.com",
        "classic": "https://apigw-apaceast.central.arubanetworks.com",
        "aka": "apac-east-1 / Japan"
    },
    "au1": {
        "cnx": "https://au1.api.central.arubanetworks.com",
        "classic": "https://apigw-apacsouth.central.arubanetworks.com",
        "aka": "apac-south-1 / Australia"
    },
    "ae1": {
        "cnx": "https://ae1.api.central.arubanetworks.com",
        "classic": "https://apigw-uaenorth1.central.arubanetworks.com",
        "aka": "uae-north1"
    }
}


class ClusterURLs:
    def __init__(self, classic: str, cnx: str):
        self.classic = classic
        self.cnx = cnx

class CentralURLs(Mapping):
    def __init__(self):
        self.names = list(CLUSTER_URLS.keys())
        self.menu_names = self.names + ["other"]
        self.urls = [ClusterURLs(cluster["classic"], cluster["cnx"]) for cluster in CLUSTER_URLS.values()]

    def __getitem__(self, item):
        return CLUSTER_URLS[item]

    def __iter__():
        for cluster in CLUSTER_URLS:
            yield CLUSTER_URLS[cluster]

    def __len__():
        return len(CLUSTER_URLS)

    def __str__(self):
        console = Console(force_terminal=False)
        with console.capture() as cap:
            console.print(self.__rich__())
        return cap.get()

    def __rich__(self) -> str:
        out = []
        for k, v in CLUSTER_URLS.items():
            aka = v.get("aka")
            aka_str = '' if not aka else f' [dim italic]({aka})[/]'
            out += [f" [dark_olive_green2]{k}[/]{aka_str}: [cyan]{v['cnx']}[/]"]

        return "\n".join(out)

    @property
    def menu(self) -> str:
        title_txt = ' Select Cluster '
        width = max(map(len, str(self).splitlines())) - 1
        title = f" {title_txt:-^{width}}"  # to accomodate left pad
        title = title.replace(title_txt, f"[bright_green]{title_txt}[/]")
        other_options = [
            " [dark_olive_green2]other[/]: [cyan]Enter Custom Base URL [dim italic](i.e. for CoP)[/][/cyan]",
            " [red]abort[/]: [cyan]Exit the wizard [dim italic](config.yaml can be created manually)[/][/cyan]"
        ]
        other = "\n".join(other_options)

        return f"{title}\n{self.__rich__()}\n{other}\n {'-' * width}\n"



clusters = CentralURLs()


def _get_config_file(dirs: List[Path]) -> Path:
    dirs = [dirs] if not isinstance(dirs, list) else dirs
    for _dir in dirs:
        for f in list(Path.glob(_dir, "config.*")):
            if f.suffix in VALID_EXT and 'base_url' in f.read_text():
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


def parse_yaml(content: str | TextIO) -> JSON_TYPE:
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
    fname: Path = Path(loader.name).parent / node.value
    try:
        if fname.suffix in ['.csv', '.tsv', '.dbf']:
            csv_data = "".join([line for line in fname.read_text(encoding="utf-8").splitlines(keepends=True) if line and not line.startswith("#")])
            try:
                ds = tablib.Dataset().load(csv_data, format="csv")
            except UnsupportedFormat:
                print(f'Unable to import data from {fname.name} verify formatting commas/headers/etc.')
                sys.exit(1)
            return yaml.load(ds.yaml, Loader=SafeLineLoader) or {}
        else:
            yaml_out = load_yaml(fname)
            text_out = fname.read_text()
            if isinstance(yaml_out, str) and "\n" not in yaml_out and "\n" in text_out:
                return [line.rstrip() for line in text_out.splitlines()]
            else:
                return yaml_out
    except FileNotFoundError as exc:
        print(f"{node.start_mark}: Unable to read file {fname}.")
        raise exc

class BaseURLs:
    def __init__(self, cnx: str, glp: str = GLP_BASE_URL):
        self.glp = glp
        self.cnx = cnx

class CNX:
    def __init__(self, central_base_url: str = None, *, client_id: str = None, client_secret: str = None, glp_base_url: str = GLP_BASE_URL):
        self.urls = BaseURLs(glp=glp_base_url, cnx=central_base_url)
        self.client_id = client_id
        self.client_secret = client_secret

    def __bool__(self) -> bool:
        return self.ok

    @property
    def ok(self) -> bool:
        return False if not self.client_id or not self.client_secret else True

    @property
    def token_info(self) -> Dict[str, Dict[str, str]]:
        return {
            "glp": {
                "base_url": self.urls.glp,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        }

    @property
    def as_dict(self) -> Dict[str, str | Dict[str, str]]:
        return {
            "base_urls": {
                "glp": self.urls.glp,
                "new_central": self.urls.cnx
            },
            "token_info": self.token_info
        }

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({'VALID' if self.ok else 'CONFIG MISSING/INVALID'}) object at {hex(id(self))}>"


class Config:
    def __init__(self, base_dir: Path = None):
        #  We don't know if it's completion at this point cli is not loaded.  BASH will hang if first_run wizard is started. Updated in cli.py all_commands_callback if completion
        self.is_completion = bool(os.environ.get("COMP_WORDS"))
        self.valid_suffix = VALID_EXT
        if base_dir and isinstance(base_dir, str):
            base_dir = Path(base_dir)
        self.base_dir = base_dir or Path(__file__).parent.parent
        try:
            self.cwd = Path.cwd()
        except FileNotFoundError:  # In the very rare event the user launches a command from a directory that they've deleted in another session.
            self.cwd = Path.home()

        self.file = _get_config_file(
            [
                Path().home() / ".config" / "centralcli",
                Path().home() / ".centralcli",
                self.cwd / "config",
                self.cwd,
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
                if not any([a in BYPASS_FIRST_RUN_FLAGS for a in sys.argv]):
                    self.first_run()

        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.capture_file = self.log_dir / "raw-capture.json"

        self.bulk_edit_file = self.dir / "bulkedit.csv"
        self.stored_tasks_file = self.dir / "stored-tasks.yaml"
        self.cache_dir = self.dir / ".cache"
        self.default_cache_file = self.cache_dir / "db.json"
        self.default_scache_file = self.cache_dir / "dbv2.json"
        self.sticky_account_file = self.cache_dir / "last_account"
        self.sanitize_file = self.dir / "redact.yaml"

        self.data = self.get_file_data(self.file) or {}
        self.forget: int | None = self.data.get("forget_account_after")
        self.debug: bool = self.data.get("debug", False)
        self.debugv: bool = self.data.get("debugv", False)
        self.sanitize: bool = self.data.get("sanitize", False)
        self.capture_raw: bool = self.data.get("capture_raw", False)
        self.limit: int | None = self.data.get("limit")  # Allows override of paging limit for pagination testing
        self.default_account: str = "default" if "default" in self.data else "central_info"
        self.last_account, self.last_cmd_ts, self.last_account_msg_shown, self.last_account_expired = self.get_last_account()
        self.account = self.get_account_from_args()
        ws_data: Dict[str, int | str | bool | Dict[str, str | int]] = self.data.get(self.account, {})  # Data for the current WorkSpace (account)
        # TODO We can probably tidy things up a bit and use the model, below, which has been tested, but can throw validation errors.
        # ws_config = WorkSpaceConfig(**ws_data)  # self.data.get(self.account, {})  # ws_data as in WorkSpace Data
        self.base_url: str | None = ws_data.get("base_url")  # self.get("base_url", workspace_only=True) or self.get("classic_base_url", workspace_only=True)
        self.username: str | None = ws_data.get("username")  # self.get("username", workspace_only=True)
        self.wss_key: str | None = ws_data.get("token", {}).get("wss_key")
        self.cache_client_days: int = self.get("cache_client_days", default.cache_client_days)
        _cnx_config: Dict[str, Dict[str, str]] = self.get("glp") or self.get("new_central", {}) or self.data.get(self.account, {}).get("cnx", {})
        if "central_base_url" not in _cnx_config:
            _cnx_config["central_base_url"] = self.get_cnx_url(self.base_url)
        self.cnx = CNX(**_cnx_config)
        try:
            self.webhook = WebHook(**self.data.get(self.account, {}).get("webhook", {}))
        except ValidationError:
            self.webhook = WebHook()

        try:
            _snow_config = self.data.get(self.account, {}).get("snow", {})
            if _snow_config:
                if _snow_config.get("token", {}):
                    _config_token = _snow_config["token"]
                    _snow_config["token"] = {}
                    _snow_config["token"]["config"] = _config_token
                if self.snow_tok_file and self.snow_tok_file.exists():  # TODO probably just remove the snow code, was never completely tested/implemented
                    _cache_token = json.loads(self.snow_tok_file.read_text())  # snow_tok_file doesn't appear to be set anywhere
                    _snow_config["token"]["cache"] = _cache_token
                _snow_config["tok_file"] = Path(self.cache_dir / f'snow_{self.tok_file.name}')
            self.snow = None if not _snow_config else ServiceNow(**_snow_config)
        except ValidationError:
            self.snow = None

        self.defined_accounts: List[str] = [k for k in self.data if k not in NOT_ACCOUNT_KEYS]
        # validators can set deprecation warnings if the format of the config changes and we are still accomodating an older format
        self.deprecation_warnings = None


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
    def ssl_verify(self):
        return self.get("ssl_verify", True)

    @property
    def is_cop(self):
        return False if self.base_url.endswith("arubanetworks.com") else True

    # not used but may be handy
    @property
    def tokens(self):
        return self.get("token", {}, workspace_only=True)

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
    def cnx_tok_file(self) -> Path:
        cust_id = self.data.get(self.account, {}).get("customer_id")
        client_id = self.data.get(self.account, {}).get("client_id")
        return Path(self.cache_dir / f'cnx_tok_{cust_id}_{client_id}.json') if cust_id and client_id else None

    @property
    def cache_file(self):
        return self.default_cache_file if self.account in ["central_info", "default"] else self.cache_dir / f"{self.account}.json"

    @property
    def cache_file_ok(self):
        return self.cache_file.is_file() and self.cache_file.stat().st_size > 0

    @property
    def last_command_file(self):
        return self.cache_dir / "last_command" if self.account in ["central_info", "default"] else self.cache_dir / f"{self.account}_last_command"

    @property
    def export_dir(self) -> Path:
        # if they are already in export dir navigate back to top for output
        outdir: Path = self.outdir / "cencli-config-export"
        if "cencli-config-export" in outdir.parent.parts[1:]:
            outdir = outdir.parent
            while outdir.name != "cencli-config-export":
                outdir = outdir.parent

        return outdir


    def get_cnx_url(self, classic_base_url: str | None):
        if not classic_base_url:  # This can occur if they use --account flag with an account that is not configured
            return

        cluster_name = [k for k, v in CLUSTER_URLS.items() if v["classic"] == classic_base_url.lower()]
        if cluster_name:
            return CLUSTER_URLS[cluster_name[0]]["cnx"]

    def get(self, key: str, default: Any = None, *, workspace_only: bool = False) -> Any:
        # prefer setting at the workspace config level first
        if self.account  and key in self.data.get(self.account, {}):
            return self.data[self.account][key]

        # fallback to global
        if not workspace_only and key in self.data:
            return self.data.get(key, default)

        return default

    def get_last_account(self) -> Tuple[str | None, float | None, bool | None]:
        """Gathers contents of last_account returns tuple with values.

        last_account file stores: name of last account, timestamp of last command, numeric bool if big (will forget) msg has been displayed.
            expiration is calculated based on the value of account_will_forget and delta between last_command timestamp and now.


        Returns:
            Tuple[None, str | None, float | bool | None, bool]:
                last_account, timestamp of last cmd using this account, if initial will_forget_msg has been displayed, if account is expired
        """
        if self.sticky_account_file.is_file():
            last_account_data = [row for row in self.sticky_account_file.read_text().split("\n") if row != ""]  # we don't add \n at end of file, but to handle it just in case
            if last_account_data:
                last_account = last_account_data[0]
                last_cmd_ts = self.sticky_account_file.stat().st_mtime if len(last_account_data) < 2 else float(last_account_data[1])
                big_msg_displayed = False if len(last_account_data) < 3 else bool(int(last_account_data[2]))
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
        elif " --account " in str(sys.argv):  # vscode debug workaround
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

    def _cnx_first_run(self, config_data: dict) -> dict | None:
        """Method to collect CNX configuration from user when no config file exists.

        Args:
            central_info (dict): The current configuration items collected from the user

        Returns:
            dict|None: Returns the Contents of the config dict or None if they've chosen
                to skip New Central Configuration.
        """
        print("[bold cyan]New Central / GreenLake API CLI Configuration.[reset]")
        client_id = None
        while True:
            base_url = self.get_cnx_url(classic_base_url=config_data["central_info"]["base_url"])
            print("\n[cyan]Client ID[reset] and [cyan]Client Secret[reset] are [dim red]required[/] for New Central.")
            print("Refer to [link='https://developer.arubanetworks.com/new-central/docs/generating-and-managing-access-tokens']HPE Aruba devhub[/] for details on how to generate the tokens.")
            print("\n[yellow]:information:[/]  Press return to skip New Central Configuration.  [dim italic][cyan]cencli[/] currently has limitted support for New Central[/]\n")
            client_id = utils.ask("[dim italic]New Central/GreenLake[/] client id", default=client_id)
            if not client_id or not client_id.strip():
                return

            client_secret = utils.ask("[dim italic]New Central/GreenLake[/] client secret")

            config_data["central_info"]["glp"] = {
                "central_base_url": base_url,
                "glp_base_url": GLP_BASE_URL,
                "client_id": client_id,
                "client_secret": client_secret
            }

            if not client_secret:
                err_console.print("[dark_orange3]:warning:[/]  client_secret is required.")
                continue

            return config_data

    def first_run(self) -> str:
        """Method to collect configuration from user when no config file exists.

        Returns:
            str|None: The contents of the config file (yaml.safe_dump) or None if
                user chooses to bypass.
        """

        # populate example config file
        config_comments = f"\n\n# See Example at link below for all options. \n# {EXAMPLE_LINK}\n"
        self.dir.mkdir(exist_ok=True)

        print(f"[red]Configuration [/red]{self.file}[red] not found.")
        print("[bold cyan]Central API CLI First Run Configuration Wizard.[reset]")
        choice = ""
        refresh_token = None
        while True:
            print(
                "\nEnter [cyan italic]abort[/cyan italic] at any prompt to exit this wizard and create the file manually.\n"
                f"\nRefer to the example @ \n{EXAMPLE_LINK}\n\n"
            )

            print(clusters.menu)
            choice = utils.ask("Central Cluster", choices=clusters.menu_names)
            if choice.lower() == "other":
                print(f"Provide [dim italic]Classic Central[/] API gateway URL in the format [cyan]{CLUSTER_URLS['us4']}")
                choice = utils.ask("[dim italic]Classic Central[/] API Gateway URL")
                base_url = choice.rstrip("/")
            else:
                base_url = clusters[choice.lower()]["classic"]

            # get common variables
            # TODO pycentral library tokeStoreUtil makes customer_id optional, but load and refresh don't  so we need it here just
            # so the file has the expected name.  Would be nice just to use the format tok_account_name.json
            print("\nYour [cyan]customer id[/cyan] can be found by clicking the user icon in the upper right of the Central UI")
            customer_id = utils.ask("customer id")
            print("\n[cyan]Client ID[reset] and [cyan]Client Secret[reset] can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print("You can double click the field in the table to select then copy, it will copy the entire token even with the token truncated with ...")
            client_id = utils.ask("[dim italic]Classic Central[/] client id")
            client_secret = utils.ask("[dim italic]Classic Central[/] client secret")

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
            print("\n\n[bold]Authentication can be handled a couple of ways for [magenta]Classic Central[/]:")
            print("1. Provide [dark_olive_green2]Access[/] and [dark_olive_green2]Refresh[/] Tokens.  cencli will automatically refresh the access token when it expires.")
            print("   However, if the refresh token expires (don't use the cli for > 2 weeks).  You would need to manually update the tokens.")
            print("   Use [cyan]cencli show cron[/] for cron/task-scheduler configuration to automatically refresh the tokens weekly to prevent this.")
            print("2. Providing user/pass")
            print("   which will allow cencli to generate new tokens if they expire.\n")
            print("You can also provide both.  Which will use the tokens initially, but if they expire it will use the user/pass to ")
            print("generate new tokens.")
            print("\nYou will be prompted for all 4 just hit enter to skip, but you need to provide one of them [dim italic](the tokens or user/pass)[/]")

            print("\n[dark_olive_green2]Access[/] and [dark_olive_green2]Refresh[/] Tokens can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print("Click the [blue]View Tokens[/blue] link for the appropriate row in the System Apps and Tokens table.")
            print("then click the [blue]Download Tokens[/blue] link in the Token List.  (Tokens will be displayed in a popup)")
            access_token = utils.ask("[dim italic]Classic Central[/] Access Token")
            if access_token:
                refresh_token = utils.ask("[dim italic]Classic Central[/] Refresh Token")
            username = utils.ask("username")
            if username.endswith("@hpe.com"):
                print("\n[red]You need to use token Auth or configure a user with an external email")
                print("[red]The OAUTH Flow does not work with hpe.com users (SSO).")
                print(f"[red]ignoring username {username}.")
                password = None
            elif not username:
                username = password = None
                print()  # They did not enter a username.  CR is for correct format of config output
            else:
                password = utils.ask("password", password=True)

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
                err_console.print("[dark_orange3]:warning:[/]  At least one of [dark_olive_green2]username/password[/] OR [dark_olive_green2]access/refresh tokens[/] must to be provided.")
                continue
            else:
                _with_cnx = self._cnx_first_run(config_data)
                config_data = _with_cnx or config_data
                config_data = f"{yaml.safe_dump(config_data)}{config_comments}"
                Console().rule("\n\n[bold cyan]Resulting Configuration File Content")
                _config_data = config_data if not password else config_data.replace(password, "*********")
                print(_config_data)
                Console().rule()
                if Confirm.ask("\nContinue?"):
                    print(f"\n\n[cyan]Writing to {self.file}")
                    self.file.write_text(config_data)
                    break
                else:
                    if not Confirm.ask("Retry Entries?"):
                        err_console.print("[dark_orange3]:warning:[/]  Aborted")
                        sys.exit()
