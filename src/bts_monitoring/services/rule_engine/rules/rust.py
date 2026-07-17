from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.services.rule_engine.base import (
    Rule,
    RuleContext,
    RuleResult,
)


class RustSeverityRule(Rule):
    name = "rust_severity"

    def __init__(
        self,
        *,
        minimum_area_ratio: float = 0.02,
        medium_area_ratio: float = 0.08,
        high_area_ratio: float = 0.20,
    ) -> None:
        self.minimum_area_ratio = (
            minimum_area_ratio
        )
        self.medium_area_ratio = (
            medium_area_ratio
        )
        self.high_area_ratio = (
            high_area_ratio
        )

    async def evaluate(
        self,
        event: AIEventModel,
        context: RuleContext,
    ) -> RuleResult:
        if event.event_type.upper() != "RUST":
            return RuleResult(triggered=False)

        ratio = float(
            event.attributes.get(
                "rust_area_ratio",
                0.0,
            )
        )

        if ratio < self.minimum_area_ratio:
            return RuleResult(triggered=False)

        if ratio < self.medium_area_ratio:
            severity = "low"
        elif ratio < self.high_area_ratio:
            severity = "medium"
        else:
            severity = "high"

        component = event.attributes.get(
            "component",
            "unknown",
        )

        return RuleResult(
            triggered=True,
            incident_type="RUST_DETECTED",
            severity=severity,
            title="Phát hiện hoen gỉ",
            message=(
                f"Phát hiện hoen gỉ tại "
                f"{component}, tỷ lệ {ratio:.2%}"
            ),
            deduplication_key=(
                f"{event.site_id}:"
                f"{event.camera_id}:"
                f"RUST_DETECTED:"
                f"{component}"
            ),
        )