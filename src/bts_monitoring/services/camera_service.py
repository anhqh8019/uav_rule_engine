from fastapi import HTTPException, status

from bts_monitoring.database.models.camera import CameraModel
from bts_monitoring.repositories.camera_repository import (
    CameraRepository,
)
from bts_monitoring.repositories.site_repository import (
    SiteRepository,
)
from bts_monitoring.schemas.camera import (
    CameraCreate,
    CameraListResponse,
    CameraResponse,
    CameraUpdate,
)


class CameraService:
    def __init__(
        self,
        camera_repository: CameraRepository,
        site_repository: SiteRepository,
    ) -> None:
        self.camera_repository = camera_repository
        self.site_repository = site_repository

    async def create_camera(
        self,
        payload: CameraCreate,
    ) -> CameraModel:
        existing_camera = (
            await self.camera_repository.get_by_id(
                payload.camera_id
            )
        )

        if existing_camera is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Camera '{payload.camera_id}' "
                    "already exists"
                ),
            )

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

        return await self.camera_repository.create(
            payload
        )

    async def get_camera(
        self,
        camera_id: str,
    ) -> CameraModel:
        normalized_camera_id = (
            camera_id.strip().upper()
        )

        camera = (
            await self.camera_repository.get_by_id(
                normalized_camera_id
            )
        )

        if camera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Camera '{normalized_camera_id}' "
                    "not found"
                ),
            )

        return camera

    async def list_cameras(
        self,
        *,
        page: int,
        page_size: int,
        site_id: str | None,
        camera_role: str | None,
        enabled: bool | None,
        keyword: str | None,
    ) -> CameraListResponse:
        normalized_site_id = (
            site_id.strip().upper()
            if site_id and site_id.strip()
            else None
        )

        normalized_keyword = (
            keyword.strip()
            if keyword and keyword.strip()
            else None
        )

        cameras, total = (
            await self.camera_repository.list(
                page=page,
                page_size=page_size,
                site_id=normalized_site_id,
                camera_role=camera_role,
                enabled=enabled,
                keyword=normalized_keyword,
            )
        )

        return CameraListResponse(
            items=[
                CameraResponse.model_validate(camera)
                for camera in cameras
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_camera(
        self,
        camera_id: str,
        payload: CameraUpdate,
    ) -> CameraModel:
        camera = await self.get_camera(camera_id)

        update_data = payload.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="No fields supplied for update",
            )

        if "site_id" in update_data:
            target_site_id = update_data["site_id"]

            site = await self.site_repository.get_by_id(
                target_site_id
            )

            if site is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Site '{target_site_id}' "
                        "not found"
                    ),
                )

        return await self.camera_repository.update(
            camera,
            payload,
        )

    async def delete_camera(
        self,
        camera_id: str,
    ) -> None:
        camera = await self.get_camera(camera_id)

        await self.camera_repository.delete(camera)