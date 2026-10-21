from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.models.ticket import Ticket
from app.models.ticket_tag import TicketTag


class TicketTagService:
    def __init__(self, db: Session):
        self.db = db

    def add_tag_to_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        tag_id: int,
    ) -> TicketTag:
        ticket = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
                Ticket.is_active.is_(True),
            )
            .first()
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        tag = (
            self.db.query(Tag)
            .filter(
                Tag.id == tag_id,
                Tag.tenant_id == tenant_id,
                Tag.is_active.is_(True),
            )
            .first()
        )

        if tag is None:
            raise ValueError(
                "Tag não encontrada ou está inativa."
            )

        existing = (
            self.db.query(TicketTag)
            .filter(
                TicketTag.tenant_id == tenant_id,
                TicketTag.ticket_id == ticket_id,
                TicketTag.tag_id == tag_id,
            )
            .first()
        )

        if existing is not None:
            raise ValueError(
                "Esta tag já está associada ao ticket."
            )

        ticket_tag = TicketTag(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            tag_id=tag_id,
        )

        self.db.add(ticket_tag)
        self.db.commit()
        self.db.refresh(ticket_tag)

        return ticket_tag

    def remove_tag_from_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        tag_id: int,
    ) -> bool:
        ticket_tag = (
            self.db.query(TicketTag)
            .filter(
                TicketTag.tenant_id == tenant_id,
                TicketTag.ticket_id == ticket_id,
                TicketTag.tag_id == tag_id,
            )
            .first()
        )

        if ticket_tag is None:
            return False

        self.db.delete(ticket_tag)
        self.db.commit()

        return True

    def list_ticket_tags(
        self,
        tenant_id: int,
        ticket_id: int,
    ) -> list[Tag]:
        ticket = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
            )
            .first()
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        return (
            self.db.query(Tag)
            .join(
                TicketTag,
                TicketTag.tag_id == Tag.id,
            )
            .filter(
                TicketTag.tenant_id == tenant_id,
                TicketTag.ticket_id == ticket_id,
                Tag.tenant_id == tenant_id,
                Tag.is_active.is_(True),
            )
            .order_by(Tag.name.asc())
            .all()
        )