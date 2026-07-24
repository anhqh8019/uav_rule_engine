from functools import lru_cache

from bts_monitoring.core.config import (
    get_settings,
)
from bts_monitoring.services.rule_engine.local_cache import (
    LocalRuleEngineCache,
)


@lru_cache
def get_local_rule_engine_cache(
) -> LocalRuleEngineCache:
    settings = get_settings()

    return LocalRuleEngineCache(
        ttl_seconds=(
            settings
            .rule_engine_local_cache_ttl_seconds
        ),
    )