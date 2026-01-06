from pydantic import BaseModel, field_serializer, ConfigDict
from typing import Any
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
    details: dict[str, Any] | None
    status: str
    stats: CloudAuthUploadStats
    submittedAt: datetime | None
    lastUpdatedAt: datetime | None
    durationNanos: int
    fileName: str

    @field_serializer("lastUpdatedAt", "submittedAt")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        if datetime(1, 1, 1, 0, 0, tzinfo=dt.tzinfo) == dt:
            return None
        return DateTime(dt.timestamp())