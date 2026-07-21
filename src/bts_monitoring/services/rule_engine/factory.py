from bts_monitoring.core.enums import RuleEventType
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.services.rule_engine.engine import (
    RuleEngine,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
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


class MissionRuleEngineFactory:
    def __init__(
        self,
        *,
        event_repository: AIEventRepository,
        provider: MissionRuleProvider,
    ) -> None:
        self.event_repository = event_repository
        self.provider = provider

    async def create(
        self,
        mission_id: str,
    ) -> RuleEngine:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        rule_definitions = (
            await self.provider.get_active_rules(
                normalized_mission_id
            )
        )

        if not rule_definitions:
            raise RuntimeError(
                "No active rules found for mission "
                f"'{normalized_mission_id}'"
            )

        rules = []

        for definition in rule_definitions:
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
                                "require_valid_calibration",
                                default=True,
                            )
                        ),
                    )
                )

        return RuleEngine(
            event_repository=self.event_repository,
            rules=rules,
        )

    @staticmethod
    def _get_float(
        config: dict,
        key: str,
    ) -> float:
        if key not in config:
            raise ValueError(
                f"Missing rule config field: {key}"
            )

        return float(config[key])

    @staticmethod
    def _get_int(
        config: dict,
        key: str,
    ) -> int:
        if key not in config:
            raise ValueError(
                f"Missing rule config field: {key}"
            )

        return int(config[key])

    @staticmethod
    def _get_bool(
        config: dict,
        key: str,
        *,
        default: bool,
    ) -> bool:
        value = config.get(key, default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in {
                "true",
                "1",
                "yes",
            }

        return bool(value)