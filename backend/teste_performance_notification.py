from datetime import datetime, timezone

from app.api.database import SessionLocal
from app.services.performance_notification_service import (
    PerformanceNotificationService,
)


db = SessionLocal()

try:
    service = PerformanceNotificationService(db=db)

    service.check_plant_performance(
        tenant_id=5,
        solar_plant_id=263,
        period_start=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
        period_end=datetime(
            2026,
            10,
            1,
            tzinfo=timezone.utc,
        ),
    )

    print("VERIFICAÇÃO CONCLUÍDA")

finally:
    db.close()