from datetime import date

from app.api.database import SessionLocal
from app.services.generation_service import GenerationService


db = SessionLocal()

try:
    service = GenerationService(db)

    result = service.sync_solarman_tenant_generation(
        tenant_id=5,
        start_time="2026-09-28",
        end_time="2026-09-28",
        limit=2,
    )

    print("Resultado do sync:")
    print(result)

finally:
    db.close()