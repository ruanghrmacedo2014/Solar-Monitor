from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_platform_admin
from app.services.platform_service import get_all_tenants, get_tenant_by_id

from app.core.security.jwt import create_access_token


router = APIRouter(
    prefix="/platform",
    tags=["Platform"],
)


@router.get("/tenants")
def list_platform_tenants(
    db: Session = Depends(get_db),
    current_user=Depends(require_platform_admin),
):
    tenants = get_all_tenants(db=db)

    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "cnpj": tenant.cnpj,
            "email": tenant.email,
            "phone": tenant.phone,
        }
        for tenant in tenants
    ]

@router.post("/tenants/{tenant_id}/select")
def select_platform_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_platform_admin),
):
    tenant = get_tenant_by_id(
        db=db,
        tenant_id=tenant_id,
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada.",
        )

    access_token = create_access_token(
        user_id=current_user.id,
        tenant_id=tenant.id,
        role="PLATFORM_ADMIN",
        platform_context=True,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "role": "PLATFORM_ADMIN",
    }