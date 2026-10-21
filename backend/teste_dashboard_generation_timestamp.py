from datetime import datetime, timezone

from app.api.database import SessionLocal
from app.services.dashboard_service import DashboardService


db = SessionLocal()

try:
    service = DashboardService(db)

    result = service.get_generation_system_by_timestamp(
        tenant_id=5,
        start_at=datetime(
            2026, 9, 28, 0, 0, 0,
            tzinfo=timezone.utc,
        ),
        end_at=datetime(
            2026, 9, 28, 23, 59, 59,
            tzinfo=timezone.utc,
        ),
    )

    print(f"Total de timestamps: {len(result)}")

    print("\nPrimeiros 10:")
    for item in result[:10]:
        print(item)

    print("\nÚltimos 10:")
    for item in result[-10:]:
        print(item)

    if result:
        peak = max(
            result,
            key=lambda item: (
                item["total_power_w"]
                if item["total_power_w"] is not None
                else 0
            ),
        )

        print("\nMaior potência agregada:")
        print(peak)

finally:
    db.close()