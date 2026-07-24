from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from bts_monitoring.database.base import Base


class AIEventModel(Base):
    __tablename__ = "ai_events"

    event_id: Mapped[UUID] = mapped_column(
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

    bbox: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    polygon: Mapped[list[Any] | None] = mapped_column(
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
            "ix_ai_events_mission_snapshot",
            "mission_id",
            "rule_snapshot_version",
        ),
    )