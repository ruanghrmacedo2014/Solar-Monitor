from app.api.database import SessionLocal
from app.services.providers.solarman_provider import SolarmanProvider


db = SessionLocal()

try:
    provider = SolarmanProvider(db)

    result = provider.get_station_history(
        tenant_id=5,
        station_id=100001,
        start_time="2026-01",
        end_time="2026-12",
        time_type=3,
    )

    print("RESPOSTA:")
    print(result)

finally:
    db.close()