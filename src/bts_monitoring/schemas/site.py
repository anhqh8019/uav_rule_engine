from pydantic import BaseModel, ConfigDict, Field, field_validator


class SiteBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
        examples=["BTS Hà Nội 001"],
    )

    latitude: float = Field(
        ge=-90,
        le=90,
        examples=[21.028511],
    )

    longitude: float = Field(
        ge=-180,
        le=180,
        examples=[105.804817],
    )

    tower_type: str = Field(
        min_length=1,
        max_length=50,
        examples=["self_supporting"],
    )

    height_m: float | None = Field(
        default=None,
        gt=0,
        le=500,
        examples=[42.0],
    )

    region: str = Field(
        min_length=1,
        max_length=100,
        examples=["Hà Nội"],
    )

    @field_validator("name", "tower_type", "region")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value must not be empty")

        return value


class SiteCreate(SiteBase):
    site_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["BTS-HN-001"],
    )

    @field_validator("site_id")
    @classmethod
    def normalize_site_id(cls, value: str) -> str:
        return value.strip().upper()


class SiteUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    tower_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    height_m: float | None = Field(
        default=None,
        gt=0,
        le=500,
    )

    region: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    @field_validator("name", "tower_type", "region")
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


class SiteResponse(SiteBase):
    site_id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class SiteListResponse(BaseModel):
    items: list[SiteResponse]
    total: int
    page: int
    page_size: int