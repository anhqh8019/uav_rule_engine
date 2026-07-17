from datetime import UTC, datetime
from uuid import uuid4

import numpy as np

from bts_monitoring.domain.ai_event import (
    AIEvent,
    BoundingBox,
)
from bts_monitoring.services.inference.base import AIModel


class InferencePipeline:
    def __init__(self, model: AIModel) -> None:
        self.model = model

    def process(
        self,
        site_id: str,
        camera_id: str,
        frame: np.ndarray,
        captured_at: datetime,
    ) -> list[AIEvent]:
        detections = self.model.predict(frame)

        events: list[AIEvent] = []

        for detection in detections:
            bbox = None

            if detection.bbox:
                bbox = BoundingBox(
                    x1=detection.bbox[0],
                    y1=detection.bbox[1],
                    x2=detection.bbox[2],
                    y2=detection.bbox[3],
                )

            events.append(
                AIEvent(
                    event_id=uuid4(),
                    site_id=site_id,
                    camera_id=camera_id,
                    event_type=detection.class_name.upper(),
                    confidence=detection.confidence,
                    model_name=self.model.name,
                    model_version=self.model.version,
                    captured_at=captured_at,
                    received_at=datetime.now(UTC),
                    bbox=bbox,
                    polygon=detection.polygon,
                    attributes=detection.attributes,
                )
            )

        return events