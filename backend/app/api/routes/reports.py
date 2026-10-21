from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import (
    get_current_user,
    require_tenant_roles,
)
from app.models.user_tenant import TenantRole
from app.models.customer import Customer
from app.services.report_service import (
    customer_can_access_plant_report,
    generate_customer_report,
    get_plant_report_chart_data,
    generate_plant_report,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.post("/plants/{solar_plant_id}")
def create_plant_report(
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
):
    if tenant_access.role == TenantRole.CUSTOMER:
        customer = (
            db.query(Customer)
            .filter(
                Customer.user_id == current_user.id,
                Customer.tenant_id == tenant_access.tenant_id,
                Customer.is_active.is_(True),
            )
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cliente não encontrado.",
            )

        if not customer_can_access_plant_report(
            db=db,
            customer_id=customer.id,
            solar_plant_id=solar_plant_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui acesso a esta usina.",
            )
    try:
        result = generate_plant_report(
            db=db,
            tenant_id=tenant_access.tenant_id,
            solar_plant_id=solar_plant_id,
            period_start=period_start,
            period_end=period_end,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {
        "id": result.report.id,
        "tenant_id": result.report.tenant_id,
        "solar_plant_id": result.report.solar_plant_id,
        "report_type": result.report.report_type,
        "period_start": result.report.period_start,
        "period_end": result.report.period_end,
        "actual_kwh": result.report.actual_kwh,
        "expected_kwh": result.report.expected_kwh,
        "performance_percent": (
            result.report.performance_percent
        ),
        "coverage_percent": result.report.coverage_percent,
        "data_quality": result.report.data_quality,
        "classification": result.report.classification,
        "status": result.report.status,
        "generated_at": result.report.generated_at,
    }

@router.post("/customers/{customer_id}")
def create_customer_report(
    customer_id: int,
    period_start: datetime,
    period_end: datetime,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
):
    if tenant_access.role == TenantRole.CUSTOMER:
        customer = (
            db.query(Customer)
            .filter(
                Customer.user_id == current_user.id,
                Customer.tenant_id == tenant_access.tenant_id,
                Customer.is_active.is_(True),
            )
            .first()
        )

        if customer is None or customer.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui acesso a este cliente.",
            )

    try:
        result = generate_customer_report(
            db=db,
            tenant_id=tenant_access.tenant_id,
            customer_id=customer_id,
            period_start=period_start,
            period_end=period_end,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {
        "id": result.report.id,
        "tenant_id": result.report.tenant_id,
        "customer_id": result.report.customer_id,
        "solar_plant_id": result.report.solar_plant_id,
        "report_type": result.report.report_type,
        "period_start": result.report.period_start,
        "period_end": result.report.period_end,
        "actual_kwh": result.report.actual_kwh,
        "expected_kwh": result.report.expected_kwh,
        "performance_percent": result.report.performance_percent,
        "coverage_percent": result.report.coverage_percent,
        "data_quality": result.report.data_quality,
        "classification": result.report.classification,
        "status": result.report.status,
        "generated_at": result.report.generated_at,
    }

@router.get("/plants/{solar_plant_id}/chart")
def get_plant_report_chart(
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
    granularity: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
):
    if tenant_access.role == TenantRole.CUSTOMER:
        customer = (
            db.query(Customer)
            .filter(
                Customer.user_id == current_user.id,
                Customer.tenant_id == tenant_access.tenant_id,
                Customer.is_active.is_(True),
            )
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cliente não encontrado.",
            )

        if not customer_can_access_plant_report(
            db=db,
            customer_id=customer.id,
            solar_plant_id=solar_plant_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui acesso a esta usina.",
            )

    try:
        chart_data = get_plant_report_chart_data(
            db=db,
            tenant_id=tenant_access.tenant_id,
            solar_plant_id=solar_plant_id,
            period_start=period_start,
            period_end=period_end,
            granularity=granularity,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {
        "solar_plant_id": solar_plant_id,
        "period_start": period_start,
        "period_end": period_end,
        "granularity": granularity,
        "data": chart_data,
    }