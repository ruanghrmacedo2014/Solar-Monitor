from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.models.tenant import Tenant
from app.models.user_tenant import TenantRole
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.tenant_service import create_tenant, update_tenant


router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
)


@router.post("/")
def create_tenant_endpoint(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
):
    tenant = create_tenant(
        db=db,
        name=tenant_data.name,
        slug=tenant_data.slug,
        cnpj=tenant_data.cnpj,
        email=tenant_data.email,
        phone=tenant_data.phone,
    )

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "cnpj": tenant.cnpj,
        "email": tenant.email,
        "phone": tenant.phone,
    }


@router.patch("/me")
def update_current_tenant_endpoint(
    tenant_data: TenantUpdate,
    tenant_access=Depends(
        require_tenant_roles(TenantRole.TENANT_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    tenant = db.scalar(
        select(Tenant).where(
            Tenant.id == tenant_access.tenant_id
        )
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada.",
        )

    tenant = update_tenant(
        db=db,
        tenant=tenant,
        name=tenant_data.name,
        slug=tenant_data.slug,
        cnpj=tenant_data.cnpj,
        email=tenant_data.email,
        phone=tenant_data.phone,
    )

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "cnpj": tenant.cnpj,
        "email": tenant.email,
        "phone": tenant.phone,
    }