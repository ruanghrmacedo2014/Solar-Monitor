from datetime import datetime, timezone

from sqlalchemy import select

from app.api.database import SessionLocal
from app.models.plant_performance_config import PlantPerformanceConfig
from app.models.solar_plant import SolarPlant
from app.models.solar_resource_snapshot import SolarResourceSnapshot


db = SessionLocal()

try:
    periodo = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    statement = (
        select(
            SolarPlant.id,
            SolarPlant.name,
        )
        .join(
            PlantPerformanceConfig,
            PlantPerformanceConfig.solar_plant_id
            == SolarPlant.id,
        )
        .join(
            SolarResourceSnapshot,
            SolarResourceSnapshot.solar_plant_id
            == SolarPlant.id,
        )
        .where(
            SolarPlant.tenant_id == 5,
            SolarPlant.is_active.is_(True),
            PlantPerformanceConfig.tenant_id == 5,
            PlantPerformanceConfig.is_active.is_(True),
            SolarResourceSnapshot.tenant_id == 5,
            SolarResourceSnapshot.provider == "PVGIS",
            SolarResourceSnapshot.resource_type == "MONTHLY",
            SolarResourceSnapshot.period_start == periodo,
        )
        .distinct()
        .limit(20)
    )

    plantas = db.execute(statement).all()

    print(
        f"Plantas com config + snapshot de setembro: "
        f"{len(plantas)}"
    )

    for planta_id, nome in plantas:
        print(
            f"PLANTA: {planta_id} | {nome}"
        )

finally:
    db.close()