from typing import Any

from uuid import UUID

from bts_monitoring.core.enums import (
    RuleEventType,
)
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.services.rule_engine.engine import (
    RuleEngine,
)
from bts_monitoring.services.rule_engine.local_cache import (
    LocalRuleEngineCache,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
)
from bts_monitoring.services.rule_engine.rules.fire import (
    FireImmediateRule,
)
from bts_monitoring.services.rule_engine.rules.rust import (
    RustSeverityRule,
)
from bts_monitoring.services.rule_engine.rules.smoke import (
    SmokePersistenceRule,
)
from bts_monitoring.services.rule_engine.rules.tower_tilt import (
    TowerTiltRule,
)

from bts_monitoring.services.rule_engine.context import (
    MissionRuleEngineContext,
)

class MissionRuleEngineFactory:
    def __init__(
        self,
        *,
        event_repository: AIEventRepository,
        provider: MissionRuleProvider,
        local_cache: LocalRuleEngineCache,
    ) -> None:
        self.event_repository = event_repository
        self.provider = provider
        self.local_cache = local_cache

    async def create(
            self,
            mission_id: str,
    ) -> MissionRuleEngineContext:
        normalized = mission_id.strip().upper()

        cached_context = await self.local_cache.get(
            normalized
        )

        if cached_context is not None:
            print(
                "LOCAL RULE ENGINE CACHE HIT:",
                normalized,
                "version=",
                cached_context.snapshot_version,
            )

            return cached_context

        lock = await self.local_cache.get_lock(
            normalized
        )

        async with lock:
            cached_context = (
                await self.local_cache.get(
                    normalized
                )
            )

            if cached_context is not None:
                return cached_context

            rule_set = (
                await self.provider
                .get_active_rule_set(
                    normalized
                )
            )

            if not rule_set.rules:
                raise RuntimeError(
                    "No active rules found for mission "
                    f"'{normalized}'"
                )

            engine = self._build_engine(
                rule_set.rules
            )

            snapshot_id = None

            if rule_set.snapshot_id:
                snapshot_id = UUID(
                    rule_set.snapshot_id
                )

            context = MissionRuleEngineContext(
                mission_id=normalized,
                engine=engine,
                snapshot_id=snapshot_id,
                snapshot_version=(
                    rule_set.snapshot_version
                ),
                checksum=rule_set.checksum,
            )

            await self.local_cache.set(
                mission_id=normalized,
                context=context,
            )

            print(
                "LOCAL RULE ENGINE CACHE CREATED:",
                normalized,
                "version=",
                context.snapshot_version,
            )

            return context

    def _build_engine(
        self,
        definitions: list[
            MissionRuleDefinition
        ],
    ) -> RuleEngine:
        rules = []

        for definition in definitions:
            if not definition.enabled:
                continue

            event_type = RuleEventType(
                definition.event_type
            )

            config = definition.config

            if event_type == RuleEventType.FIRE:
                rules.append(
                    FireImmediateRule(
                        confidence_threshold=(
                            self._get_float(
                                config,
                                "confidence_threshold",
                            )
                        ),
                    )
                )

            elif event_type == RuleEventType.SMOKE:
                rules.append(
                    SmokePersistenceRule(
                        confidence_threshold=(
                            self._get_float(
                                config,
                                "confidence_threshold",
                            )
                        ),
                        required_events=(
                            self._get_int(
                                config,
                                "required_events",
                            )
                        ),
                        window_seconds=(
                            self._get_int(
                                config,
                                "window_seconds",
                            )
                        ),
                    )
                )

            elif event_type == RuleEventType.RUST:
                rules.append(
                    RustSeverityRule(
                        minimum_area_ratio=(
                            self._get_float(
                                config,
                                "minimum_area_ratio",
                            )
                        ),
                        medium_area_ratio=(
                            self._get_float(
                                config,
                                "medium_area_ratio",
                            )
                        ),
                        high_area_ratio=(
                            self._get_float(
                                config,
                                "high_area_ratio",
                            )
                        ),
                    )
                )

            elif (
                event_type
                == RuleEventType.TOWER_TILT
            ):
                rules.append(
                    TowerTiltRule(
                        warning_angle=(
                            self._get_float(
                                config,
                                "warning_angle",
                            )
                        ),
                        high_angle=(
                            self._get_float(
                                config,
                                "high_angle",
                            )
                        ),
                        critical_angle=(
                            self._get_float(
                                config,
                                "critical_angle",
                            )
                        ),
                        require_valid_calibration=(
                            self._get_bool(
                                config,
                                (
                                    "require_valid_"
                                    "calibration"
                                ),
                                default=True,
                            )
                        ),
                    )
                )

        if not rules:
            raise RuntimeError(
                "Mission rule set does not contain "
                "any supported enabled rule"
            )

        return RuleEngine(
            event_repository=self.event_repository,
            rules=rules,
        )

    @staticmethod
    def _get_float(
        config: dict[str, Any],
        key: str,
    ) -> float:
        if key not in config:
            raise ValueError(
                f"Missing rule config field: {key}"
            )

        return float(config[key])

    @staticmethod
    def _get_int(
        config: dict[str, Any],
        key: str,
    ) -> int:
        if key not in config:
            raise ValueError(
                f"Missing rule config field: {key}"
            )

        return int(config[key])

    @staticmethod
    def _get_bool(
        config: dict[str, Any],
        key: str,
        *,
        default: bool,
    ) -> bool:
        value = config.get(key, default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
            }

        return bool(value)