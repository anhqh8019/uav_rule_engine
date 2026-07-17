from dataclasses import dataclass
from sqlalchemy.orm import Mapped, mapped_column, relationship

@dataclass(frozen=True)
class Site:
    site_id: str
    name: str
    latitude: float
    longitude: float
    tower_type: str
    height_m: float | None
    region: str


from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from bts_monitoring.database.base import Base


class SiteModel(Base):
    __tablename__ = "sites"

    site_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    tower_type: Mapped[str] = mapped_column(String(50))
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    region: Mapped[str] = mapped_column(String(100))
    
    cameras = relationship(
        "CameraModel",
        back_populates="site",
        passive_deletes=True,
    )