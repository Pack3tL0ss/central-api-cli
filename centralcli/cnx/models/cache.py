from __future__ import annotations

from typing import Any, List, Dict, Optional, Literal

from pydantic import BaseModel, Field, AliasChoices, field_validator, model_validator
import pendulum
from functools import cached_property
from centralcli.render import unstyle
from centralcli import utils, log

class Subscription(BaseModel):
    id: str
    name: str = Field(alias=AliasChoices("tier", "name"))
    type: str = Field(alias=AliasChoices("type", "subscriptionType"))
    key: str
    qty: int = Field(alias=AliasChoices("qty", "quantity"))
    available: int = Field(alias=AliasChoices("available", "availableQuantity"))
    is_eval: bool = Field(alias=AliasChoices("is_eval", "isEval"))
    sku: str
    start_date: int = Field(alias=AliasChoices("start_date", "startTime"))
    end_date: int = Field(alias=AliasChoices("end_date", "endTime"))
    # -- Available fields that are not used --
    # created_at: int = Field(alias=AliasChoices("created_at", "createdAt"))
    # updated_at: int = Field(alias=AliasChoices("updated_at", "updatedAt"))
    # sku_description: str = Field(alias=AliasChoices("sku_description", "skuDescription"))
    # contract: Any
    # subscription_status: str | None = Field(alias=AliasChoices("subscription_status", "subscriptionStatus"))
    # tags: List[str] | None
    # product_type: str = Field(alias=AliasChoices("product_type", "productType"))
    # tier_description: Any = Field(alias=AliasChoices("tier_description", "tierDescription"))
    # quote: Optional[str]
    # po: Any
    # reseller_po: Any
    # def __init__(self, **kwargs):
    #     self.expired: bool = self._expired
    #     self.expiring_soon: bool = self._expiring_soon
    #     self.started: bool = self._started
    #     self.valid: bool = self._valid

    @cached_property
    def expired(self) -> bool:
        return pendulum.now(tz="UTC").timestamp() >= self.end_date

    @cached_property
    def expiring_soon(self) -> bool:
        return not self.expired and (pendulum.now(tz="UTC") + pendulum.duration(months=3) >= pendulum.from_timestamp(self.end_date))

    @cached_property
    def started(self) -> bool:
        return pendulum.now(tz="UTC").timestamp() >= self.start_date

    @cached_property
    def valid(self) -> bool:
        return self.started and not self.expired and self.available > 0

    @property
    def subscription_expires(self) -> int:
        return self.end_date

    @field_validator("type", mode="before")
    @classmethod
    def simplify_sub_type(cls, sub_type: str) -> str:
        return sub_type.removeprefix("CENTRAL_")

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, sub_name: str) -> str:
        return sub_name.lower().replace("_", "-")

    @model_validator(mode="before")
    def convert_none_strings(data: dict) -> Dict[str, Any]:
        def convert_dates(date_str: str):
            return pendulum.from_format(date_str.rstrip("Z"), "YYYY-MM-DDTHH:mm:ss.SSS", tz="UTC").int_timestamp

        time_fields = ["created_at", "createdAt", "updated_at", "updatedAt", "start_time", "startTime", "end_time", "endTime"]
        data = {k: v if not isinstance(v, str) or v != "NONE" else None for k, v in data.items()}
        return {k: v if k not in time_fields else convert_dates(v) for k, v in data.items() if v != "subscriptions/subscription"}


class SubCounts:
    __slots__ = ["total", "expired", "valid", "expiring_soon", "not_started"]

    def __init__(self, subs: List[Subscription]):
        self.total = len(subs)
        self.expired = len([s for s in subs if s.expired])
        self.valid = len([s for s in subs if s.valid])
        self.expiring_soon = len([s for s in subs if s.expiring_soon])
        self.not_started = len([s for s in subs if not s.started])

    def __rich__(self):
        ret = f"[magenta]Subscription counts[/] Total: [cyan]{self.total}[/], [green]Valid[/]: [cyan]{self.valid}[/], [red]Expired[/]: [cyan]{self.expired}[/]"
        if self.not_started:
            ret += f", [yellow]Not Started[/]: [cyan]{self.not_started}[/]"
        if self.expiring_soon:
            ret += f", [dark_orange3]Expiring Soon[/]: [cyan]{self.expiring_soon}[/]"

        return ret

    def __str__(self):
        return unstyle(self.__rich__())

class Subscriptions(BaseModel):
    items: List[Subscription]
    count: int
    offset: int
    total: int

    @cached_property
    def by_id(self) -> dict[str, dict[str, Any]]:
        return {
            sub.id: {k: v for k, v in sub.model_dump().items() if k != "id"}
            for sub in self.items
        }

    def __len__(self) -> int:
        return self.total

    def __bool__(self) -> bool:
        return bool(self.total)

    @cached_property
    def counts(self) -> SubCounts:
        return SubCounts(self.items)

    def output(self):
        return [
            {**sub.model_dump(), "status": "OK" if not sub.expired else "EXPIRED"}
            for sub in self.items
        ]

    def cache_dump(self):
        return [
            {**sub.model_dump(), "started": sub.started, "expired": sub.expired, "valid": sub.valid}
            for sub in self.items
        ]

    def get_inv_cache_fields(self, sub_id: str) -> dict[str, str | int]:
        if not sub_id or sub_id[0] not in self.by_id:
            return {
                "subscription_expires": None,
                "subscription_key": None,
                "services": None
            }

        sub = self.by_id[sub_id[0]]
        return {
            "subscription_expires": sub["end_date"],
            "subscription_key": sub["key"],
            "services": sub["name"]
        }


class InventoryDevice(BaseModel):
    id: str
    mac: str = Field(alias=AliasChoices("mac", "macAddress"))
    serial: str = Field(alias=AliasChoices("serial", "serialNumber"))
    sku: Optional[str] = Field(None, alias=AliasChoices("sku", "partNumber"))
    type: Optional[str] = Field(None, alias=AliasChoices("type", "deviceType"))
    model: Optional[str] = None
    created_at: int = Field(alias=AliasChoices("created_at", "createdAt"))
    updated_at: int = Field(alias=AliasChoices("updated_at", "updatedAt"))
    archived: Optional[bool] = None
    assigned: Optional[bool | None] = Field(None, alias=AliasChoices("assigned", "assignedState"))
    region: Optional[str] = None
    subscription: list[str] | str| None = None
    application: str | None = None

    @field_validator("application", mode="before")
    @classmethod
    def get_app_id(cls, app: dict[str, str] | None) -> list[str] | None:
        return None if not app else app["id"]

    @field_validator("subscription", mode="before")
    @classmethod
    def get_sub_ids(cls, subs: list[dict[str, str]] | None) -> list[str] | None:
        return None if not subs else [s["id"] for s in subs]

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def convert_dates(cls, date_str: str) -> int:
        return pendulum.from_format(date_str.rstrip("Z"), "YYYY-MM-DDTHH:mm:ss.SSS", tz="UTC").int_timestamp

    @field_validator("mac", mode="after")
    @classmethod
    def _normalize_mac(cls, mac: str) -> str:
        mac_out = utils.Mac(mac)
        if not mac_out.ok:
            log.warning(f"MAC Address {mac} passed into Inventory via import does not appear to be valid.", show=True, caption=True, log=True)
        return mac_out.cols.upper()

    @field_validator("assigned", mode="before")
    @classmethod
    def _assigned_to_bool(cls, value: str) -> bool | None:
        if value is None:
            return value

        return value == "ASSIGNED_TO_SERVICE"

    @cached_property
    def subscribed(self) -> bool:
        return bool(self.subscription)


class InvCounts:
    __slots__ = ["total", "expired", "expiring_soon", "subscribed", "no_subscription", "archived", "assigned"]

    def __init__(self, devs: list[InventoryDevice]):
        self.total = len(devs)
        self.subscribed = len([d for d in devs if d.subscribed])
        self.no_subscription = self.total - self.subscribed
        self.archived = len([d for d in devs if d.archived])
        self.assigned = len([d for d in devs if d.assigned])

    def __rich__(self):
        ret = f"[magenta]Inventory counts[/] Total: [cyan]{self.total}[/], [green]Subscription Assigned[/]: [cyan]{self.subscribed}[/]"
        if self.no_subscription:
            ret += f", [yellow]No Subscription Assigned[/]: [cyan]{self.no_subscription}[/]"
        if self.assigned:
            ret += f", [green]Assinged to Service[/]: [cyan]{self.assigned}[/]"
        if self.archived:
            ret += f", [dim][red]Archived[/]: [cyan]{self.archived}[/][/dim]"

        return ret

    def __str__(self):
        return unstyle(self.__rich__())


class Inventory(BaseModel):
    items: list[InventoryDevice]
    count: int
    offset: int
    total: int

    def __len__(self) -> int:
        return self.total

    def __bool__(self) -> bool:
        return bool(self.total)

    @property
    def by_id(self) -> dict[str, dict[str, Any]]:
        return {
            dev.id: {k: v for k, v in dev.model_dump().items() if k != "id"}
            for dev in self.items
        }

    @property
    def counts(self) -> InvCounts:
        return InvCounts(self.items)

    @model_validator(mode="before")
    def prep_for_cache(data: list[dict[str, int | dict[str, Any]]]) -> list[dict[str, int | dict[str, Any]]]:
        def _inv_type(dev_type: str, model: str | None) -> Literal["ap", "gw", "sw", "cx", "bridge", "sdwan"] | None:
                if dev_type is None:  # Only occurs when import data is passed into this model, inventory data from API should have the type
                    return None

                if dev_type == "IAP":
                    return "ap"
                if dev_type == "SWITCH":  # SWITCH, AP, GATEWAY, BRIDGE, SDWAN
                    aos_sw_models = ["2530", "2540", "2920", "2930", "3810", "5400"]  # current as of 2.5.8 not expected to change.  MAS not supported.
                    return "sw" if model[0:4] in aos_sw_models else "cx"

                return "gw" if dev_type == "GATEWAY" else dev_type.lower()

        items = [{k: v if k not in ["deviceType"] else _inv_type(v, model=dev.get("model")) for k, v in dev.items() if v != 'devices/device'} for dev in data.get("items", [])]
        return {**data, "items": items}

    @cached_property
    def by_serial(self) -> dict[str, dict[str, Any]]:
        return {s.serial: s.model_dump() for s in self.items}

async def get_inventory_with_sub_data(inv_data: Inventory, sub_data: Subscriptions) -> list[dict[str, Any]]:
    return [{"id": devid, **dev_data, **sub_data.get_inv_cache_fields(dev_data["subscription"])} for devid, dev_data in inv_data.by_id.items()]
