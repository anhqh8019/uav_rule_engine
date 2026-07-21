from functools import lru_cache

from redis.asyncio import Redis

from bts_monitoring.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )


async def close_redis_client() -> None:
    client = get_redis_client()

    await client.aclose()

    get_redis_client.cache_clear()