from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GenerationSyncLog(Base):
    __tablename__ = "generation_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="RUNNING",
    )

    total_plants: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    successful_plants: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_plants: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    total_records_received: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    total_records_saved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failures: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )