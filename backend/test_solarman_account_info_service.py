from unittest.mock import patch

from app.api.database import SessionLocal
from app.services.tenant_integration_service import (
    get_solarman_account_info,
)


db = SessionLocal()

try:
    fake_response = {
        "code": 0,
        "msg": "success",
        "orgInfoList": [
            {
                "companyId": 123456,
                "companyName": "Empresa Teste Solar",
                "roleName": "Admin",
            }
        ],
    }

    with patch(
        "app.services.tenant_integration_service.get_valid_solarman_token",
        return_value="TEST_ACCESS_TOKEN",
    ) as mock_token, patch(
        "app.services.tenant_integration_service.SolarmanClient.get_account_info",
        return_value=fake_response,
    ) as mock_account_info:

        response = get_solarman_account_info(
            db=db,
            tenant_id=5,
            integration_id=1,
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
            "Token válido foi solicitado:",
            mock_token.called,
        )

        print(
            "Account info foi consultado:",
            mock_account_info.called,
        )

finally:
    db.close()