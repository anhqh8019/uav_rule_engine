from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
)
from bts_monitoring.services.rule_engine.engine import RuleEngine
from bts_monitoring.services.rule_engine.rules.fire import (
    FireImmediateRule,
)
from bts_monitoring.services.rule_engine.rules.smoke import (
    SmokePersistenceRule,
)


class MissionRuleEngineFactory:
    def __init__(
        self,
        *,
        event_repository: AIEventRepository,
        mission_rule_repository: MissionRuleRepository,
    ) -> None:
        self.event_repository = event_repository
        self.mission_rule_repository = (
            mission_rule_repository
        )

    async def create(
        self,
        mission_id: str,
    ) -> RuleEngine:
        rule_models = (
            await self.mission_rule_repository
            .list_active_by_mission(
                mission_id.strip().upper()
            )
        )

        rules = []

        for rule_model in rule_models:
            config = rule_model.config

            if rule_model.event_type == "FIRE":
                rules.append(
                    FireImmediateRule(
                        confidence_threshold=float(
                            config["confidence_threshold"]
                        )
                    )
                )

            elif rule_model.event_type == "SMOKE":
                rules.append(
                    SmokePersistenceRule(
                        confidence_threshold=float(
                            config["confidence_threshold"]
                        ),
                        required_events=int(
                            config["required_events"]
                        ),
                        window_seconds=int(
                            config["window_seconds"]
                        ),
                    )
                )

        return RuleEngine(
            event_repository=self.event_repository,
            rules=rules,
        )