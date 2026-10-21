from unittest.mock import Mock, patch

from app.services.integrations.solarman_client import (
    SolarmanClient,
    SolarmanIntegrationError,
)


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)

fake_response = Mock()
fake_response.raise_for_status.return_value = None
fake_response.json.return_value = {
    "code": "2101019",
    "msg": "auth invalid token",
    "success": False,
    "requestId": "TEST_REQUEST_ID",
}

with patch(
    "app.services.integrations.solarman_client.requests.post",
    return_value=fake_response,
):

    try:
        client.get_account_info(
            access_token="INVALID_TEST_TOKEN",
        )

        print("ERRO: a exceção era esperada.")

    except SolarmanIntegrationError as exc:
        print(
            "Exceção correta:",
            type(exc).__name__ == "SolarmanIntegrationError",
        )

        print(
            "Código preservado:",
            "2101019" in str(exc),
        )

        print(
            "Mensagem preservada:",
            "auth invalid token" in str(exc),
        )