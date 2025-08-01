from __future__ import annotations

from typing import Any, Dict, Optional, KeysView
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, RootModel, model_validator, field_validator
from ..constants import CLUSTER_URLS, ClusterName

class Defaults:
    def __init__(self):
        self.cache_client_days: int = 90
        self.glp_base_url: str = "https://global.api.greenlake.hpe.com"
        self.account: str = "default"
        self.config_version: int = 2

default = Defaults()

def _ensure_base_urls(data: dict) -> Dict[str, Any]:
    if "cluster" in data and data["cluster"] in CLUSTER_URLS:
        url_dict = CLUSTER_URLS[data["cluster"]]
        if "central" in data and not data["central"].get("base_url"):
            data["central"]["base_url"] = url_dict["cnx"]
        else:
            data["central"] = {"base_url": url_dict["cnx"]}

        if "classic" in data and not data["classic"].get("base_url"):
            data["classic"]["base_url"] = url_dict["classic"]

    return data

# CNX New Central
class Glp(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    base_url: Optional[str] = default.glp_base_url

    @property
    def ok(self) -> bool:
        return True if self.client_id and self.client_secret else False

    @property
    def token_info(self) -> Dict[str, Dict[str, str]]:
        return {
            "glp": {
                "base_url": self.base_url,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        }


class Central(BaseModel):  # New Central
    base_url: Optional[str] = None


class Tokens(BaseModel):
    access: Optional[str] = Field(..., alias=AliasChoices("access", "access_token", "access-token"))
    refresh: Optional[str] = Field(..., alias=AliasChoices("refresh", "refresh_token", "refresh-token"))
    webhook: Optional[str] = Field(None, alias=AliasChoices("webhook", "webhook_token", "webhook-token"))
    wss_key: Optional[str] = None

    @property
    def ok(self) -> bool:
        return True if self.access and self.refresh else False


class Webhook(BaseModel):
    token: Optional[str] = None
    port: Optional[int] = 9443


class Classic(BaseModel):
    base_url: Optional[str] = None
    customer_id: Optional[str] = None
    client_id: Optional[str] = Field(None, alias=AliasChoices("client_id", "client-id"))
    client_secret: Optional[str] = Field(None, alias=AliasChoices("client_secret", "client-secret"))
    username: Optional[str] = Field(None, alias=AliasChoices("username", "user"))
    password: Optional[str] = Field(None, alias=AliasChoices("password", "pass"))
    tokens: Optional[Tokens] = Field(None, alias=AliasChoices("tokens", "token"))
    webhook: Optional[Webhook] = Webhook()

    @field_validator("customer_id", mode="before")
    @classmethod
    def to_str(cls, v: int | str):
        return str(v)

    @field_validator("base_url", mode="before")
    @classmethod
    def _handle_trailing_slash(cls, v: str):
        return v.rstrip("/")

    @property
    def ok(self) -> bool:
        if all([self.client_id, self.client_secret, any([self.tokens is not None and self.tokens.ok, self.username and self.password])]):
            return True
        return False

    @property
    def central_info(self) -> Dict[str, Dict[str, str]]:
        return {
            "central_info": {
                "base_url": self.base_url,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password
            }
        }


class WorkSpace(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    cluster: Optional[ClusterName] = ClusterName.us6
    ssl_verify: Optional[bool] = Field(None, alias=AliasChoices("ssl_verify", "ssl-verify", "verify_ssl", "verify-ssl"))
    glp: Optional[Glp] = Field(Glp(), alias=AliasChoices("glp", "GLP"))
    central: Optional[Central] = Field(Central(), alias=AliasChoices("central", "new_central", "cnx", "new-central"))
    classic: Optional[Classic] = Classic()
    cache_client_days: Optional[int] = default.cache_client_days

    @property
    def ok(self) -> bool:
        cluster_ok = True if self.cluster else False
        if not cluster_ok:
            if self.classic.base_url and self.classic.ok:
                return True
            return False
        return self.classic.ok

    @model_validator(mode="before")
    def ensure_base_urls(data: dict) -> Dict[str, Any]:
        return _ensure_base_urls(data)

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return default


class Workspaces(RootModel):
    root: Optional[Dict[str, WorkSpace]] = None

    def __init__(self, **kwargs) -> None:
        super().__init__({k: WorkSpace(**v) for k, v in kwargs.items()})

    def __getitem__(self, item: str):
        return self.root[item]

    def __getattr__(self, name):
        if hasattr(self.root, name):
            return getattr(self.root, name)
        if name in self.root:
            return self.root[name]

        raise AttributeError(f"'{type(self)}' object has no attribute '{name}'")

    def __iter__(self):
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    @property
    def default(self):
        if "default" not in self.root and "central_info" in self.root:
            return self.root["central_info"]
        else:
            return self.root["default"]

    # __getattr__ would get this defining for benefit of IDE
    def get(self, key: str, default: Any = None) -> Any:
        return self.root.get(key, default)

    def keys(self) -> KeysView:
        return self.model_dump().keys()


class DevOptions(BaseModel):
    limit: Optional[int] = None
    sanitize: Optional[bool] = False
    capture_raw: Optional[bool] = False


class ConfigData(BaseModel):
    workspace: str
    model_config = ConfigDict(extra="allow")
    CFG_VERSION: Optional[int] = default.config_version
    workspaces: Optional[Workspaces] = Workspaces()
    central_info: Optional[Classic] = Classic()
    ssl_verify: Optional[bool] = True
    debug: Optional[bool] = False
    debugv: Optional[bool] = False
    cache_client_days: Optional[int] = default.cache_client_days
    forget_ws_after: Optional[int] = Field(None, alias=AliasChoices("forget_ws_after", "forget_account_after"))
    dev_options: Optional[DevOptions] = DevOptions()

    @model_validator(mode="before")
    def pre_parse(data: dict) -> Dict[str, Any]:
        if data.get("debugv") is True and not data.get("debug"):
            data = {**data, "debug": True}

        _ws_data = data.get("workspaces", {}).get(data["workspace"], {})
        data["central_info"] = _ws_data.get("classic", {})
        tok_key = "tokens" if "token" not in data.get("default", data.get("central_info", "{}")) else "token"
        wh_tok_key = "webhook_token" if "webhook_token" in data["central_info"].get(tok_key, {}) else "webhook"
        if data["central_info"].get(tok_key, {}).get(wh_tok_key):
            wh_token = data["central_info"][tok_key][wh_tok_key]
            del data["central_info"][tok_key][wh_tok_key]
            if "webhook" in data["central_info"]:
                data["central_info"]["webhook"]["token"] = wh_token
            else:
                data["central_info"]["webhook"] = {"token": wh_token}

        return data

    @model_validator(mode="before")
    def convert_v1_config(data: dict) -> Dict[str, Any]:
        # Old config format, convert to new
        if "workspaces" in data:
            return data
        workspaces = {k: v for k, v in data.items() if isinstance(v, dict) and (v.get("client_id") or v.get("base_url"))}
        data = {k: v for k, v in data.items() if k not in workspaces.keys()}
        if workspaces.get("central_info"):
            workspaces["default"] = workspaces.pop("central_info")

        top_level = list(WorkSpace.model_fields.keys())
        for k, v in workspaces.items():
            out = {key: v[key] for key in top_level if key in v}
            out["classic"] = {k: v for k, v in v.items() if k not in out}
            if "cluster" not in out and "base_url" in out["classic"]:
                out["cluster"] = {v["classic"]: k for k, v in CLUSTER_URLS.items()}.get(out["classic"]["base_url"].rstrip("/"))
            workspaces[k] = out

        data["workspaces"] = workspaces

        dev_options = list(DevOptions.model_fields.keys())
        for key in dev_options:
            if key in data:
                data["dev_options"] = data.get("dev_options") or {}
                data["dev_options"][key] = data.pop(key)

        return data

    @property
    def current_workspace(self) -> WorkSpace:
        return self.workspaces.get(self.workspace, WorkSpace())

    @property
    def extra(self):
        return self.__pydantic_extra__

    @property
    def classic_info(self) -> Dict[str, str | Dict[str, str]]:
        if self.central_info is None:
            return {}
        out = {
            "base_url": self.central_info.base_url,
            "client_id": self.central_info.client_id,
            "client_secret": self.central_info.client_secret,
            "customer_id": self.central_info.customer_id,
            "username": self.central_info.username,
            "password": self.central_info.password
            }
        if self.central_info.tokens:
            out["token"] = {
                "access_token": self.central_info.tokens.access,
                "refresh_token": self.central_info.tokens.refresh
            }
        return out

    # @property
    # def cnx_info(self) -> Dict[str, str]:
    #     glp_info: Glp = self.workspaces.get(self.workspace, {}).get("glp")
    #     if not glp_info:
    #         return {"glp": {}}
    #     return glp_info.token_info