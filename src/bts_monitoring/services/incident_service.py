from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.database.models.incident import IncidentModel
from bts_monitoring.repositories.incident_repository import (
    IncidentRepository,
)
from bts_monitoring.schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
)
from bts_monitoring.services.rule_engine.base import RuleResult


SEVERITY_PRIORITY = {
    "low": 1,
    "warning": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


class IncidentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: IncidentRepository,
    ) -> None:
        self.session = session
        self.repository = repository

    async def create_or_update_from_rule(
        self,
        *,
        event: AIEventModel,
        result: RuleResult,
        commit: bool = False,
    ) -> IncidentModel:
        self._validate_rule_result(result)

        deduplication_key = result.deduplication_key
        assert deduplication_key is not None

        existing = (
            await self.repository
            .find_active_by_deduplication_key(
                deduplication_key
            )
        )

        if existing is not None:
            incident = await self._update_existing(
                existing=existing,
                event=event,
                result=result,
            )
        else:
            incident = await self._create_new(
                event=event,
                result=result,
            )

        if commit:
            await self.session.commit()
            await self.session.refresh(incident)

        return incident

    async def handle_rule_result(
        self,
        *,
        event: AIEventModel,
        result: RuleResult,
        commit: bool = False,
    ) -> IncidentModel:
        """Backward-compatible alias for older callers."""
        return await self.create_or_update_from_rule(
            event=event,
            result=result,
            commit=commit,
        )

    async def _update_existing(
        self,
        *,
        existing: IncidentModel,
        event: AIEventModel,
        result: RuleResult,
    ) -> IncidentModel:
        existing.source_event_id = event.event_id
        existing.last_seen_at = event.captured_at
        existing.occurrence_count += 1

        if self._is_higher_severity(
            result.severity,
            existing.severity,
        ):
            assert result.severity is not None
            existing.severity = result.severity

        if result.title:
            existing.title = result.title

        if result.message:
            existing.message = result.message

        existing.mission_id = event.mission_id
        existing.rule_snapshot_id = (
            event.rule_snapshot_id
        )
        existing.rule_snapshot_version = (
            event.rule_snapshot_version
        )
        existing.rule_snapshot_checksum = (
            event.rule_snapshot_checksum
        )

        await self.session.flush()
        await self.session.refresh(existing)

        return existing

    async def _create_new(
        self,
        *,
        event: AIEventModel,
        result: RuleResult,
    ) -> IncidentModel:
        assert result.incident_type is not None
        assert result.severity is not None
        assert result.deduplication_key is not None

        payload = IncidentCreate(
            mission_id=event.mission_id,
            site_id=event.site_id,
            camera_id=event.camera_id,
            source_event_id=event.event_id,
            incident_type=result.incident_type,
            severity=result.severity,
            status="open",
            title=(
                result.title
                or result.incident_type
            ),
            message=(
                result.message
                or result.incident_type
            ),
            deduplication_key=(
                result.deduplication_key
            ),
            first_seen_at=event.captured_at,
            last_seen_at=event.captured_at,
            occurrence_count=1,
            acknowledged_at=None,
            resolved_at=None,
            closed_at=None,
            assigned_to=None,
            rule_snapshot_id=(
                event.rule_snapshot_id
            ),
            rule_snapshot_version=(
                event.rule_snapshot_version
            ),
            rule_snapshot_checksum=(
                event.rule_snapshot_checksum
            ),
        )

        return await self.repository.create(payload)

    async def get_incident(
        self,
        incident_id: UUID,
    ) -> IncidentModel:
        incident = await self.repository.get_by_id(
            incident_id
        )

        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Incident '{incident_id}' not found"
                ),
            )

        return incident

    async def acknowledge(
        self,
        incident_id: UUID,
        *,
        assigned_to: str | None = None,
    ) -> IncidentModel:
        incident = await self.get_incident(
            incident_id
        )

        if incident.status not in (
            "open",
            "acknowledged",
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot acknowledge incident "
                    f"in status '{incident.status}'"
                ),
            )

        incident.status = "acknowledged"

        if incident.acknowledged_at is None:
            incident.acknowledged_at = (
                datetime.now(UTC)
            )

        if assigned_to is not None:
            incident.assigned_to = assigned_to

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def resolve(
        self,
        incident_id: UUID,
        *,
        message: str | None = None,
    ) -> IncidentModel:
        incident = await self.get_incident(
            incident_id
        )

        if incident.status in (
            "resolved",
            "closed",
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Incident is already "
                    f"'{incident.status}'"
                ),
            )

        incident.status = "resolved"
        incident.resolved_at = datetime.now(UTC)

        if message:
            incident.message = message

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def close(
        self,
        incident_id: UUID,
    ) -> IncidentModel:
        incident = await self.get_incident(
            incident_id
        )

        if incident.status != "resolved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only resolved incidents can be closed"
                ),
            )

        incident.status = "closed"
        incident.closed_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def assign(
        self,
        incident_id: UUID,
        *,
        assigned_to: str,
    ) -> IncidentModel:
        incident = await self.get_incident(
            incident_id
        )

        if incident.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cannot assign a closed incident"
                ),
            )

        incident.assigned_to = assigned_to

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def list_incidents(
        self,
        **filters,
    ) -> IncidentListResponse:
        incidents, total = await self.repository.list(
            **filters
        )

        return IncidentListResponse(
            items=[
                IncidentResponse.model_validate(
                    incident
                )
                for incident in incidents
            ],
            total=total,
            page=filters["page"],
            page_size=filters["page_size"],
        )

    @staticmethod
    def _validate_rule_result(
        result: RuleResult,
    ) -> None:
        if not result.triggered:
            raise ValueError(
                "Cannot create incident from "
                "a non-triggered rule result"
            )

        if not result.incident_type:
            raise ValueError(
                "Triggered rule result requires "
                "incident_type"
            )

        if not result.severity:
            raise ValueError(
                "Triggered rule result requires severity"
            )

        if not result.deduplication_key:
            raise ValueError(
                "Triggered rule result requires "
                "deduplication_key"
            )

    @staticmethod
    def _is_higher_severity(
        new_severity: str | None,
        old_severity: str,
    ) -> bool:
        if new_severity is None:
            return False

        return (
            SEVERITY_PRIORITY.get(new_severity, 0)
            > SEVERITY_PRIORITY.get(
                old_severity,
                0,
            )
        )