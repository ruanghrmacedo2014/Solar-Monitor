from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, require_tenant_roles
from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.models.user_tenant import TenantRole
from app.schemas.solar_plant import (
    SolarPlantCreate,
    SolarPlantResponse,
    SolarPlantCustomerLink,
    SolarDeviceResponse,
)
from app.services.solar_plant_service import (
    create_solar_plant,
    get_solar_plants_by_tenant,
    get_solar_plant_by_id,
    link_solar_plant_to_customer,
    get_solar_plants_by_customer,
)
from app.services.customer_service import get_customer_by_user
from app.services.solar_device_service import get_solar_devices_by_plant


router = APIRouter(
    prefix="/solar-plants",
    tags=["Solar Plants"],
)

@router.get(
    "/",
    response_model=list[SolarPlantResponse],
)
def list_plants(
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
    if tenant_access.role == TenantRole.CUSTOMER:
        customer = get_customer_by_user(
            db=db,
            tenant_id=tenant_access.tenant_id,
            user_id=current_user.id,
        )

        if customer is None:
            return []

        return get_solar_plants_by_customer(
            db=db,
            tenant_id=tenant_access.tenant_id,
            customer_id=customer.id,
        )

    return get_solar_plants_by_tenant(
        db=db,
        tenant_id=tenant_access.tenant_id,
    )

@router.post(
    "/{solar_plant_id}/customer",
    response_model=SolarPlantResponse,
)
def link_plant_to_customer(
    solar_plant_id: int,
    data: SolarPlantCustomerLink,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
        )
    ),
    db: Session = Depends(get_db),
):
    try:
        return link_solar_plant_to_customer(
            db=db,
            tenant_id=tenant_access.tenant_id,
            solar_plant_id=solar_plant_id,
            customer_id=data.customer_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

@router.get(
    "/{solar_plant_id}/devices",
    response_model=list[SolarDeviceResponse],
)
def list_plant_devices(
    solar_plant_id: int,
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

    return get_solar_devices_by_plant(
        db=db,
        tenant_id=tenant_access.tenant_id,
        solar_plant_id=solar_plant_id,
    )

@router.get(
    "/{solar_plant_id}",
    response_model=SolarPlantResponse,
)
def get_plant(
    solar_plant_id: int,
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

    return solar_plant

@router.post(
    "/",
    response_model=SolarPlantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plant(
    data: SolarPlantCreate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
        )
    ),
    db: Session = Depends(get_db),
):
    try:
        return create_solar_plant(
            db=db,
            tenant_id=tenant_access.tenant_id,
            solarman_station_id=data.solarman_station_id,
            name=data.name,
            installed_power=data.installed_power,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            timezone=data.timezone,
            plant_type=data.plant_type,
            grid_interconnection_type=data.grid_interconnection_type,
            start_operating_at=data.start_operating_at,
            owner_name=data.owner_name,
            contact_phone=data.contact_phone,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma planta solar com este Station ID nesta empresa.",
        )