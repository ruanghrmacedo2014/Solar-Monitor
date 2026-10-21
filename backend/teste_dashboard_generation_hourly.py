from datetime import datetime, timezone

from app.api.database import SessionLocal
from app.services.dashboard_service import DashboardService


db = SessionLocal()

try:
    service = DashboardService(db)

    start_at = datetime(
        2026, 9, 28, 0, 0, 0,
        tzinfo=timezone.utc,
    )

    end_at = datetime(
        2026, 9, 28, 23, 59, 59,
        tzinfo=timezone.utc,
    )

    result = service.get_generation_summary_by_hour(
        tenant_id=5,
        start_at=start_at,
        end_at=end_at,
    )

    print(f"Total de horas: {len(result)}")
    print()

    for row in result:
        print(
            f"{row['measured_at']} | "
            f"média: {row['average_power_w']:.2f} W | "
            f"pico: {row['peak_power_w']:.2f} W | "
            f"mínimo: {row['minimum_power_w']:.2f} W"
        )

finally:
    db.close()