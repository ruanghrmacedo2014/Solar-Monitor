from unittest.mock import patch

from app.api.database import SessionLocal
from app.services.tenant_integration_service import (
    authenticate_solarman_integration,
)


db = SessionLocal()

try:
    fake_response = {
        "code": 0,
        "msg": "success",
        "access_token": "TEST_ACCESS_TOKEN",
        "token_type": "Bearer",
        "expires_in": 5184000,
    }

    with patch(
        "app.services.tenant_integration_service.SolarmanClient.authenticate",
        return_value=fake_response,
    ) as mock_authenticate:

        response = authenticate_solarman_integration(
            db=db,
            tenant_id=5,
            integration_id=1,
        )

        print("Resposta recebida:", response)
        print(
            "Authenticate chamado:",
            mock_authenticate.called,
        )

        if mock_authenticate.called:
            kwargs = mock_authenticate.call_args.kwargs

            print(
                "Email correto:",
                kwargs["email"] == "teste@example.com",
            )

            print(
                "Password SHA-256 presente:",
                len(kwargs["password_sha256"]) == 64,
            )

finally:
    db.close()