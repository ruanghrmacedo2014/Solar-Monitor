from app.api.database import SessionLocal
from app.services.tenant_integration_service import get_solarman_client


db = SessionLocal()

try:
    client = get_solarman_client(
        db=db,
        tenant_id=5,
        integration_id=1,
    )

    if client is None:
        print("Client não foi criado.")
    else:
        print("SolarmanClient criado com sucesso.")
        print("Base URL:", client.base_url)
        print("App ID presente:", bool(client.app_id))
        print("App Secret presente:", bool(client.app_secret))

finally:
    db.close()