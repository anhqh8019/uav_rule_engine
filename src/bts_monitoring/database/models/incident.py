from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from bts_monitoring.database.base import Base


class IncidentModel(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    mission_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    site_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    camera_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    incident_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
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

    rule_snapshot_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    rule_snapshot_version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    rule_snapshot_checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_incidents_mission_snapshot",
            "mission_id",
            "rule_snapshot_version",
        ),
    )