from pydantic import BaseModel
from typing import Optional
from enum import Enum


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


class SnowResponse(Result):
    result: Result

# _example_snow_payload = {
#         "u_affected_user": "blah",
#         "u_assignment_group":"TE-sn-servicenow",
#         "u_business_service": "",
#         "u_call_back": False,
#         "u_category": "",
#         "u_contact_type": "integration",
#         "u_description": "",
#         "u_configuration_item": "valid snow config item",
#         "u_external_source": "40 chars",
#         "u_external_ticket": "40 chars",
#         "u_raised_severity": 2,
#         "u_reported_by": "valid TE ID",
#         "u_servicenow_number": "Only on Update",
#         "u_service_offering": "snow valid service offering",
#         "u_short_description":"Test Ticket Mandatory Create 160 char",
#         "u_state": "resolved",
#         "u_subcategory": "must be valid sub cat of cat",
#         "u_work_notes": "4000 chars",
#         "u_attachment_name":"Integration_Sample.txt",
#         "u_attachment_type":"text/plain",
#         "u_attachment_encoded_code":"SW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA0KSW50ZWdyYXRpb25fU2FtcGxlLnR4dA==",
#         "u_impact": 2,
#         "u_urgency": 2,
#         "u_watch_list":"TE308801,TE163762"
#     }
#
#


class HighMedLow(str, Enum):
    High = 1
    Medium = 2
    Low = 3


class SnowCreate(BaseModel):
    u_affected_user: Optional[str] = None
    u_assignment_group: str
    u_business_service: Optional[str] = None
    u_call_back: Optional[bool] = None
    u_category: Optional[str] = None
    u_contact_type: Optional[str] = None
    u_description: Optional[str] = None
    u_configuration_item: Optional[str] = None
    u_external_source: Optional[str] = None
    u_external_ticket: Optional[str] = None
    u_raised_severity: Optional[int] = None
    u_reported_by: Optional[str] = None
    u_service_offering: Optional[str] = None
    u_short_description: str  # = Field(..., le=160)
    u_state: Optional[str] = None
    u_subcategory: Optional[str] = None
    u_work_notes: Optional[str] = None
    u_attachment_name: Optional[str] = None
    u_attachment_type: Optional[str] = None
    u_attachment_encoded_code: Optional[str] = None
    u_impact: Optional[HighMedLow] = None
    u_urgency: Optional[HighMedLow] = None
    u_watch_list: Optional[str] = None


class SnowUpdate(BaseModel):
    u_affected_user: Optional[str] = None
    u_assignment_group: Optional[str] = None
    u_business_service: Optional[str] = None
    u_call_back: Optional[bool] = None
    u_category: Optional[str] = None
    u_contact_type: Optional[str] = None
    u_description: Optional[str] = None
    u_configuration_item: Optional[str] = None
    u_external_source: Optional[str] = None
    u_external_ticket: Optional[str] = None
    u_raised_severity: Optional[int] = None
    u_reported_by: Optional[str] = None
    u_servicenow_number: str
    u_service_offering: Optional[str] = None
    u_short_description: Optional[str] = None
    u_state: Optional[str] = None
    u_subcategory: Optional[str] = None
    u_work_notes: Optional[str] = None
    u_attachment_name: Optional[str] = None
    u_attachment_type: Optional[str] = None
    u_attachment_encoded_code: Optional[str] = None
    u_impact: Optional[HighMedLow] = None
    u_urgency: Optional[HighMedLow] = None
    u_watch_list: Optional[str] = None