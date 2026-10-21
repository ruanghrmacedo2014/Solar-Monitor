from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class TicketMessageHistoryAction(str, Enum):
    EDITED = "EDITED"
    DELETED = "DELETED"

class TicketMessageEditHistory(Base):
    __tablename__ = "ticket_message_edit_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    action: Mapped[TicketMessageHistoryAction] = mapped_column(
        SqlEnum(
            TicketMessageHistoryAction,
            name="ticket_message_history_action",
        ),
        nullable=False,
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

    edited_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    old_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    new_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    edited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )