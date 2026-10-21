from app.api.database import SessionLocal
from app.services.tenant_integration_service import get_solarman_credentials


db = SessionLocal()

try:
    credentials = get_solarman_credentials(
        db=db,
        tenant_id=5,
        integration_id=1,
    )

    print("Credenciais recuperadas com sucesso.")
    print("App ID:", credentials["app_id"])
    print("Email:", credentials["email"])
    print("Possui app_secret:", bool(credentials["app_secret"]))
    print("Possui password_sha256:", bool(credentials["password_sha256"]))

finally:
    db.close()