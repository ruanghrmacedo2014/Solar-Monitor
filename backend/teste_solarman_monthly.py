from app.api.database import SessionLocal
from app.services.providers.solarman_provider import SolarmanProvider


db = SessionLocal()

try:
    provider = SolarmanProvider(db)

    result = provider.get_station_history(
        tenant_id=5,
        station_id=2795333,
        start_time="2020",
        end_time="2026",
        time_type=4,
    )

    items = result.get("stationDataItems") or []

    print("SUCCESS:", result.get("success"))
    print("TOTAL:", result.get("total"))
    print("REGISTROS:", len(items))

    for item in items:
        print(
            item.get("year"),
            "generationValue=",
            item.get("generationValue"),
            "generationPower=",
            item.get("generationPower"),
            "irradiate=",
            item.get("irradiate"),
            "PR=",
            item.get("pr"),
        )

finally:
    db.close()