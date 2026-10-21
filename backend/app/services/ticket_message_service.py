from sqlalchemy.orm import Session
from datetime import datetime
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.ticket_message import (
    TicketMessage,
    TicketMessageVisibility,
)
from app.models.ticket_message_edit_history import TicketMessageHistoryAction
from app.schemas.ticket import (
    TicketMessageCreate,
    TicketMessageUpdate,
)
from app.services.ticket_message_edit_history_service import (
    TicketMessageEditHistoryService,
)
from app.models.ticket_message_edit_history import (
    TicketMessageHistoryAction,
)
from app.models.ticket_message_mention import TicketMessageMention
from app.models.user_tenant import UserTenant
from app.models.user import User



class TicketMessageService:
    def __init__(self, db: Session):
        self.db = db

    def _get_customer_for_user(
        self,
        tenant_id: int,
        user_id: int,
    ) -> Customer | None:
        return (
            self.db.query(Customer)
            .filter(
                Customer.tenant_id == tenant_id,
                Customer.user_id == user_id,
                Customer.is_active.is_(True),
            )
            .first()
        )

    def _get_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
    ) -> Ticket | None:
        return (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
                Ticket.is_active.is_(True),
            )
            .first()
        )

    def create_message(
        self,
        tenant_id: int,
        ticket_id: int,
        author_user_id: int,
        data: TicketMessageCreate,
        is_customer: bool = False,
    ) -> TicketMessage:
        ticket = self._get_ticket(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=author_user_id,
            )

            if customer is None:
                raise ValueError(
                    "Cliente associado ao usuário não encontrado."
                )

            if ticket.customer_id != customer.id:
                raise ValueError(
                    "Cliente não pode adicionar comentários "
                    "a este ticket."
                )

            if data.visibility != TicketMessageVisibility.PUBLIC:
                raise ValueError(
                    "Cliente só pode criar comentários públicos."
                )

        try:
            message = TicketMessage(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                author_user_id=author_user_id,
                content=data.content,
                visibility=data.visibility,
            )

            self.db.add(message)
            self.db.flush()

            mentioned_user_ids = self._validate_mentioned_users(
                tenant_id=tenant_id,
                mentioned_user_ids=data.mentioned_user_ids,
                is_customer=is_customer,
            )

            for mentioned_user_id in mentioned_user_ids:
                mention = TicketMessageMention(
                    tenant_id=tenant_id,
                    message_id=message.id,
                    mentioned_user_id=mentioned_user_id,
                )

                self.db.add(mention)

            self.db.commit()
            self.db.refresh(message)

            return message

        except Exception:
            self.db.rollback()
            raise

    def update_message(
        self,
        tenant_id: int,
        ticket_id: int,
        message_id: int,
        user_id: int,
        data: TicketMessageUpdate,
        is_customer: bool = False,
    ) -> TicketMessage | None:
        ticket = self._get_ticket(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        message = (
            self.db.query(TicketMessage)
            .filter(
                TicketMessage.id == message_id,
                TicketMessage.tenant_id == tenant_id,
                TicketMessage.ticket_id == ticket_id,
                TicketMessage.deleted_at.is_(None),
            )
            .first()
        )

        if message is None:
            return None

        if message.author_user_id != user_id:
            raise ValueError(
                "Somente o autor da mensagem pode editá-la."
            )

        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=user_id,
            )

            if customer is None:
                raise ValueError(
                    "Cliente associado ao usuário não encontrado."
                )

            if ticket.customer_id != customer.id:
                raise ValueError(
                    "Cliente não possui acesso a este ticket."
                )

        if message.content == data.content:
            return message

        old_content = message.content

        message.content = data.content

        history_service = TicketMessageEditHistoryService(self.db)

        history_service.create_history(
            tenant_id=tenant_id,
            message_id=message.id,
            edited_by_user_id=user_id,
            action=TicketMessageHistoryAction.EDITED,
            old_content=old_content,
            new_content=data.content,
        )

        self.db.commit()
        self.db.refresh(message)

        return message

    def list_messages(
        self,
        tenant_id: int,
        ticket_id: int,
        user_id: int,
        is_customer: bool = False,
    ) -> list[TicketMessage]:
        ticket = self._get_ticket(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        query = (
            self.db.query(TicketMessage)
            .filter(
                TicketMessage.tenant_id == tenant_id,
                TicketMessage.ticket_id == ticket_id,
                TicketMessage.deleted_at.is_(None),
            )
        )

        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=user_id,
            )

            if customer is None:
                raise ValueError(
                    "Cliente associado ao usuário não encontrado."
                )

            if ticket.customer_id != customer.id:
                raise ValueError(
                    "Cliente não possui acesso a este ticket."
                )

            query = query.filter(
                TicketMessage.visibility
                == TicketMessageVisibility.PUBLIC
            )

        return query.order_by(
            TicketMessage.created_at.asc()
        ).all()

    def delete_message(
        self,
        tenant_id: int,
        ticket_id: int,
        message_id: int,
        user_id: int,
        is_customer: bool = False,
    ) -> TicketMessage | None:
        ticket = self._get_ticket(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        message = (
            self.db.query(TicketMessage)
            .filter(
                TicketMessage.id == message_id,
                TicketMessage.tenant_id == tenant_id,
                TicketMessage.ticket_id == ticket_id,
                TicketMessage.deleted_at.is_(None),
            )
            .first()
        )

        if message is None:
            return None

        if message.author_user_id != user_id:
            raise ValueError(
                "Somente o autor da mensagem pode excluí-la."
            )

        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=user_id,
            )

            if customer is None:
                raise ValueError(
                    "Cliente associado ao usuário não encontrado."
                )

            if ticket.customer_id != customer.id:
                raise ValueError(
                    "Cliente não possui acesso a este ticket."
                )

        message.deleted_at = datetime.utcnow()

        history_service = TicketMessageEditHistoryService(self.db)

        history_service.create_history(
            tenant_id=tenant_id,
            message_id=message.id,
            edited_by_user_id=user_id,
            action=TicketMessageHistoryAction.DELETED,
            old_content=message.content,
            new_content="[MENSAGEM EXCLUÍDA]",
        )

        self.db.commit()
        self.db.refresh(message)

        return message

    def _validate_mentioned_users(
        self,
        tenant_id: int,
        mentioned_user_ids: list[int],
        is_customer: bool = False,
    ) -> list[int]:
        if not mentioned_user_ids:
            return []

        unique_user_ids = list(dict.fromkeys(mentioned_user_ids))

        query = (
            self.db.query(
                User.id,
            )
            .join(
                UserTenant,
                UserTenant.user_id == User.id,
            )
            .filter(
                User.id.in_(unique_user_ids),
                User.is_active.is_(True),
                UserTenant.tenant_id == tenant_id,
                UserTenant.is_active.is_(True),
            )
        )

        if is_customer:
            query = query.filter(
                UserTenant.role != "CUSTOMER",
            )

        users = query.all()

        valid_user_ids = {
            user_id
            for (user_id,) in users
        }

        invalid_user_ids = [
            user_id
            for user_id in unique_user_ids
            if user_id not in valid_user_ids
        ]

        if invalid_user_ids:
            raise ValueError(
                "Um ou mais usuários mencionados não pertencem "
                "à equipe desta empresa, não estão ativos ou "
                "não podem ser mencionados."
            )

        return unique_user_ids