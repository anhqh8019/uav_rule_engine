import hashlib
import json
from datetime import UTC, datetime

from fastapi import HTTPException, status

from bts_monitoring.database.models.mission_rule import (
    MissionRuleModel,
)
from bts_monitoring.database.models.mission_rule_snapshot import (
    MissionRuleSnapshotModel,
)
from bts_monitoring.repositories.mission_rule_snapshot_repository import (
    MissionRuleSnapshotRepository,
)


class MissionRuleSnapshotService:
    def __init__(
        self,
        repository: MissionRuleSnapshotRepository,
    ) -> None:
        self.repository = repository

    async def create_snapshot(
        self,
        *,
        mission_id: str,
        rules: list[MissionRuleModel],
        created_by: str | None = None,
    ) -> MissionRuleSnapshotModel:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        snapshot_rules = [
            {
                "event_type": rule.event_type,
                "enabled": rule.enabled,
                "config": dict(rule.config or {}),
                "rule_version": rule.version,
            }
            for rule in rules
            if rule.enabled
        ]

        if not snapshot_rules:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    f"Mission '{normalized_mission_id}' "
                    "does not have any enabled rule"
                ),
            )

        snapshot_rules.sort(
            key=lambda item: item["event_type"]
        )

        checksum = self.calculate_checksum(
            snapshot_rules
        )

        version = await self.repository.get_next_version(
            normalized_mission_id
        )

        now = datetime.now(UTC)

        snapshot = MissionRuleSnapshotModel(
            mission_id=normalized_mission_id,
            version=version,
            rules=snapshot_rules,
            checksum=checksum,
            created_at=now,
            activated_at=now,
            created_by=created_by,
        )

        return await self.repository.create(snapshot)

    async def get_latest_snapshot(
        self,
        mission_id: str,
    ) -> MissionRuleSnapshotModel:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        snapshot = await self.repository.get_latest(
            normalized_mission_id
        )

        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No rule snapshot found for mission "
                    f"'{normalized_mission_id}'"
                ),
            )

        return snapshot

    async def get_snapshot_by_version(
        self,
        *,
        mission_id: str,
        version: int,
    ) -> MissionRuleSnapshotModel:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        snapshot = await self.repository.get_by_version(
            mission_id=normalized_mission_id,
            version=version,
        )

        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Snapshot version {version} not found "
                    f"for mission '{normalized_mission_id}'"
                ),
            )

        return snapshot

    async def list_snapshots(
        self,
        mission_id: str,
    ) -> list[MissionRuleSnapshotModel]:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        return await self.repository.list_by_mission(
            normalized_mission_id
        )

    @staticmethod
    def calculate_checksum(
        rules: list[dict],
    ) -> str:
        canonical_json = json.dumps(
            rules,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical_json.encode("utf-8")
        ).hexdigest()