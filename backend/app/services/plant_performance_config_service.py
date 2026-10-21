from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.plant_performance_config import PlantPerformanceConfig
from app.models.solar_plant import SolarPlant
from app.models.customer import Customer

from app.models.tenant_performance_config import (
    TenantPerformanceConfig,
)


def get_plant_performance_config(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    user_id: int | None = None,
    role: str | None = None,
) -> PlantPerformanceConfig | None:
    statement = (
        select(PlantPerformanceConfig)
        .join(
            SolarPlant,
            SolarPlant.id
            == PlantPerformanceConfig.solar_plant_id,
        )
        .where(
            PlantPerformanceConfig.tenant_id == tenant_id,
            PlantPerformanceConfig.solar_plant_id == solar_plant_id,
            PlantPerformanceConfig.is_active.is_(True),
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.is_active.is_(True),
        )
    )

    if role == "CUSTOMER":
        statement = statement.where(
            SolarPlant.customer_id.in_(
                select(Customer.id).where(
                    Customer.tenant_id == tenant_id,
                    Customer.user_id == user_id,
                    Customer.is_active.is_(True),
                )
            )
        )

    return db.scalar(statement)


def create_plant_performance_config(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    data,
    created_by_user_id: int | None = None,
) -> PlantPerformanceConfig:

    plant_statement = select(SolarPlant).where(
        SolarPlant.id == solar_plant_id,
        SolarPlant.tenant_id == tenant_id,
        SolarPlant.is_active.is_(True),
    )

    plant = db.scalar(plant_statement)

    if plant is None:
        raise ValueError(
            "Usina não encontrada ou não pertence a esta empresa."
        )

    existing = get_plant_performance_config(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
    )

    if existing is not None:
        raise ValueError(
            "Esta usina já possui uma configuração de performance."
        )

    config = PlantPerformanceConfig(
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
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


def update_plant_performance_config(
    db: Session,
    config: PlantPerformanceConfig,
    data,
) -> PlantPerformanceConfig:

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return config


def deactivate_plant_performance_config(
    db: Session,
    config: PlantPerformanceConfig,
) -> PlantPerformanceConfig:

    config.is_active = False

    db.commit()
    db.refresh(config)

    return config

def get_effective_performance_config(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    user_id: int | None = None,
    role: str | None = None,
) -> tuple[
    PlantPerformanceConfig | TenantPerformanceConfig | None,
    str | None,
]:
    plant_config = get_plant_performance_config(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        user_id=user_id,
        role=role,
    )

    if plant_config is not None:
        return plant_config, "PLANT"

    plant_statement = select(SolarPlant).where(
        SolarPlant.id == solar_plant_id,
        SolarPlant.tenant_id == tenant_id,
        SolarPlant.is_active.is_(True),
    )

    plant = db.scalar(plant_statement)

    if plant is None:
        return None, None

    if role == "CUSTOMER":
        customer_statement = select(Customer).where(
            Customer.id == plant.customer_id,
            Customer.tenant_id == tenant_id,
            Customer.user_id == user_id,
            Customer.is_active.is_(True),
        )

        customer = db.scalar(customer_statement)

        if customer is None:
            return None, None

    tenant_statement = (
        select(TenantPerformanceConfig)
        .where(
            TenantPerformanceConfig.tenant_id == tenant_id,
            TenantPerformanceConfig.is_active.is_(True),
        )
    )

    tenant_config = db.scalar(tenant_statement)

    if tenant_config is not None:
        return tenant_config, "TENANT"

    return None, None