from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.camera import CameraModel
from bts_monitoring.schemas.camera import (
    CameraCreate,
    CameraUpdate,
)


class CameraRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        payload: CameraCreate,
    ) -> CameraModel:
        camera = CameraModel(
            **payload.model_dump(
                mode="json",
            )
        )

        self.session.add(camera)

        await self.session.commit()
        await self.session.refresh(camera)

        return camera

    async def get_by_id(
        self,
        camera_id: str,
    ) -> CameraModel | None:
        statement = select(CameraModel).where(
            CameraModel.camera_id == camera_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        site_id: str | None = None,
        camera_role: str | None = None,
        enabled: bool | None = None,
        keyword: str | None = None,
    ) -> tuple[list[CameraModel], int]:
        filters = []

        if site_id:
            filters.append(
                CameraModel.site_id == site_id,
            )

        if camera_role:
            filters.append(
                CameraModel.camera_role == camera_role,
            )

        if enabled is not None:
            filters.append(
                CameraModel.enabled == enabled,
            )

        if keyword:
            search_value = f"%{keyword.strip()}%"

            filters.append(
                or_(
                    CameraModel.camera_id.ilike(search_value),
                    CameraModel.name.ilike(search_value),
                )
            )

        count_statement = select(
            func.count(CameraModel.camera_id)
        )

        list_statement = select(CameraModel)

        if filters:
            count_statement = count_statement.where(*filters)
            list_statement = list_statement.where(*filters)

        offset = (page - 1) * page_size

        list_statement = (
            list_statement
            .order_by(CameraModel.camera_id.asc())
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
        items = list(list_result.scalars().all())

        return items, total

    async def update(
        self,
        camera: CameraModel,
        payload: CameraUpdate,
    ) -> CameraModel:
        update_data = payload.model_dump(
            exclude_unset=True,
            mode="json",
        )

        for field_name, value in update_data.items():
            setattr(camera, field_name, value)

        await self.session.commit()
        await self.session.refresh(camera)

        return camera

    async def delete(
        self,
        camera: CameraModel,
    ) -> None:
        await self.session.delete(camera)
        await self.session.commit()