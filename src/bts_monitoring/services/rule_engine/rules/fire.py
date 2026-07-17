from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.services.rule_engine.base import (
    Rule,
    RuleContext,
    RuleResult,
)


class FireImmediateRule(Rule):
    name = "fire_immediate"

    def __init__(
        self,
        confidence_threshold: float = 0.80,
    ) -> None:
        self.confidence_threshold = confidence_threshold

    async def evaluate(
        self,
        event: AIEventModel,
        context: RuleContext,
    ) -> RuleResult:
        if event.event_type.upper() != "FIRE":
            return RuleResult(triggered=False)

        if event.confidence < self.confidence_threshold:
            return RuleResult(triggered=False)

        return RuleResult(
            triggered=True,
            incident_type="FIRE_CONFIRMED",
            severity="critical",
            title="Phát hiện cháy",
            message=(
                f"Camera {event.camera_id} phát hiện cháy "
                f"với độ tin cậy {event.confidence:.2%}"
            ),
            deduplication_key=(
                f"{event.site_id}:"
                f"{event.camera_id}:"
                "FIRE_CONFIRMED"
            ),
        )