from functools import lru_cache

from redis.asyncio import Redis

from bts_monitoring.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    """
    Redis client dùng cho GET/SET/PUBLISH thông thường.

    Có timeout ngắn để API không bị treo lâu nếu Redis lỗi.
    """
    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )


@lru_cache
def get_pubsub_redis_client() -> Redis:
    """
    Redis client riêng cho Pub/Sub subscriber.

    socket_timeout=None vì pubsub.listen() cần chờ message
    trong thời gian dài.
    """
    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=None,
        health_check_interval=30,
    )


async def close_redis_clients() -> None:
    normal_client = get_redis_client()
    pubsub_client = get_pubsub_redis_client()

    await normal_client.aclose()
    await pubsub_client.aclose()

    get_redis_client.cache_clear()
    get_pubsub_redis_client.cache_clear()


# Giữ tương thích với code cũ.
async def close_redis_client() -> None:
    await close_redis_clients()