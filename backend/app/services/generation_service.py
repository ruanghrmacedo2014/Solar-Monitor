from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.providers.provider_factory import get_generation_provider
from app.models.generation_record import GenerationRecord
from app.services.providers.generation_provider import GenerationProvider
from app.models.generation_sync_log import GenerationSyncLog
from datetime import datetime, timezone
from dataclasses import dataclass
import time

@dataclass
class GenerationSyncResult:
    solar_plant_id: int
    station_id: int
    records_received: int
    records_saved: int

@dataclass
class GenerationBatchSyncResult:
    total_plants: int
    successful_plants: int
    failed_plants: int
    total_records_received: int
    total_records_saved: int
    failures: list[dict]

class GenerationService:
    def __init__(
        self,
        db: Session,
        provider: GenerationProvider | None = None,
    ):
        self.db = db
        self.provider = provider or get_generation_provider(db)

    def get_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        return self.provider.get_generation(
            tenant_id=tenant_id,
            solar_plant_id=solar_plant_id,
            start_at=start_at,
            end_at=end_at,
        )

    def save_generation(
        self,
        db: Session,
        records: list[dict],
    ) -> list[GenerationRecord]:
        if not records:
            return []

        statement = insert(GenerationRecord).values(records)

        statement = statement.on_conflict_do_update(
            constraint="uq_generation_records_tenant_plant_measured_at",
            set_={
                "synced_at": statement.excluded.synced_at,
                "power_w": statement.excluded.power_w,
                "energy_today_kwh": statement.excluded.energy_today_kwh,
                "energy_total_kwh": statement.excluded.energy_total_kwh,
                "voltage_v": statement.excluded.voltage_v,
                "current_a": statement.excluded.current_a,
                "frequency_hz": statement.excluded.frequency_hz,
                "raw_data": statement.excluded.raw_data,
            },
        ).returning(GenerationRecord)

        result = db.execute(statement)
        db.commit()

        return list(result.scalars().all())

    def sync_solarman_plant_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_time: str,
        end_time: str,
        time_type: int = 1,
    ) -> GenerationSyncResult:
        from app.models.solar_plant import SolarPlant
        from app.services.providers.solarman_provider import SolarmanProvider

        solar_plant = (
            self.db.query(SolarPlant)
            .filter(
                SolarPlant.id == solar_plant_id,
                SolarPlant.tenant_id == tenant_id,
            )
            .first()
        )

        if solar_plant is None:
            raise ValueError(
                "Planta solar não encontrada para este tenant."
            )

        station_id = solar_plant.solarman_station_id

        provider = SolarmanProvider(self.db)

        start_date = start_time[:10]
        end_date = end_time[:10]

        result = provider.get_station_history(
            tenant_id=tenant_id,
            station_id=station_id,
            start_time=start_date,
            end_time=end_date,
            time_type=time_type,
        )

        items = result.get("stationDataItems") or []

        records = [
            map_solarman_history_item_to_generation_record(
                tenant_id=tenant_id,
                solar_plant_id=solar_plant_id,
                item=item,
            )
            for item in items
        ]

        saved_records = self.save_generation(
            db=self.db,
            records=records,
        )

        return GenerationSyncResult(
            solar_plant_id=solar_plant_id,
            station_id=station_id,
            records_received=len(items),
            records_saved=len(saved_records),
        )

    def sync_solarman_tenant_generation(
        self,
        tenant_id: int,
        start_time: str,
        end_time: str,
        limit: int | None = None,
    ) -> GenerationBatchSyncResult:
        from app.models.solar_plant import SolarPlant

        sync_log = GenerationSyncLog(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            status="RUNNING",
        )

        self.db.add(sync_log)
        self.db.commit()
        self.db.refresh(sync_log)

        solar_plants = (
            self.db.query(SolarPlant)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
                SolarPlant.source_provider == "SOLARMAN",
            )
            .order_by(SolarPlant.id)
            .all()
        )

        if limit is not None:
            solar_plants = solar_plants[:limit]

        sync_log.total_plants = len(solar_plants)
        self.db.commit()

        batch_started_at = time.perf_counter()
        successful_plants = 0
        failed_plants = 0
        total_records_received = 0
        total_records_saved = 0
        failures = []

        for solar_plant in solar_plants:
            plant_started_at = time.perf_counter()
            try:
                result = self.sync_solarman_plant_generation(
                    tenant_id=tenant_id,
                    solar_plant_id=solar_plant.id,
                    start_time=start_time,
                    end_time=end_time,
                )

                successful_plants += 1
                total_records_received += result.records_received
                total_records_saved += result.records_saved

                sync_log.successful_plants = successful_plants
                sync_log.total_records_received = total_records_received
                sync_log.total_records_saved = total_records_saved
                self.db.commit()

                plant_duration = time.perf_counter() - plant_started_at
                print(
                    f"Planta {solar_plant.id} sincronizada em "
                    f"{plant_duration:.2f}s"
                )

            except Exception as exc:
                self.db.rollback()
                failed_plants += 1

                failures.append(
                    {
                        "solar_plant_id": solar_plant.id,
                        "station_id": solar_plant.solarman_station_id,
                        "error": str(exc),
                    }
                )

                sync_log.failed_plants = failed_plants
                sync_log.failures = str(failures)
                self.db.commit()

        sync_log.finished_at = datetime.now(timezone.utc)
        sync_log.status = "SUCCESS" if failed_plants == 0 else "PARTIAL"
        sync_log.successful_plants = successful_plants
        sync_log.failed_plants = failed_plants
        sync_log.total_records_received = total_records_received
        sync_log.total_records_saved = total_records_saved
        sync_log.failures = str(failures) if failures else None

        self.db.commit()

        batch_duration = time.perf_counter() - batch_started_at
        print(
            f"Lote concluído em {batch_duration:.2f}s | "
            f"Sucesso: {successful_plants} | "
            f"Falhas: {failed_plants}"
        )

        return GenerationBatchSyncResult(
            total_plants=len(solar_plants),
            successful_plants=successful_plants,
            failed_plants=failed_plants,
            total_records_received=total_records_received,
            total_records_saved=total_records_saved,
            failures=failures,
        )

    def get_saved_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[GenerationRecord]:
        return (
            self.db.query(GenerationRecord)
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id == solar_plant_id,
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
            )
            .order_by(GenerationRecord.measured_at)
            .all()
        )

    def get_generation_summary(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> dict:
        from sqlalchemy import func

        result = (
            self.db.query(
                func.count(GenerationRecord.id),
                func.max(GenerationRecord.power_w),
                func.avg(GenerationRecord.power_w),
                func.min(GenerationRecord.measured_at),
                func.max(GenerationRecord.measured_at),
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id == solar_plant_id,
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
            )
            .first()
        )

        records = result[0] or 0
        peak_power_w = (
            float(result[1])
            if result[1] is not None
            else None
        )
        average_power_w = (
            float(result[2])
            if result[2] is not None
            else None
        )

        return {
            "solar_plant_id": solar_plant_id,
            "start_at": start_at,
            "end_at": end_at,
            "records": records,
            "peak_power_w": peak_power_w,
            "average_power_w": average_power_w,
            "first_measured_at": result[3],
            "last_measured_at": result[4],
        }

    def calculate_energy(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> float:
        records = (
            self.db.query(
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.solar_plant_id == solar_plant_id,
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .order_by(GenerationRecord.measured_at)
            .all()
        )

        if len(records) < 2:
            return 0.0

        energy_kwh = 0.0

        for current, next_record in zip(records, records[1:]):
            current_time, current_power = current
            next_time, next_power = next_record

            interval_minutes = (
                next_time - current_time
            ).total_seconds() / 60

            if interval_minutes > 30:
                continue

            interval_hours = interval_minutes / 60

            average_power_w = (
                float(current_power) + float(next_power)
            ) / 2

            energy_kwh += (
                average_power_w * interval_hours
            ) / 1000

        return energy_kwh

    def calculate_tenant_energy(
        self,
        tenant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> float:
        records = (
            self.db.query(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.measured_at >= start_at,
                GenerationRecord.measured_at <= end_at,
                GenerationRecord.power_w.is_not(None),
            )
            .order_by(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
            )
            .all()
        )

        if len(records) < 2:
            return 0.0

        energy_kwh = 0.0
        previous_plant_id = None
        previous_time = None
        previous_power = None

        for plant_id, measured_at, power_w in records:
            if (
                previous_plant_id == plant_id
                and previous_time is not None
                and previous_power is not None
            ):
                interval_minutes = (
                    measured_at - previous_time
                ).total_seconds() / 60

                if interval_minutes <= 30:
                    interval_hours = interval_minutes / 60

                    average_power_w = (
                        float(previous_power) + float(power_w)
                    ) / 2

                    energy_kwh += (
                        average_power_w * interval_hours
                    ) / 1000

            previous_plant_id = plant_id
            previous_time = measured_at
            previous_power = power_w

        return energy_kwh

    def get_plant_statuses(
        self,
        tenant_id: int,
        reference_time: datetime,
        validity_minutes: int = 30,
    ) -> dict[int, str]:
        from app.models.solar_plant import SolarPlant

        solar_plants = (
            self.db.query(SolarPlant.id)
            .filter(
                SolarPlant.tenant_id == tenant_id,
                SolarPlant.is_active.is_(True),
            )
            .all()
        )

        statuses = {
            plant_id: "OFFLINE"
            for (plant_id,) in solar_plants
        }

        validity_start = reference_time.timestamp() - (
            validity_minutes * 60
        )

        latest_records = (
            self.db.query(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at,
                GenerationRecord.power_w,
            )
            .filter(
                GenerationRecord.tenant_id == tenant_id,
                GenerationRecord.measured_at >= datetime.fromtimestamp(
                    validity_start,
                    tz=reference_time.tzinfo,
                ),
                GenerationRecord.measured_at <= reference_time,
                GenerationRecord.power_w.is_not(None),
            )
            .order_by(
                GenerationRecord.solar_plant_id,
                GenerationRecord.measured_at.desc(),
            )
            .all()
        )

        seen_plants = set()

        for plant_id, measured_at, power_w in latest_records:
            if plant_id in seen_plants:
                continue

            seen_plants.add(plant_id)

            if float(power_w) > 0:
                statuses[plant_id] = "GENERATING"
            else:
                statuses[plant_id] = "ONLINE"

        return statuses

    def sync_solarman_aggregate_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_time: str,
        end_time: str,
        time_type: int,
    ) -> int:
        from app.models.solar_plant import SolarPlant
        from app.services.generation_aggregate_mapper import (
            map_solarman_aggregate_item,
        )
        from app.services.generation_aggregate_service import (
            GenerationAggregateService,
        )
        from app.services.providers.solarman_provider import (
            SolarmanProvider,
        )

        solar_plant = (
            self.db.query(SolarPlant)
            .filter(
                SolarPlant.id == solar_plant_id,
                SolarPlant.tenant_id == tenant_id,
            )
            .first()
        )

        if solar_plant is None:
            raise ValueError(
                "Planta solar não encontrada para este tenant."
            )

        if not solar_plant.solarman_station_id:
            raise ValueError(
                "Planta não possui solarman_station_id."
            )

        provider = SolarmanProvider(self.db)

        result = provider.get_station_history(
            tenant_id=tenant_id,
            station_id=solar_plant.solarman_station_id,
            start_time=start_time,
            end_time=end_time,
            time_type=time_type,
        )

        items = result.get("stationDataItems") or []

        if time_type == 3:
            granularity = "MONTH"
        elif time_type == 4:
            granularity = "YEAR"
        else:
            raise ValueError(
                "sync_solarman_aggregate_generation suporta "
                "apenas time_type 3 ou 4."
            )

        records = [
            map_solarman_aggregate_item(
                tenant_id=tenant_id,
                solar_plant_id=solar_plant_id,
                item=item,
                granularity=granularity,
            )
            for item in items
        ]

        aggregate_service = GenerationAggregateService(
            db=self.db
        )

        saved_records = aggregate_service.save_aggregates(
            records
        )

        return len(saved_records)

def map_solarman_history_item_to_generation_record(
    tenant_id: int,
    solar_plant_id: int,
    item: dict,
) -> dict:
    timestamp = item.get("dateTime")

    if timestamp is not None:
        measured_at = datetime.fromtimestamp(
            float(timestamp),
            tz=timezone.utc,
        )
    else:
        year = item.get("year")
        month = item.get("month")
        day = item.get("day")

        if not all(value is not None for value in (year, month, day)):
            raise ValueError(
                "Registro SolarMan sem dateTime ou data year/month/day."
            )

        measured_at = datetime(
            int(year),
            int(month),
            int(day),
            tzinfo=timezone.utc,
        )

    generation_power = item.get("generationPower")
    generation_value = item.get("generationValue")

    return {
        "tenant_id": tenant_id,
        "solar_plant_id": solar_plant_id,
        "measured_at": measured_at,
        "power_w": generation_power,
        "energy_today_kwh": generation_value,
        "energy_total_kwh": None,
        "voltage_v": None,
        "current_a": None,
        "frequency_hz": None,
        "raw_data": item,
    }

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

def get_generation_history(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
    granularity: str,
) -> list[dict]:
    """
    Retorna geração histórica agregada para gráficos.

    granularity:
    - hour: geração por hora
    - day: geração por dia
    - month: geração por mês
    """

    from collections import defaultdict
    from datetime import timedelta
    from decimal import Decimal

    if period_end <= period_start:
        raise ValueError(
            "O fim do período deve ser posterior ao início."
        )

    if granularity not in {"hour", "day", "month"}:
        raise ValueError(
            "Granularidade inválida. Use: hour, day ou month."
        )

    service = GenerationService(db=db)

    records = service.get_saved_generation(
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        start_at=period_start,
        end_at=period_end,
    )

    grouped = defaultdict(Decimal)

    for current, next_record in zip(records, records[1:]):
        current_time = current.measured_at
        next_time = next_record.measured_at

        interval_minutes = (
            next_time - current_time
        ).total_seconds() / 60

        if interval_minutes <= 0 or interval_minutes > 30:
            continue

        interval_hours = Decimal(
            str(interval_minutes / 60)
        )

        current_power = Decimal(
            str(current.power_w or 0)
        )

        next_power = Decimal(
            str(next_record.power_w or 0)
        )

        average_power_w = (
            current_power + next_power
        ) / Decimal("2")

        energy_kwh = (
            average_power_w * interval_hours
        ) / Decimal("1000")

        if granularity == "hour":
            key = current_time.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

        elif granularity == "day":
            key = current_time.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        else:
            key = current_time.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        grouped[key] += energy_kwh

    if not grouped:
        return []

    if granularity == "hour":
        step = timedelta(hours=1)
    elif granularity == "day":
        step = timedelta(days=1)
    else:
        step = None

    periods = []

    if granularity in {"hour", "day"}:
        current = min(grouped.keys())

        while current <= max(grouped.keys()):
            periods.append(current)
            current += step

    else:
        current = min(grouped.keys())
        last_period = max(grouped.keys())

        while current <= last_period:
            periods.append(current)

            if current.month == 12:
                current = current.replace(
                    year=current.year + 1,
                    month=1,
                )
            else:
                current = current.replace(
                    month=current.month + 1,
                )

    return [
        {
            "period": period,
            "generation_kwh": grouped.get(period),
        }
        for period in periods
    ]