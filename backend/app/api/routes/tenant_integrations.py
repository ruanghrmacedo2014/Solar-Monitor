from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.models.user_tenant import TenantRole
from app.schemas.tenant_integration import (
    SolarmanCredentialsUpdate,
    TenantIntegrationCreate,
    TenantIntegrationResponse,
)
from app.services.integrations.solarman_client import (
    SolarmanIntegrationError,
)
from app.services.tenant_integration_service import (
    create_tenant_integration,
    get_tenant_integrations,
    get_tenant_integration_by_id,
    update_solarman_credentials,
    get_solarman_account_info,
    authenticate_solarman_integration_for_tenant,
)

router = APIRouter(
    prefix="/tenant-integrations",
    tags=["Tenant Integrations"],
)


@router.post(
    "/",
    response_model=TenantIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_integration(
    data: TenantIntegrationCreate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
        )
    ),
    db: Session = Depends(get_db),
):
    return create_tenant_integration(
        db=db,
        tenant_id=tenant_access.tenant_id,
        provider=data.provider,
        name=data.name,
    )


@router.get(
    "/",
    response_model=list[TenantIntegrationResponse],
)
def list_integrations(
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.SUPPORT,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    return get_tenant_integrations(
        db=db,
        tenant_id=tenant_access.tenant_id,
    )


@router.get(
    "/{integration_id}",
    response_model=TenantIntegrationResponse,
)
def get_integration(
    integration_id: int,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.SUPPORT,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_access.tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integração não encontrada.",
        )

    return integration

@router.put(
    "/{integration_id}/solarman-credentials",
    response_model=TenantIntegrationResponse,
)
def update_solarman_credentials_route(
    integration_id: int,
    data: SolarmanCredentialsUpdate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
        )
    ),
    db: Session = Depends(get_db),
):
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_access.tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integração não encontrada.",
        )

    if integration.provider.value != "SOLARMAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta integração não é da Solarman.",
        )

    return update_solarman_credentials(
        db=db,
        tenant_id=tenant_access.tenant_id,
        integration_id=integration_id,
        credentials=data,
    )

@router.get(
    "/{integration_id}/solarman/account-info",
)
def get_solarman_account_info_route(
    integration_id: int,
    tenant_access=Depends(
        require_tenant_roles(TenantRole.TENANT_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    try:
        return get_solarman_account_info(
            db=db,
            tenant_id=tenant_access.tenant_id,
            integration_id=integration_id,
        )

    except (ValueError, SolarmanIntegrationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.post(
    "/{integration_id}/solarman/authenticate",
)
def authenticate_solarman_integration_route(
    integration_id: int,
    tenant_access=Depends(
        require_tenant_roles(TenantRole.TENANT_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    try:
        return authenticate_solarman_integration_for_tenant(
            db=db,
            tenant_id=tenant_access.tenant_id,
            integration_id=integration_id,
        )

    except (ValueError, SolarmanIntegrationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )