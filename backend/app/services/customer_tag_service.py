from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_tag import CustomerTag
from app.models.tag import Tag


class CustomerTagService:
    def __init__(self, db: Session):
        self.db = db

    def add_tag_to_customer(
        self,
        tenant_id: int,
        customer_id: int,
        tag_id: int,
    ) -> CustomerTag:
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
            self.db.query(CustomerTag)
            .filter(
                CustomerTag.tenant_id == tenant_id,
                CustomerTag.customer_id == customer_id,
                CustomerTag.tag_id == tag_id,
            )
            .first()
        )

        if existing is not None:
            raise ValueError(
                "Esta tag já está associada ao cliente."
            )

        customer_tag = CustomerTag(
            tenant_id=tenant_id,
            customer_id=customer_id,
            tag_id=tag_id,
        )

        self.db.add(customer_tag)
        self.db.commit()
        self.db.refresh(customer_tag)

        return customer_tag

    def remove_tag_from_customer(
        self,
        tenant_id: int,
        customer_id: int,
        tag_id: int,
    ) -> bool:
        customer_tag = (
            self.db.query(CustomerTag)
            .filter(
                CustomerTag.tenant_id == tenant_id,
                CustomerTag.customer_id == customer_id,
                CustomerTag.tag_id == tag_id,
            )
            .first()
        )

        if customer_tag is None:
            return False

        self.db.delete(customer_tag)
        self.db.commit()

        return True

    def list_customer_tags(
        self,
        tenant_id: int,
        customer_id: int,
    ) -> list[Tag]:
        customer = (
            self.db.query(Customer)
            .filter(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id,
            )
            .first()
        )

        if customer is None:
            raise ValueError(
                "Cliente não encontrado nesta empresa."
            )

        return (
            self.db.query(Tag)
            .join(
                CustomerTag,
                CustomerTag.tag_id == Tag.id,
            )
            .filter(
                CustomerTag.tenant_id == tenant_id,
                CustomerTag.customer_id == customer_id,
                Tag.tenant_id == tenant_id,
                Tag.is_active.is_(True),
            )
            .order_by(Tag.name.asc())
            .all()
        )