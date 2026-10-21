from unittest.mock import patch

from app.api.database import SessionLocal
from app.models.tenant_integration import SyncStatus
from app.services.tenant_integration_service import (
    get_solarman_account_info,
)


db = SessionLocal()

try:
    with patch(
        "app.services.tenant_integration_service.get_valid_solarman_token",
        return_value="INVALID_TEST_TOKEN",
    ), patch(
        "app.services.tenant_integration_service.SolarmanClient.get_account_info",
        side_effect=Exception(
            "Erro da API da Solarman (2101019): auth invalid token"
        ),
    ):

        try:
            get_solarman_account_info(
                db=db,
                tenant_id=5,
                integration_id=1,
            )

            print("ERRO: a exceção era esperada.")

        except Exception as exc:
            print(
                "Exceção preservada:",
                "2101019" in str(exc),
            )

            integration = db.get(
                __import__(
                    "app.models.tenant_integration",
                    fromlist=["TenantIntegration"],
                ).TenantIntegration,
                1,
            )

            print(
                "Status ERROR salvo:",
                integration.last_sync_status
                == SyncStatus.ERROR,
            )

            print(
                "Mensagem salva:",
                integration.last_sync_error
                == str(exc),
            )

            print(
                "Data da sincronização salva:",
                integration.last_sync_at is not None,
            )

finally:
    db.close()