import logging

from bts_monitoring.infrastructure.cache.mission_rule_cache import (
    MissionRuleCache,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleSet,
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

    async def get_active_rule_set(
            self,
            mission_id: str,
    ) -> MissionRuleSet:
        normalized = mission_id.strip().upper()

        cached_rule_set = (
            await self.cache.get_rule_set(
                normalized
            )
        )

        if cached_rule_set is not None:
            print(
                "REDIS CACHE HIT:",
                normalized,
                "version=",
                cached_rule_set.snapshot_version,
            )

            return cached_rule_set

        print("REDIS CACHE MISS:", normalized)

        rule_set = (
            await self.fallback_provider
            .get_active_rule_set(
                normalized
            )
        )

        if (
                rule_set.snapshot_id is not None
                and rule_set.snapshot_version is not None
                and rule_set.checksum is not None
        ):
            await self.cache.set_snapshot(
                mission_id=normalized,
                snapshot_id=rule_set.snapshot_id,
                version=rule_set.snapshot_version,
                checksum=rule_set.checksum,
                rules=rule_set.rules,
            )
        else:
            await self.cache.set(
                mission_id=normalized,
                rules=rule_set.rules,
            )

        return rule_set