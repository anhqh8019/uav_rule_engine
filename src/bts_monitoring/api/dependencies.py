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
from bts_monitoring.services.site_service import SiteService

from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
)
from bts_monitoring.services.mission_rule_service import (
    MissionRuleService,
)

# =========================================================
# Repository dependencies
# =========================================================

def get_mission_rule_repository(
    session: AsyncSession = Depends(get_db),
) -> MissionRuleRepository:
    return MissionRuleRepository(session)


def get_mission_rule_service(
    session: AsyncSession = Depends(get_db),
    repository: MissionRuleRepository = Depends(
        get_mission_rule_repository
    ),
) -> MissionRuleService:
    return MissionRuleService(
        session=session,
        repository=repository,
    )

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

def get_inference_pipeline(
    session: AsyncSession = Depends(get_db),
    event_service: AIEventService = Depends(
        get_ai_event_service
    ),
    rule_engine: RuleEngine = Depends(
        get_rule_engine
    ),
    incident_service: IncidentService = Depends(
        get_incident_service
    ),
) -> InferencePipeline:
    return InferencePipeline(
        session=session,
        event_service=event_service,
        rule_engine=rule_engine,
        incident_service=incident_service,
    )

