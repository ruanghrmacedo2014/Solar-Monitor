from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def create_tenant(
    db: Session,
    name: str,
    slug: str,
    cnpj: str,
    email: str,
    phone: str | None = None,
) -> Tenant:
    tenant = Tenant(
        name=name.strip(),
        slug=slug.strip().lower(),
        cnpj=cnpj.strip(),
        email=email.strip().lower(),
        phone=phone.strip() if phone else None,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant


def get_tenant_by_slug(
    db: Session,
    slug: str,
) -> Tenant | None:
    statement = select(Tenant).where(
        Tenant.slug == slug.strip().lower()
    )

    return db.scalar(statement)


def get_tenant_by_cnpj(
    db: Session,
    cnpj: str,
) -> Tenant | None:
    statement = select(Tenant).where(
        Tenant.cnpj == cnpj.strip()
    )

    return db.scalar(statement)

def update_tenant(
    db: Session,
    tenant: Tenant,
    name: str | None = None,
    slug: str | None = None,
    cnpj: str | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> Tenant:
    if name is not None:
        tenant.name = name.strip()

    if slug is not None:
        tenant.slug = slug.strip().lower()

    if cnpj is not None:
        tenant.cnpj = cnpj.strip()

    if email is not None:
        tenant.email = email.strip().lower()

    if phone is not None:
        tenant.phone = phone.strip() or None

    db.commit()
    db.refresh(tenant)

    return tenant