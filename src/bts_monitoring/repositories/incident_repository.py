from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.incident import (
    IncidentModel,
)
from bts_monitoring.schemas.incident import IncidentCreate


ACTIVE_STATUSES = (
    "open",
    "acknowledged",
)


class IncidentRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        payload: IncidentCreate,
    ) -> IncidentModel:
        incident = IncidentModel(
            **payload.model_dump(
                mode="json",
            ),
            status="open",
        )

        self.session.add(incident)

        await self.session.flush()
        await self.session.refresh(incident)

        return incident

    async def get_by_id(
        self,
        incident_id: UUID,
    ) -> IncidentModel | None:
        statement = select(IncidentModel).where(
            IncidentModel.incident_id == incident_id
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def find_active_by_deduplication_key(
        self,
        deduplication_key: str,
    ) -> IncidentModel | None:
        statement = select(IncidentModel).where(
            IncidentModel.deduplication_key
            == deduplication_key,
            IncidentModel.status.in_(ACTIVE_STATUSES),
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        site_id: str | None = None,
        camera_id: str | None = None,
        incident_type: str | None = None,
        severity: str | None = None,
        incident_status: str | None = None,
    ) -> tuple[list[IncidentModel], int]:
        filters = []

        if site_id:
            filters.append(
                IncidentModel.site_id == site_id
            )

        if camera_id:
            filters.append(
                IncidentModel.camera_id == camera_id
            )

        if incident_type:
            filters.append(
                IncidentModel.incident_type
                == incident_type
            )

        if severity:
            filters.append(
                IncidentModel.severity == severity
            )

        if incident_status:
            filters.append(
                IncidentModel.status == incident_status
            )

        count_statement = select(
            func.count(IncidentModel.incident_id)
        )

        list_statement = select(IncidentModel)

        if filters:
            count_statement = count_statement.where(
                *filters
            )

            list_statement = list_statement.where(
                *filters
            )

        offset = (page - 1) * page_size

        list_statement = (
            list_statement
            .order_by(
                IncidentModel.last_seen_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        count_result = await self.session.execute(
            count_statement
        )

        list_result = await self.session.execute(
            list_statement
        )

        total = int(count_result.scalar_one())
        incidents = list(
            list_result.scalars().all()
        )

        return incidents, total