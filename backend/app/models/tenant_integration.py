from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IntegrationProvider(str, Enum):
    SOLARMAN = "SOLARMAN"


class SyncStatus(str, Enum):
    NEVER = "NEVER"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class TenantIntegration(Base):
    __tablename__ = "tenant_integrations"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[IntegrationProvider] = mapped_column(
        SQLEnum(IntegrationProvider),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Dados de autenticação/configuração do provedor.
    # Serão criptografados posteriormente.
    credentials_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    access_token_encrypted: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
    )

    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    configuration: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_sync_status: Mapped[SyncStatus] = mapped_column(
        SQLEnum(SyncStatus),
        default=SyncStatus.NEVER,
        nullable=False,
    )

    last_sync_error: Mapped[str | None] = mapped_column(
        Text,
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