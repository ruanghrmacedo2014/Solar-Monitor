from app.api.database import SessionLocal
from app.services.providers.solarman_provider import SolarmanProvider


db = SessionLocal()

try:
    provider = SolarmanProvider(db)

    result = provider.get_station_history(
        tenant_id=5,
        station_id=2795333,
        start_time="2026-09-28",
        end_time="2026-09-28",
        time_type=1,
    )

    items = result.get("stationDataItems") or []

    if not items:
        print("Nenhum registro encontrado.")
    else:
        print(f"Total de registros: {len(items)}")
        print("\nCAMPOS COM ALGUM VALOR PREENCHIDO:")

        fields = items[0].keys()

        for field in fields:
            values = [
                item.get(field)
                for item in items
                if item.get(field) is not None
            ]

            if values:
                print(
                    f"{field}: "
                    f"{len(values)} preenchidos | "
                    f"exemplo={values[0]}"
                )

finally:
    db.close()