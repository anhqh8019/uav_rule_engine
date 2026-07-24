from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.core.enums import (
    MissionRuleStatus,
    RuleEventType,
)
from bts_monitoring.database.models.mission_rule import (
    MissionRuleModel,
)
from bts_monitoring.infrastructure.cache.mission_rule_cache import (
    MissionRuleCache,
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
from bts_monitoring.services.rule_engine.providers.models import (
    MissionRuleDefinition,
)
from bts_monitoring.services.rule_engine.snapshots.service import (
    MissionRuleSnapshotService,
)

from bts_monitoring.infrastructure.messaging.rule_event_publisher import (
    RuleEventPublisher,
)
from bts_monitoring.services.rule_engine.events import (
    RuleSnapshotActivatedEvent,
)


class MissionRuleService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        repository: MissionRuleRepository,
        cache: MissionRuleCache,
        snapshot_service: MissionRuleSnapshotService,
        event_publisher: RuleEventPublisher,
    ) -> None:
        self.session = session
        self.repository = repository
        self.cache = cache
        self.snapshot_service = snapshot_service
        self.event_publisher = event_publisher

    @staticmethod
    def normalize_mission_id(
        mission_id: str,
    ) -> str:
        normalized = mission_id.strip().upper()

        if not normalized:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
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
            if (
                rule.status
                == MissionRuleStatus.ACTIVE.value
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Active mission rules are locked. "
                        "Deactivate them before editing."
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
                activated_at=None,
            )

            self.session.add(rule)

        try:
            await self.session.commit()
            await self.session.refresh(rule)
        except IntegrityError as exc:
            await self.session.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Mission rule already exists or "
                    "violates a database constraint"
                ),
            ) from exc

        await self.cache.delete(mission_id)

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
                MissionRuleResponse.model_validate(rule)
                for rule in rules
            ],
        )

    async def delete_rule(
        self,
        *,
        mission_id: str,
        event_type: RuleEventType,
    ) -> None:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        rule = await self.get_rule(
            mission_id=mission_id,
            event_type=event_type,
        )

        if (
            rule.status
            == MissionRuleStatus.ACTIVE.value
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot delete an active mission rule"
                ),
            )

        await self.repository.delete(rule)
        await self.session.commit()

        await self.cache.delete(mission_id)

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
                    dict(rule.config or {}),
                )
            except Exception as exc:
                errors.append(
                    f"{rule.event_type}: {exc}"
                )

        if not any(rule.enabled for rule in rules):
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
        *,
        created_by: str | None = None,
    ) -> MissionRuleListResponse:
        mission_id = self.normalize_mission_id(
            mission_id
        )

        validation = (
            await self.validate_mission_rules(
                mission_id
            )
        )

        if not validation.valid:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail={
                    "message": (
                        "Mission rules are invalid"
                    ),
                    "errors": validation.errors,
                },
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
                MissionRuleStatus.ACTIVE.value
            )
            rule.activated_at = now
            rule.updated_at = now

        try:
            snapshot = (
                await self.snapshot_service
                .create_snapshot(
                    mission_id=mission_id,
                    rules=rules,
                    created_by=created_by,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        for rule in rules:
            await self.session.refresh(rule)

        await self.session.refresh(snapshot)

        definitions = [
            MissionRuleDefinition(
                mission_id=mission_id,
                event_type=item["event_type"],
                enabled=item["enabled"],
                config=dict(item["config"]),
                version=int(
                    item.get("rule_version", 1)
                ),
            )
            for item in snapshot.rules
        ]

        await self.cache.set_snapshot(
            mission_id=mission_id,
            snapshot_id=str(snapshot.snapshot_id),
            version=snapshot.version,
            checksum=snapshot.checksum,
            rules=definitions,
        )

        event = RuleSnapshotActivatedEvent.create(
            mission_id=mission_id,
            snapshot_id=snapshot.snapshot_id,
            snapshot_version=snapshot.version,
            checksum=snapshot.checksum,
        )

        await self.event_publisher.publish_snapshot_activated(
            event
        )

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

        await self.cache.delete(mission_id)

        return await self.list_rules(mission_id)