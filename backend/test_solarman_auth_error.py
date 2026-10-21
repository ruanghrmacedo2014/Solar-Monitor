from unittest.mock import patch

from app.api.database import SessionLocal
from app.models.tenant_integration import SyncStatus
from app.services.tenant_integration_service import (
    get_tenant_integration_by_id,
    get_valid_solarman_token,
)


db = SessionLocal()

try:
    fake_response = {
        "code": 401,
        "msg": "Invalid credentials",
    }

    with patch(
        "app.services.tenant_integration_service.solarman_token_is_valid",
        return_value=False,
    ), patch(
        "app.services.tenant_integration_service.SolarmanClient.authenticate",
        return_value=fake_response,
    ):

        try:
            get_valid_solarman_token(
                db=db,
                tenant_id=5,
                integration_id=1,
            )

            print("ERRO: a exceção era esperada.")

        except ValueError as exc:
            print(
                "Erro detectado:",
                str(exc),
            )

    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=5,
        integration_id=1,
    )

    print(
        "Status ERROR salvo:",
        integration.last_sync_status == SyncStatus.ERROR,
    )

    print(
        "Mensagem salva:",
        integration.last_sync_error == "Invalid credentials",
    )

    print(
        "Data salva:",
        integration.last_sync_at is not None,
    )

finally:
    db.close()