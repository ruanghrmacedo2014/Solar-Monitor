from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import (
    get_current_tenant,
    require_tenant_roles,
)
from app.core.permissions.roles import (
    CUSTOMER_CREATE_ROLES,
    USER_TENANT_MANAGE_ROLES,
)
from app.services.customer_service import (
    create_customer,
    get_customers_by_tenant,
    get_customer_by_id,
    get_customer_by_user,
    link_customer_to_user,
    update_customer,
    deactivate_customer,
    create_customer_with_user,
)
from app.models.user_tenant import TenantRole, UserTenant
from app.models.user_tenant import UserTenant
from app.schemas.customer import (
    CustomerCreate,
    CustomerUserLink,
    CustomerUpdate,
)
from app.models.customer import Customer
from sqlalchemy import select

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post("/")
def create_customer_endpoint(
    customer_data: CustomerCreate,
    tenant_access: UserTenant = Depends(
        require_tenant_roles(*CUSTOMER_CREATE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    customer = create_customer_with_user(
        db=db,
        tenant_id=tenant_access.tenant_id,
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
        document=customer_data.document,
        address=customer_data.address,
        city=customer_data.city,
        state=customer_data.state,
    )

    return {
        "id": customer.id,
        "tenant_id": customer.tenant_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "document": customer.document,
        "address": customer.address,
        "city": customer.city,
        "state": customer.state,
        "is_active": customer.is_active,
    }

@router.get("/")
def list_customers(
    tenant_access: UserTenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    if tenant_access.role == TenantRole.CUSTOMER:
        customer = get_customer_by_user(
            db=db,
            tenant_id=tenant_access.tenant_id,
            user_id=tenant_access.user_id,
        )

        if customer is None:
            return []

        return [
            {
                "id": customer.id,
                "tenant_id": customer.tenant_id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "document": customer.document,
                "address": customer.address,
                "city": customer.city,
                "state": customer.state,
                "is_active": customer.is_active,
            }
        ]

    customers = get_customers_by_tenant(
        db=db,
        tenant_id=tenant_access.tenant_id,
    )

    return [
        {
            "id": customer.id,
            "tenant_id": customer.tenant_id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "document": customer.document,
            "address": customer.address,
            "city": customer.city,
            "state": customer.state,
            "is_active": customer.is_active,
        }
        for customer in customers
    ]

@router.get("/me")
def get_my_customer(
    tenant_access: UserTenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user(
        db=db,
        tenant_id=tenant_access.tenant_id,
        user_id=tenant_access.user_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado para este usuário.",
        )

    return {
        "id": customer.id,
        "tenant_id": customer.tenant_id,
        "user_id": customer.user_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "document": customer.document,
        "address": customer.address,
        "city": customer.city,
        "state": customer.state,
        "is_active": customer.is_active,
    }

@router.get("/{customer_id}")
def get_customer_endpoint(
    customer_id: int,
    tenant_access: UserTenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    if tenant_access.role == TenantRole.CUSTOMER:
        customer = get_customer_by_user(
            db=db,
            tenant_id=tenant_access.tenant_id,
            user_id=tenant_access.user_id,
        )

        if customer is None or customer.id != customer_id:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado.",
            )
    else:
        customer = get_customer_by_id(
            db=db,
            tenant_id=tenant_access.tenant_id,
            customer_id=customer_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado.",
            )

    return {
        "id": customer.id,
        "tenant_id": customer.tenant_id,
        "user_id": customer.user_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "document": customer.document,
        "address": customer.address,
        "city": customer.city,
        "state": customer.state,
        "is_active": customer.is_active,
    }

@router.post("/{customer_id}/link-user")
def link_customer_user_endpoint(
    customer_id: int,
    link_data: CustomerUserLink,
    tenant_access: UserTenant = Depends(
        require_tenant_roles(*USER_TENANT_MANAGE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    try:
        customer = link_customer_to_user(
            db=db,
            tenant_id=tenant_access.tenant_id,
            customer_id=customer_id,
            user_id=link_data.user_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "id": customer.id,
        "tenant_id": customer.tenant_id,
        "user_id": customer.user_id,
        "name": customer.name,
        "email": customer.email,
    }

@router.patch("/{customer_id}")
def update_customer_endpoint(
    customer_id: int,
    customer_data: CustomerUpdate,
    tenant_access=Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_access.tenant_id,
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    customer = update_customer(
        db=db,
        customer=customer,
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
        document=customer_data.document,
        address=customer_data.address,
        city=customer_data.city,
        state=customer_data.state,
    )

    return {
        "id": customer.id,
        "tenant_id": customer.tenant_id,
        "user_id": customer.user_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "document": customer.document,
        "address": customer.address,
        "city": customer.city,
        "state": customer.state,
        "is_active": customer.is_active,
    }

@router.delete("/{customer_id}")
def delete_customer_endpoint(
    customer_id: int,
    tenant_access=Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    customer = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_access.tenant_id,
        )
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    customer = deactivate_customer(
        db=db,
        customer=customer,
    )

    return {
        "message": "Cliente desativado com sucesso.",
        "id": customer.id,
        "is_active": customer.is_active,
    }