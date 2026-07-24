from dataclasses import dataclass
from uuid import UUID

from bts_monitoring.services.rule_engine.engine import (
    RuleEngine,
)


@dataclass(frozen=True, slots=True)
class MissionRuleEngineContext:
    mission_id: str
    engine: RuleEngine

    snapshot_id: UUID | None
    snapshot_version: int | None
    checksum: str | None