from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MissionRuleSnapshotResponse(BaseModel):
    snapshot_id: UUID
    mission_id: str
    version: int
    rules: list[dict[str, Any]]
    checksum: str
    created_at: datetime
    activated_at: datetime
    created_by: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MissionRuleSnapshotListResponse(BaseModel):
    mission_id: str
    items: list[MissionRuleSnapshotResponse]