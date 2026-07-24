from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
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
        repository: MissionRuleRepository,
    ) -> None:
        self.repository = repository

    async def get_active_rule_set(
        self,
        mission_id: str,
    ) -> MissionRuleSet:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        models = (
            await self.repository
            .list_active_by_mission(
                normalized_mission_id
            )
        )

        rules = [
            MissionRuleDefinition(
                mission_id=model.mission_id,
                event_type=model.event_type,
                enabled=model.enabled,
                config=dict(model.config or {}),
                version=model.version,
            )
            for model in models
        ]

        return MissionRuleSet(
            mission_id=normalized_mission_id,
            snapshot_id=None,
            snapshot_version=None,
            checksum=None,
            rules=rules,
        )