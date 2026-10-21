from unittest.mock import Mock, patch

from app.services.integrations.solarman_client import SolarmanClient


client = SolarmanClient(
    app_id="TEST_APP_ID",
    app_secret="TEST_APP_SECRET",
)

fake_response = Mock()
fake_response.raise_for_status.return_value = None
fake_response.json.return_value = {
    "code": 0,
    "msg": "success",
    "success": True,
    "orgInfoList": [
        {
            "companyId": 123456,
            "companyName": "Empresa Teste Solar",
            "roleName": "Admin",
        }
    ],
}

with patch(
    "app.services.integrations.solarman_client.requests.post",
    return_value=fake_response,
) as mock_post:

    response = client.get_account_info(
        access_token="TEST_ACCESS_TOKEN",
    )

    print(
        "Resposta recebida:",
        response["msg"] == "success",
    )

    print(
        "Empresa recebida:",
        response["orgInfoList"][0]["companyName"]
        == "Empresa Teste Solar",
    )

    print(
        "POST foi chamado:",
        mock_post.called,
    )

    if mock_post.called:
        kwargs = mock_post.call_args.kwargs

        print(
            "URL correta:",
            mock_post.call_args.args[0]
            .endswith("/account/v1.0/info"),
        )

        print(
            "App ID correto:",
            kwargs["params"]["appId"] == "TEST_APP_ID",
        )

        print(
            "Bearer token correto:",
            kwargs["headers"]["Authorization"]
            == "Bearer TEST_ACCESS_TOKEN",
        )

        print(
            "JSON enviado:",
            kwargs["json"] == {},
        )