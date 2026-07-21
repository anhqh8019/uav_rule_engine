import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
)


logger = logging.getLogger(__name__)


class MissionRuleCache:
    def __init__(
        self,
        *,
        redis: Redis,
        key_prefix: str,
        ttl_seconds: int,
    ) -> None:
        self.redis = redis
        self.key_prefix = key_prefix.rstrip(":")
        self.ttl_seconds = ttl_seconds

    def build_key(
        self,
        mission_id: str,
    ) -> str:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        return (
            f"{self.key_prefix}:"
            f"{normalized_mission_id}"
        )

    async def get(
        self,
        mission_id: str,
    ) -> list[MissionRuleDefinition] | None:
        payload = await self.get_payload(mission_id)

        if payload is None:
            return None

        raw_rules = payload.get("rules")

        if not isinstance(raw_rules, list):
            await self.delete(mission_id)
            return None

        try:
            return [
                MissionRuleDefinition.from_dict(item)
                for item in raw_rules
            ]
        except (
            TypeError,
            ValueError,
            KeyError,
        ):
            logger.exception(
                "Invalid mission-rule definitions "
                "inside cache payload",
                extra={
                    "mission_id": mission_id,
                },
            )

            await self.delete(mission_id)

            return None

    async def get_payload(
        self,
        mission_id: str,
    ) -> dict[str, Any] | None:
        key = self.build_key(mission_id)

        try:
            raw_value = await self.redis.get(key)
        except RedisError:
            logger.exception(
                "Could not read mission-rule cache",
                extra={
                    "mission_id": mission_id,
                    "cache_key": key,
                },
            )
            return None

        if raw_value is None:
            return None

        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            logger.exception(
                "Mission-rule cache contains invalid JSON",
                extra={
                    "mission_id": mission_id,
                    "cache_key": key,
                },
            )

            await self.delete(mission_id)

            return None

        if not isinstance(payload, dict):
            await self.delete(mission_id)
            return None

        return payload

    async def set(
        self,
        *,
        mission_id: str,
        rules: list[MissionRuleDefinition],
    ) -> None:
        payload = {
            "schema_version": 1,
            "mission_id": (
                mission_id.strip().upper()
            ),
            "rules": [
                rule.to_dict()
                for rule in rules
            ],
        }

        await self._write_payload(
            mission_id=mission_id,
            payload=payload,
        )

    async def set_snapshot(
        self,
        *,
        mission_id: str,
        snapshot_id: str,
        version: int,
        checksum: str,
        rules: list[MissionRuleDefinition],
    ) -> None:
        payload = {
            "schema_version": 2,
            "mission_id": (
                mission_id.strip().upper()
            ),
            "snapshot_id": snapshot_id,
            "snapshot_version": version,
            "checksum": checksum,
            "rules": [
                rule.to_dict()
                for rule in rules
            ],
        }

        await self._write_payload(
            mission_id=mission_id,
            payload=payload,
        )

    async def _write_payload(
        self,
        *,
        mission_id: str,
        payload: dict[str, Any],
    ) -> None:
        key = self.build_key(mission_id)

        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        try:
            await self.redis.set(
                key,
                serialized,
                ex=self.ttl_seconds,
            )
        except RedisError:
            logger.exception(
                "Could not write mission-rule cache",
                extra={
                    "mission_id": mission_id,
                    "cache_key": key,
                },
            )

    async def delete(
        self,
        mission_id: str,
    ) -> None:
        key = self.build_key(mission_id)

        try:
            await self.redis.delete(key)
        except RedisError:
            logger.exception(
                "Could not invalidate mission-rule cache",
                extra={
                    "mission_id": mission_id,
                    "cache_key": key,
                },
            )

    async def ping(self) -> bool:
        try:
            return bool(await self.redis.ping())
        except RedisError:
            return False