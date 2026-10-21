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


class TenantPerformanceConfig(Base):
    __tablename__ = "tenant_performance_configs"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            name="uq_tenant_performance_configs_tenant",
        ),
    )

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

    performance_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )

    availability_target: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )

    degradation_rate: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )

    alert_threshold_percent: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    configuration_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )