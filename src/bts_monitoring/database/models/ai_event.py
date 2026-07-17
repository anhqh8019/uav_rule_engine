from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bts_monitoring.database.base import Base


class AIEventModel(Base):
    __tablename__ = "ai_events"

    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    site_id: Mapped[str] = mapped_column(
        ForeignKey(
            "sites.site_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    camera_id: Mapped[str] = mapped_column(
        ForeignKey(
            "cameras.camera_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    bbox: Mapped[dict[str, float] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    polygon: Mapped[list[list[float]] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    evidence_uri: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    incidents = relationship(
        "IncidentModel",
        back_populates="source_event",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "ix_ai_events_camera_type_captured",
            "camera_id",
            "event_type",
            "captured_at",
        ),
    )