from __future__ import annotations
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

# SNOW Response

class SysTargetSysId(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class SysImportSet(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class ImportSetRun(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class SysTransformMap(BaseModel):
    display_value: Optional[str] = None
    link: Optional[str] = None


class Result(BaseModel):
    u_comments_to_customer: Optional[str] = None
    template_import_log: Optional[str] = None
    u_service_offering: Optional[str] = None
    sys_updated_on: Optional[str] = None
    u_urgency: Optional[str] = None
    sys_target_sys_id: SysTargetSysId
    u_watch_list: Optional[str] = None
    u_reported_by: Optional[str] = None
    u_business_service: Optional[str] = None
    sys_updated_by: Optional[str] = None
    u_short_description: Optional[str] = None
    sys_created_on: Optional[str] = None
    sys_import_set: SysImportSet
    u_additional_comments: Optional[str] = None
    sys_created_by: Optional[str] = None
    sys_import_row: Optional[str] = None
    sys_row_error: Optional[str] = None
    u_work_notes: Optional[str] = None
    u_subcategory: Optional[str] = None
    u_state: Optional[str] = None
    u_attachment_type: Optional[str] = None
    import_set_run: ImportSetRun
    u_contact_type: Optional[str] = None
    u_attachment_encoded_code: Optional[str] = None
    u_description: Optional[str] = None
    u_close_notes: Optional[str] = None
    u_call_back: Optional[str] = None
    sys_import_state_comment: Optional[str] = None
    sys_class_name: Optional[str] = None
    u_priority: Optional[str] = None
    sys_id: Optional[str] = None
    u_external_source: Optional[str] = None
    sys_transform_map: SysTransformMap
    u_external_ticket: Optional[str] = None
    u_servicenow_number: Optional[str] = None
    u_resolved_by_group: Optional[str] = None
    u_assigned_to: Optional[str] = None
    u_raised_severity: Optional[str] = None
    u_hold_reason: Optional[str] = None
    sys_target_table: Optional[str] = None
    sys_mod_count: Optional[str] = None
    u_assignment_group: Optional[str] = None
    u_affected_user: Optional[str] = None
    u_impact: Optional[str] = None
    sys_tags: Optional[str] = None
    sys_import_state: Optional[str] = None
    u_contact_number: Optional[str] = None
    u_category: Optional[str] = None
    u_cause_code: Optional[str] = None
    u_close_code: Optional[str] = None
    u_configuration_item: Optional[str] = None
    u_cause_sub_code: Optional[str] = None
    u_attachment_name: Optional[str] = None


class SnowResponse(BaseModel):
    result: Result
