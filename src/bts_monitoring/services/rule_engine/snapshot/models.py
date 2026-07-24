from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MissionRuleSnapshot:
    snapshot_id: UUID
    mission_id: str
    version: int
    checksum: str
    rules: list[dict[str, Any]] = field(
        default_factory=list,
    )