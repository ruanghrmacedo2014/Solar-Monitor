from datetime import datetime, timedelta, timezone

from app.api.database import SessionLocal
from app.services.tenant_integration_service import (
    get_tenant_integration_by_id,
    solarman_token_is_valid,
)


db = SessionLocal()

try:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=5,
        integration_id=1,
    )

    print(
        "Token atualmente válido:",
        solarman_token_is_valid(integration),
    )

    integration.token_expires_at = (
        datetime.now(timezone.utc)
        - timedelta(minutes=1)
    )

    print(
        "Token expirado detectado:",
        not solarman_token_is_valid(integration),
    )

finally:
    db.close()