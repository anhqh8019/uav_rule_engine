from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from bts_monitoring.api.dependencies import get_site_service
from bts_monitoring.schemas.site import (
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
)
from bts_monitoring.services.site_service import SiteService


router = APIRouter(
    prefix="/api/sites",
    tags=["sites"],
)

SiteServiceDependency = Annotated[
    SiteService,
    Depends(get_site_service),
]


@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_site(
    payload: SiteCreate,
    service: SiteServiceDependency,
) -> SiteResponse:
    site = await service.create_site(payload)

    return SiteResponse.model_validate(site)


@router.get(
    "",
    response_model=SiteListResponse,
)
async def list_sites(
    service: SiteServiceDependency,
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    region: Annotated[
        str | None,
        Query(max_length=100),
    ] = None,
    keyword: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
) -> SiteListResponse:
    return await service.list_sites(
        page=page,
        page_size=page_size,
        region=region,
        keyword=keyword,
    )


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
)
async def get_site(
    site_id: str,
    service: SiteServiceDependency,
) -> SiteResponse:
    site = await service.get_site(site_id)

    return SiteResponse.model_validate(site)


@router.patch(
    "/{site_id}",
    response_model=SiteResponse,
)
async def update_site(
    site_id: str,
    payload: SiteUpdate,
    service: SiteServiceDependency,
) -> SiteResponse:
    site = await service.update_site(
        site_id,
        payload,
    )

    return SiteResponse.model_validate(site)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_site(
    site_id: str,
    service: SiteServiceDependency,
) -> Response:
    await service.delete_site(site_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )