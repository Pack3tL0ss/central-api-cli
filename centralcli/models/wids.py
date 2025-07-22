from __future__ import annotations

from pydantic import BaseModel, RootModel, Field, ConfigDict, AliasChoices, field_serializer
from typing import Optional, List
from datetime import datetime
from ..objects import DateTime

class WidsItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    acknowledged: Optional[bool] = Field(default=None)
    containment_status: Optional[str] = Field(default_factory=str)
    classification: Optional[str] = Field(default_factory=str)
    classification_method: Optional[str] = Field(default_factory=str)
    cust_id: Optional[str] = Field(default_factory=str)
    encryption: Optional[str] = Field(default_factory=str)
    first_det_device: Optional[str] = Field(default_factory=str)
    first_det_device_name: Optional[str] = Field(default_factory=str)
    first_seen: Optional[datetime] = Field(default=None)
    group: Optional[str] = Field(default_factory=str, alias=AliasChoices("group_name", "group"))
    id: Optional[str] = Field(default_factory=str)
    labels: Optional[str] = Field(default_factory=str)
    lan_mac: Optional[str] = Field(default_factory=str)
    last_det_device: Optional[str] = Field(default_factory=str)
    last_det_device_name: Optional[str] = Field(default_factory=str)
    last_seen: Optional[datetime] = Field(default=None)
    mac_vendor: Optional[str] = Field(default_factory=str)
    name: Optional[str] = Field(default_factory=str)
    signal: Optional[int] = Field(default_factory=int)
    ssid: Optional[str] = Field(default_factory=str)

    @field_serializer("first_seen", "last_seen")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        return DateTime(dt.timestamp(), "mdyt")


class Wids(RootModel):
    root: List[WidsItem]

    def __init__(self, data: List[dict]) -> None:
        super().__init__([WidsItem(**w) for w in data])

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self) -> int:
        return len(self.model_dump())