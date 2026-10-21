from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import get_current_user, require_tenant_roles
from app.models.user_tenant import TenantRole
from app.schemas.generation import (
    GenerationResponse,
    GenerationSummaryResponse,
)
from app.services.customer_service import get_customer_by_user
from app.services.generation_service import GenerationService
from app.services.solar_plant_service import get_solar_plant_by_id


router = APIRouter(
    prefix="/generation",
    tags=["Generation"],
)


@router.get(
    "/solar-plants/{solar_plant_id}",
    response_model=list[GenerationResponse],
)
def get_plant_generation(
    solar_plant_id: int,
    start_at: datetime = Query(...),
    end_at: datetime = Query(...),
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.SUPPORT,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    solar_plant = get_solar_plant_by_id(
        db=db,
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
    )

    if solar_plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta solar não encontrada.",
        )

    if tenant_access.role == TenantRole.CUSTOMER:
        customer = get_customer_by_user(
            db=db,
            tenant_id=tenant_access.tenant_id,
            user_id=current_user.id,
        )

        if customer is None or solar_plant.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planta solar não encontrada.",
            )

    if start_at > end_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_at deve ser menor ou igual a end_at.",
        )

    service = GenerationService(db)

    return service.get_saved_generation(
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
        start_at=start_at,
        end_at=end_at,
    )

@router.get(
    "/solar-plants/{solar_plant_id}/summary",
    response_model=GenerationSummaryResponse,
)
def get_plant_generation_summary(
    solar_plant_id: int,
    start_at: datetime = Query(...),
    end_at: datetime = Query(...),
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.SUPPORT,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    solar_plant = get_solar_plant_by_id(
        db=db,
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
    )

    if solar_plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planta solar não encontrada.",
        )

    if tenant_access.role == TenantRole.CUSTOMER:
        customer = get_customer_by_user(
            db=db,
            tenant_id=tenant_access.tenant_id,
            user_id=current_user.id,
        )

        if customer is None or solar_plant.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planta solar não encontrada.",
            )

    if start_at > end_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_at deve ser menor ou igual a end_at.",
        )

    service = GenerationService(db)

    return service.get_generation_summary(
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
        start_at=start_at,
        end_at=end_at,
    )