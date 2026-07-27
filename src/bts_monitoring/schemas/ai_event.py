from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoundingBoxSchema(BaseModel):
    x1: float = Field(ge=0)
    y1: float = Field(ge=0)
    x2: float = Field(ge=0)
    y2: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "BoundingBoxSchema":
        if self.x2 <= self.x1:
            raise ValueError("bbox.x2 must be greater than bbox.x1")
        if self.y2 <= self.y1:
            raise ValueError("bbox.y2 must be greater than bbox.y1")
        return self


class AIEventCreate(BaseModel):
    mission_id: str | None = Field(default=None, min_length=1, max_length=100)
    site_id: str = Field(min_length=1, max_length=100)
    camera_id: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=50)
    confidence: float = Field(ge=0, le=1)

    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=50)

    captured_at: datetime
    received_at: datetime

    bbox: BoundingBoxSchema | None = None
    polygon: list[Any] | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence_uri: str | None = Field(default=None, max_length=1000)

    rule_snapshot_id: UUID | None = None
    rule_snapshot_version: int | None = Field(default=None, ge=1)
    rule_snapshot_checksum: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-fA-F]{64}$",
    )


class AIEventResponse(AIEventCreate):
    event_id: UUID

    model_config = ConfigDict(from_attributes=True)


class AIEventListResponse(BaseModel):
    items: list[AIEventResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)