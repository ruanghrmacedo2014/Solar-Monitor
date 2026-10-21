from unittest.mock import Mock, patch

from app.services.integrations.solarman_client import SolarmanClient


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)


fake_response = Mock()
fake_response.raise_for_status.return_value = None
fake_response.json.return_value = {
    "code": 401,
    "msg": "Invalid credentials",
}


with patch(
    "app.services.integrations.solarman_client.requests.post",
    return_value=fake_response,
):
    response = client.authenticate(
        email="teste@example.com",
        password_sha256="a" * 64,
    )

    print("Resposta recebida:", response)
    print("Código de erro preservado:", response["code"] == 401)
    print("Mensagem preservada:", response["msg"] == "Invalid credentials")