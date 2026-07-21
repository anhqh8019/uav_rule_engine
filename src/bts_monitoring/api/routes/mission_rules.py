from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Response,
    status,
)

from bts_monitoring.api.dependencies import (
    get_mission_rule_service,
    get_mission_rule_snapshot_service,
)
from bts_monitoring.core.enums import RuleEventType
from bts_monitoring.schemas.mission_rule import (
    MissionRuleListResponse,
    MissionRuleResponse,
    MissionRulesValidationResponse,
    MissionRuleUpsert,
)
from bts_monitoring.schemas.mission_rule_snapshot import (
    MissionRuleSnapshotListResponse,
    MissionRuleSnapshotResponse,
)
from bts_monitoring.services.mission_rule_service import (
    MissionRuleService,
)
from bts_monitoring.services.rule_engine.snapshots.service import (
    MissionRuleSnapshotService,
)


router = APIRouter(
    prefix="/api/missions/{mission_id}/rules",
    tags=["mission rules"],
)


MissionRuleServiceDependency = Annotated[
    MissionRuleService,
    Depends(get_mission_rule_service),
]

MissionRuleSnapshotServiceDependency = Annotated[
    MissionRuleSnapshotService,
    Depends(get_mission_rule_snapshot_service),
]


@router.get(
    "",
    response_model=MissionRuleListResponse,
)
async def list_rules(
    mission_id: str,
    service: MissionRuleServiceDependency,
) -> MissionRuleListResponse:
    return await service.list_rules(mission_id)


@router.post(
    "/validate",
    response_model=MissionRulesValidationResponse,
)
async def validate_rules(
    mission_id: str,
    service: MissionRuleServiceDependency,
) -> MissionRulesValidationResponse:
    return await service.validate_mission_rules(
        mission_id
    )


@router.post(
    "/activate",
    response_model=MissionRuleListResponse,
)
async def activate_rules(
    mission_id: str,
    service: MissionRuleServiceDependency,
    actor_id: Annotated[
        str | None,
        Header(
            alias="X-Actor-Id",
            max_length=255,
        ),
    ] = None,
) -> MissionRuleListResponse:
    return await service.activate(
        mission_id,
        created_by=actor_id,
    )


@router.post(
    "/deactivate",
    response_model=MissionRuleListResponse,
)
async def deactivate_rules(
    mission_id: str,
    service: MissionRuleServiceDependency,
) -> MissionRuleListResponse:
    return await service.deactivate(mission_id)


@router.get(
    "/snapshot",
    response_model=MissionRuleSnapshotResponse,
)
async def get_latest_snapshot(
    mission_id: str,
    service: MissionRuleSnapshotServiceDependency,
) -> MissionRuleSnapshotResponse:
    snapshot = await service.get_latest_snapshot(
        mission_id
    )

    return MissionRuleSnapshotResponse.model_validate(
        snapshot
    )


@router.get(
    "/snapshots",
    response_model=MissionRuleSnapshotListResponse,
)
async def list_snapshots(
    mission_id: str,
    service: MissionRuleSnapshotServiceDependency,
) -> MissionRuleSnapshotListResponse:
    snapshots = await service.list_snapshots(
        mission_id
    )

    return MissionRuleSnapshotListResponse(
        mission_id=mission_id.strip().upper(),
        items=[
            MissionRuleSnapshotResponse.model_validate(
                snapshot
            )
            for snapshot in snapshots
        ],
    )


@router.get(
    "/snapshots/{version}",
    response_model=MissionRuleSnapshotResponse,
)
async def get_snapshot_by_version(
    mission_id: str,
    version: int,
    service: MissionRuleSnapshotServiceDependency,
) -> MissionRuleSnapshotResponse:
    snapshot = (
        await service.get_snapshot_by_version(
            mission_id=mission_id,
            version=version,
        )
    )

    return MissionRuleSnapshotResponse.model_validate(
        snapshot
    )


@router.put(
    "/{event_type}",
    response_model=MissionRuleResponse,
)
async def upsert_rule(
    mission_id: str,
    event_type: RuleEventType,
    payload: MissionRuleUpsert,
    service: MissionRuleServiceDependency,
) -> MissionRuleResponse:
    rule = await service.upsert_rule(
        mission_id=mission_id,
        event_type=event_type,
        payload=payload,
    )

    return MissionRuleResponse.model_validate(rule)


@router.get(
    "/{event_type}",
    response_model=MissionRuleResponse,
)
async def get_rule(
    mission_id: str,
    event_type: RuleEventType,
    service: MissionRuleServiceDependency,
) -> MissionRuleResponse:
    rule = await service.get_rule(
        mission_id=mission_id,
        event_type=event_type,
    )

    return MissionRuleResponse.model_validate(rule)


@router.delete(
    "/{event_type}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rule(
    mission_id: str,
    event_type: RuleEventType,
    service: MissionRuleServiceDependency,
) -> Response:
    await service.delete_rule(
        mission_id=mission_id,
        event_type=event_type,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )