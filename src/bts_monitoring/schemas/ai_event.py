from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BoundingBoxSchema(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class AIEventCreate(BaseModel):
    site_id: str = Field(
        min_length=1,
        max_length=64,
    )

    camera_id: str = Field(
        min_length=1,
        max_length=64,
    )

    event_type: str = Field(
        min_length=1,
        max_length=50,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    model_name: str = Field(
        min_length=1,
        max_length=100,
    )

    model_version: str = Field(
        min_length=1,
        max_length=50,
    )

    captured_at: datetime
    received_at: datetime

    bbox: BoundingBoxSchema | None = None
    polygon: list[tuple[float, float]] | None = None

    attributes: dict[str, Any] = Field(
        default_factory=dict,
    )

    evidence_uri: str | None = Field(
        default=None,
        max_length=1000,
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