from sqlalchemy import func

from app.api.database import SessionLocal
from app.models.generation_record import GenerationRecord


db = SessionLocal()

try:
    total = (
        db.query(func.count(GenerationRecord.id))
        .filter(
            GenerationRecord.tenant_id == 5,
        )
        .scalar()
    )

    ultimo = (
        db.query(
            func.max(
                GenerationRecord.measured_at
            )
        )
        .filter(
            GenerationRecord.tenant_id == 5,
        )
        .scalar()
    )

    print(
        f"Total de GenerationRecord do tenant 5: {total}"
    )

    print(
        f"Último GenerationRecord: {ultimo}"
    )

finally:
    db.close()