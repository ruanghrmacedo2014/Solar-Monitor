from app.api.database import SessionLocal
from app.models.tenant_integration import SyncStatus
from app.services.tenant_integration_service import (
    save_solarman_sync_error,
)


db = SessionLocal()

try:
    integration = save_solarman_sync_error(
        db=db,
        tenant_id=5,
        integration_id=1,
        error_message="Invalid credentials",
    )

    print(
        "Status ERROR:",
        integration.last_sync_status == SyncStatus.ERROR,
    )

    print(
        "Mensagem correta:",
        integration.last_sync_error == "Invalid credentials",
    )

    print(
        "Data da sincronização preenchida:",
        integration.last_sync_at is not None,
    )

finally:
    db.close()