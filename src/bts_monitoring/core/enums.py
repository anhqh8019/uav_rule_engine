from enum import StrEnum


class CameraRole(StrEnum):
    TOWER_OVERVIEW = "tower_overview"
    TOWER_BASE = "tower_base"
    POWER_CABINET = "power_cabinet"
    EQUIPMENT_ROOM = "equipment_room"
    GENERATOR = "generator"
    PTZ = "ptz"
    OTHER = "other"

from enum import StrEnum


class IncidentSeverity(StrEnum):
    LOW = "low"
    WARNING = "warning"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"

class RuleEventType(StrEnum):
    FIRE = "FIRE"
    SMOKE = "SMOKE"
    RUST = "RUST"
    TOWER_TILT = "TOWER_TILT"


class MissionRuleStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"