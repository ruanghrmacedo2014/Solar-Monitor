from app.services.historical_aggregate_sync_service import (
    sync_plant_yearly_history,
)


result = sync_plant_yearly_history(
    tenant_id=5,
    solar_plant_id=8,
    start_year=2020,
    end_year=2026,
)

print("RESULTADO:")
print(result)