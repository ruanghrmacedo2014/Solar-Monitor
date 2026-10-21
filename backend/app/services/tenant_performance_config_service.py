from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant_performance_config import (
    TenantPerformanceConfig,
)


def get_tenant_performance_config(
    db: Session,
    tenant_id: int,
) -> TenantPerformanceConfig | None:

    statement = (
        select(TenantPerformanceConfig)
        .where(
            TenantPerformanceConfig.tenant_id == tenant_id,
            TenantPerformanceConfig.is_active.is_(True),
        )
    )

    return db.scalar(statement)


def create_tenant_performance_config(
    db: Session,
    tenant_id: int,
    data,
    created_by_user_id: int | None = None,
) -> TenantPerformanceConfig:

    existing = get_tenant_performance_config(
        db=db,
        tenant_id=tenant_id,
    )

    if existing is not None:
        raise ValueError(
            "Esta empresa já possui uma configuração de performance."
        )

    config = TenantPerformanceConfig(
        tenant_id=tenant_id,
        performance_ratio=data.performance_ratio,
        availability_target=data.availability_target,
        degradation_rate=data.degradation_rate,
        alert_threshold_percent=data.alert_threshold_percent,
        configuration_source=data.configuration_source,
        notes=data.notes,
        created_by_user_id=created_by_user_id,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return config


def update_tenant_performance_config(
    db: Session,
    config: TenantPerformanceConfig,
    data,
) -> TenantPerformanceConfig:

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return config


def deactivate_tenant_performance_config(
    db: Session,
    config: TenantPerformanceConfig,
) -> TenantPerformanceConfig:

    config.is_active = False

    db.commit()
    db.refresh(config)

    return config