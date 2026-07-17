from datetime import UTC, datetime

from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.services.rule_engine.base import (
    Rule,
    RuleContext,
    RuleResult,
)


class RuleEngine:
    def __init__(
        self,
        *,
        rules: list[Rule],
        event_repository: AIEventRepository,
    ) -> None:
        self.rules = rules
        self.event_repository = event_repository

    async def evaluate(
        self,
        event: AIEventModel,
    ) -> list[RuleResult]:
        context = RuleContext(
            now=datetime.now(UTC),
            event_repository=self.event_repository,
        )

        results: list[RuleResult] = []

        for rule in self.rules:
            result = await rule.evaluate(
                event,
                context,
            )

            if result.triggered:
                results.append(result)

        return results