from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SolarResourceSnapshot(Base):
    __table_args__ = (
        UniqueConstraint(
            "solar_plant_id",
            "provider",
            "resource_type",
            "period_start",
            name="uq_solar_resource_snapshot_period",
        ),
    )

    __tablename__ = "solar_resource_snapshots"

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

    solar_plant_id: Mapped[int] = mapped_column(
        ForeignKey("solar_plants.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
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

    latitude: Mapped[float] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Numeric(10, 7),
        nullable=False,
    )

    solar_radiation_kwh_m2: Mapped[float | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    pv_output_kwh_kwp: Mapped[float | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    is_manual_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    override_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )