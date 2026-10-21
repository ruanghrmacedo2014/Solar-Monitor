from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.tenant import Tenant

from app.models.user_tenant import TenantRole, UserTenant


def add_user_to_tenant(
    db: Session,
    user_id: int,
    tenant_id: int,
    role: TenantRole,
) -> UserTenant:
    existing = get_user_tenant(
        db=db,
        user_id=user_id,
        tenant_id=tenant_id,
    )

    if existing:
        raise ValueError(
            "Usuário já está associado a esta empresa."
        )

    user_tenant = UserTenant(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
    )

    db.add(user_tenant)
    db.commit()
    db.refresh(user_tenant)

    return user_tenant


def get_user_tenant(
    db: Session,
    user_id: int,
    tenant_id: int,
) -> UserTenant | None:
    statement = select(UserTenant).where(
        UserTenant.user_id == user_id,
        UserTenant.tenant_id == tenant_id,
    )

    return db.scalar(statement)

def get_user_tenants(
    db: Session,
    user_id: int,
) -> list[UserTenant]:
    statement = select(UserTenant).where(
        UserTenant.user_id == user_id,
        UserTenant.is_active.is_(True),
    )

    return list(db.scalars(statement).all())

def get_user_tenants_with_details(
    db: Session,
    user_id: int,
):
    statement = (
        select(
            UserTenant.tenant_id,
            Tenant.name,
            UserTenant.role,
        )
        .join(
            Tenant,
            Tenant.id == UserTenant.tenant_id,
        )
        .where(
            UserTenant.user_id == user_id,
            UserTenant.is_active.is_(True),
        )
    )

    return db.execute(statement).all()

def user_has_tenant_access(
    db: Session,
    user_id: int,
    tenant_id: int,
) -> UserTenant | None:
    statement = select(UserTenant).where(
        UserTenant.user_id == user_id,
        UserTenant.tenant_id == tenant_id,
        UserTenant.is_active.is_(True),
    )

    return db.scalar(statement)

def get_user_tenants_by_tenant(
    db: Session,
    user_id: int,
    tenant_id: int,
) -> list[UserTenant]:
    statement = (
        select(UserTenant)
        .where(
            UserTenant.user_id == user_id,
            UserTenant.tenant_id == tenant_id,
            UserTenant.is_active.is_(True),
        )
    )

    return list(db.scalars(statement).all())