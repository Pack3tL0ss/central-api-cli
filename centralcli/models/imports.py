from __future__ import annotations

import asyncio
import time
from typing import Any, Coroutine, Dict, Generator, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, RootModel, field_validator

from centralcli import cache, utils
from centralcli.render import Spinner

from ..cache import Cache, CacheInvDevice, CacheInvMonDevice, CacheSub
from ..constants import SiteStates, state_abbrev_to_pretty
from .common import MpskStatus


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
    def short_to_long(cls, v: str | None) -> str | None:
        if v is None:
            return

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
            _country = data.get("country") or ""
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


class BySubId():
    def __init__(self, cache_sub: CacheSub, devices: list[ImportSubDevice] = None):
        self.cache_sub = cache_sub
        self.devices = devices or []

    @property
    def ids(self) -> list[str]:
        return [d.inv.id for d in self.devices]

    def __add__(self, other):
        self.devices += [other] if not isinstance(other, list) else other

    def append(self, other):
        self.devices += [other] if not isinstance(other, list) else other

    def __repr__(self) -> str:
        return f"<{self.__module__}.{type(self).__name__} ({self.cache_sub.name}: assigning {len(self)} of {self.cache_sub.available}|{'TOO MANY' if self.is_overrun else 'OK'}) object at {hex(id(self))}>"

    def __len__(self) -> int:
        return len(self.devices)

    def __iter__(self) -> Generator[CacheInvMonDevice, None, None]:
        for dev in self.devices:
            yield dev.inv

    @property
    def is_overrun(self) -> bool:
        return len(self.devices) > self.cache_sub.available

    async def _get_confirm_msgs(self, tags: bool = False, is_update: bool = True) -> list[Coroutine]:
        tasks = [
            asyncio.create_task(dev._get_confirm_msg(tags_override=tags and dev.tags)) for dev in self.devices
        ]
        return await asyncio.gather(*tasks)

    def get_confirm_msg(self, tags: bool = False, max: int = 12) -> str:
        confirm_header = f"\n[deep_sky_blue1]\u2139[/]  [dark_olive_green2]Assigning[/] {self.cache_sub.summary_text}|[magenta]Qty being assigned[/magenta][dim]:[/dim] {len(self)}"
        confirm_msgs = asyncio.run(self._get_confirm_msgs(tags=tags))
        return "\n".join([confirm_header, utils.summarize_list(confirm_msgs, color=None, max=max)])


class _ImportSubDevice(BaseModel):
    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True, ignored_types=(CacheSub,))
    serial: str = Field(alias=AliasChoices("serial", "SERIAL"))
    tags: Optional[dict[str, str]] = Field(None, alias=AliasChoices("tags", "tag", "TAG", "TAGS"))
    archived: Optional[bool] = Field(None, alias=AliasChoices("archived", "archive", "ARCHIVED", "ARCHIVE"))
    subscription: Optional[str] = Field(alias=AliasChoices("subscription", "license", "services", "SUBSCRIPTION"))

    @field_validator("subscription")
    @classmethod
    def _normalize_subscription(cls, v: str) -> str:
        return v.lower().replace("_", "-")

    @field_validator("tags", mode="before")
    @classmethod
    def _convert_csv_tags(cls, v: str | dict[str, str]) -> dict[str, str]:
        if isinstance(v, str):
            v = v.replace(",", " ")
            return dict(map(lambda pair: map(str.strip, pair.split(":")), v.split()))

        return v.lower().replace("_", "-")

