from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.solar_plant import SolarPlant
from app.models.solar_resource_snapshot import SolarResourceSnapshot
from app.services.providers.pvgis_provider import (
    get_pvgis_monthly_output,
)


def create_pvgis_monthly_snapshots(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    created_by_user_id: int | None = None,
) -> list[SolarResourceSnapshot]:
    statement = select(SolarPlant).where(
        SolarPlant.id == solar_plant_id,
        SolarPlant.tenant_id == tenant_id,
        SolarPlant.is_active.is_(True),
    )

    plant = db.scalar(statement)

    if plant is None:
        raise ValueError(
            "Usina não encontrada ou inativa."
        )

    if plant.latitude is None or plant.longitude is None:
        raise ValueError(
            "A usina precisa possuir latitude e longitude."
        )

    if plant.installed_power is None:
        raise ValueError(
            "A usina precisa possuir potência instalada."
        )

    resultados = get_pvgis_monthly_output(
        latitude=Decimal(str(plant.latitude)),
        longitude=Decimal(str(plant.longitude)),
        peak_power_kw=Decimal(str(plant.installed_power)),
    )

    snapshots: list[SolarResourceSnapshot] = []

    current_year = datetime.now(timezone.utc).year

    for resultado in resultados:
        period_start = datetime(
            current_year,
            resultado.month,
            1,
            tzinfo=timezone.utc,
        )

        if resultado.month == 12:
            period_end = datetime(
                current_year + 1,
                1,
                1,
                tzinfo=timezone.utc,
            )
        else:
            period_end = datetime(
                current_year,
                resultado.month + 1,
                1,
                tzinfo=timezone.utc,
            )

        existing_statement = select(
            SolarResourceSnapshot
        ).where(
            SolarResourceSnapshot.solar_plant_id
            == solar_plant_id,
            SolarResourceSnapshot.provider == "PVGIS",
            SolarResourceSnapshot.resource_type
            == "MONTHLY",
            SolarResourceSnapshot.period_start
            == period_start,
        )

        existing_snapshot = db.scalar(
            existing_statement
        )

        if existing_snapshot is not None:
            if not existing_snapshot.is_manual_override:
                existing_snapshot.period_end = period_end
                existing_snapshot.latitude = plant.latitude
                existing_snapshot.longitude = plant.longitude
                existing_snapshot.solar_radiation_kwh_m2 = (
                    resultado.solar_radiation_kwh_m2
                )
                existing_snapshot.pv_output_kwh_kwp = (
                    resultado.pv_output_kwh_kwp
                )
                existing_snapshot.source_reference = (
                    "PVGIS v5.3"
                )
                existing_snapshot.retrieved_at = (
                    datetime.now(timezone.utc)
                )

            snapshots.append(existing_snapshot)
            continue

        snapshot = SolarResourceSnapshot(
            tenant_id=tenant_id,
            solar_plant_id=solar_plant_id,
            provider="PVGIS",
            resource_type="MONTHLY",
            period_start=period_start,
            period_end=period_end,
            latitude=plant.latitude,
            longitude=plant.longitude,
            solar_radiation_kwh_m2=(
                resultado.solar_radiation_kwh_m2
            ),
            pv_output_kwh_kwp=(
                resultado.pv_output_kwh_kwp
            ),
            source_reference="PVGIS v5.3",
            retrieved_at=datetime.now(timezone.utc),
            is_manual_override=False,
            created_by_user_id=created_by_user_id,
        )

        db.add(snapshot)
        snapshots.append(snapshot)

    db.commit()

    for snapshot in snapshots:
        db.refresh(snapshot)

    return snapshots