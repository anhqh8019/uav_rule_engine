import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
    MissionRuleSet,
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

    @staticmethod
    def normalize_mission_id(
        mission_id: str,
    ) -> str:
        return mission_id.strip().upper()

    def build_key(
        self,
        mission_id: str,
    ) -> str:
        normalized = self.normalize_mission_id(
            mission_id
        )

        return f"{self.key_prefix}:{normalized}"

    async def get_rule_set(
        self,
        mission_id: str,
    ) -> MissionRuleSet | None:
        normalized = self.normalize_mission_id(
            mission_id
        )

        payload = await self.get_payload(
            normalized
        )

        if payload is None:
            return None

        raw_rules = payload.get("rules")

        if not isinstance(raw_rules, list):
            logger.warning(
                "Rule cache payload has no valid rules",
                extra={
                    "mission_id": normalized,
                },
            )

            await self.delete(normalized)
            return None

        try:
            rules = [
                MissionRuleDefinition.from_dict(item)
                for item in raw_rules
            ]
        except (
            TypeError,
            ValueError,
            KeyError,
        ):
            logger.exception(
                "Cannot deserialize cached rules",
                extra={
                    "mission_id": normalized,
                },
            )

            await self.delete(normalized)
            return None

        snapshot_id = payload.get("snapshot_id")
        snapshot_version = payload.get(
            "snapshot_version"
        )
        checksum = payload.get("checksum")

        return MissionRuleSet(
            mission_id=normalized,
            snapshot_id=(
                str(snapshot_id)
                if snapshot_id is not None
                else None
            ),
            snapshot_version=(
                int(snapshot_version)
                if snapshot_version is not None
                else None
            ),
            checksum=(
                str(checksum)
                if checksum is not None
                else None
            ),
            rules=rules,
        )

    async def get(
        self,
        mission_id: str,
    ) -> list[MissionRuleDefinition] | None:
        rule_set = await self.get_rule_set(
            mission_id
        )

        if rule_set is None:
            return None

        return rule_set.rules

    async def get_payload(
        self,
        mission_id: str,
    ) -> dict[str, Any] | None:
        key = self.build_key(mission_id)

        try:
            raw_value = await self.redis.get(key)
        except RedisError:
            logger.exception(
                "Cannot read mission rule Redis cache",
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
                "Mission rule Redis payload is invalid JSON",
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
        normalized = self.normalize_mission_id(
            mission_id
        )

        payload = {
            "schema_version": 1,
            "mission_id": normalized,
            "rules": [
                rule.to_dict()
                for rule in rules
            ],
        }

        await self._write_payload(
            mission_id=normalized,
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
        normalized = self.normalize_mission_id(
            mission_id
        )

        payload = {
            "schema_version": 2,
            "mission_id": normalized,
            "snapshot_id": snapshot_id,
            "snapshot_version": version,
            "checksum": checksum,
            "rules": [
                rule.to_dict()
                for rule in rules
            ],
        }

        await self._write_payload(
            mission_id=normalized,
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
                "Cannot write mission rule Redis cache",
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
                "Cannot invalidate mission rule cache",
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