from datetime import datetime
from typing import List, Optional, Union

import pendulum
from pydantic import ConfigDict, BaseModel, Field, validator


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
    # TODO json_encoders above removed from pydantic in v2 below was what migration tool came up with but causes last command dump
    # to file to puke [TypeError: keys must be str, int, float, bool or None, not type]
    # json.dumps @ line 370 of clicommon _display_results
            # if stash:
            #     config.last_command_file.write_text(
            # ==>        json.dumps({k: v for k, v in kwargs.items() if k != "config"})
            #     )

    # Pydantic v2 conversion result that causes the    !!! Pinning to pydantic <2 until fully migrated
    # model_config = ConfigDict(json_encoders={
    #     datetime: lambda v: pendulum.from_format(v.rstrip("Z"), "YYYY-MM-DDTHH:mm:s.SSS").to_day_datetime_string(),
    # })

class WIDS_LIST(BaseModel):
    rogue: Optional[List[WIDS]] = Field(default_factory=list)
    interfering: Optional[List[WIDS]] = Field(default_factory=list)
    neighbor: Optional[List[WIDS]] = Field(default_factory=list)
    suspectrogue: Optional[List[WIDS]] = Field(default_factory=list)

# Client Cache
class Client(BaseModel):
    mac: str = Field(default_factory=str)
    name: str = Field(default_factory=str)
    ip: str = Field(default_factory=str)
    type: str = Field(default_factory=str)
    connected_port: str = Field(default_factory=str)
    connected_serial: str = Field(default_factory=str)
    connected_name: str = Field(default_factory=str)
    site: str = Field(default_factory=str)
    group: str = Field(default_factory=str)
    last_connected: datetime = Field(default=None)