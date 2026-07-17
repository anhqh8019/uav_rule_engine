import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

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
from bts_monitoring.services.rule_engine.engine import (
    RuleEngine,
)
from bts_monitoring.services.rule_engine.rules.fire import (
    FireImmediateRule,
)
from bts_monitoring.services.rule_engine.rules.smoke import (
    SmokePersistenceRule,
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

    async with AsyncSessionFactory() as session:
        event_repository = AIEventRepository(session)
        site_repository = SiteRepository(session)
        camera_repository = CameraRepository(session)
        incident_repository = IncidentRepository(session)

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

        rule_engine = RuleEngine(
            event_repository=event_repository,
            rules=[
                FireImmediateRule(
                    confidence_threshold=0.80,
                ),
                SmokePersistenceRule(
                    confidence_threshold=0.65,
                    required_events=1,
                    window_seconds=10,
                ),
            ],
        )

        pipeline = InferencePipeline(
            session=session,
            event_service=event_service,
            rule_engine=rule_engine,
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

            for incident in incidents:
                print(
                    "Incident:",
                    incident.incident_id,
                    incident.incident_type,
                    incident.severity,
                )


if __name__ == "__main__":
    asyncio.run(main())