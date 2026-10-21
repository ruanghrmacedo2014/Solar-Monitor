from app.api.database import SessionLocal
from app.services.providers.solarman_provider import SolarmanProvider


db = SessionLocal()

try:
    provider = SolarmanProvider(db)

    result = provider.get_station_history(
        tenant_id=5,
        station_id=2795333,
        start_time="2026-09-28",
        end_time="2026-09-28",
        time_type=1,
    )

    items = result.get("stationDataItems") or []

    print(f"Total de registros: {len(items)}")

    if items:
        print("\nPRIMEIRO REGISTRO BRUTO:")
        print(items[0])

        print("\nCAMPOS DISPONÍVEIS:")
        print(list(items[0].keys()))

finally:
    db.close()