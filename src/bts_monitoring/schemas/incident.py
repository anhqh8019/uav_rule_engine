from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bts_monitoring.core.enums import (
    IncidentSeverity,
    IncidentStatus,
)


class IncidentCreate(BaseModel):
    site_id: str
    camera_id: str | None = None
    source_event_id: UUID | None = None

    incident_type: str
    severity: IncidentSeverity

    title: str
    message: str | None = None

    deduplication_key: str

    first_seen_at: datetime
    last_seen_at: datetime


class IncidentResponse(BaseModel):
    incident_id: UUID

    site_id: str
    camera_id: str | None
    source_event_id: UUID | None

    incident_type: str
    severity: IncidentSeverity
    status: IncidentStatus

    title: str
    message: str | None

    deduplication_key: str

    first_seen_at: datetime
    last_seen_at: datetime

    occurrence_count: int

    acknowledged_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None

    assigned_to: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int


class IncidentAcknowledgeRequest(BaseModel):
    assigned_to: str | None = Field(
        default=None,
        max_length=255,
    )


class IncidentResolveRequest(BaseModel):
    message: str | None = Field(
        default=None,
        max_length=2000,
    )


class IncidentAssignRequest(BaseModel):
    assigned_to: str = Field(
        min_length=1,
        max_length=255,
    )