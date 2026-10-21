from datetime import datetime, timezone

from app.api.database import SessionLocal
from app.models.generation_record import GenerationRecord


db = SessionLocal()

try:
    inicio = datetime(
        2026,
        8,
        1,
        tzinfo=timezone.utc,
    )

    fim = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    registros = (
        db.query(GenerationRecord)
        .filter(
            GenerationRecord.tenant_id == 5,
            GenerationRecord.measured_at >= inicio,
            GenerationRecord.measured_at < fim,
        )
        .count()
    )

    print(
        f"Registros de geração em agosto/2026: {registros}"
    )

finally:
    db.close()