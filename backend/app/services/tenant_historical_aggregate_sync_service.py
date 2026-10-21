from dataclasses import dataclass

from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant
from app.services.historical_aggregate_sync_service import (
    sync_plant_monthly_history,
    sync_plant_yearly_history,
)


@dataclass
class TenantHistoricalAggregateSyncResult:
    tenant_id: int
    plants_processed: int
    plants_successful: int
    plants_failed: int
    monthly_records_saved: int
    yearly_records_saved: int
    failures: list[dict]


def sync_tenant_historical_aggregates(
    tenant_id: int,
    start_year: int,
    end_year: int,
    max_plants: int | None = None,
) -> TenantHistoricalAggregateSyncResult:
    db = SessionLocal()

    plants_processed = 0
    plants_successful = 0
    plants_failed = 0
    monthly_records_saved = 0
    yearly_records_saved = 0
    failures: list[dict] = []

    try:
        query = (
            db.query(SolarPlant)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
                SolarPlant.solarman_station_id.isnot(None),
                SolarPlant.solarman_station_id.notin_(
                    [100001, 100002, 999002]
                ),
            )
            .order_by(SolarPlant.id)
        )

        if max_plants is not None:
            query = query.limit(max_plants)

        plants = query.all()

        print(
            f"Encontradas {len(plants)} plantas ativas "
            f"com estação SolarMan."
        )

        for plant in plants:
            plants_processed += 1

            print(
                f"Progresso: {plants_processed}/{len(plants)}"
            )

            print(
                f"\nProcessando planta "
                f"{plant.id} - {plant.name}"
            )

            monthly_result = None
            yearly_result = None
            plant_errors = []

            try:
                monthly_result = sync_plant_monthly_history(
                    tenant_id=tenant_id,
                    solar_plant_id=plant.id,
                    start_year=start_year,
                    end_year=end_year,
                )

                if monthly_result.error:
                    plant_errors.append(
                        f"Mensal: {monthly_result.error}"
                    )
                else:
                    monthly_records_saved += (
                        monthly_result.records_saved
                    )

            except Exception as exc:
                db.rollback()

                plant_errors.append(
                    f"Mensal: {exc}"
                )

            try:
                yearly_result = sync_plant_yearly_history(
                    tenant_id=tenant_id,
                    solar_plant_id=plant.id,
                    start_year=start_year,
                    end_year=end_year,
                )

                if yearly_result.error:
                    plant_errors.append(
                        f"Anual: {yearly_result.error}"
                    )
                else:
                    yearly_records_saved += (
                        yearly_result.records_saved
                    )

            except Exception as exc:
                db.rollback()

                plant_errors.append(
                    f"Anual: {exc}"
                )

            if plant_errors:
                plants_failed += 1

                failure = {
                    "solar_plant_id": plant.id,
                    "plant_name": plant.name,
                    "errors": plant_errors,
                }

                failures.append(failure)

                print(
                    f"ERRO planta {plant.id}: "
                    f"{' | '.join(plant_errors)}"
                )

            else:
                plants_successful += 1

                print(
                    f"Planta {plant.id} concluída | "
                    f"mensal={monthly_result.records_saved} | "
                    f"anual={yearly_result.records_saved}"
                )

        return TenantHistoricalAggregateSyncResult(
            tenant_id=tenant_id,
            plants_processed=plants_processed,
            plants_successful=plants_successful,
            plants_failed=plants_failed,
            monthly_records_saved=monthly_records_saved,
            yearly_records_saved=yearly_records_saved,
            failures=failures,
        )

    finally:
        db.close()