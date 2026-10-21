from unittest.mock import patch

import requests

from app.services.integrations.solarman_client import (
    SolarmanClient,
    SolarmanIntegrationError,
)


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)


with patch(
    "app.services.integrations.solarman_client.requests.post",
    side_effect=requests.ConnectionError("Teste de conexão"),
):

    try:
        client.authenticate(
            email="teste@example.com",
            password_sha256="a" * 64,
        )

        print("ERRO: a exceção era esperada.")

    except SolarmanIntegrationError as exc:
        print("Exceção correta:", type(exc).__name__)
        print("Mensagem correta:", str(exc))