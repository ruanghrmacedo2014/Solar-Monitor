from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SolarPlant(Base):
    __tablename__ = "solar_plants"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "solarman_station_id",
            name="uq_solar_plants_tenant_station",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

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

    # ID da estação/planta no Solarman.
    solarman_station_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    source_provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="MANUAL",
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    installed_power: Mapped[float | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    plant_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    grid_interconnection_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    start_operating_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    owner_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contact_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )