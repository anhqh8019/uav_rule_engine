from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bts_monitoring.database.base import Base


class IncidentModel(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[UUID] = mapped_column(
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

    camera_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "cameras.camera_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    source_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "ai_events.event_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    incident_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open",
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    deduplication_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    occurrence_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_event = relationship(
        "AIEventModel",
        back_populates="incidents",
    )

    __table_args__ = (
        Index(
            "ix_incidents_dedup_status",
            "deduplication_key",
            "status",
        ),
    )