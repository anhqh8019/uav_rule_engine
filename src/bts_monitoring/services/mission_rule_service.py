from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.core.enums import (
    MissionRuleStatus,
    RuleEventType,
)
from bts_monitoring.database.models.mission_rule import (
    MissionRuleModel,
)
from bts_monitoring.repositories.mission_rule_repository import (
    MissionRuleRepository,
)
from bts_monitoring.schemas.mission_rule import (
    MissionRuleListResponse,
    MissionRuleResponse,
    MissionRulesValidationResponse,
    MissionRuleUpsert,
    validate_rule_config,
)


class MissionRuleService:
    def __init__(
        self,
        session: AsyncSession,
        repository: MissionRuleRepository,
    ) -> None:
        self.session = session
        self.repository = repository

    @staticmethod
    def normalize_mission_id(
        mission_id: str,
    ) -> str:
        normalized = mission_id.strip().upper()

        if not normalized:
            raise HTTPException(
                status_code=422,
                detail="mission_id must not be empty",
            )

        return normalized

    async def upsert_rule(
        self,
        *,
        mission_id: str,
        event_type: RuleEventType,
        payload: MissionRuleUpsert,
    ) -> MissionRuleModel:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        validated_config = validate_rule_config(
            event_type,
            payload.config,
        )

        rule = (
            await self.repository
            .get_by_mission_and_event(
                mission_id=mission_id,
                event_type=event_type.value,
            )
        )

        now = datetime.now(UTC)

        if rule is not None:
            if rule.status == MissionRuleStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Active mission rules are locked. "
                        "Deactivate the mission rules "
                        "before editing."
                    ),
                )

            rule.config = validated_config
            rule.enabled = payload.enabled
            rule.status = (
                MissionRuleStatus.DRAFT.value
            )
            rule.version += 1
            rule.updated_at = now

        else:
            rule = MissionRuleModel(
                mission_id=mission_id,
                event_type=event_type.value,
                enabled=payload.enabled,
                config=validated_config,
                status=MissionRuleStatus.DRAFT.value,
                version=1,
                created_at=now,
                updated_at=now,
            )

            self.session.add(rule)

        await self.session.commit()
        await self.session.refresh(rule)

        return rule

    async def get_rule(
        self,
        *,
        mission_id: str,
        event_type: RuleEventType,
    ) -> MissionRuleModel:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        rule = (
            await self.repository
            .get_by_mission_and_event(
                mission_id=mission_id,
                event_type=event_type.value,
            )
        )

        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Rule '{event_type.value}' "
                    f"for mission '{mission_id}' "
                    "was not found"
                ),
            )

        return rule

    async def list_rules(
        self,
        mission_id: str,
    ) -> MissionRuleListResponse:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        rules = await self.repository.list_by_mission(
            mission_id
        )

        statuses = {
            rule.status
            for rule in rules
        }

        combined_status = None

        if len(statuses) == 1:
            combined_status = MissionRuleStatus(
                next(iter(statuses))
            )

        return MissionRuleListResponse(
            mission_id=mission_id,
            status=combined_status,
            items=[
                MissionRuleResponse.model_validate(
                    rule
                )
                for rule in rules
            ],
        )

    async def delete_rule(
        self,
        *,
        mission_id: str,
        event_type: RuleEventType,
    ) -> None:
        rule = await self.get_rule(
            mission_id=mission_id,
            event_type=event_type,
        )

        if rule.status == MissionRuleStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot delete an active mission rule"
                ),
            )

        await self.repository.delete(rule)
        await self.session.commit()

    async def validate_mission_rules(
        self,
        mission_id: str,
    ) -> MissionRulesValidationResponse:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        rules = await self.repository.list_by_mission(
            mission_id
        )

        errors: list[str] = []

        if not rules:
            errors.append(
                "Mission does not have any rule"
            )

        for rule in rules:
            try:
                validate_rule_config(
                    RuleEventType(rule.event_type),
                    rule.config,
                )
            except Exception as exc:
                errors.append(
                    f"{rule.event_type}: {exc}"
                )

        enabled_rules = [
            rule
            for rule in rules
            if rule.enabled
        ]

        if not enabled_rules:
            errors.append(
                "Mission requires at least one enabled rule"
            )

        return MissionRulesValidationResponse(
            valid=not errors,
            errors=errors,
        )

    async def activate(
        self,
        mission_id: str,
    ) -> MissionRuleListResponse:
        validation = (
            await self.validate_mission_rules(
                mission_id
            )
        )

        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": (
                        "Mission rules are invalid"
                    ),
                    "errors": validation.errors,
                },
            )

        mission_id = self.normalize_mission_id(
            mission_id
        )

        rules = await self.repository.list_by_mission(
            mission_id
        )

        now = datetime.now(UTC)

        for rule in rules:
            rule.status = (
                MissionRuleStatus.ACTIVE.value
            )
            rule.activated_at = now
            rule.updated_at = now

        await self.session.commit()

        for rule in rules:
            await self.session.refresh(rule)

        return await self.list_rules(mission_id)

    async def deactivate(
        self,
        mission_id: str,
    ) -> MissionRuleListResponse:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        rules = await self.repository.list_by_mission(
            mission_id
        )

        if not rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Mission '{mission_id}' "
                    "does not have rules"
                ),
            )

        now = datetime.now(UTC)

        for rule in rules:
            rule.status = (
                MissionRuleStatus.INACTIVE.value
            )
            rule.updated_at = now

        await self.session.commit()

        for rule in rules:
            await self.session.refresh(rule)

        return await self.list_rules(mission_id)