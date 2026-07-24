import asyncio
import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from bts_monitoring.services.rule_engine.local_cache import (
    LocalRuleEngineCache,
)


logger = logging.getLogger(__name__)


class RuleEventSubscriber:
    def __init__(
        self,
        *,
        redis: Redis,
        channel: str,
        local_cache: LocalRuleEngineCache,
    ) -> None:
        self.redis = redis
        self.channel = channel
        self.local_cache = local_cache

        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self._listen_once()

            except asyncio.CancelledError:
                raise

            except RedisError:
                logger.exception(
                    "Redis Pub/Sub connection failed"
                )

                await self._wait_before_retry()

            except Exception:
                logger.exception(
                    "Unexpected rule subscriber error"
                )

                await self._wait_before_retry()

    async def _listen_once(self) -> None:
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe(
                self.channel
            )

            logger.info(
                "Subscribed to rule update channel",
                extra={
                    "channel": self.channel,
                },
            )

            print(
                "SUBSCRIBED RULE CHANNEL:",
                self.channel,
            )

            async for message in pubsub.listen():
                if self._stop_event.is_set():
                    break

                if message.get("type") != "message":
                    continue

                await self._handle_message(
                    message.get("data")
                )

    async def _handle_message(
        self,
        raw_data: Any,
    ) -> None:
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode(
                "utf-8"
            )

        if not isinstance(raw_data, str):
            logger.warning(
                "Ignoring non-string Pub/Sub message"
            )
            return

        try:
            message = json.loads(raw_data)

            if (
                message.get("event_type")
                != "rule_snapshot_activated"
            ):
                return

            payload = message["payload"]

            mission_id = str(
                payload["mission_id"]
            ).strip().upper()

            snapshot_version = payload.get(
                "snapshot_version"
            )

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            logger.exception(
                "Invalid rule update Pub/Sub message"
            )
            return

        removed = await self.local_cache.invalidate(
            mission_id
        )

        logger.info(
            "Invalidated local RuleEngine cache",
            extra={
                "mission_id": mission_id,
                "snapshot_version": (
                    snapshot_version
                ),
                "cache_entry_removed": removed,
            },
        )

        print(
            "LOCAL CACHE INVALIDATED:",
            mission_id,
            "version=",
            snapshot_version,
            "removed=",
            removed,
        )

    async def _wait_before_retry(
        self,
    ) -> None:
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=2,
            )
        except TimeoutError:
            pass

    async def stop(self) -> None:
        self._stop_event.set()