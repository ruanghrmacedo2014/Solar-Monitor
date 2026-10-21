from datetime import datetime, timezone

from app.api.database import SessionLocal
from app.models.tenant_integration import TenantIntegration


db = SessionLocal()

try:
    integration = db.get(TenantIntegration, 1)

    if integration is None:
        print("Integração não encontrada.")
    else:
        integration.access_token_encrypted = None
        integration.token_expires_at = None

        db.commit()

        print("Token de teste removido: True")
        print("Expiração removida: True")

finally:
    db.close()