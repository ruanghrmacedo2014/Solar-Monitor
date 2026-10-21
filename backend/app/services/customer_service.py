from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.user_tenant import TenantRole, UserTenant

from app.core.security.password import hash_password
from app.models.user import User
from app.services.password_setup_service import send_password_setup_email
from app.services.password_token_service import generate_temporary_password
from app.services.user_service import get_user_by_email


def create_customer(
    db: Session,
    tenant_id: int,
    name: str,
    email: str | None = None,
    phone: str | None = None,
    document: str | None = None,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
) -> Customer:
    customer = Customer(
        tenant_id=tenant_id,
        name=name.strip(),
        email=email.strip().lower() if email else None,
        phone=phone.strip() if phone else None,
        document=document.strip() if document else None,
        address=address.strip() if address else None,
        city=city.strip() if city else None,
        state=state.strip().upper() if state else None,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer

def update_customer(
    db: Session,
    customer: Customer,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    document: str | None = None,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
) -> Customer:
    if name is not None:
        customer.name = name.strip()

    if email is not None:
        customer.email = email.strip().lower()

    if phone is not None:
        customer.phone = phone.strip() or None

    if document is not None:
        customer.document = document.strip() or None

    if address is not None:
        customer.address = address.strip() or None

    if city is not None:
        customer.city = city.strip() or None

    if state is not None:
        customer.state = state.strip() or None

    db.commit()
    db.refresh(customer)

    return customer

def get_customers_by_tenant(
    db: Session,
    tenant_id: int,
) -> list[Customer]:
    statement = (
        select(Customer)
        .where(
            Customer.tenant_id == tenant_id,
            Customer.is_active.is_(True),
        )
        .order_by(Customer.name)
    )

    return list(db.scalars(statement).all())

def get_customer_by_id(
    db: Session,
    tenant_id: int,
    customer_id: int,
) -> Customer | None:
    statement = (
        select(Customer)
        .where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
            Customer.is_active.is_(True),
        )
    )

    return db.scalar(statement)

def link_customer_to_user(
    db: Session,
    tenant_id: int,
    customer_id: int,
    user_id: int,
) -> Customer:
    customer = get_customer_by_id(
        db=db,
        tenant_id=tenant_id,
        customer_id=customer_id,
    )

    if customer is None:
        raise ValueError("Cliente não encontrado.")

    if customer.user_id is not None:
        raise ValueError("Este cliente já possui um usuário vinculado.")

    # Verifica se o usuário pertence à mesma empresa
    # e está associado como CUSTOMER.
    statement = select(UserTenant).where(
        UserTenant.user_id == user_id,
        UserTenant.tenant_id == tenant_id,
        UserTenant.role == TenantRole.CUSTOMER,
        UserTenant.is_active.is_(True),
    )

    user_tenant = db.scalar(statement)

    if user_tenant is None:
        raise ValueError(
            "O usuário precisa estar associado a esta empresa como CUSTOMER."
        )

    # Um usuário só pode estar vinculado a um cliente.
    statement = select(Customer).where(
        Customer.user_id == user_id,
    )

    existing_customer = db.scalar(statement)

    if existing_customer is not None:
        raise ValueError(
            "Este usuário já está vinculado a um cliente."
        )

    customer.user_id = user_id

    db.commit()
    db.refresh(customer)

    return customer

def get_customer_by_user(
    db: Session,
    tenant_id: int,
    user_id: int,
) -> Customer | None:
    statement = (
        select(Customer)
        .where(
            Customer.tenant_id == tenant_id,
            Customer.user_id == user_id,
            Customer.is_active.is_(True),
        )
    )

    return db.scalar(statement)

def deactivate_customer(
    db: Session,
    customer: Customer,
) -> Customer:
    customer.is_active = False

    db.commit()
    db.refresh(customer)

    return customer
def create_customer_with_user(
    db: Session,
    tenant_id: int,
    name: str,
    email: str,
    phone: str | None = None,
    document: str | None = None,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
) -> Customer:
    normalized_email = email.strip().lower()

    existing_user = get_user_by_email(
        db=db,
        email=normalized_email,
    )

    if existing_user is not None:
        raise ValueError(
            "Já existe um usuário com este e-mail."
        )

    temporary_password = generate_temporary_password()

    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(temporary_password),
        is_active=True,
    )

    db.add(user)
    db.flush()

    user_tenant = UserTenant(
        user_id=user.id,
        tenant_id=tenant_id,
        role=TenantRole.CUSTOMER,
        is_active=True,
    )

    db.add(user_tenant)
    db.flush()

    customer = Customer(
        tenant_id=tenant_id,
        user_id=user.id,
        name=name.strip(),
        email=normalized_email,
        phone=phone.strip() if phone else None,
        document=document.strip() if document else None,
        address=address.strip() if address else None,
        city=city.strip() if city else None,
        state=state.strip().upper() if state else None,
    )

    db.add(customer)
    db.flush()

    db.commit()
    db.refresh(customer)

    try:
        send_password_setup_email(
            db=db,
            user=user,
        )
    except Exception:
        pass

    return customer