from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.api.database import SessionLocal
from app.services.tenant_integration_service import (
    get_tenant_integration_by_id,
    get_solarman_access_token,
    get_valid_solarman_token,
)


db = SessionLocal()

try:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=5,
        integration_id=1,
    )

    # Expira somente em memória.
    # Não fazemos commit dessa alteração.
    integration.token_expires_at = (
        datetime.now(timezone.utc)
        - timedelta(minutes=1)
    )

    fake_response = {
        "code": 0,
        "msg": "success",
        "access_token": "NEW_TEST_ACCESS_TOKEN",
        "token_type": "Bearer",
        "expires_in": 5184000,
    }

    with patch(
        "app.services.tenant_integration_service.SolarmanClient.authenticate",
        return_value=fake_response,
    ) as mock_authenticate:

        token = get_valid_solarman_token(
            db=db,
            tenant_id=5,
            integration_id=1,
        )

        print(
            "Novo token recebido:",
            token == "NEW_TEST_ACCESS_TOKEN",
        )

        print(
            "Authenticate foi chamado:",
            mock_authenticate.called,
        )

        saved_token = get_solarman_access_token(
            db=db,
            tenant_id=5,
            integration_id=1,
        )

        print(
            "Novo token foi salvo:",
            saved_token == "NEW_TEST_ACCESS_TOKEN",
        )

finally:
    db.close()