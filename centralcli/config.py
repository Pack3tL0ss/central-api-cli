#!/usr/bin/env python3
#
# Author: Wade Wells github/Pack3tL0ss

from pathlib import Path
from typing import Any, List
import yaml
import json
import tablib

valid_ext = ['.yaml', '.yml', '.json', '.csv', '.tsv', '.dbf', '.xls', '.xlsx']


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
                self.outdir = self.dir.parent / "out"
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

        self.data = self.get_file_data(self.file) or {}
        self.debug = self.data.get("debug", False)
        self.debugv = self.data.get("debugv", False)
        self.account = None  # Updated by cli account callback

    def __bool__(self):
        return len(self.data) > 0

    def __len__(self):
        return len(self.data)

    def __getattr__(self, item: str, default: Any = None) -> Any:
        return self.data.get(item, default)

    # not used but may be handy
    @property
    def tokens(self):
        return self.data.get(self.account, {}).get("token", {})

    @property
    def cache_file(self):
        return self.default_cache_file if self.account == "central_info" else self.cache_dir / f"{self.account}.json"

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    @staticmethod
    def get_file_data(import_file: Path) -> dict:
        '''Return dict from yaml file.'''
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
                        raise UserWarning("Provide valid file with "
                                          "format/extension [.json/.yaml/.yml/.csv]!")
                except Exception as e:
                    raise UserWarning(f'Unable to load configuration from {import_file}\n{e.__class__}\n\n{e}')
