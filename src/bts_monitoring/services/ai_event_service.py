from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.repositories.ai_event_repository import (
    AIEventRepository,
)
from bts_monitoring.repositories.camera_repository import (
    CameraRepository,
)
from bts_monitoring.repositories.site_repository import (
    SiteRepository,
)
from bts_monitoring.schemas.ai_event import (
    AIEventCreate,
    AIEventListResponse,
    AIEventResponse,
)


class AIEventService:
    def __init__(
        self,
        session: AsyncSession,
        event_repository: AIEventRepository,
        site_repository: SiteRepository,
        camera_repository: CameraRepository,
    ) -> None:
        self.session = session
        self.event_repository = event_repository
        self.site_repository = site_repository
        self.camera_repository = camera_repository

    async def create_event(
        self,
        payload: AIEventCreate,
        *,
        commit: bool = True,
    ) -> AIEventModel:
        site = await self.site_repository.get_by_id(
            payload.site_id
        )

        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Site '{payload.site_id}' not found"
                ),
            )

        camera = await self.camera_repository.get_by_id(
            payload.camera_id
        )

        if camera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Camera '{payload.camera_id}' "
                    "not found"
                ),
            )

        if camera.site_id != payload.site_id:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    f"Camera '{payload.camera_id}' does not "
                    f"belong to site '{payload.site_id}'"
                ),
            )

        event = await self.event_repository.create(
            payload
        )

        if commit:
            await self.session.commit()
            await self.session.refresh(event)

        return event

    async def get_event(
        self,
        event_id: UUID,
    ) -> AIEventModel:
        event = await self.event_repository.get_by_id(
            event_id
        )

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI event '{event_id}' not found",
            )

        return event

    async def list_events(
        self,
        **filters,
    ) -> AIEventListResponse:
        events, total = await self.event_repository.list(
            **filters
        )

        return AIEventListResponse(
            items=[
                AIEventResponse.model_validate(event)
                for event in events
            ],
            total=total,
            page=filters["page"],
            page_size=filters["page_size"],
        )