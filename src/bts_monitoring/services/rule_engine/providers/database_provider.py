from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
)
from bts_monitoring.repositories.mission_rule_snapshot_repository import (
    MissionRuleSnapshotRepository,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
    MissionRuleSet,
)


class DatabaseMissionRuleProvider(
    MissionRuleProvider
):
    def __init__(
        self,
        *,
        rule_repository: MissionRuleRepository,
        snapshot_repository: MissionRuleSnapshotRepository,
    ) -> None:
        self.rule_repository = rule_repository
        self.snapshot_repository = snapshot_repository

    async def get_active_rule_set(
        self,
        mission_id: str,
    ) -> MissionRuleSet:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        # Không cho inference dùng snapshot khi
        # mission hiện không có active rule.
        active_rules = (
            await self.rule_repository
            .list_active_by_mission(
                normalized_mission_id
            )
        )

        if not active_rules:
            return MissionRuleSet(
                mission_id=normalized_mission_id,
                rules=[],
                snapshot_id=None,
                snapshot_version=None,
                checksum=None,
            )

        snapshot = (
            await self.snapshot_repository
            .get_latest(
                normalized_mission_id
            )
        )

        # Tương thích dữ liệu cũ nếu mission active
        # nhưng chưa từng tạo snapshot.
        if snapshot is None:
            definitions = [
                MissionRuleDefinition(
                    mission_id=rule.mission_id,
                    event_type=rule.event_type,
                    enabled=rule.enabled,
                    config=dict(rule.config or {}),
                    version=rule.version,
                )
                for rule in active_rules
            ]

            return MissionRuleSet(
                mission_id=normalized_mission_id,
                rules=definitions,
                snapshot_id=None,
                snapshot_version=None,
                checksum=None,
            )

        definitions = [
            MissionRuleDefinition(
                mission_id=normalized_mission_id,
                event_type=str(item["event_type"]),
                enabled=bool(
                    item.get("enabled", True)
                ),
                config=dict(
                    item.get("config") or {}
                ),
                version=int(
                    item.get("rule_version", 1)
                ),
            )
            for item in snapshot.rules
        ]

        return MissionRuleSet(
            mission_id=normalized_mission_id,
            rules=definitions,
            snapshot_id=str(snapshot.snapshot_id),
            snapshot_version=snapshot.version,
            checksum=snapshot.checksum,
        )