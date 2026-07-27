from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bts_monitoring.database.base import Base


class SiteModel(Base):
    __tablename__ = "sites"

    site_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    tower_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    height_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    region: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    cameras = relationship(
        "CameraModel",
        back_populates="site",
        passive_deletes=True,
    )