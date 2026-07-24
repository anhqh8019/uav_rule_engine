from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.core.config import get_settings
from bts_monitoring.database.models.ai_event import (
    AIEventModel,
)
from bts_monitoring.database.models.incident import (
    IncidentModel,
)
from bts_monitoring.schemas.ai_event import (
    AIEventCreate,
    BoundingBoxSchema,
)
from bts_monitoring.services.ai_event_service import (
    AIEventService,
)
from bts_monitoring.services.incident_service import (
    IncidentService,
)
from bts_monitoring.services.inference.base import (
    ModelDetection,
)
from bts_monitoring.services.rule_engine.engine import (
    RuleEngine,
)

from bts_monitoring.services.rule_engine.factory import (
    MissionRuleEngineFactory,
)

from datetime import UTC, datetime

from bts_monitoring.schemas.ai_event import AIEventCreate

class InferencePipeline:
    def __init__(
        self,
        *,
        session: AsyncSession,
        event_service: AIEventService,
        rule_engine_factory: MissionRuleEngineFactory,
        incident_service: IncidentService,
    ) -> None:
        self.session = session
        self.event_service = event_service
        self.rule_engine_factory = rule_engine_factory
        self.incident_service = incident_service

    async def process_detection(
            self,
            *,
            mission_id: str,
            site_id: str,
            camera_id: str,
            detection: ModelDetection,
            captured_at: datetime,
            evidence_uri: str | None = None,
    ) -> tuple[
        AIEventModel,
        list[IncidentModel],
    ]:
        normalized_mission_id = (
            mission_id.strip().upper()
        )

        rule_context = (
            await self.rule_engine_factory.create(
                normalized_mission_id
            )
        )

        bbox = None

        if detection.bbox is not None:
            x1, y1, x2, y2 = detection.bbox

            bbox = {
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
            }

        attributes = dict(
            detection.attributes or {}
        )

        settings = get_settings()

        attributes = {
            "inference_ms": getattr(
                detection,
                "inference_ms",
                None,
            ),
            "model_name": settings.fire_smoke_model_name,
            "model_version": settings.fire_smoke_model_version,
        }

        attributes = {
            key: value
            for key, value in attributes.items()
            if value is not None
        }

        event_payload = AIEventCreate(
            mission_id=normalized_mission_id,
            site_id=site_id,
            camera_id=camera_id,
            event_type=detection.class_name.upper(),
            confidence=float(detection.confidence),
            model_name=settings.fire_smoke_model_name,
            model_version=settings.fire_smoke_model_version,
            captured_at=captured_at,
            received_at=datetime.now(UTC),
            bbox=bbox,
            polygon=None,
            attributes=attributes,
            evidence_uri=evidence_uri,
            rule_snapshot_id=rule_context.snapshot_id,
            rule_snapshot_version=rule_context.snapshot_version,
            rule_snapshot_checksum=rule_context.checksum,
        )

        event = await self.event_service.create_event(
            event_payload
        )

        rule_results = (
            await rule_context.engine.evaluate(
                event
            )
        )

        incidents: list[IncidentModel] = []

        for result in rule_results:
            if not result.triggered:
                continue

            incident = (
                await self.incident_service
                .create_or_update_from_rule(
                    event=event,
                    result=result,
                )
            )

            incidents.append(incident)

        await self.session.commit()

        return event, incidents

    async def process_detections(
            self,
            *,
            mission_id: str,
            site_id: str,
            camera_id: str,
            detections: list[ModelDetection],
            captured_at: datetime,
            evidence_uri: str | None = None,
    ) -> list[
        tuple[AIEventModel, list[IncidentModel]]
    ]:
        results = []

        for detection in detections:
            item = await self.process_detection(
                mission_id=mission_id,
                site_id=site_id,
                camera_id=camera_id,
                detection=detection,
                captured_at=captured_at,
                evidence_uri=evidence_uri,
            )

            results.append(item)

        return results