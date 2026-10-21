from dataclasses import dataclass
from datetime import date

from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant
from app.services.generation_service import GenerationService


@dataclass
class HistoricalAggregateSyncResult:
    solar_plant_id: int
    station_id: int
    granularity: str
    records_received: int
    records_saved: int
    error: str | None = None


def sync_plant_monthly_history(
    tenant_id: int,
    solar_plant_id: int,
    start_year: int,
    end_year: int,
) -> HistoricalAggregateSyncResult:
    db = SessionLocal()

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

        service = GenerationService(db=db)

        total_saved = 0
        total_received = 0

        for year in range(start_year, end_year + 1):
            try:
                result = service.sync_solarman_aggregate_generation(
                    tenant_id=tenant_id,
                    solar_plant_id=solar_plant_id,
                    start_time=f"{year}-01",
                    end_time=f"{year}-12",
                    time_type=3,
                )

                total_received += result
                total_saved += result

                print(
                    f"Histórico mensal | "
                    f"planta={solar_plant_id} | "
                    f"ano={year} | "
                    f"registros={result}"
                )

            except Exception as exc:
                db.rollback()

                print(
                    f"Erro histórico mensal | "
                    f"planta={solar_plant_id} | "
                    f"ano={year} | "
                    f"erro={exc}"
                )

        return HistoricalAggregateSyncResult(
            solar_plant_id=solar_plant_id,
            station_id=plant.solarman_station_id,
            granularity="MONTH",
            records_received=total_received,
            records_saved=total_saved,
        )

    except Exception as exc:
        db.rollback()

        return HistoricalAggregateSyncResult(
            solar_plant_id=solar_plant_id,
            station_id=(
                plant.solarman_station_id
                if "plant" in locals() and plant is not None
                else 0
            ),
            granularity="MONTH",
            records_received=0,
            records_saved=0,
            error=str(exc),
        )

    finally:
        db.close()

def sync_plant_yearly_history(
    tenant_id: int,
    solar_plant_id: int,
    start_year: int,
    end_year: int,
) -> HistoricalAggregateSyncResult:
    db = SessionLocal()

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

        service = GenerationService(db=db)

        try:
            result = service.sync_solarman_aggregate_generation(
                tenant_id=tenant_id,
                solar_plant_id=solar_plant_id,
                start_time=str(start_year),
                end_time=str(end_year),
                time_type=4,
            )

            print(
                f"Histórico anual | "
                f"planta={solar_plant_id} | "
                f"período={start_year}-{end_year} | "
                f"registros={result}"
            )

            return HistoricalAggregateSyncResult(
                solar_plant_id=solar_plant_id,
                station_id=plant.solarman_station_id,
                granularity="YEAR",
                records_received=result,
                records_saved=result,
            )

        except Exception as exc:
            db.rollback()

            print(
                f"Erro histórico anual | "
                f"planta={solar_plant_id} | "
                f"período={start_year}-{end_year} | "
                f"erro={exc}"
            )

            return HistoricalAggregateSyncResult(
                solar_plant_id=solar_plant_id,
                station_id=plant.solarman_station_id,
                granularity="YEAR",
                records_received=0,
                records_saved=0,
                error=str(exc),
            )

    except Exception as exc:
        db.rollback()

        return HistoricalAggregateSyncResult(
            solar_plant_id=solar_plant_id,
            station_id=(
                plant.solarman_station_id
                if "plant" in locals() and plant is not None
                else 0
            ),
            granularity="YEAR",
            records_received=0,
            records_saved=0,
            error=str(exc),
        )

    finally:
        db.close()