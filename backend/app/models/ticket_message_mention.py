from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TicketMessageMention(Base):
    __tablename__ = "ticket_message_mentions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "message_id",
            "mentioned_user_id",
            name="uq_ticket_message_mentions_user",
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

    message_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_messages.id"),
        nullable=False,
        index=True,
    )

    mentioned_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )