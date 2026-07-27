from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentAcknowledgeRequest(BaseModel):
    assigned_to: str | None = Field(default=None, min_length=1, max_length=255)


class IncidentResolveRequest(BaseModel):
    message: str | None = Field(default=None, min_length=1, max_length=2000)


class IncidentAssignRequest(BaseModel):
    assigned_to: str = Field(min_length=1, max_length=255)


class IncidentCreate(BaseModel):
    mission_id: str | None = Field(default=None, min_length=1, max_length=100)
    site_id: str = Field(min_length=1, max_length=100)
    camera_id: str = Field(min_length=1, max_length=100)
    source_event_id: UUID

    incident_type: str = Field(min_length=1, max_length=100)
    severity: str = Field(min_length=1, max_length=30)
    status: str = Field(default="open", min_length=1, max_length=30)

    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=2000)
    deduplication_key: str = Field(min_length=1, max_length=500)

    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int = Field(default=1, ge=1)

    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    assigned_to: str | None = Field(default=None, min_length=1, max_length=255)

    rule_snapshot_id: UUID | None = None
    rule_snapshot_version: int | None = Field(default=None, ge=1)
    rule_snapshot_checksum: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-fA-F]{64}$",
    )


class IncidentResponse(IncidentCreate):
    incident_id: UUID

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)