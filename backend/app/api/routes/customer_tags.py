from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.core.permissions.roles import TenantRole
from app.schemas.customer_tag import (
    CustomerTagCreate,
    CustomerTagResponse,
)
from app.schemas.tag import TagResponse
from app.services.customer_tag_service import CustomerTagService


router = APIRouter(
    prefix="/customers",
    tags=["Customer Tags"],
)


@router.post(
    "/{customer_id}/tags",
    response_model=CustomerTagResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_tag_to_customer(
    customer_id: int,
    data: CustomerTagCreate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerTagService(db)

    try:
        return service.add_tag_to_customer(
            tenant_id=tenant_access.tenant_id,
            customer_id=customer_id,
            tag_id=data.tag_id,
        )
    except ValueError as exc:
        detail = str(exc)

        if "já está associada" in detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


@router.get(
    "/{customer_id}/tags",
    response_model=list[TagResponse],
)
def list_customer_tags(
    customer_id: int,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerTagService(db)

    try:
        return service.list_customer_tags(
            tenant_id=tenant_access.tenant_id,
            customer_id=customer_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete(
    "/{customer_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_tag_from_customer(
    customer_id: int,
    tag_id: int,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerTagService(db)

    removed = service.remove_tag_from_customer(
        tenant_id=tenant_access.tenant_id,
        customer_id=customer_id,
        tag_id=tag_id,
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag não está associada a este cliente.",
        )

    return None