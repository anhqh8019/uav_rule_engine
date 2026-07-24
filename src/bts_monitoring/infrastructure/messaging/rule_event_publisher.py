import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from bts_monitoring.services.rule_engine.events import (
    RuleSnapshotActivatedEvent,
)


logger = logging.getLogger(__name__)


class RuleEventPublisher:
    def __init__(
        self,
        *,
        redis: Redis,
        channel: str,
    ) -> None:
        self.redis = redis
        self.channel = channel

    async def publish_snapshot_activated(
        self,
        event: RuleSnapshotActivatedEvent,
    ) -> bool:
        message = {
            "event_type": (
                "rule_snapshot_activated"
            ),
            "payload": event.to_dict(),
        }

        serialized = json.dumps(
            message,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        try:
            subscriber_count = (
                await self.redis.publish(
                    self.channel,
                    serialized,
                )
            )
        except RedisError:
            logger.exception(
                "Cannot publish rule snapshot event",
                extra={
                    "mission_id": event.mission_id,
                    "snapshot_version": (
                        event.snapshot_version
                    ),
                },
            )

            return False

        logger.info(
            "Published rule snapshot event",
            extra={
                "mission_id": event.mission_id,
                "snapshot_version": (
                    event.snapshot_version
                ),
                "subscriber_count": (
                    subscriber_count
                ),
            },
        )

        print(
            "PUBLISHED RULE UPDATE:",
            event.mission_id,
            "version=",
            event.snapshot_version,
            "subscribers=",
            subscriber_count,
        )

        return True