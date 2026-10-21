from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SolarDevice(Base):
    __tablename__ = "solar_devices"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "solarman_device_id",
            name="uq_solar_devices_tenant_device",
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

    solarman_device_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    device_sn: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    device_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    connect_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    collection_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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