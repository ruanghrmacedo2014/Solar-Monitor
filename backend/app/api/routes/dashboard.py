
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.api.database import get_db
from app.api.dependencies import (
    get_current_user,
    require_tenant_roles,
)
from app.core.permissions.roles import TenantRole
from app.schemas.dashboard import (
    DashboardGenerationHourlyResponse,
    DashboardGenerationPointResponse,
    DashboardOverviewResponse,
    DashboardPlantsResponse,
    DashboardDevicesResponse,
    DashboardSyncResponse,
    DashboardGenerationDailyResponse,
    DashboardGenerationMonthlyResponse,
    DashboardGenerationYearlyResponse,
)
from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
)
def get_dashboard_overview(
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
    service = DashboardService(db)

    return service.get_overview(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
    )

@router.get(
    "/generation",
    response_model=list[DashboardGenerationPointResponse],
)
def get_dashboard_generation(
    start_at: datetime,
    end_at: datetime,
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
    service = DashboardService(db)

    return service.get_generation(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
        start_at=start_at,
        end_at=end_at,
    )

@router.get(
    "/generation/hourly",
    response_model=list[DashboardGenerationHourlyResponse],
)
def get_dashboard_generation_hourly(
    start_at: datetime,
    end_at: datetime,
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
    service = DashboardService(db)

    return service.get_generation_summary_by_hour(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
        start_at=start_at,
        end_at=end_at,
    )

@router.get(
    "/generation/daily",
    response_model=list[DashboardGenerationDailyResponse],
)
def get_dashboard_generation_daily(
    start_at: datetime,
    end_at: datetime,
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
    service = DashboardService(db)

    return service.get_generation_daily(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
        start_at=start_at,
        end_at=end_at,
    )

@router.get(
    "/generation/monthly",
    response_model=list[DashboardGenerationMonthlyResponse],
)
def get_dashboard_generation_monthly(
    start_at: datetime,
    end_at: datetime,
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
    service = DashboardService(db)

    return service.get_generation_monthly(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
        start_at=start_at,
        end_at=end_at,
    )

@router.get(
    "/generation/yearly",
    response_model=list[DashboardGenerationYearlyResponse],
)
def get_dashboard_generation_yearly(
    start_at: datetime,
    end_at: datetime,
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
    service = DashboardService(db)

    return service.get_generation_yearly(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
        start_at=start_at,
        end_at=end_at,
    )

@router.get(
    "/plants",
    response_model=DashboardPlantsResponse,
)
def get_dashboard_plants(
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
    service = DashboardService(db)

    return service.get_plants(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
    )

@router.get(
    "/devices",
    response_model=DashboardDevicesResponse,
)
def get_dashboard_devices(
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
    service = DashboardService(db)

    return service.get_devices(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        user_role=tenant_access.role,
    )

@router.get(
    "/sync",
    response_model=DashboardSyncResponse,
)
def get_dashboard_sync(
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
    service = DashboardService(db)

    return service.get_sync(
        tenant_id=tenant_access.tenant_id,
    )