class ImportSubDevice(_ImportSubDevice):
    _sub_object: CacheSub | None = None
    _sub_fetched: bool = False
    _inv_object: CacheInvDevice | None = None
    _inv_fetched: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def sub(self):
        if self.subscription is None:
            return None
        if not self._sub_object:
            self._sub_object = cache.get_sub_identifier(self.subscription, silent=True, best_match=True)
            self._sub_fetched = True

        return self._sub_object

    @property
    def exact_sub(self) -> bool:
        if self.subscription is None or self.sub is None:
            return False
        return self.subscription in [field for field in [self.sub.id, self.sub.key] if field]

    async def _get_inv_object(self) -> CacheInvDevice | None:
        inv_dev = cache.InvDB.search(cache.Q.serial == self.serial)  # this is much faster than calling cache.get_combined_inv_dev_identifier > 4x faster this method is about .1s per lookup
        if inv_dev is None and cache.responses.inv is None:
            return cache.get_inv_identifier(self.serial, exit_on_fail=False)
        self._inv_fetched = True
        self._inv_object = None if inv_dev is None else CacheInvDevice(inv_dev[0])
        return self._inv_object

    @property
    def inv(self) -> CacheInvDevice | None:
        if not self._inv_fetched:
            self._inv_object = asyncio.run(self._get_inv_object())
        return self._inv_object

    @property
    def assigned(self) -> bool:
        return False if self.inv is None else self.inv.assigned

    @property
    def exists(self) -> bool:
        return False if self.inv is None else True

    @property
    def override_tags_warning(self) -> str:
        _tag_msg = "" if not self.tags else f"|[green]GreenLake[/] tags: {', '.join([f'[turquoise2]{k}[/]: [turquoise4]{v}[/]' for k, v in self.tags.items()])}"
        return f"{self.inv.help_text}{_tag_msg}"

    @property
    def glp_id(self):
        return self.inv.id

    @property
    def sub_is_id(self) -> bool:
        return False if not self.subscription else utils.is_resource_id(self.subscription)

    @property
    def help_text(self) -> str:
        return self.get_confirm_msg()

    @property
    def rich_help_text(self) -> str:
        if self.inv is not None:
            return f"{self.inv.rich_help_text}"
        return f"[dark_orange3]\u26a0[/]  {self.serial}  Does not exist in [green]GreenLake[/]"

    def __rich__(self) -> str:
        return self.get_confirm_msg()

    async def _get_confirm_msg(self, tags_override: bool = False, skipped: bool = False) -> str:
        if not self.tags:
            return self.rich_help_text

        _tag_msg = f"[green]GreenLake[/] tags: {', '.join([f'[turquoise2]{k}[/]: [turquoise4]{v}[/]' for k, v in self.tags.items()])}"
        _tag_msg = f"|{_tag_msg}" if not tags_override else f"|[dark_orange3]\u26a0[/]  [bright_red]IGNORING[/] {_tag_msg}"
        _ret = f"{self.rich_help_text}{_tag_msg}"
        if skipped and not self.assigned:
            _error = "Not assigned to Aruba Central app in GLP." if self.exists else "Does not exist in GLP"
            return f"[dark_orange3]\u26a0[/]  [bright_red]SKIPPING[/] {_ret}... [dim italic]{_error}[/]"
        else:
            return _ret

    def get_confirm_msg(self, tags_override: bool = False, skipped: bool = False) -> str:
        return asyncio.run(self._get_confirm_msg(tags_override=tags_override, skipped=skipped))

