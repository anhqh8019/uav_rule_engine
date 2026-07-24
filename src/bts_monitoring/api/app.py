import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bts_monitoring.api.routes.ai_events import (
    router as ai_events_router,
)
from bts_monitoring.api.routes.cameras import (
    router as cameras_router,
)
from bts_monitoring.api.routes.health import (
    router as health_router,
)
from bts_monitoring.api.routes.incidents import (
    router as incidents_router,
)
from bts_monitoring.api.routes.mission_rules import (
    router as mission_rules_router,
)
from bts_monitoring.api.routes.sites import (
    router as sites_router,
)
from bts_monitoring.core.config import (
    get_settings,
)
from bts_monitoring.database.session import engine

# from bts_monitoring.infrastructure.cache.redis_client import (
#     close_redis_client,
#     get_redis_client,
# )

from bts_monitoring.infrastructure.messaging.rule_event_subscriber import (
    RuleEventSubscriber,
)
from bts_monitoring.services.rule_engine.runtime import (
    get_local_rule_engine_cache,
)

from bts_monitoring.infrastructure.cache.redis_client import (
    close_redis_clients,
    get_pubsub_redis_client,
)

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings

    local_cache = get_local_rule_engine_cache()

    subscriber = RuleEventSubscriber(
        redis=get_pubsub_redis_client(),
        channel=settings.rule_update_channel,
        local_cache=local_cache,
    )

    subscriber_task = asyncio.create_task(
        subscriber.run(),
        name="rule-event-subscriber",
    )

    app.state.rule_event_subscriber = subscriber
    app.state.rule_event_subscriber_task = subscriber_task

    try:
        yield

    finally:
        await subscriber.stop()

        subscriber_task.cancel()

        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass

        await local_cache.clear()
        await close_redis_clients()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.include_router(health_router)
    app.include_router(sites_router)
    app.include_router(cameras_router)
    app.include_router(ai_events_router)
    app.include_router(incidents_router)
    app.include_router(mission_rules_router)

    return app