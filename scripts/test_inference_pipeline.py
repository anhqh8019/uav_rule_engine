import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from bts_monitoring.database.session import (
    AsyncSessionFactory,
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


async def main() -> None:
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

        rule_engine_factory = MissionRuleEngineFactory(
            event_repository=event_repository,
            mission_rule_repository=(
                mission_rule_repository
            ),
        )

        pipeline = InferencePipeline(
            session=session,
            event_service=event_service,
            rule_engine_factory=rule_engine_factory,
            incident_service=incident_service,
        )

        results = await pipeline.process_detections(
            mission_id="MISSION-001",
            site_id="BTS-HN-001",
            camera_id="CAM-HN-001",
            detections=detections,
            captured_at=datetime.now(UTC),
        )

        for event, incidents in results:
            print(
                "AI event:",
                event.event_id,
                event.event_type,
                event.confidence,
            )

            if not incidents:
                print(
                    "No incident created for event:",
                    event.event_id,
                )

            for incident in incidents:
                print(
                    "Incident:",
                    incident.incident_id,
                    incident.incident_type,
                    incident.severity,
                    incident.occurrence_count,
                )


if __name__ == "__main__":
    asyncio.run(main())