from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def get_all_tenants(
    db: Session,
) -> list[Tenant]:
    statement = select(Tenant).order_by(Tenant.name)
    return list(db.scalars(statement).all())


def get_tenant_by_id(
    db: Session,
    tenant_id: int,
) -> Tenant | None:
    statement = select(Tenant).where(
        Tenant.id == tenant_id
    )
    return db.scalar(statement)