from abc import ABC, abstractmethod

from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
)


class MissionRuleProvider(ABC):
    @abstractmethod
    async def get_active_rules(
        self,
        mission_id: str,
    ) -> list[MissionRuleDefinition]:
        """Lấy các rule đang active và enabled của mission."""
        raise NotImplementedError