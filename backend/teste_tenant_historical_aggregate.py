from app.services.tenant_historical_aggregate_sync_service import (
    sync_tenant_historical_aggregates,
)


result = sync_tenant_historical_aggregates(
    tenant_id=5,
    start_year=2025,
    end_year=2025,
    max_plants=None,
)

print("\nRESULTADO FINAL:")
print(result)