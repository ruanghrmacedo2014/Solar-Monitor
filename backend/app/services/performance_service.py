from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.services.expected_generation_service import (
    get_expected_generation_for_period,
)
from app.services.generation_service import (
    GenerationService,
)
from app.services.performance_engine import (
    PerformanceComparisonResult,
    calculate_performance_percentage,
    classify_data_quality,
    classify_performance,
)

@dataclass
class DataCoverageResult:
    period_hours: Decimal
    covered_hours: Decimal
    coverage_percent: Decimal


def calculate_data_coverage(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
) -> DataCoverageResult:
    from app.models.generation_record import GenerationRecord

    if period_end <= period_start:
        raise ValueError(
            "O fim do período deve ser posterior ao início."
        )

    records = (
        db.query(GenerationRecord.measured_at)
        .filter(
            GenerationRecord.tenant_id == tenant_id,
            GenerationRecord.solar_plant_id == solar_plant_id,
            GenerationRecord.measured_at >= period_start,
            GenerationRecord.measured_at < period_end,
        )
        .order_by(GenerationRecord.measured_at)
        .all()
    )

    period_hours = Decimal(
        str(
            (
                period_end - period_start
            ).total_seconds() / 3600
        )
    )

    if not records:
        return DataCoverageResult(
            period_hours=period_hours,
            covered_hours=Decimal("0"),
            coverage_percent=Decimal("0"),
        )

    first_record_time = records[0][0]
    last_record_time = records[-1][0]

    observed_period_hours = Decimal(
        str(
            (
                last_record_time - first_record_time
            ).total_seconds() / 3600
        )
    )

    if observed_period_hours <= Decimal("0"):
        return DataCoverageResult(
            period_hours=period_hours,
            covered_hours=Decimal("0"),
            coverage_percent=Decimal("0"),
        )

    covered_hours = Decimal("0")

    for current, next_record in zip(
        records,
        records[1:],
    ):
        current_time = current[0]
        next_time = next_record[0]

        interval_hours = Decimal(
            str(
                (
                    next_time - current_time
                ).total_seconds() / 3600
            )
        )

        # Ignora lacunas superiores a 30 minutos.
        if interval_hours <= Decimal("0.5"):
            covered_hours += interval_hours

    coverage_percent = (
        covered_hours
        / observed_period_hours
        * Decimal("100")
    )

    if coverage_percent > Decimal("100"):
        coverage_percent = Decimal("100")

    return DataCoverageResult(
        period_hours=period_hours,
        covered_hours=covered_hours,
        coverage_percent=coverage_percent,
    )

@dataclass
class PlantPerformanceResult:
    solar_plant_id: int
    period_start: datetime
    period_end: datetime
    actual_kwh: Decimal
    expected_kwh: Decimal
    performance_percent: Decimal | None
    classification: str
    coverage_percent: Decimal
    data_quality: str

def calculate_plant_performance(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
) -> PlantPerformanceResult:
    expected = get_expected_generation_for_period(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        period_start=period_start,
        period_end=period_end,
    )

    generation_service = GenerationService(db=db)

    actual_kwh = generation_service.calculate_energy(
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        start_at=period_start,
        end_at=period_end,
    )

    actual_kwh_decimal = Decimal(
        str(actual_kwh)
    )

    coverage = calculate_data_coverage(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        period_start=period_start,
        period_end=period_end,
    )

    data_quality = classify_data_quality(
        coverage.coverage_percent
    )

    if data_quality in (
        "NO_DATA",
        "INSUFFICIENT_DATA",
    ):
        performance_percent = None
    else:
        comparison: PerformanceComparisonResult = (
            calculate_performance_percentage(
                actual_kwh=actual_kwh_decimal,
                expected_kwh=expected.expected_kwh,
            )
        )

        performance_percent = comparison.performance_percent

    if data_quality == "NO_DATA":
        classification = "NO_DATA"
    elif data_quality == "INSUFFICIENT_DATA":
        classification = "INSUFFICIENT_DATA"
    else:
        classification = classify_performance(
            performance_percent
        )

    return PlantPerformanceResult(
        solar_plant_id=solar_plant_id,
        period_start=period_start,
        period_end=period_end,
        actual_kwh=actual_kwh_decimal,
        expected_kwh=expected.expected_kwh,
        performance_percent=performance_percent,
        classification=classification,
        coverage_percent=coverage.coverage_percent,
        data_quality=data_quality,
    )