from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import (
    get_current_tenant,
    get_current_user,
    require_tenant_roles,
)
from app.schemas.plant_performance_config import (
    EffectivePlantPerformanceConfigResponse,
    PlantPerformanceConfigCreate,
    PlantPerformanceConfigResponse,
    PlantPerformanceConfigUpdate,
)
from app.services.plant_performance_config_service import (
    create_plant_performance_config,
    get_plant_performance_config,
    update_plant_performance_config,
    get_effective_performance_config
)

router = APIRouter(
    prefix="/solar-plants",
    tags=["Plant Performance Config"],
)


@router.get(
    "/{solar_plant_id}/performance-config",
    response_model=EffectivePlantPerformanceConfigResponse,
)
def get_performance_config(
    solar_plant_id: int,
    db: Session = Depends(get_db),
    tenant_access=Depends(get_current_tenant),
):
    config, source = get_effective_performance_config(
        db=db,
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
        user_id=getattr(tenant_access, "user_id", None),
        role=tenant_access.role,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de performance não encontrada.",
        )

    return {
        "performance_ratio": config.performance_ratio,
        "availability_target": config.availability_target,
        "degradation_rate": config.degradation_rate,
        "alert_threshold_percent": config.alert_threshold_percent,
        "configuration_source": config.configuration_source,
        "notes": config.notes,
        "id": config.id,
        "tenant_id": config.tenant_id,
        "solar_plant_id": getattr(config, "solar_plant_id", None),
        "is_active": config.is_active,
        "source": source,
    }

@router.post(
    "/{solar_plant_id}/performance-config",
    response_model=PlantPerformanceConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_performance_config(
    solar_plant_id: int,
    data: PlantPerformanceConfigCreate,
    db: Session = Depends(get_db),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
        )
    ),
    current_user=Depends(get_current_user),
):
    try:
        return create_plant_performance_config(
            db=db,
            tenant_id=tenant_access.tenant_id,
            solar_plant_id=solar_plant_id,
            data=data,
            created_by_user_id=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.patch(
    "/{solar_plant_id}/performance-config",
    response_model=PlantPerformanceConfigResponse,
)
def update_performance_config(
    solar_plant_id: int,
    data: PlantPerformanceConfigUpdate,
    db: Session = Depends(get_db),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
        )
    ),
):
    config = get_plant_performance_config(
        db=db,
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de performance não encontrada.",
        )

    return update_plant_performance_config(
        db=db,
        config=config,
        data=data,
    )