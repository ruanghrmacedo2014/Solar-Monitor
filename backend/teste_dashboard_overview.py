from app.api.database import SessionLocal
from app.services.dashboard_service import DashboardService

db = SessionLocal()

try:
    service = DashboardService(db)

    result = service.get_overview(
        tenant_id=5,
    )

    print("\n=== DASHBOARD OVERVIEW ===")
    print(result)

finally:
    db.close()