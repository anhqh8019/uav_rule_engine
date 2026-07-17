from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)


@dataclass(frozen=True)
class RuleResult:
    triggered: bool

    incident_type: str | None = None
    severity: str | None = None
    title: str | None = None
    message: str | None = None

    deduplication_key: str | None = None


@dataclass(frozen=True)
class RuleContext:
    now: datetime
    event_repository: AIEventRepository


class Rule(ABC):
    name: str

    @abstractmethod
    async def evaluate(
        self,
        event: AIEventModel,
        context: RuleContext,
    ) -> RuleResult:
        raise NotImplementedError