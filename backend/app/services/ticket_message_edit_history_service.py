from sqlalchemy.orm import Session

from app.models.ticket_message_edit_history import (
    TicketMessageEditHistory,
    TicketMessageHistoryAction,
)


class TicketMessageEditHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_history(
        self,
        tenant_id: int,
        message_id: int,
        edited_by_user_id: int,
        action: TicketMessageHistoryAction,
        old_content: str,
        new_content: str,
    ) -> TicketMessageEditHistory:
        history = TicketMessageEditHistory(
            tenant_id=tenant_id,
            message_id=message_id,
            edited_by_user_id=edited_by_user_id,
            action=action,
            old_content=old_content,
            new_content=new_content,
        )

        self.db.add(history)
        self.db.flush()

        return history