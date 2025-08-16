from __future__ import annotations

import json
import sys
import time
from collections.abc import Mapping

# from os import environ as env
from pathlib import Path
from typing import Any, Optional, TextIO

import tablib
import yaml
from pydantic import ValidationError
from rich import print
from rich.console import Console
from rich.prompt import Confirm, Prompt
from tablib.exceptions import UnsupportedFormat

from .constants import CLUSTER_URLS
from .environment import env
from .models.config import ConfigData
from .typedefs import JSON_TYPE

try:
    import readline  # noqa
except Exception:
    pass

econsole = Console(stderr=True)
clear = Console().clear


GLP_BASE_URL = "https://global.api.greenlake.hpe.com"
VALID_EXT = ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf']
EXAMPLE_LINK = "https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example"
BYPASS_FIRST_RUN_FLAGS = [
    "--install-completion",
    "--show-completion",
    "restore-config",
    "-V",
    "-v",
    "--help",
    "?"
]
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


# We can't import render without causing circular imports so confirm() and ask() are duplicated here.  Confirm is slightly customized vs confirm() in render
def confirm(
    prompt: str = "",
    *,
    console: Optional[Console] = None,
) -> bool:
    """wrapper function for rich.Confirm().ask()

    Handles KeyBoardInterrupt, EoFError, and exits if user inputs "abort".
    """
    console = console or Console()
    econsole = Console(stderr=True)

    try:
        choice = Confirm.ask(
            prompt,
            console=console,
        )
    except (KeyboardInterrupt, EOFError):
        econsole.print("\n[dark_orange3]:warning:[/]  [red]Aborted[/]", emoji=True)
        sys.exit(1)  # Needs to be sys.exit not raise Typer.Exit as that causes an issue when catching KeyboardInterrupt

    return choice


def ask(
    prompt: str = "",
    *,
    rich_console: Optional[Console] = None,
    password: bool = False,
    choices: Optional[list[str]] = None,
    show_default: bool = True,
    show_choices: bool = True,
    default: Any = ...,
) -> str:
    """wrapper function for rich.Prompt().ask()

    Handles KeyBoardInterrupt, EoFError, and exits if user inputs "abort".
    """
    con = rich_console or econsole
    def abort():
        con.print("\n[dark_orange3]:warning:[/]  [red]Aborted[/]", emoji=True)
        sys.exit(1)  # Needs to be sys.exit not raise Typer.Exit as that causes an issue when catching KeyboardInterrupt

    choices = choices if choices is None or "abort" in choices else ["abort", *choices]

    try:
        choice = Prompt.ask(
            prompt,
            console=Console(stderr=True),
            password=password,
            choices=choices,
            show_default=show_default,
            show_choices=show_choices,
            default=default,
        )
    except (KeyboardInterrupt, EOFError):
        abort()

    if choice == "abort":
        abort()

    return choice


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


def _get_config_file(dirs: list[Path]) -> Path:
    dirs = [dirs] if not isinstance(dirs, list) else dirs
    for _dir in dirs:
        if Path.joinpath(_dir, "config.yaml").is_file():
            return _dir / "config.yaml"
        if Path.joinpath(_dir, "config.yml").is_file():
            return _dir / "config.yml"
        for f in (Path.glob(_dir, "config.*")):
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


