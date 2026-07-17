from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from bts_monitoring.api.dependencies import (
    get_camera_service,
)
from bts_monitoring.core.enums import CameraRole
from bts_monitoring.schemas.camera import (
    CameraCreate,
    CameraListResponse,
    CameraResponse,
    CameraUpdate,
)
from bts_monitoring.services.camera_service import (
    CameraService,
)


router = APIRouter(
    prefix="/api/cameras",
    tags=["cameras"],
)

CameraServiceDependency = Annotated[
    CameraService,
    Depends(get_camera_service),
]


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_camera(
    payload: CameraCreate,
    service: CameraServiceDependency,
) -> CameraResponse:
    camera = await service.create_camera(payload)

    return CameraResponse.model_validate(camera)


@router.get(
    "",
    response_model=CameraListResponse,
)
async def list_cameras(
    service: CameraServiceDependency,
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    site_id: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=64,
        ),
    ] = None,
    camera_role: Annotated[
        CameraRole | None,
        Query(),
    ] = None,
    enabled: Annotated[
        bool | None,
        Query(),
    ] = None,
    keyword: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
) -> CameraListResponse:
    return await service.list_cameras(
        page=page,
        page_size=page_size,
        site_id=site_id,
        camera_role=(
            camera_role.value
            if camera_role is not None
            else None
        ),
        enabled=enabled,
        keyword=keyword,
    )


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
)
async def get_camera(
    camera_id: str,
    service: CameraServiceDependency,
) -> CameraResponse:
    camera = await service.get_camera(camera_id)

    return CameraResponse.model_validate(camera)


@router.patch(
    "/{camera_id}",
    response_model=CameraResponse,
)
async def update_camera(
    camera_id: str,
    payload: CameraUpdate,
    service: CameraServiceDependency,
) -> CameraResponse:
    camera = await service.update_camera(
        camera_id,
        payload,
    )

    return CameraResponse.model_validate(camera)


@router.delete(
    "/{camera_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_camera(
    camera_id: str,
    service: CameraServiceDependency,
) -> Response:
    await service.delete_camera(camera_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )