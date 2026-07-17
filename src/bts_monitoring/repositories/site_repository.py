from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bts_monitoring.database.models.site import SiteModel
from bts_monitoring.schemas.site import SiteCreate, SiteUpdate


class SiteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        payload: SiteCreate,
    ) -> SiteModel:
        site = SiteModel(
            **payload.model_dump(),
        )

        self.session.add(site)

        await self.session.commit()
        await self.session.refresh(site)

        return site

    async def get_by_id(
        self,
        site_id: str,
    ) -> SiteModel | None:
        statement = select(SiteModel).where(
            SiteModel.site_id == site_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        region: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list[SiteModel], int]:
        filters = []

        if region:
            filters.append(
                SiteModel.region == region,
            )

        if keyword:
            search_value = f"%{keyword.strip()}%"

            filters.append(
                or_(
                    SiteModel.site_id.ilike(search_value),
                    SiteModel.name.ilike(search_value),
                )
            )

        count_statement = select(
            func.count(SiteModel.site_id)
        )

        list_statement = select(SiteModel)

        if filters:
            count_statement = count_statement.where(*filters)
            list_statement = list_statement.where(*filters)

        offset = (page - 1) * page_size

        list_statement = (
            list_statement
            .order_by(SiteModel.site_id.asc())
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
        site: SiteModel,
        payload: SiteUpdate,
    ) -> SiteModel:
        update_data = payload.model_dump(
            exclude_unset=True,
        )

        for field_name, value in update_data.items():
            setattr(site, field_name, value)

        await self.session.commit()
        await self.session.refresh(site)

        return site

    async def delete(
        self,
        site: SiteModel,
    ) -> None:
        await self.session.delete(site)
        await self.session.commit()