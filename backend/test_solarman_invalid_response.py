from unittest.mock import Mock, patch

from app.services.integrations.solarman_client import SolarmanClient


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)


fake_response = Mock()
fake_response.raise_for_status.return_value = None
fake_response.json.side_effect = ValueError("JSON inválido")


with patch(
    "app.services.integrations.solarman_client.requests.post",
    return_value=fake_response,
):

    try:
        client.authenticate(
            email="teste@example.com",
            password_sha256="a" * 64,
        )

        print("ERRO: a exceção era esperada.")

    except RuntimeError as exc:
        print("Erro controlado:", str(exc))