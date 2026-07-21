import logging

from bts_monitoring.infrastructure.cache.mission_rule_cache import (
    MissionRuleCache,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
)



logger = logging.getLogger(__name__)


class CachedMissionRuleProvider(
    MissionRuleProvider
):
    def __init__(
        self,
        *,
        cache: MissionRuleCache,
        fallback_provider: MissionRuleProvider,
    ) -> None:
        self.cache = cache
        self.fallback_provider = fallback_provider

    async def get_active_rules(
        self,
        mission_id: str,
    ) -> list[MissionRuleDefinition]:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        cached_rules = await self.cache.get(
            normalized_mission_id
        )

        if cached_rules is not None:
            logger.debug(
                "Mission-rule cache hit",
                extra={
                    "mission_id": (
                        normalized_mission_id
                    )
                },
            )
            print("========== CACHE HIT ==========")
            return cached_rules
        print("========== CACHE MISS ==========")
        logger.debug(
            "Mission-rule cache miss",
            extra={
                "mission_id": normalized_mission_id
            },
        )

        rules = (
            await self.fallback_provider
            .get_active_rules(
                normalized_mission_id
            )
        )

        # Cache cả danh sách rỗng để tránh DB bị query
        # liên tục đối với mission chưa có active rule.
        await self.cache.set(
            mission_id=normalized_mission_id,
            rules=rules,
        )

        return rules