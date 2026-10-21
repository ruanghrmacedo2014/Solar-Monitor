from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GenerationRecord(Base):
    __tablename__ = "generation_records"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "solar_plant_id",
            "measured_at",
            name="uq_generation_records_tenant_plant_measured_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    solar_plant_id: Mapped[int] = mapped_column(
        ForeignKey("solar_plants.id"),
        nullable=False,
        index=True,
    )

    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    energy_today_kwh: Mapped[float | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
    )

    energy_total_kwh: Mapped[float | None] = mapped_column(
        Numeric(16, 3),
        nullable=True,
    )

    voltage_v: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    current_a: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    frequency_hz: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )