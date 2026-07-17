from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.services.rule_engine.base import (
    Rule,
    RuleContext,
    RuleResult,
)


class RustSeverityRule(Rule):
    name = "rust_severity"

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

        if ratio < 0.02:
            return RuleResult(triggered=False)

        if ratio < 0.08:
            severity = "low"
        elif ratio < 0.20:
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
                f"Phát hiện hoen gỉ tại {component}, "
                f"tỷ lệ vùng gỉ {ratio:.2%}"
            ),
            deduplication_key=(
                f"{event.site_id}:"
                f"{event.camera_id}:"
                f"RUST_DETECTED:"
                f"{component}"
            ),
        )