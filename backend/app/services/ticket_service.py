from sqlalchemy.orm import Session
from datetime import datetime
from app.models.customer import Customer
from app.models.solar_device import SolarDevice
from app.models.solar_plant import SolarPlant
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.ticket_history_service import TicketHistoryService
from app.models.user import User
from app.models.user_tenant import UserTenant


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    def claim_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        user_id: int,
    ) -> Ticket | None:
        ticket = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if ticket is None:
            return None

        if ticket.owner_user_id is not None:
            raise ValueError(
                "Ticket já está atribuído a outro usuário."
            )

        ticket.owner_user_id = user_id
        ticket.claimed_at = datetime.utcnow()

        history_service = TicketHistoryService(self.db)

        history_service.create_history(
            tenant_id=tenant_id,
            ticket_id=ticket.id,
            user_id=user_id,
            action="TICKET_CLAIMED",
            old_value=None,
            new_value=str(user_id),
        )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def unclaim_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        user_id: int,
    ) -> Ticket | None:
        ticket = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if ticket is None:
            return None

        if ticket.owner_user_id is None:
            raise ValueError(
                "Ticket não possui responsável."
            )

        old_owner_user_id = ticket.owner_user_id

        ticket.owner_user_id = None
        ticket.claimed_at = None

        history_service = TicketHistoryService(self.db)

        history_service.create_history(
            tenant_id=tenant_id,
            ticket_id=ticket.id,
            user_id=user_id,
            action="TICKET_UNCLAIMED",
            old_value=str(old_owner_user_id),
            new_value=None,
        )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def reassign_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        current_user_id: int,
        new_owner_user_id: int,
    ) -> Ticket | None:
        ticket = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
            )
            .with_for_update()
            .first()
        )

        if ticket is None:
            return None

        if ticket.owner_user_id is None:
            raise ValueError(
                "Ticket não possui responsável para ser reatribuído."
            )

        if ticket.owner_user_id == new_owner_user_id:
            raise ValueError(
                "O novo responsável já é o responsável atual."
            )

        new_owner = (
            self.db.query(UserTenant)
            .join(User, User.id == UserTenant.user_id)
            .filter(
                UserTenant.tenant_id == tenant_id,
                UserTenant.user_id == new_owner_user_id,
                UserTenant.is_active.is_(True),
                User.is_active.is_(True),
                UserTenant.role.in_(
                    [
                        "TENANT_ADMIN",
                        "OPERATOR",
                        "TECHNICIAN",
                    ]
                ),
            )
            .first()
        )

        if new_owner is None:
            raise ValueError(
                "Novo responsável não encontrado nesta empresa."
            )

        old_owner_user_id = ticket.owner_user_id

        ticket.owner_user_id = new_owner_user_id
        ticket.claimed_at = datetime.utcnow()

        history_service = TicketHistoryService(self.db)

        history_service.create_history(
            tenant_id=tenant_id,
            ticket_id=ticket.id,
            user_id=current_user_id,
            action="TICKET_REASSIGNED",
            old_value=str(old_owner_user_id),
            new_value=str(new_owner_user_id),
        )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket

    def _validate_status_transition(
        self,
        current_status,
        new_status,
    ) -> None:
        allowed_transitions = {
            "OPEN": {"IN_PROGRESS"},
            "IN_PROGRESS": {
                "WAITING_CUSTOMER",
                "WAITING_INTERNAL",
                "RESOLVED",
            },
            "WAITING_CUSTOMER": {
                "IN_PROGRESS",
            },
            "WAITING_INTERNAL": {
                "IN_PROGRESS",
            },
            "RESOLVED": {
                "CLOSED",
            },
            "CLOSED": {
                "OPEN",
            },
            "CANCELLED": set(),
        }

        current_value = current_status.value
        new_value = new_status.value

        if new_value not in allowed_transitions.get(
            current_value,
            set(),
        ):
            raise ValueError(
                f"Transição de status inválida: "
                f"{current_value} -> {new_value}."
            )

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

    def _validate_customer(
        self,
        tenant_id: int,
        customer_id: int | None,
    ) -> None:
        if customer_id is None:
            return

        customer = (
            self.db.query(Customer)
            .filter(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
                Customer.is_active.is_(True),
            )
            .first()
        )

        if customer is None:
            raise ValueError(
                "Cliente não encontrado nesta empresa."
            )

    def _validate_solar_plant(
        self,
        tenant_id: int,
        solar_plant_id: int | None,
        customer_id: int | None = None,
    ) -> SolarPlant | None:
        if solar_plant_id is None:
            return None

        plant = (
            self.db.query(SolarPlant)
            .filter(
                SolarPlant.id == solar_plant_id,
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
            .first()
        )

        if plant is None:
            raise ValueError(
                "Usina solar não encontrada nesta empresa."
            )

        if customer_id is not None and plant.customer_id != customer_id:
            raise ValueError(
                "A usina solar não pertence ao cliente informado."
            )

        return plant

    def _validate_solar_device(
        self,
        tenant_id: int,
        solar_device_id: int | None,
        customer_id: int | None = None,
        solar_plant_id: int | None = None,
    ) -> SolarDevice | None:
        if solar_device_id is None:
            return None

        device = (
            self.db.query(SolarDevice)
            .join(
                SolarPlant,
                SolarPlant.id == SolarDevice.solar_plant_id,
            )
            .filter(
                SolarDevice.id == solar_device_id,
                SolarDevice.tenant_id == tenant_id,
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
            .first()
        )

        if device is None:
            raise ValueError(
                "Dispositivo solar não encontrado nesta empresa."
            )

        if customer_id is not None:
            plant = (
                self.db.query(SolarPlant)
                .filter(
                    SolarPlant.id == device.solar_plant_id,
                    SolarPlant.tenant_id == tenant_id,
                    SolarPlant.is_active.is_(True),
                )
                .first()
            )

            if plant is None or plant.customer_id != customer_id:
                raise ValueError(
                    "O dispositivo solar não pertence ao cliente informado."
                )

        if (
            solar_plant_id is not None
            and device.solar_plant_id != solar_plant_id
        ):
            raise ValueError(
                "O dispositivo solar não pertence à usina informada."
            )

        return device

    def create_ticket(
        self,
        tenant_id: int,
        created_by_user_id: int,
        data: TicketCreate,
        is_customer: bool = False,
    ) -> Ticket:
        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=created_by_user_id,
            )

            if customer is None:
                raise ValueError(
                    "Cliente associado ao usuário não encontrado."
                )

            if data.customer_id != customer.id:
                raise ValueError(
                    "Cliente não pode abrir ticket para outro cliente."
                )

        self._validate_customer(
            tenant_id=tenant_id,
            customer_id=data.customer_id,
        )

        customer_id = data.customer_id if is_customer else None

        self._validate_solar_plant(
            tenant_id=tenant_id,
            solar_plant_id=data.solar_plant_id,
            customer_id=customer_id,
        )

        self._validate_solar_device(
            tenant_id=tenant_id,
            solar_device_id=data.solar_device_id,
            customer_id=customer_id,
            solar_plant_id=data.solar_plant_id,
        )

        ticket = Ticket(
            tenant_id=tenant_id,
            customer_id=data.customer_id,
            solar_plant_id=data.solar_plant_id,
            solar_device_id=data.solar_device_id,
            created_by_user_id=created_by_user_id,
            owner_user_id=None,
            title=data.title,
            description=data.description,
            priority=data.priority,
            category=data.category,
            subcategory=data.subcategory,
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        history_service = TicketHistoryService(self.db)

        history_service.create_history(
            tenant_id=tenant_id,
            ticket_id=ticket.id,
            user_id=created_by_user_id,
            action="TICKET_CREATED",
        )

        return ticket

    def get_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        user_id: int | None = None,
        is_customer: bool = False,
    ) -> Ticket | None:
        query = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
                Ticket.is_active.is_(True),
            )
        )

        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=user_id,
            )

            if customer is None:
                return None

            query = query.filter(
                Ticket.customer_id == customer.id,
            )

        return query.first()

    def list_tickets(
        self,
        tenant_id: int,
        user_id: int | None = None,
        is_customer: bool = False,
    ) -> list[Ticket]:
        query = (
            self.db.query(Ticket)
            .filter(
                Ticket.tenant_id == tenant_id,
                Ticket.is_active.is_(True),
            )
        )

        if is_customer:
            customer = self._get_customer_for_user(
                tenant_id=tenant_id,
                user_id=user_id,
            )

            if customer is None:
                return []

            query = query.filter(
                Ticket.customer_id == customer.id,
            )

        return (
            query
            .order_by(Ticket.created_at.desc())
            .all()
        )

    def update_ticket(
        self,
        tenant_id: int,
        ticket_id: int,
        data: TicketUpdate,
        user_id: int | None = None,
        is_customer: bool = False,
    ) -> Ticket | None:
        ticket = self.get_ticket(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            user_id=user_id,
            is_customer=is_customer,
        )

        if ticket is None:
            return None

        if is_customer:
            if (
                data.priority is not None
                or data.category is not None
                or data.subcategory is not None
                or data.status is not None
            ):
                raise ValueError(
                    "Cliente pode alterar apenas o título e a descrição do ticket."
                )

        if data.title is not None and data.title != ticket.title:
            old_title = ticket.title

            ticket.title = data.title

            history_service = TicketHistoryService(self.db)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                user_id=user_id,
                action="TICKET_UPDATED",
                old_value=old_title,
                new_value=data.title,
            )

        if data.description is not None and data.description != ticket.description:
            old_description = ticket.description

            ticket.description = data.description

            history_service = TicketHistoryService(self.db)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                user_id=user_id,
                action="TICKET_UPDATED",
                old_value=old_description,
                new_value=data.description,
            )

        if data.priority is not None and data.priority != ticket.priority:
            old_priority = ticket.priority.value

            ticket.priority = data.priority

            history_service = TicketHistoryService(self.db)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                user_id=user_id,
                action="TICKET_PRIORITY_CHANGED",
                old_value=old_priority,
                new_value=data.priority.value,
            )

        if data.category is not None and data.category != ticket.category:
            old_category = ticket.category

            ticket.category = data.category

            history_service = TicketHistoryService(self.db)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                user_id=user_id,
                action="TICKET_UPDATED",
                old_value=old_category,
                new_value=data.category,
            )

        if data.subcategory is not None and data.subcategory != ticket.subcategory:
            old_subcategory = ticket.subcategory

            ticket.subcategory = data.subcategory

            history_service = TicketHistoryService(self.db)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                user_id=user_id,
                action="TICKET_UPDATED",
                old_value=old_subcategory,
                new_value=data.subcategory,
            )

        if data.status is not None and data.status != ticket.status:
            self._validate_status_transition(
                current_status=ticket.status,
                new_status=data.status,
            )

            old_status = ticket.status.value

            ticket.status = data.status

            if data.status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()

            if data.status == TicketStatus.CLOSED:
                ticket.closed_at = datetime.utcnow()

            if data.status == TicketStatus.OPEN and old_status == TicketStatus.CLOSED.value:
                ticket.closed_at = None

            history_service = TicketHistoryService(self.db)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket.id,
                user_id=user_id,
                action="TICKET_STATUS_CHANGED",
                old_value=old_status,
                new_value=data.status.value,
            )

        self.db.commit()
        self.db.refresh(ticket)

        return ticket