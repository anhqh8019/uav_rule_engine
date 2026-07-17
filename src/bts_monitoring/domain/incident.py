from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Incident:
    incident_id: UUID
    site_id: str
    camera_id: str | None

    incident_type: str
    severity: str
    status: str

    first_seen_at: datetime
    last_seen_at: datetime

    occurrence_count: int = 1
    assigned_to: str | None = None