class Config:
    def __init__(self, base_dir: Path = None):
        #  We don't know if it's completion at this point cli is not loaded.  BASH will hang if first_run wizard is started. Updated in cli.py all_commands_callback if completion
        self.is_completion = env.is_completion
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
        self.sticky_workspace_file = self.cache_dir / "last_workspace"
        self.sanitize_file = self.dir / "redact.yaml"

        self.data = self.get_file_data(self.file) or {}
        self.forget: int | None = self.data.get("forget_ws_after", self.data.get("forget_account_after"))
        self.default_workspace = "default"  # if they still use old `central_info` it is transformed to `default` in ConfigData model
        self.last_workspace, self.last_cmd_ts, self.last_workspace_msg_shown, self.last_workspace_expired = self.get_last_workspace()
        self._workspace = self.get_workspace_from_args()
        self.set_attributes()
        self.snow = None  # snow proxy is deprecated

    def set_attributes(self):
        self._normalized_workspace = self._workspace.replace(" ", "_")
        try:
            c = ConfigData(workspace=self.workspace, **self.data)
        except ValidationError as e:
            econsole.print("\n".join([line for line in str(e).splitlines() if "errors.pydantic.dev" not in line]))
            sys.exit(1)
        self.base_url = c.current_workspace.classic.base_url
        self.username = c.current_workspace.classic.username
        self.cache_client_days = c.current_workspace.cache_client_days
        self.webhook = c.current_workspace.classic.webhook
        self.wss_key = c.current_workspace.classic.webhook.token
        self.defined_workspaces: list[str] = list(c.workspaces.keys())
        self.is_old_cfg = True if "workspaces" not in self.data else False
        if self.is_old_cfg:
            config_dict = c.model_dump(exclude={"workspace", "central_info"}, exclude_none=True, exclude_unset=True)
            workspaces: dict[str, Any] = config_dict.get("workspaces")
            if workspaces and "default" in workspaces:
                config_dict["workspaces"] = {"default": workspaces["default"], **{k: v for k, v in workspaces.items() if k != "default"}}
            self.data = config_dict
        self.ssl_verify = c.current_workspace.ssl_verify if c.current_workspace.ssl_verify is not None else c.ssl_verify
        self.debug = False if c is None else c.debug
        self.debugv = False if c is None else c.debugv
        self.dev = c.dev_options
        self.central_info = {} if c is None else c.classic_info
        self.classic = c.current_workspace.classic
        self.glp = c.current_workspace.glp
        self.cnx = c.current_workspace.central
        self.workspace_config = c.current_workspace.model_dump()
        self.workspace_object = c.current_workspace
        if "snow" in c.extra:
            self.deprecation_warnings = ["Snow Proxy functionality is deprecated, as it was never tested.  Please open an issue, if you need the functionality."]
        else:
            self.deprecation_warnings = None
        extras = [k for k in c.extra if k != "snow"]
        if extras:
            self.deprecation_warnings = self.deprecation_warnings or []
            self.deprecation_warning += [f'The following configuration items [dim italic]({", ".join(extras)})[/] were found in the config, but are not recognized by [cyan]cencli[/]']

    def __bool__(self):
        return len(self.data) > 0 and self.workspace in self.data

    def __len__(self):
        return len(self.data)

    @property
    def workspace(self) -> str:
        return self._workspace

    @workspace.setter
    def workspace(self, workspace: str):
        self._workspace = workspace
        self.set_attributes()

    @property
    def closed_capture_file(self) -> Path:
        file = self.log_dir / "raw-capture-closed.json"
        if file.exists():
            return file
        if self.capture_file.exists():
            file.write_text(f"{self.capture_file.read_text().rstrip().rstrip(',')}\n]")
            return file
        raise FileNotFoundError(f"Neither {file} nor {self.capture_file} exist.  Run tests with 'mock_tests: false' (under dev_options:) in the config to populate the capture file.")

    @property
    def workspaces(self) -> dict[str, Any]:
        return self.data.get("workspaces", {})

    @property
    def is_cop(self):
        return False if self.base_url is None or self.base_url.endswith("arubanetworks.com") else True

    # not used but may be handy
    @property
    def tokens(self):
        return self.central_info.get("token")

    @property
    def valid(self):
        return self.workspace in self.data.get("workspaces", {}) or self.workspace in self.data

    @property
    def token_store(self):
        return self.data.get(
            "token_store",
            {"type": "local", "path": str(self.dir / ".cache")}
        )

    @property
    def tok_file(self) -> Path:
        return Path(self.cache_dir / f'tok_{self.classic.customer_id}_{self.classic.client_id}.json') if self.classic.ok else None

    @property
    def cnx_tok_file(self) -> Path:
        return Path(self.cache_dir / f'cnx_tok_{self._normalized_workspace}_{self.classic.client_id}.json') if self.classic.client_id else None

    @property
    def cache_file(self):
        return self.default_cache_file if self.workspace in ["central_info", "default"] else self.cache_dir / f"{self._normalized_workspace}.json"

    @property
    def cache_file_ok(self):
        return self.cache_file.is_file() and self.cache_file.stat().st_size > 0

    @property
    def last_command_file(self):
        return self.cache_dir / "last_command" if self.workspace in ["central_info", "default"] else self.cache_dir / f"{self._normalized_workspace}_last_command"

    @property
    def export_dir(self) -> Path:
        # if they are already in export dir navigate back to top for output
        outdir: Path = self.outdir / "cencli-config-export"
        if "cencli-config-export" in outdir.parent.parts[1:]:
            outdir = outdir.parent
            while outdir.name != "cencli-config-export":
                outdir = outdir.parent

        return outdir

    @property
    def new_config(self) -> str | None:
        if not self.is_old_cfg:
            return
        example_str = "\n# See Example at link below for all options.\n"
        example_str += "# https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/config/config.yaml.example"
        data_str = yaml.safe_dump(self.data, sort_keys=False)
        return f"CFG_VERSION: 2\n\n{data_str}{example_str}\n"

    def get_cnx_url(self, classic_base_url: str | None):
        if not classic_base_url:  # This can occur if they use --workspace flag with an account that is not configured
            return

        cluster_name = [k for k, v in CLUSTER_URLS.items() if v["classic"] == classic_base_url.lower()]
        if cluster_name:
            return CLUSTER_URLS[cluster_name[0]]["cnx"]

    def get(self, key: str, default: Any = None, *, workspace_only: bool = False) -> Any:
        # prefer setting at the workspace config level first
        #config format v1 (classic)
        if self.workspace:
            if key in self.data.get(self.workspace, {}):
                return self.data[self.workspace][key]

            if "workspaces" in self.data and key in self.data["workspaces"].get(self.workspace, {}):
                return self.data["workspaces"][self.workspace][key]

        # fallback to global
        if not workspace_only and key in self.data:
            return self.data.get(key, default)

        return default

    def get_last_workspace(self) -> tuple[str | None, float | None, bool | None]:
        """Gathers contents of last_workspace returns tuple with values.

        last_workspace file stores: name of last workspace, timestamp of last command, numeric bool if big (will forget) msg has been displayed.
            expiration is calculated based on the value of workspace_will_forget and delta between last_command timestamp and now.


        Returns:
            tuple[None, str | None, float | bool | None, bool]:
                last_workspace, timestamp of last cmd using the workspace, if initial will_forget_msg has been displayed, if workspace is expired
        """
        if self.sticky_workspace_file.is_file():
            last_workspace_data = [row for row in self.sticky_workspace_file.read_text().split("\n") if row != ""]  # we don't add \n at end of file, but to handle it just in case
            if last_workspace_data:
                last_workspace = last_workspace_data[0]
                last_cmd_ts = self.sticky_workspace_file.stat().st_mtime if len(last_workspace_data) < 2 else float(last_workspace_data[1])
                big_msg_displayed = False if len(last_workspace_data) < 3 else bool(int(last_workspace_data[2]))
                expired = True if self.forget is not None and time.time() > last_cmd_ts + (self.forget * 60) else False
                return last_workspace, last_cmd_ts, big_msg_displayed, expired
        return None, None, False, None

    def update_last_workspace_file(self, workspace: str, last_cmd_ts: int | float = round(time.time(), 2), msg_shown: bool = False):
        self.sticky_workspace_file.parent.mkdir(exist_ok=True)
        self.sticky_workspace_file.write_text(f"{workspace}\n{last_cmd_ts}\n{int(msg_shown)}")

    @staticmethod
    def get_file_data(import_file: Path, text_ok: bool = False, model: Any = None) -> dict | list:
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
        if not (import_file.exists() and import_file.stat().st_size > 0):
            return

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

    def get_workspace_from_args(self) -> str:
        """Determine account to use based on arguments & last_workspace file.

        Method does no harm / triggers no errors.  Any errors are handled
        in account_name_callback after cli is loaded.  We need to determine the
        account during init to load the cache for auto completion.

        Returns:
            str: The workspace to use based on --workspace --ws -d flags and last_workspace file.
        """
        # No printing, any printing messes with completion
        # env_ws = env.get("ARUBACLI_ACCOUNT", env.get("CENCLI_WORKSPACE", ""))
        if "-d" in sys.argv or " -d " in str(sys.argv) or str(sys.argv).rstrip("']").endswith("-d"):
            return self.default_workspace
        elif [arg for arg in sys.argv if arg.startswith("-") and arg.count("-") == 1 and "d" in arg]:
            return self.default_workspace
        elif "--workspace" in sys.argv:
            workspace = sys.argv[sys.argv.index("--workspace") + 1]
        elif "--ws" in sys.argv:
            workspace = sys.argv[sys.argv.index("--ws") + 1]
        else:
            workspace = self.default_workspace if not env.workspace else env.workspace

        if workspace in ["central_info", "default"]:
            if self.forget and self.last_workspace_expired:
                pass  # all_commands_callback will handle messaging can't do here, along with last_workspace file reset.
            else:
                workspace = self.last_workspace or workspace
        elif (workspace in self.data or workspace in self.data.get("workspaces", {})) and workspace != env.workspace:
            if self.forget is not None and self.forget > 0:
                self.update_last_workspace_file(workspace)

        return workspace

    def _cnx_first_run(self, workspace_dict: dict) -> dict | None:
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
            base_url = self.get_cnx_url(classic_base_url=workspace_dict["classic"]["base_url"])
            print("\n[cyan]Client ID[reset] and [cyan]Client Secret[reset] are [dim red]required[/] for New Central.")
            print("Refer to [link='https://developer.arubanetworks.com/new-central/docs/generating-and-managing-access-tokens']HPE Aruba devhub[/] for details on how to generate the tokens.")
            print("\n[yellow]:information:[/]  Press return to skip New Central Configuration.  [dim italic][cyan]cencli[/] currently has limitted support for New Central[/]\n")
            client_id = ask("[dim italic]New Central/GreenLake[/] client id", default=client_id)
            if not client_id or not client_id.strip():
                return

            client_secret = ask("[dim italic]New Central/GreenLake[/] client secret")

            workspace_dict["glp"] = {
                "base_url": GLP_BASE_URL,
                "client_id": client_id,
                "client_secret": client_secret
            }
            workspace_dict["central"] = {"base_url": base_url}

            if not client_secret:
                econsole.print("[dark_orange3]:warning:[/]  client_secret is required.")
                continue

            return workspace_dict

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
            choice = ask("Central Cluster", choices=clusters.menu_names)
            if choice.lower() == "other":
                print(f"Provide [dim italic]Classic Central[/] API gateway URL in the format [cyan]{CLUSTER_URLS['us5']['classic']}")
                choice = ask("[dim italic]Classic Central[/] API Gateway URL")
                base_url = choice.rstrip("/")
            else:
                base_url = clusters[choice.lower()]["classic"]

            # get common variables
            # TODO pycentral library tokeStoreUtil makes customer_id optional, but load and refresh don't  so we need it here just
            # so the file has the expected name.  Would be nice just to use the format tok_account_name.json
            print("\nYour [cyan]customer id[/cyan] can be found by clicking the user icon in the upper right of the Central UI")
            customer_id = ask("customer id")
            print("\n[cyan]Client ID[reset] and [cyan]Client Secret[reset] can be found after creating Tokens in Central UI -> API Gateway -> System Apps & Tokens")
            print("You can double click the field in the table to select then copy, it will copy the entire token even with the token truncated with ...")
            client_id = ask("[dim italic]Classic Central[/] client id")
            client_secret = ask("[dim italic]Classic Central[/] client secret")

            workspace_dict = {
                "classic": {
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
            access_token = ask("[dim italic]Classic Central[/] Access Token")
            if access_token:
                refresh_token = ask("[dim italic]Classic Central[/] Refresh Token")
            username = ask("username")
            if username.endswith("@hpe.com"):
                print("\n[red]You need to use token Auth or configure a user with an external email")
                print("[red]The OAUTH Flow does not work with hpe.com users (SSO).")
                print(f"[red]ignoring username {username}.")
                password = None
            elif not username:
                username = password = None
                print()  # They did not enter a username.  CR is for correct format of config output
            else:
                password = ask("password", password=True)

            valid = False
            if access_token:
                workspace_dict["classic"]["tokens"] = {
                    "access": access_token
                }
                valid = True
                if refresh_token:
                    workspace_dict["classic"]["tokens"]["refresh"] = refresh_token
            if username and password:
                workspace_dict["classic"]["username"] = username
                workspace_dict["classic"]["password"] = password
                valid = True

            if not valid:
                econsole.print("[dark_orange3]:warning:[/]  At least one of [dark_olive_green2]username/password[/] OR [dark_olive_green2]access/refresh tokens[/] must to be provided.")
                continue

            _with_cnx = self._cnx_first_run(workspace_dict)
            workspace_dict = {"workspaces": {"default": _with_cnx or workspace_dict}}
            workspace_dict = f"{yaml.safe_dump(workspace_dict, sort_keys=False)}{config_comments}"
            Console().rule("\n\n[bold cyan]Resulting Configuration File Content")
            _config_data = workspace_dict if not password else workspace_dict.replace(password, "*********")
            print(_config_data)
            Console().rule()
            if confirm("\nContinue?"):
                print(f"\n\n[cyan]Writing to {self.file}")
                self.file.write_text(workspace_dict)
                break
            else:
                if not confirm("Retry Entries?"):
                    econsole.print("[dark_orange3]:warning:[/]  Aborted")
                    sys.exit(1)


if __name__ == "__main__":
    file = Path(__file__).parent / "delme.yaml"
    file_text = "\n".join([line for line in file.read_text().splitlines() if not line.lstrip().startswith("#")])
    data = yaml.safe_load(file_text)
    config = ConfigData(**data)
    ...