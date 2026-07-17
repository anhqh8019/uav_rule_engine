from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from bts_monitoring.api.dependencies import (
    get_ai_event_service,
)
from bts_monitoring.schemas.ai_event import (
    AIEventListResponse,
    AIEventResponse,
)
from bts_monitoring.services.ai_event_service import (
    AIEventService,
)


router = APIRouter(
    prefix="/api/events",
    tags=["AI events"],
)

AIEventServiceDependency = Annotated[
    AIEventService,
    Depends(get_ai_event_service),
]


@router.get(
    "",
    response_model=AIEventListResponse,
)
async def list_events(
    service: AIEventServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    site_id: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    min_confidence: Annotated[
        float | None,
        Query(ge=0, le=1),
    ] = None,
    captured_from: datetime | None = None,
    captured_to: datetime | None = None,
) -> AIEventListResponse:
    return await service.list_events(
        page=page,
        page_size=page_size,
        site_id=site_id,
        camera_id=camera_id,
        event_type=event_type,
        min_confidence=min_confidence,
        captured_from=captured_from,
        captured_to=captured_to,
    )


@router.get(
    "/{event_id}",
    response_model=AIEventResponse,
)
async def get_event(
    event_id: UUID,
    service: AIEventServiceDependency,
) -> AIEventResponse:
    event = await service.get_event(event_id)

    return AIEventResponse.model_validate(event)