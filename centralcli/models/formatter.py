from pydantic import AliasChoices, BaseModel, field_serializer, ConfigDict, Field, field_validator
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
    duration_secs: float = Field(None, alias=AliasChoices("durationNanos", "duration_secs"))
    fileName: str

    @field_validator("duration_secs", mode="before")
    @classmethod
    def convert_duration(cls, duration: int) -> float:
        return round(duration / 1_000_000_000, 2)

    @field_serializer("lastUpdatedAt", "submittedAt")
    @classmethod
    def pretty_dt(cls, dt: datetime) -> DateTime:
        return None if datetime(1, 1, 1, 0, 0, tzinfo=dt.tzinfo) == dt else DateTime(dt.timestamp())
