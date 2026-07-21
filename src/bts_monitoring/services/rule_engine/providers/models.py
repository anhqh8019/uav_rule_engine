from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class MissionRuleDefinition:
    mission_id: str
    event_type: str
    enabled: bool
    config: dict[str, Any] = field(
        default_factory=dict,
    )
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        value: dict[str, Any],
    ) -> "MissionRuleDefinition":
        return cls(
            mission_id=str(
                value["mission_id"]
            ),
            event_type=str(
                value["event_type"]
            ),
            enabled=bool(
                value.get("enabled", True)
            ),
            config=dict(
                value.get("config") or {}
            ),
            version=int(
                value.get("version", 1)
            ),
        )