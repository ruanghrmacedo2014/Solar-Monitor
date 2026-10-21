from sqlalchemy.orm import Session

from app.models.ticket_history import TicketHistory


class TicketHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_history(
        self,
        tenant_id: int,
        ticket_id: int,
        user_id: int,
        action: str,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> TicketHistory:
        history = TicketHistory(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            user_id=user_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

        self.db.add(history)
        self.db.flush()

        return history