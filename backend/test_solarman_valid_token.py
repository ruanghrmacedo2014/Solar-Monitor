from unittest.mock import patch

from app.api.database import SessionLocal
from app.services.tenant_integration_service import (
    get_valid_solarman_token,
)


db = SessionLocal()

try:
    with patch(
        "app.services.tenant_integration_service.SolarmanClient.authenticate"
    ) as mock_authenticate:

        token = get_valid_solarman_token(
            db=db,
            tenant_id=5,
            integration_id=1,
        )

        print(
            "Token encontrado:",
            token is not None,
        )

        print(
            "Token correto:",
            token == "TEST_ACCESS_TOKEN_123456",
        )

        print(
            "Authenticate NÃO foi chamado:",
            not mock_authenticate.called,
        )

finally:
    db.close()