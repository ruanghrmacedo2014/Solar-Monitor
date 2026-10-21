from app.api.database import SessionLocal
from app.services.tenant_integration_service import (
    get_solarman_access_token,
)


db = SessionLocal()

try:
    token = get_solarman_access_token(
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

finally:
    db.close()