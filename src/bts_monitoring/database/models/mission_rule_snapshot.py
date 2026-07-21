from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from bts_monitoring.database.base import Base


class MissionRuleSnapshotModel(Base):
    __tablename__ = "mission_rule_snapshots"

    snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    mission_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "mission_id",
            "version",
            name="uq_mission_rule_snapshot_version",
        ),
        Index(
            "ix_mission_rule_snapshot_latest",
            "mission_id",
            "version",
        ),
    )