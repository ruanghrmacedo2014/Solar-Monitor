from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import (
    get_current_user,
    require_tenant_roles,
)
from app.schemas.tenant_performance_config import (
    TenantPerformanceConfigCreate,
    TenantPerformanceConfigResponse,
    TenantPerformanceConfigUpdate,
)
from app.services.tenant_performance_config_service import (
    create_tenant_performance_config,
    get_tenant_performance_config,
    update_tenant_performance_config,
)

router = APIRouter(
    prefix="/tenant",
    tags=["Tenant Performance Config"],
)


@router.get(
    "/performance-config",
    response_model=TenantPerformanceConfigResponse,
)
def get_performance_config(
    db: Session = Depends(get_db),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
            "CUSTOMER",
        )
    ),
):
    config = get_tenant_performance_config(
        db=db,
        tenant_id=tenant_access.tenant_id,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de performance da empresa não encontrada.",
        )

    return config


@router.post(
    "/performance-config",
    response_model=TenantPerformanceConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_performance_config(
    data: TenantPerformanceConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
        )
    ),
):
    try:
        return create_tenant_performance_config(
            db=db,
            tenant_id=tenant_access.tenant_id,
            data=data,
            created_by_user_id=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.patch(
    "/performance-config",
    response_model=TenantPerformanceConfigResponse,
)
def update_performance_config(
    data: TenantPerformanceConfigUpdate,
    db: Session = Depends(get_db),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
        )
    ),
):
    config = get_tenant_performance_config(
        db=db,
        tenant_id=tenant_access.tenant_id,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de performance da empresa não encontrada.",
        )

    return update_tenant_performance_config(
        db=db,
        config=config,
        data=data,
    )