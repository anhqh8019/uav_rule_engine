import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from bts_monitoring.core.config import get_settings
from bts_monitoring.database.session import AsyncSessionFactory
from bts_monitoring.infrastructure.cache.mission_rule_cache import (
    MissionRuleCache,
)
from bts_monitoring.infrastructure.cache.redis_client import (
    close_redis_client,
    get_redis_client,
)
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.repositories.camera_repository import (
    CameraRepository,
)
from bts_monitoring.repositories.incident_repository import (
    IncidentRepository,
)
from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
)
from bts_monitoring.repositories.site_repository import (
    SiteRepository,
)
from bts_monitoring.services.ai_event_service import (
    AIEventService,
)
from bts_monitoring.services.incident_service import (
    IncidentService,
)
from bts_monitoring.services.inference.factory import (
    get_fire_smoke_detector,
)
from bts_monitoring.services.inference.pipeline import (
    InferencePipeline,
)
from bts_monitoring.services.rule_engine.factory import (
    MissionRuleEngineFactory,
)
from bts_monitoring.services.rule_engine.providers.cached_provider import (
    CachedMissionRuleProvider,
)
from bts_monitoring.services.rule_engine.providers.database_provider import (
    DatabaseMissionRuleProvider,
)

from bts_monitoring.services.rule_engine.runtime import (
    get_local_rule_engine_cache,
)

async def main() -> None:
    try:
        image_path = PROJECT_ROOT / "data" / "smoke.jpg"

        frame = cv2.imread(str(image_path))

        if frame is None:
            raise RuntimeError(
                f"Cannot read image: {image_path}"
            )

        detector = get_fire_smoke_detector()
        detections = detector.predict(frame)

        print(f"Detections found: {len(detections)}")

        for detection in detections:
            print(
                "Detection:",
                detection.class_name,
                detection.confidence,
                detection.bbox,
            )

        settings = get_settings()

        async with AsyncSessionFactory() as session:
            event_repository = AIEventRepository(session)
            site_repository = SiteRepository(session)
            camera_repository = CameraRepository(session)
            incident_repository = IncidentRepository(session)
            mission_rule_repository = MissionRuleRepository(
                session
            )

            event_service = AIEventService(
                session=session,
                event_repository=event_repository,
                site_repository=site_repository,
                camera_repository=camera_repository,
            )

            incident_service = IncidentService(
                session=session,
                repository=incident_repository,
            )

            database_provider = DatabaseMissionRuleProvider(
                repository=mission_rule_repository,
            )

            cache = MissionRuleCache(
                redis=get_redis_client(),
                key_prefix=settings.rule_cache_key_prefix,
                ttl_seconds=settings.rule_cache_ttl_seconds,
            )

            rule_provider = CachedMissionRuleProvider(
                cache=cache,
                fallback_provider=database_provider,
            )

            rule_engine_factory = MissionRuleEngineFactory(
                event_repository=event_repository,
                provider=rule_provider,
                local_cache=get_local_rule_engine_cache(),
            )

            pipeline = InferencePipeline(
                session=session,
                event_service=event_service,
                rule_engine_factory=rule_engine_factory,
                incident_service=incident_service,
            )

            print("\n========== FIRST PIPELINE RUN ==========")

            first_results = await pipeline.process_detections(
                mission_id="MISSION-001",
                site_id="BTS-HN-001",
                camera_id="CAM-HN-001",
                detections=detections,
                captured_at=datetime.now(UTC),
            )

            print("\n========== SECOND PIPELINE RUN ==========")

            second_results = await pipeline.process_detections(
                mission_id="MISSION-001",
                site_id="BTS-HN-001",
                camera_id="CAM-HN-001",
                detections=detections,
                captured_at=datetime.now(UTC),
            )
            print("=========================first_results===========================")
            print(first_results)
            print("=========================second_results===========================")
            print(second_results)

            # for event, incidents in results:
            #     print(
            #         "AI event:",
            #         event.event_id,
            #         event.event_type,
            #         event.confidence,
            #     )
            #
            #     if not incidents:
            #         print(
            #             "No incident created for event:",
            #             event.event_id,
            #         )
            #
            #     for incident in incidents:
            #         print(
            #             "Incident:",
            #             incident.incident_id,
            #             incident.incident_type,
            #             incident.severity,
            #             incident.occurrence_count,
            #         )

    finally:
        await get_local_rule_engine_cache().clear()
        await close_redis_client()


if __name__ == "__main__":
    asyncio.run(main())