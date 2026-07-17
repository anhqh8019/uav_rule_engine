from fastapi import HTTPException, status

from bts_monitoring.database.models.site import SiteModel
from bts_monitoring.repositories.site_repository import (
    SiteRepository,
)
from bts_monitoring.schemas.site import (
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
)


class SiteService:
    def __init__(
        self,
        repository: SiteRepository,
    ) -> None:
        self.repository = repository

    async def create_site(
        self,
        payload: SiteCreate,
    ) -> SiteModel:
        existing_site = await self.repository.get_by_id(
            payload.site_id
        )

        if existing_site is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Site '{payload.site_id}' already exists"
                ),
            )

        return await self.repository.create(payload)

    async def get_site(
        self,
        site_id: str,
    ) -> SiteModel:
        normalized_site_id = site_id.strip().upper()

        site = await self.repository.get_by_id(
            normalized_site_id
        )

        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Site '{normalized_site_id}' not found"
                ),
            )

        return site

    async def list_sites(
        self,
        *,
        page: int,
        page_size: int,
        region: str | None,
        keyword: str | None,
    ) -> SiteListResponse:
        normalized_region = (
            region.strip()
            if region and region.strip()
            else None
        )

        normalized_keyword = (
            keyword.strip()
            if keyword and keyword.strip()
            else None
        )

        sites, total = await self.repository.list(
            page=page,
            page_size=page_size,
            region=normalized_region,
            keyword=normalized_keyword,
        )

        return SiteListResponse(
            items=[
                SiteResponse.model_validate(site)
                for site in sites
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_site(
        self,
        site_id: str,
        payload: SiteUpdate,
    ) -> SiteModel:
        site = await self.get_site(site_id)

        update_data = payload.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields supplied for update",
            )

        return await self.repository.update(
            site,
            payload,
        )

    async def delete_site(
        self,
        site_id: str,
    ) -> None:
        site = await self.get_site(site_id)

        await self.repository.delete(site)