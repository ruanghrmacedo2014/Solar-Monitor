from dataclasses import dataclass
from datetime import date, timedelta

from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant
from app.services.generation_service import GenerationService


@dataclass
class HistoricalPlantSyncResult:
    solar_plant_id: int
    station_id: int
    days_processed: int
    records_received: int
    records_saved: int
    failures: list[dict]


def sync_plant_history(
    tenant_id: int,
    solar_plant_id: int,
    start_date: date,
    end_date: date,
) -> HistoricalPlantSyncResult:
    db = SessionLocal()

    records_received = 0
    records_saved = 0
    days_processed = 0
    failures: list[dict] = []

    try:
        plant = (
            db.query(SolarPlant)
            .filter(
                SolarPlant.id == solar_plant_id,
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
            .first()
        )

        if plant is None:
            raise ValueError(
                "Planta solar não encontrada ou inativa."
            )

        if not plant.solarman_station_id:
            raise ValueError(
                "Planta não possui solarman_station_id."
            )

        current_date = start_date

        while current_date <= end_date:
            block_end = min(
                current_date + timedelta(days=30),
                end_date,
            )

            try:
                service = GenerationService(db=db)

                result = service.sync_solarman_plant_generation(
                    tenant_id=tenant_id,
                    solar_plant_id=solar_plant_id,
                    start_time=current_date.isoformat(),
                    end_time=block_end.isoformat(),
                    time_type=2,
                )

                records_received += result.records_received
                records_saved += result.records_saved

                days_processed += (
                    block_end - current_date
                ).days + 1

                print(
                    f"Histórico | planta={solar_plant_id} | "
                    f"período={current_date} até {block_end} | "
                    f"recebidos={result.records_received} | "
                    f"salvos={result.records_saved}"
                )

            except Exception as exc:
                db.rollback()

                failures.append(
                    {
                        "start_date": current_date.isoformat(),
                        "end_date": block_end.isoformat(),
                        "error": str(exc),
                    }
                )

                print(
                    f"Erro histórico | planta={solar_plant_id} | "
                    f"período={current_date} até {block_end} | "
                    f"erro={exc}"
                )

            current_date = block_end + timedelta(days=1)

        return HistoricalPlantSyncResult(
            solar_plant_id=solar_plant_id,
            station_id=plant.solarman_station_id,
            days_processed=days_processed,
            records_received=records_received,
            records_saved=records_saved,
            failures=failures,
        )

    finally:
        db.close()