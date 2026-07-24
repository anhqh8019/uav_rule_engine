from abc import ABC, abstractmethod

from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
    MissionRuleSet,
)


class MissionRuleProvider(ABC):
    @abstractmethod
    async def get_active_rule_set(
        self,
        mission_id: str,
    ) -> MissionRuleSet:
        raise NotImplementedError

    async def get_active_rules(
        self,
        mission_id: str,
    ) -> list[MissionRuleDefinition]:
        rule_set = await self.get_active_rule_set(
            mission_id
        )

        return rule_set.rules