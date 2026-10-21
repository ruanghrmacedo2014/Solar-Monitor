from app.api.database import SessionLocal
from app.services.dashboard_service import DashboardService


db = SessionLocal()

try:
    service = DashboardService(db)

    result = service.get_plants(tenant_id=5)

    print("=== RESUMO ===")
    print(f"Total: {result['total']}")
    print(f"Gerando: {result['generating']}")
    print(f"Online: {result['online']}")
    print(f"Offline: {result['offline']}")

    print()
    print("=== POR PROVIDER ===")

    for provider in result["by_provider"]:
        print(
            f"{provider['provider']} | "
            f"total: {provider['total']} | "
            f"gerando: {provider['generating']} | "
            f"online: {provider['online']} | "
            f"offline: {provider['offline']}"
        )

    print()
    print("=== PRIMEIRAS 10 PLANTAS ===")

    for plant in result["plants"][:10]:
        print(
            f"ID: {plant['id']} | "
            f"Nome: {plant['name']} | "
            f"Provider: {plant['source_provider']} | "
            f"Status: {plant['status']} | "
            f"Potência: {plant['current_power_w']} W | "
            f"Última leitura: {plant['last_measured_at']}"
        )

finally:
    db.close()