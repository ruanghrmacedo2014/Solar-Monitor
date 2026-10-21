from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.core.permissions.roles import USER_TENANT_MANAGE_ROLES
from app.models.user_tenant import UserTenant
from app.schemas.user_tenant import UserTenantCreate
from app.services.user_tenant_service import (
    add_user_to_tenant,
    get_user_tenants_by_tenant,
)


router = APIRouter(
    prefix="/user-tenants",
    tags=["User Tenants"],
)


@router.post("/")
def add_user_to_tenant_endpoint(
    association_data: UserTenantCreate,
    tenant_access: UserTenant = Depends(
        require_tenant_roles(*USER_TENANT_MANAGE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    if association_data.tenant_id != tenant_access.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Usuário não possui permissão para esta empresa.",
        )

    try:
        association = add_user_to_tenant(
            db=db,
            user_id=association_data.user_id,
            tenant_id=association_data.tenant_id,
            role=association_data.role,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "id": association.id,
        "user_id": association.user_id,
        "tenant_id": association.tenant_id,
        "role": association.role,
        "is_active": association.is_active,
    }


@router.get("/user/{user_id}")
def get_user_tenants_endpoint(
    user_id: int,
    tenant_access: UserTenant = Depends(
        require_tenant_roles(*USER_TENANT_MANAGE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    associations = get_user_tenants_by_tenant(
        db=db,
        user_id=user_id,
        tenant_id=tenant_access.tenant_id,
    )

    return [
        {
            "id": association.id,
            "user_id": association.user_id,
            "tenant_id": association.tenant_id,
            "role": association.role,
            "is_active": association.is_active,
        }
        for association in associations
    ]