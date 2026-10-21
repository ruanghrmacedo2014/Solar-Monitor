from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    solar_plant_id: Mapped[int | None] = mapped_column(
        ForeignKey("solar_plants.id"),
        nullable=True,
        index=True,
    )

    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    actual_kwh: Mapped[float | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    expected_kwh: Mapped[float | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    performance_percent: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    coverage_percent: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    data_quality: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    classification: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="GENERATED",
        index=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )