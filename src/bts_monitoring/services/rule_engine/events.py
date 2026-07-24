from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RuleSnapshotActivatedEvent:
    mission_id: str
    snapshot_id: UUID
    snapshot_version: int
    checksum: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        mission_id: str,
        snapshot_id: UUID,
        snapshot_version: int,
        checksum: str,
    ) -> "RuleSnapshotActivatedEvent":
        return cls(
            mission_id=(
                mission_id.strip().upper()
            ),
            snapshot_id=snapshot_id,
            snapshot_version=snapshot_version,
            checksum=checksum,
            occurred_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)

        value["snapshot_id"] = str(
            self.snapshot_id
        )

        value["occurred_at"] = (
            self.occurred_at.isoformat()
        )

        return value