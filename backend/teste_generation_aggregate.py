from app.api.database import SessionLocal
from app.services.generation_service import GenerationService


db = SessionLocal()

try:
    service = GenerationService(db=db)

    saved = service.sync_solarman_aggregate_generation(
        tenant_id=5,
        solar_plant_id=8,
        start_time="2026-01",
        end_time="2026-12",
        time_type=3,
    )

    print("REGISTROS SALVOS:", saved)

finally:
    db.close()