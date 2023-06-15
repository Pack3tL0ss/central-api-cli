from datetime import datetime
from typing import List, Optional, Union

import pendulum
from pydantic import BaseModel, Field, validator


# fields from Response.output after cleaner
class Inventory(BaseModel):
    sku: str
    type: str
    mac: str
    model: str
    serial: str
    services: Union[List[str], str]

def pretty_dt(dt: datetime) -> str:
    return pendulum.from_timestamp(dt.timestamp(), tz="local").to_day_datetime_string()

class WIDS(BaseModel):
    acknowledged: Optional[bool] = Field(default=None)
    containment_status: Optional[str] = Field(default_factory=str)
    classification: Optional[str] = Field(default_factory=str)
    classification_method: Optional[str] = Field(default_factory=str)
    cust_id: Optional[str] = Field(default_factory=str)
    encryption: Optional[str] = Field(default_factory=str)
    first_det_device: Optional[str] = Field(default_factory=str)
    first_det_device_name: Optional[str] = Field(default_factory=str)
    first_seen: Optional[datetime] = Field(default=None)
    group: Optional[str] = Field(default_factory=str, alias="group_name")
    id: Optional[str] = Field(default_factory=str)
    _labels: Optional[str] = Field(default_factory=str, alias="labels")
    lan_mac: Optional[str] = Field(default_factory=str)
    last_det_device: Optional[str] = Field(default_factory=str)
    last_det_device_name: Optional[str] = Field(default_factory=str)
    last_seen: Optional[datetime] = Field(default=None)
    mac_vendor: Optional[str] = Field(default_factory=str)
    name: Optional[str] = Field(default_factory=str)
    signal: Optional[str] = Field(default_factory=str)
    ssid: Optional[str] = Field(default_factory=str)

    # custom input conversion for timestamp
    _normalize_datetimes = validator("first_seen", "last_seen", allow_reuse=True)(pretty_dt)

    class Config:
        json_encoders = {
            datetime: lambda v: pendulum.from_format(v.rstrip("Z"), "YYYY-MM-DDTHH:mm:s.SSS").to_day_datetime_string(),
        }

class WIDS_LIST(BaseModel):
    rogue: Optional[List[WIDS]] = Field(default_factory=list)
    interfering: Optional[List[WIDS]] = Field(default_factory=list)
    neighbor: Optional[List[WIDS]] = Field(default_factory=list)
    suspectrogue: Optional[List[WIDS]] = Field(default_factory=list)

