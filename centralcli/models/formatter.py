from pydantic import BaseModel, field_serializer, ConfigDict
from typing import Dict, Any
from datetime import datetime
import pendulum
from ..objects import DateTime


class CloudAuthUploadStats(BaseModel):
    completed: int
    failed: int
    total: int


class CloudAuthUploadResponse(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: pendulum.from_timestamp(v).to_day_datetime_string(),
        },
    )
    details: Dict[str, Any]
    status: str
    stats: CloudAuthUploadStats
    submittedAt: datetime
    lastUpdatedAt: datetime
    durationNanos: int
    fileName: str

    @field_serializer("lastUpdatedAt", "submittedAt")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        return DateTime(dt.timestamp())