from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.session import get_db
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.repositories.camera_repository import (
    CameraRepository,
)
from bts_monitoring.repositories.incident_repository import (
    IncidentRepository,
)
from bts_monitoring.repositories.site_repository import (
    SiteRepository,
)
from bts_monitoring.services.ai_event_service import (
    AIEventService,
)
from bts_monitoring.services.camera_service import CameraService
from bts_monitoring.services.incident_service import (
    IncidentService,
)
from bts_monitoring.services.inference.pipeline import (
    InferencePipeline,
)
from bts_monitoring.services.rule_engine.engine import RuleEngine
from bts_monitoring.services.rule_engine.rules.fire import (
    FireImmediateRule,
)
from bts_monitoring.services.rule_engine.rules.rust import (
    RustSeverityRule,
)
from bts_monitoring.services.rule_engine.rules.smoke import (
    SmokePersistenceRule,
)
from bts_monitoring.services.rule_engine.rules.tower_tilt import (
    TowerTiltRule,
)
from bts_monitoring.services.rule_engine.snapshot.service import MissionRuleSnapshotService
from bts_monitoring.services.site_service import SiteService

from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
)
from bts_monitoring.services.mission_rule_service import (
    MissionRuleService,
)
from bts_monitoring.services.rule_engine.factory import (
    MissionRuleEngineFactory,
)

from bts_monitoring.services.rule_engine.providers.database_provider import (
    DatabaseMissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
)

from bts_monitoring.infrastructure.messaging.rule_event_publisher import (
    RuleEventPublisher,
)
from bts_monitoring.services.rule_engine.runtime import (
    get_local_rule_engine_cache,
)

from redis.asyncio import Redis

