from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bts_monitoring.database.base import Base


class CameraModel(Base):
    __tablename__ = "cameras"

    camera_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    site_id: Mapped[str] = mapped_column(
        ForeignKey(
            "sites.site_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    camera_role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    stream_url_secret_ref: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    site = relationship(
        "SiteModel",
        back_populates="cameras",
    )