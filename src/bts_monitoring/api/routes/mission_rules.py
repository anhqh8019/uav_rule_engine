from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)

from bts_monitoring.api.dependencies import (
    get_mission_rule_service,
)
from bts_monitoring.core.enums import RuleEventType
from bts_monitoring.schemas.mission_rule import (
    MissionRuleListResponse,
    MissionRuleResponse,
    MissionRulesValidationResponse,
    MissionRuleUpsert,
)
from bts_monitoring.services.mission_rule_service import (
    MissionRuleService,
)


router = APIRouter(
    prefix="/api/missions/{mission_id}/rules",
    tags=["mission rules"],
)

MissionRuleServiceDependency = Annotated[
    MissionRuleService,
    Depends(get_mission_rule_service),
]


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

    return MissionRuleResponse.model_validate(
        rule
    )


@router.get(
    "",
    response_model=MissionRuleListResponse,
)
async def list_rules(
    mission_id: str,
    service: MissionRuleServiceDependency,
) -> MissionRuleListResponse:
    return await service.list_rules(mission_id)


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

    return MissionRuleResponse.model_validate(
        rule
    )


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
) -> MissionRuleListResponse:
    return await service.activate(mission_id)


@router.post(
    "/deactivate",
    response_model=MissionRuleListResponse,
)
async def deactivate_rules(
    mission_id: str,
    service: MissionRuleServiceDependency,
) -> MissionRuleListResponse:
    return await service.deactivate(mission_id)