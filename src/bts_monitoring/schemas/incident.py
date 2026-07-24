from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    mission_id: str | None = Field(
        default=None,
        max_length=100,
    )

    site_id: str
    camera_id: str
    source_event_id: UUID

    incident_type: str
    severity: str
    status: str = "open"

    title: str
    message: str
    deduplication_key: str

    first_seen_at: datetime
    last_seen_at: datetime

    occurrence_count: int = 1

    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    assigned_to: str | None = None

    rule_snapshot_id: UUID | None = None

    rule_snapshot_version: int | None = Field(
        default=None,
        ge=1,
    )

    rule_snapshot_checksum: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )


class IncidentResponse(IncidentCreate):
    incident_id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )

class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int