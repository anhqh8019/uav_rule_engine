from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from bts_monitoring.core.enums import MissionRuleStatus, RuleEventType


class FireRuleConfig(BaseModel):
    confidence_threshold: float = Field(default=0.80, ge=0, le=1)

    model_config = ConfigDict(extra="forbid")


class SmokeRuleConfig(BaseModel):
    confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    required_events: int = Field(default=5, ge=1, le=100)
    window_seconds: int = Field(default=10, ge=1, le=3600)

    model_config = ConfigDict(extra="forbid")


class RustRuleConfig(BaseModel):
    minimum_area_ratio: float = Field(default=0.02, ge=0, le=1)
    medium_area_ratio: float = Field(default=0.08, ge=0, le=1)
    high_area_ratio: float = Field(default=0.20, ge=0, le=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "RustRuleConfig":
        if not (
            self.minimum_area_ratio
            < self.medium_area_ratio
            < self.high_area_ratio
        ):
            raise ValueError("Rust thresholds must satisfy: minimum < medium < high")
        return self


class TowerTiltRuleConfig(BaseModel):
    warning_angle: float = Field(default=1.0, ge=0, le=90)
    high_angle: float = Field(default=2.0, ge=0, le=90)
    critical_angle: float = Field(default=3.0, ge=0, le=90)
    require_valid_calibration: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_angle_order(self) -> "TowerTiltRuleConfig":
        if not self.warning_angle < self.high_angle < self.critical_angle:
            raise ValueError("Tilt thresholds must satisfy: warning < high < critical")
        return self


class MissionRuleUpsert(BaseModel):
    enabled: bool = True
    config: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class MissionRuleResponse(BaseModel):
    rule_id: UUID
    mission_id: str
    event_type: RuleEventType
    enabled: bool
    config: dict[str, Any]
    status: MissionRuleStatus
    version: int
    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class MissionRuleListResponse(BaseModel):
    mission_id: str
    status: MissionRuleStatus | None
    items: list[MissionRuleResponse]


class MissionRulesValidationResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


_RULE_CONFIG_ADAPTERS: dict[RuleEventType, TypeAdapter[Any]] = {
    RuleEventType.FIRE: TypeAdapter(FireRuleConfig),
    RuleEventType.SMOKE: TypeAdapter(SmokeRuleConfig),
    RuleEventType.RUST: TypeAdapter(RustRuleConfig),
    RuleEventType.TOWER_TILT: TypeAdapter(TowerTiltRuleConfig),
}


def validate_rule_config(
    event_type: RuleEventType,
    config: dict[str, Any],
) -> dict[str, Any]:
    adapter = _RULE_CONFIG_ADAPTERS.get(event_type)
    if adapter is None:
        raise ValueError(f"Unsupported rule event type: {event_type}")

    validated = adapter.validate_python(config)
    return validated.model_dump()