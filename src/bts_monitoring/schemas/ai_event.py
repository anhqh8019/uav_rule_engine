from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BoundingBoxSchema(BaseModel):
    x1: float = Field(ge=0)
    y1: float = Field(ge=0)
    x2: float = Field(ge=0)
    y2: float = Field(ge=0)


class AIEventCreate(BaseModel):
    mission_id: str | None = Field(
        default=None,
        max_length=100,
    )

    site_id: str = Field(
        min_length=1,
        max_length=100,
    )

    camera_id: str = Field(
        min_length=1,
        max_length=100,
    )

    event_type: str = Field(
        min_length=1,
        max_length=50,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    model_name: str
    model_version: str

    captured_at: datetime
    received_at: datetime

    bbox: BoundingBoxSchema | None = None
    polygon: list[Any] | None = None
    attributes: dict[str, Any] = Field(
        default_factory=dict,
    )
    evidence_uri: str | None = None

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


class AIEventResponse(AIEventCreate):
    event_id: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


class AIEventListResponse(BaseModel):
    items: list[AIEventResponse]
    total: int
    page: int
    page_size: int