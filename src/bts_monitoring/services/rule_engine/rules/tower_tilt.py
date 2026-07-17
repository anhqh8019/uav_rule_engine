from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.services.rule_engine.base import (
    Rule,
    RuleContext,
    RuleResult,
)


class TowerTiltRule(Rule):
    name = "tower_tilt"

    def __init__(
        self,
        *,
        warning_angle: float = 1.0,
        high_angle: float = 2.0,
        critical_angle: float = 3.0,
    ) -> None:
        self.warning_angle = warning_angle
        self.high_angle = high_angle
        self.critical_angle = critical_angle

    async def evaluate(
        self,
        event: AIEventModel,
        context: RuleContext,
    ) -> RuleResult:
        if event.event_type.upper() != "TOWER_TILT":
            return RuleResult(triggered=False)

        calibration_valid = bool(
            event.attributes.get(
                "calibration_valid",
                False,
            )
        )

        if not calibration_valid:
            return RuleResult(triggered=False)

        angle = float(
            event.attributes.get(
                "tilt_angle_deg",
                0.0,
            )
        )

        if angle < self.warning_angle:
            return RuleResult(triggered=False)

        if angle >= self.critical_angle:
            severity = "critical"
        elif angle >= self.high_angle:
            severity = "high"
        else:
            severity = "warning"

        return RuleResult(
            triggered=True,
            incident_type="TOWER_TILT_DETECTED",
            severity=severity,
            title="Phát hiện cột BTS bị nghiêng",
            message=(
                f"Góc nghiêng đo được: {angle:.2f}°"
            ),
            deduplication_key=(
                f"{event.site_id}:"
                "TOWER_TILT_DETECTED"
            ),
        )