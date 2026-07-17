from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from bts_monitoring.api.dependencies import (
    get_incident_service,
)
from bts_monitoring.core.enums import (
    IncidentSeverity,
    IncidentStatus,
)
from bts_monitoring.schemas.incident import (
    IncidentAcknowledgeRequest,
    IncidentAssignRequest,
    IncidentListResponse,
    IncidentResolveRequest,
    IncidentResponse,
)
from bts_monitoring.services.incident_service import (
    IncidentService,
)


router = APIRouter(
    prefix="/api/incidents",
    tags=["incidents"],
)

IncidentServiceDependency = Annotated[
    IncidentService,
    Depends(get_incident_service),
]


@router.get(
    "",
    response_model=IncidentListResponse,
)
async def list_incidents(
    service: IncidentServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    site_id: str | None = None,
    camera_id: str | None = None,
    incident_type: str | None = None,
    severity: IncidentSeverity | None = None,
    incident_status: IncidentStatus | None = None,
) -> IncidentListResponse:
    return await service.list_incidents(
        page=page,
        page_size=page_size,
        site_id=site_id,
        camera_id=camera_id,
        incident_type=incident_type,
        severity=(
            severity.value
            if severity is not None
            else None
        ),
        incident_status=(
            incident_status.value
            if incident_status is not None
            else None
        ),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(
    incident_id: UUID,
    service: IncidentServiceDependency,
) -> IncidentResponse:
    incident = await service.get_incident(
        incident_id
    )

    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/acknowledge",
    response_model=IncidentResponse,
)
async def acknowledge_incident(
    incident_id: UUID,
    payload: IncidentAcknowledgeRequest,
    service: IncidentServiceDependency,
) -> IncidentResponse:
    incident = await service.acknowledge(
        incident_id,
        assigned_to=payload.assigned_to,
    )

    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
async def resolve_incident(
    incident_id: UUID,
    payload: IncidentResolveRequest,
    service: IncidentServiceDependency,
) -> IncidentResponse:
    incident = await service.resolve(
        incident_id,
        message=payload.message,
    )

    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/close",
    response_model=IncidentResponse,
)
async def close_incident(
    incident_id: UUID,
    service: IncidentServiceDependency,
) -> IncidentResponse:
    incident = await service.close(
        incident_id
    )

    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/assign",
    response_model=IncidentResponse,
)
async def assign_incident(
    incident_id: UUID,
    payload: IncidentAssignRequest,
    service: IncidentServiceDependency,
) -> IncidentResponse:
    incident = await service.assign(
        incident_id,
        assigned_to=payload.assigned_to,
    )

    return IncidentResponse.model_validate(incident)