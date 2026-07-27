from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.schemas.ai_event import AIEventCreate


class AIEventRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        payload: AIEventCreate,
    ) -> AIEventModel:
        event = AIEventModel(
            **payload.model_dump(mode="python")
        )

        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)

        return event

    async def get_by_id(
        self,
        event_id: UUID,
    ) -> AIEventModel | None:
        statement = select(AIEventModel).where(
            AIEventModel.event_id == event_id
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
        event_type: str | None = None,
        min_confidence: float | None = None,
        captured_from: datetime | None = None,
        captured_to: datetime | None = None,
    ) -> tuple[list[AIEventModel], int]:
        filters = []

        if site_id:
            filters.append(
                AIEventModel.site_id == site_id
            )

        if camera_id:
            filters.append(
                AIEventModel.camera_id == camera_id
            )

        if event_type:
            filters.append(
                AIEventModel.event_type == event_type
            )

        if min_confidence is not None:
            filters.append(
                AIEventModel.confidence
                >= min_confidence
            )

        if captured_from:
            filters.append(
                AIEventModel.captured_at
                >= captured_from
            )

        if captured_to:
            filters.append(
                AIEventModel.captured_at
                <= captured_to
            )

        count_statement = select(
            func.count(AIEventModel.event_id)
        )
        list_statement = select(AIEventModel)

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
                AIEventModel.captured_at.desc()
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

        return (
            list(list_result.scalars().all()),
            int(count_result.scalar_one()),
        )

    async def count_recent_events(
        self,
        *,
        camera_id: str,
        event_type: str,
        min_confidence: float,
        captured_from: datetime,
        captured_to: datetime,
    ) -> int:
        statement = select(
            func.count(AIEventModel.event_id)
        ).where(
            AIEventModel.camera_id == camera_id,
            AIEventModel.event_type == event_type,
            AIEventModel.confidence >= min_confidence,
            AIEventModel.captured_at >= captured_from,
            AIEventModel.captured_at <= captured_to,
        )

        result = await self.session.execute(statement)

        return int(result.scalar_one())