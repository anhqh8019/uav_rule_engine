from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

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


class InferencePipeline:
    def __init__(
        self,
        *,
        session: AsyncSession,
        event_service: AIEventService,
        rule_engine: RuleEngine,
        incident_service: IncidentService,
    ) -> None:
        self.session = session
        self.event_service = event_service
        self.rule_engine = rule_engine
        self.incident_service = incident_service

    async def process_detection(
        self,
        *,
        site_id: str,
        camera_id: str,
        detection: ModelDetection,
        captured_at: datetime,
        evidence_uri: str | None = None,
    ) -> tuple[
        AIEventModel,
        list[IncidentModel],
    ]:
        bbox = None

        if detection.bbox is not None:
            x1, y1, x2, y2 = detection.bbox

            bbox = BoundingBoxSchema(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            )

        payload = AIEventCreate(
            site_id=site_id,
            camera_id=camera_id,
            event_type=detection.class_name.upper(),
            confidence=detection.confidence,
            model_name=str(
                detection.attributes.get(
                    "model_name",
                    "unknown-model",
                )
            ),
            model_version=str(
                detection.attributes.get(
                    "model_version",
                    "unknown-version",
                )
            ),
            captured_at=captured_at,
            received_at=datetime.now(UTC),
            bbox=bbox,
            polygon=detection.polygon,
            attributes=detection.attributes,
            evidence_uri=evidence_uri,
        )

        try:
            event = await self.event_service.create_event(
                payload,
                commit=False,
            )

            results = await self.rule_engine.evaluate(
                event
            )

            incidents: list[IncidentModel] = []

            for result in results:
                incident = (
                    await self.incident_service
                    .handle_rule_result(
                        event=event,
                        result=result,
                        commit=False,
                    )
                )

                incidents.append(incident)

            await self.session.commit()

            return event, incidents

        except Exception:
            await self.session.rollback()
            raise

    async def process_detections(
        self,
        *,
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
                site_id=site_id,
                camera_id=camera_id,
                detection=detection,
                captured_at=captured_at,
                evidence_uri=evidence_uri,
            )

            results.append(item)

        return results