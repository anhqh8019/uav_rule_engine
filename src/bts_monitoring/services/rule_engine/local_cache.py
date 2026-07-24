import asyncio
from dataclasses import dataclass
from time import monotonic

from bts_monitoring.services.rule_engine.context import (
    MissionRuleEngineContext,
)


@dataclass(slots=True)
class RuleEngineCacheEntry:
    context: MissionRuleEngineContext
    expires_at: float


class LocalRuleEngineCache:
    def __init__(
        self,
        *,
        ttl_seconds: int,
    ) -> None:
        self.ttl_seconds = ttl_seconds

        self._entries: dict[
            str,
            RuleEngineCacheEntry,
        ] = {}

        self._locks: dict[
            str,
            asyncio.Lock,
        ] = {}

        self._lock_registry_guard = (
            asyncio.Lock()
        )

    @staticmethod
    def normalize_mission_id(
        mission_id: str,
    ) -> str:
        return mission_id.strip().upper()

    async def get(
        self,
        mission_id: str,
    ) -> MissionRuleEngineContext | None:
        normalized = self.normalize_mission_id(
            mission_id
        )

        entry = self._entries.get(normalized)

        if entry is None:
            return None

        if entry.expires_at <= monotonic():
            self._entries.pop(
                normalized,
                None,
            )
            return None

        return entry.context

    async def set(
        self,
        *,
        mission_id: str,
        context: MissionRuleEngineContext,
    ) -> None:
        normalized = self.normalize_mission_id(
            mission_id
        )

        self._entries[normalized] = (
            RuleEngineCacheEntry(
                context=context,
                expires_at=(
                    monotonic()
                    + self.ttl_seconds
                ),
            )
        )

    async def invalidate(
        self,
        mission_id: str,
    ) -> bool:
        normalized = self.normalize_mission_id(
            mission_id
        )

        removed = self._entries.pop(
            normalized,
            None,
        )

        return removed is not None

    async def clear(self) -> None:
        self._entries.clear()

    async def get_lock(
        self,
        mission_id: str,
    ) -> asyncio.Lock:
        normalized = self.normalize_mission_id(
            mission_id
        )

        lock = self._locks.get(normalized)

        if lock is not None:
            return lock

        async with self._lock_registry_guard:
            lock = self._locks.get(normalized)

            if lock is None:
                lock = asyncio.Lock()
                self._locks[normalized] = lock

            return lock