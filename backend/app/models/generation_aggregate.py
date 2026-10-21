from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GenerationAggregate(Base):
    __tablename__ = "generation_aggregates"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
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

    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    granularity: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    generation_kwh: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "solar_plant_id",
            "period_start",
            "granularity",
            name="uq_generation_aggregates_tenant_plant_period_granularity",
        ),
    )