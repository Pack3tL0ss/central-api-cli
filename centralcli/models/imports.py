from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, RootModel, field_validator

from .. import Cache, config, utils
from ..cache import CacheInvDevice
from ..constants import SiteStates, state_abbrev_to_pretty
from .common import MpskStatus

if TYPE_CHECKING:
    from ..cache import CacheSub


cache = Cache(config=config)
class ImportSite(BaseModel):
    # model_config = ConfigDict(extra="allow", use_enum_values=True)
    model_config = ConfigDict(use_enum_values=True)
    site_name: str = Field(..., alias=AliasChoices("site_name", "site", "name"))
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None  # Field(None, min_length=3)
    zipcode: Optional[str | int] = Field(None, alias=AliasChoices("zip", "zipcode"))
    latitude: Optional[str | float] = Field(None, alias=AliasChoices("lat", "latitude"))
    longitude: Optional[str | float] = Field(None, alias=AliasChoices("lon", "longitude"))

    @field_validator("state")
    @classmethod
    def short_to_long(cls, v: str) -> str:
        if v.lower() == "district of columbia":
            return "District of Columbia"

        try:
            return SiteStates(state_abbrev_to_pretty.get(v.upper(), v.title())).value
        except ValueError:
            return SiteStates(v).value


class ImportSites(RootModel):
    root: List[ImportSite]

    def __init__(self, data: List[Dict[str, Any]]) -> None:
        formatted = self._convert_site_key(data)
        super().__init__([ImportSite(**s) for s in formatted])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    @staticmethod
    def _convert_site_key(_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def auto_usa(data: Dict[str, str | int | float]) -> str | None:
            _country = data.get("country", "")
            if _country.isdigit():  # Data from large customer had country as '1' for some sites
                _country = ""

            if not _country and data.get("state") and data["state"].upper() in [kk.upper() for k, v in state_abbrev_to_pretty.items() for kk in [k, v]]:
                return "United States"
            if _country.upper() in ["USA", "US"]:
                return "United States"

            return _country or None

        _data = [
            {
                **inner.get("site_address", {}),
                **inner.get("geolocation", {}),
                **{k: v for k, v in inner.items() if k not in ["site_address", "geolocation"]},
                "country": auto_usa(inner),
            }
            for inner in _data
        ]

        return _data


# API-FLAW order actually matters here, it throws an error if not Name,Client Role,Status
# Also no longer accepts MPSK field
class ImportMPSK(BaseModel):
    name: str = Field(alias=AliasChoices("name", "Name"))
    role: str = Field(alias=AliasChoices("client_role", "role", "Client Role"))
    status: MpskStatus = Field(MpskStatus.enabled, alias=AliasChoices("status", "Status"))
    # mpsk: str = Field(alias=AliasChoices("mpsk", "MPSK"))   # This does not appear to be accepted anymore


class ImportMPSKs(RootModel):
    root: List[ImportMPSK]

    def __init__(self, data: List[Dict[str, Any]]) -> None:
        # formatted = [ImportsMPSKAllFields(m) for m in data]
        super().__init__([ImportMPSK(**s) for s in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

# MAC Imports for Cloud Auth
class ImportMAC(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    mac: str = Field(alias=AliasChoices("mac", "mac_address", "Mac Address"))
    name: str = Field(alias=AliasChoices("name", "Name", "client_name", "Client Name"))

class ImportMACs(RootModel):
    root: List[ImportMAC]

    def __init__(self, data: List[Dict[str, Any]]) -> None:
        super().__init__([ImportMAC(**s) for s in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)


# Device Imports / device add / site, group, subscription assignment
class ImportDevice(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    serial: str = Field(alias=AliasChoices("serial", "SERIAL"))
    mac: Optional[str] = Field(alias=AliasChoices("mac", "MAC", "mac_address", "Mac Address"))
    group: Optional[str] = Field(alias=AliasChoices("group", "GROUP", "group_name"))
    site: Optional[str] = Field(alias=AliasChoices("site", "SITE", "site_name"))
    subscription: Optional[str] = Field(alias=AliasChoices("subscription", "license", "services"))

    @field_validator("subscription")
    @classmethod
    def _normalize_subscription(cls, v: str) -> str:
        return v.lower().replace("_", "-")

    @property
    def sub_object(self) -> CacheSub:
        return cache.get_sub_identifier(self.subscription, silent=True, best_match=True)

    @property
    def inv_object(self) -> CacheInvDevice | None:
        for _ in range(0, 2):
            inv_dict = cache.inventory_by_serial.get(self.serial)
            if inv_dict:
                return CacheInvDevice(inv_dict)
            if not cache.responses.inv:
                asyncio.run(cache.refresh_inv_db())

    @property
    def sub_is_id(self) -> bool:
        return utils.is_resource_id(self.subscription)


class BySubId:
    def __init__(self, cache_sub: CacheSub, devices: list[str] = None):
        self.cache_sub = cache_sub
        self.devices = devices or []

    def __add__(self, other):
        self.devices += [other] if not isinstance(other, list) else other

    def append(self, other):
        self.devices += [other] if not isinstance(other, list) else other

    def __len__(self) -> int:
        return len(self.devices)


class ImportDevices(RootModel):
    root: list[ImportDevice]

    def __init__(self, data: list[Dict[str, Any]]) -> None:
        super().__init__([ImportDevice(**s) for s in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    def serials_by_subscription(self) -> dict[str, list[str]]:
        subs = set(dev.subscription for dev in self.root)
        out_dict = {sub: [] for sub in subs}
        _ = [out_dict[dev.subscription].append(dev.serial) for dev in self.root]
        return out_dict

    def serials_by_subscription_id(self) -> dict[str, BySubId]:
        subs: set[CacheSub] = set(cache.get_sub_identifier(dev.subscription, silent=True, best_match=True) for dev in self.root)
        out_dict = {sub.id: BySubId(sub) for sub in subs}
        _ = [out_dict[dev.sub_object.id].append(dev.inv_object.id) for dev in self.root if dev.inv_object is not None and dev.inv_object.id is not None]
        # skipped = [dev for dev in self.root if dev.inv_object is None or dev.inv_object.id is None]

        # This logic distributes devices to subscriptions based on available qty
        _additional_subs = {}
        for sub_id in out_dict:
            if len(out_dict[sub_id].devices) > out_dict[sub_id].cache_sub.available:
                this_subs: list[CacheSub] = cache.get_sub_identifier(out_dict[sub_id].cache_sub.name, silent=True, all_match=True)
                if len(utils.listify(this_subs)) > 1:
                    dev_ids = out_dict[sub_id].devices
                    out_dict[sub_id].devices = dev_ids[0:out_dict[sub_id].cache_sub.available]
                    _start = out_dict[sub_id].cache_sub.available
                    for csub in this_subs[1:]:
                        _slice = slice(_start, _start + csub.available)
                        _dev_ids = dev_ids[_slice]
                        _start += csub.available
                        if not dev_ids:
                            break
                        _additional_subs[csub.id] = BySubId(csub, devices=_dev_ids)
                    if dev_ids[_start:]:  # devices remain after assigning to all available subs, dump remainder i best_match
                        out_dict[sub_id].devices += dev_ids[_start:]


        out_dict = {**out_dict, **_additional_subs}

        return out_dict


