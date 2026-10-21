from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant


db = SessionLocal()

try:
    plants = (
        db.query(SolarPlant)
        .filter(
            SolarPlant.tenant_id == 5,
            SolarPlant.is_active.is_(True),
            SolarPlant.solarman_station_id.isnot(None),
        )
        .order_by(SolarPlant.id)
        .all()
    )

    print(f"TOTAL: {len(plants)}")

    for plant in plants:
        print(
            f"ID={plant.id} | "
            f"NOME={plant.name} | "
            f"STATION={plant.solarman_station_id}"
        )

finally:
    db.close()