class ImportSubDevices(RootModel):
    root: list[ImportSubDevice]

    def __init__(self, cache: Cache, data: list[Dict[str, Any]]) -> None:
        super().__init__([ImportSubDevice(cache=cache, **s) for s in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    def __rich__(self) -> str:
        return "\n".join([dev.__rich__() for dev in self.root])

    @property
    def help_text(self) -> str:
        return self.__rich__()

    @property
    def warning_ovverride_tags(self) -> str:
        if not self.has_tags:
            return ""
        return "  [dark_orange3]\u26a0[/]  Tags found in Import file are being overriden by [cyan]--tags[/] flag:"

    @property
    def warning_skip_not_assigned(self) -> str:
        if not self.not_assigned_devs:
            return ""
        return "\n".join([dev.get_confirm_msg(skipped=True) for dev in self.not_assigned_devs])

    @property
    def by_serial(self) -> dict[str, ImportSubDevice]:
        return {dev.serial: dev for dev in self.root}

    @property
    def has_tags(self) -> bool:
        return any([True for dev in self.root if dev.tags])

    @property
    def not_assigned_devs(self) -> list[ImportSubDevice]:
        return [dev for dev in self.root if not dev.assigned]

    @property
    def assigned_devs(self) -> list[ImportSubDevice]:
        return [dev for dev in self.root if dev.assigned]

    def ids_by_tags(self) -> Generator[tuple[dict[str, str], list[str]], None, None]:
        ret = {}
        hash_to_tags  = {}
        for dev in self.root:
            if dev.tags:
                tag_hash = hash(str(dev.tags))
                utils.update_dict(ret, tag_hash, [dev.glp_id])
                if tag_hash not in hash_to_tags:
                    hash_to_tags[tag_hash] = dev.tags

        for tag_hash, ids in ret.items():
            yield hash_to_tags[tag_hash], ids

    def get(self, serial: str, default: Any = None) -> ImportSubDevice | Any:
        return self.by_serial.get(serial, default)

    def get_confirm_msg(self, sub: CacheSub, pad: int = 4, max: int = 15, tags_override: bool = False, is_update: bool = False) -> str:
        if tags_override:
            devs = [*[dev for dev in self.root if dev.tags], *[dev for dev in self.root if not dev.tags]]
        else:
            devs = self.root

        if is_update:
            devs = [dev for dev in devs if dev.assigned]

        dev_msgs = [dev.get_confirm_msg(tags_override=tags_override) for dev in devs if sub == dev.sub]
        return utils.summarize_list(dev_msgs, pad=pad, max=max, color=None).lstrip()

    def serials_by_subscription(self) -> dict[str, list[str]]:
        subs = set(dev.subscription for dev in self.root)
        out_dict = {sub: [] for sub in subs}
        _ = [out_dict[dev.subscription].append(dev.serial) for dev in self.root]
        return out_dict

    async def get_inv_objects(self) -> list[CacheInvDevice | None]:
        # tasks = [asyncio.create_task(lambda: dev.inv) for dev in self.root]
        tasks = [asyncio.create_task(dev._get_inv_object()) for dev in self.root]
        # return [await t for t in tasks]
        return await asyncio.gather(*tasks)

    def serials_by_subscription_id(self, assigned: bool = None) -> dict[str, BySubId]:
        subs: set[CacheSub] = set(cache.get_sub_identifier(dev.subscription, silent=True, best_match=True) for dev in self.root)
        out_dict = {sub.id: BySubId(sub) for sub in subs}
        start = time.perf_counter()
        with Spinner(f"Gathering [green]GreenLake[/] device_ids from cache for [cyan]{len(self)}[/] devices found in import") as spinner:
            inv_devs = asyncio.run(self.get_inv_objects())  # TODO if import has id field spot check a few to see that the id matches up with the serial in the cache, then assume all id fields are good... no need to lookup all of them
        duration = round(time.perf_counter() - start, 3)
        spinner.succeed(f"[cyan]{len(self)}[/] device_ids fetched in {duration}s.  Avg: {round(duration / len(self), 3)}")

        for inv_dev, dev in zip(inv_devs, self.root):
            if inv_dev is None or inv_dev.id is None:
                continue
            if assigned and inv_dev.assigned:
                out_dict[dev.sub.id].append(dev)
            elif assigned is False and not inv_dev.assigned:
                out_dict[dev.sub.id].append(dev)
            else:  # assigned is None / All devices
                out_dict[dev.sub.id].append(dev)

        # This logic distributes devices to subscriptions based on available qty
        _additional_subs = {}
        for sub_id in out_dict:
            if len(out_dict[sub_id].devices) > out_dict[sub_id].cache_sub.available:
                this_subs: list[CacheSub] = cache.get_sub_identifier(out_dict[sub_id].cache_sub.name, silent=True, all_match=True)
                if len(utils.listify(this_subs)) > 1:
                    devs = out_dict[sub_id].devices
                    exact_matches = [devs.pop(devs.index(d)) for d in devs if d.exact_sub]
                    out_dict[sub_id].devices = exact_matches or devs
                    if not devs:  # They have specified more subs than it appears they have available, but they are exact matches by sub id so just send it
                        continue
                    if out_dict[sub_id].cache_sub.available > len(exact_matches):
                        _slice = slice(0, out_dict[sub_id].cache_sub.available - len(exact_matches))
                        out_dict[sub_id].devices += [devs.pop(devs.index(d)) for d in devs[_slice]]
                    if not devs:
                        continue
                    for csub in this_subs[1:]:
                        _additional_subs[csub.id] = BySubId(csub, devices=[devs.pop(devs.index(d)) for d in devs[0:csub.available]])
                    if devs:  # devices remain after assigning to all available subs, dump remainder... best_match
                        out_dict[sub_id].devices += devs

        out_dict = {**out_dict, **_additional_subs}
        return out_dict