from bts_monitoring.core.config import (
    Settings,
    get_settings,
)
from bts_monitoring.infrastructure.cache.mission_rule_cache import (
    MissionRuleCache,
)
from bts_monitoring.infrastructure.cache.redis_client import (
    get_redis_client,
)
from bts_monitoring.services.rule_engine.providers.cached_provider import (
    CachedMissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.database_provider import (
    DatabaseMissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.base import (
    MissionRuleProvider,
)

from bts_monitoring.repositories.mission_rule_snapshot_repository import (
    MissionRuleSnapshotRepository,
)

# from bts_monitoring.services.rule_engine.snapshots.service import (
#     MissionRuleSnapshotService,
# )


# =========================================================
# Repository dependencies
# =========================================================



def get_mission_rule_repository(
    session: AsyncSession = Depends(get_db),
) -> MissionRuleRepository:
    return MissionRuleRepository(session)

def get_site_repository(
    session: AsyncSession = Depends(get_db),
) -> SiteRepository:
    return SiteRepository(session)


def get_camera_repository(
    session: AsyncSession = Depends(get_db),
) -> CameraRepository:
    return CameraRepository(session)


def get_ai_event_repository(
    session: AsyncSession = Depends(get_db),
) -> AIEventRepository:
    return AIEventRepository(session)


def get_incident_repository(
    session: AsyncSession = Depends(get_db),
) -> IncidentRepository:
    return IncidentRepository(session)


# =========================================================
# Site / Camera services
# =========================================================

def get_site_service(
    repository: SiteRepository = Depends(
        get_site_repository
    ),
) -> SiteService:
    return SiteService(repository)


def get_camera_service(
    camera_repository: CameraRepository = Depends(
        get_camera_repository
    ),
    site_repository: SiteRepository = Depends(
        get_site_repository
    ),
) -> CameraService:
    return CameraService(
        camera_repository=camera_repository,
        site_repository=site_repository,
    )


# =========================================================
# AI Event / Incident services
# =========================================================

def get_ai_event_service(
    session: AsyncSession = Depends(get_db),
    event_repository: AIEventRepository = Depends(
        get_ai_event_repository
    ),
    site_repository: SiteRepository = Depends(
        get_site_repository
    ),
    camera_repository: CameraRepository = Depends(
        get_camera_repository
    ),
) -> AIEventService:
    return AIEventService(
        session=session,
        event_repository=event_repository,
        site_repository=site_repository,
        camera_repository=camera_repository,
    )


def get_incident_service(
    session: AsyncSession = Depends(get_db),
    repository: IncidentRepository = Depends(
        get_incident_repository
    ),
) -> IncidentService:
    return IncidentService(
        session=session,
        repository=repository,
    )


# =========================================================
# Rule engine
# =========================================================

def get_rule_engine(
    event_repository: AIEventRepository = Depends(
        get_ai_event_repository
    ),
) -> RuleEngine:
    return RuleEngine(
        event_repository=event_repository,
        rules=[
            FireImmediateRule(
                confidence_threshold=0.80,
            ),
            SmokePersistenceRule(
                confidence_threshold=0.65,
                required_events=5,
                window_seconds=10,
            ),
            RustSeverityRule(),
            TowerTiltRule(
                warning_angle=1.0,
                high_angle=2.0,
                critical_angle=3.0,
            ),
        ],
    )


# =========================================================
# Inference pipeline
# =========================================================
def get_app_settings() -> Settings:
    return get_settings()

def get_redis() -> Redis:
    return get_redis_client()

def get_mission_rule_cache(
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(
        get_app_settings
    ),
) -> MissionRuleCache:
    return MissionRuleCache(
        redis=redis,
        key_prefix=(
            settings.rule_cache_key_prefix
        ),
        ttl_seconds=(
            settings.rule_cache_ttl_seconds
        ),
    )


def get_mission_rule_provider(
    cache: MissionRuleCache = Depends(
        get_mission_rule_cache
    ),
    database_provider: (
        DatabaseMissionRuleProvider
    ) = Depends(
        get_database_mission_rule_provider
    ),
) -> MissionRuleProvider:
    return CachedMissionRuleProvider(
        cache=cache,
        fallback_provider=database_provider,
    )

def get_mission_rule_engine_factory(
    event_repository: AIEventRepository = Depends(
        get_ai_event_repository
    ),
    provider: MissionRuleProvider = Depends(
        get_mission_rule_provider
    ),
) -> MissionRuleEngineFactory:
    return MissionRuleEngineFactory(
        event_repository=event_repository,
        provider=provider,
        local_cache=(
            get_local_rule_engine_cache()
        ),
    )

def get_inference_pipeline(
    session: AsyncSession = Depends(get_db),
    event_service: AIEventService = Depends(
        get_ai_event_service
    ),
    rule_engine_factory: MissionRuleEngineFactory = Depends(
        get_mission_rule_engine_factory
    ),
    incident_service: IncidentService = Depends(
        get_incident_service
    ),
) -> InferencePipeline:
    return InferencePipeline(
        session=session,
        event_service=event_service,
        rule_engine_factory=rule_engine_factory,
        incident_service=incident_service,
    )

def get_mission_rule_snapshot_repository(
    session: AsyncSession = Depends(get_db),
) -> MissionRuleSnapshotRepository:
    return MissionRuleSnapshotRepository(
        session
    )

def get_mission_rule_snapshot_service(
    repository: MissionRuleSnapshotRepository = Depends(
        get_mission_rule_snapshot_repository
    ),
) -> MissionRuleSnapshotService:
    return MissionRuleSnapshotService(
        repository=repository,
    )

def get_rule_event_publisher(
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(
        get_app_settings
    ),
) -> RuleEventPublisher:
    return RuleEventPublisher(
        redis=redis,
        channel=settings.rule_update_channel,
    )


def get_mission_rule_service(
    session: AsyncSession = Depends(get_db),
    repository: MissionRuleRepository = Depends(
        get_mission_rule_repository
    ),
    cache: MissionRuleCache = Depends(
        get_mission_rule_cache
    ),
    snapshot_service: MissionRuleSnapshotService = Depends(
        get_mission_rule_snapshot_service
    ),
    event_publisher: RuleEventPublisher = Depends(
        get_rule_event_publisher
    ),
) -> MissionRuleService:
    return MissionRuleService(
        session=session,
        repository=repository,
        cache=cache,
        snapshot_service=snapshot_service,
        event_publisher=event_publisher,
    )

def get_database_mission_rule_provider(
    rule_repository: MissionRuleRepository = Depends(
        get_mission_rule_repository
    ),
    snapshot_repository: MissionRuleSnapshotRepository = Depends(
        get_mission_rule_snapshot_repository
    ),
) -> DatabaseMissionRuleProvider:
    return DatabaseMissionRuleProvider(
        rule_repository=rule_repository,
        snapshot_repository=snapshot_repository,
    )


