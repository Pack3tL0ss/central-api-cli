from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, AliasChoices, field_validator, RootModel
from typing import Optional, List, Dict, Any
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


