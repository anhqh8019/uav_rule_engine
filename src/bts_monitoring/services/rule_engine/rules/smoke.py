from datetime import timedelta

from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.services.rule_engine.base import (
    Rule,
    RuleContext,
    RuleResult,
)


class SmokePersistenceRule(Rule):
    name = "smoke_persistence"

    def __init__(
        self,
        *,
        confidence_threshold: float = 0.65,
        required_events: int = 5,
        window_seconds: int = 10,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.required_events = required_events
        self.window_seconds = window_seconds

    async def evaluate(
        self,
        event: AIEventModel,
        context: RuleContext,
    ) -> RuleResult:
        if event.event_type.upper() != "SMOKE":
            return RuleResult(triggered=False)

        if event.confidence < self.confidence_threshold:
            return RuleResult(triggered=False)

        captured_from = (
            event.captured_at
            - timedelta(seconds=self.window_seconds)
        )

        count = (
            await context.event_repository.count_recent_events(
                camera_id=event.camera_id,
                event_type="SMOKE",
                min_confidence=self.confidence_threshold,
                captured_from=captured_from,
                captured_to=event.captured_at,
            )
        )

        if count < self.required_events:
            return RuleResult(triggered=False)

        return RuleResult(
            triggered=True,
            incident_type="SMOKE_CONFIRMED",
            severity="high",
            title="Phát hiện khói kéo dài",
            message=(
                f"Camera {event.camera_id} phát hiện "
                f"{count} sự kiện khói trong "
                f"{self.window_seconds} giây"
            ),
            deduplication_key=(
                f"{event.site_id}:"
                f"{event.camera_id}:"
                "SMOKE_CONFIRMED"
            ),
        )