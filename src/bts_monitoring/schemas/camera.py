from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from bts_monitoring.core.enums import CameraRole


class CameraBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        examples=["Camera tổng quan cột"],
    )

    camera_role: CameraRole = Field(
        examples=[CameraRole.TOWER_OVERVIEW],
    )

    stream_url_secret_ref: str = Field(
        min_length=1,
        max_length=500,
        examples=["vault://cameras/CAM-HN-001"],
    )

    enabled: bool = True

    @field_validator(
        "name",
        "stream_url_secret_ref",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value must not be empty")

        return value


class CameraCreate(CameraBase):
    camera_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["CAM-HN-001"],
    )

    site_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["BTS-HN-001"],
    )

    @field_validator(
        "camera_id",
        "site_id",
    )
    @classmethod
    def normalize_ids(cls, value: str) -> str:
        return value.strip().upper()


class CameraUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    site_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    camera_role: CameraRole | None = None

    stream_url_secret_ref: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    enabled: bool | None = None

    @field_validator("site_id")
    @classmethod
    def normalize_site_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip().upper()

    @field_validator(
        "name",
        "stream_url_secret_ref",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Value must not be empty")

        return value


class CameraResponse(CameraBase):
    camera_id: str
    site_id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CameraListResponse(BaseModel):
    items: list[CameraResponse]
    total: int
    page: int
    page_size: int