from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.report import Report
from app.services.performance_service import (
    calculate_plant_performance,
)


@dataclass
class ReportGenerationResult:
    report: Report
    created: bool


def generate_plant_report(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
    report_type: str = "PLANT",
) -> ReportGenerationResult:
    performance = calculate_plant_performance(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        period_start=period_start,
        period_end=period_end,
    )

    report = Report(
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        actual_kwh=Decimal(str(performance.actual_kwh)),
        expected_kwh=Decimal(str(performance.expected_kwh)),
        performance_percent=(
            Decimal(str(performance.performance_percent))
            if performance.performance_percent is not None
            else None
        ),
        coverage_percent=Decimal(
            str(performance.coverage_percent)
        ),
        data_quality=performance.data_quality,
        classification=performance.classification,
        status="GENERATED",
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportGenerationResult(
        report=report,
        created=True,
    )

def customer_can_access_plant_report(
    db: Session,
    customer_id: int,
    solar_plant_id: int,
) -> bool:
    from app.models.solar_plant import SolarPlant

    statement = (
        db.query(SolarPlant.id)
        .filter(
            SolarPlant.id == solar_plant_id,
            SolarPlant.customer_id == customer_id,
            SolarPlant.is_active.is_(True),
        )
    )

    return statement.first() is not None

def generate_customer_report(
    db: Session,
    tenant_id: int,
    customer_id: int,
    period_start: datetime,
    period_end: datetime,
    report_type: str = "CUSTOMER",
) -> ReportGenerationResult:
    from app.models.customer import Customer
    from app.models.solar_plant import SolarPlant
    from app.services.performance_engine import (
        calculate_performance_percentage,
        classify_data_quality,
        classify_performance,
    )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
            Customer.is_active.is_(True),
        )
        .first()
    )

    if customer is None:
        raise ValueError(
            "Cliente não encontrado ou inativo."
        )

    plants = (
        db.query(SolarPlant)
        .filter(
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.customer_id == customer_id,
            SolarPlant.is_active.is_(True),
        )
        .order_by(SolarPlant.id)
        .all()
    )

    if not plants:
        raise ValueError(
            "O cliente não possui usinas ativas associadas."
        )

    total_actual_kwh = Decimal("0")
    total_expected_kwh = Decimal("0")
    total_coverage_percent = Decimal("0")

    for plant in plants:
        performance = calculate_plant_performance(
            db=db,
            tenant_id=tenant_id,
            solar_plant_id=plant.id,
            period_start=period_start,
            period_end=period_end,
        )

        total_actual_kwh += Decimal(
            str(performance.actual_kwh)
        )

        total_expected_kwh += Decimal(
            str(performance.expected_kwh)
        )

        total_coverage_percent += Decimal(
            str(performance.coverage_percent)
        )

    average_coverage_percent = (
        total_coverage_percent
        / Decimal(str(len(plants)))
    )

    data_quality = classify_data_quality(
        average_coverage_percent
    )

    performance_percent = None

    if (
        data_quality != "NO_DATA"
        and data_quality != "INSUFFICIENT_DATA"
    ):
        comparison = calculate_performance_percentage(
            actual_kwh=total_actual_kwh,
            expected_kwh=total_expected_kwh,
        )

        performance_percent = (
            comparison.performance_percent
        )

        classification = classify_performance(
            performance_percent
        )
    elif data_quality == "NO_DATA":
        classification = "NO_DATA"
    else:
        classification = "INSUFFICIENT_DATA"

    report = Report(
        tenant_id=tenant_id,
        customer_id=customer_id,
        solar_plant_id=None,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        actual_kwh=total_actual_kwh,
        expected_kwh=total_expected_kwh,
        performance_percent=performance_percent,
        coverage_percent=average_coverage_percent,
        data_quality=data_quality,
        classification=classification,
        status="GENERATED",
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportGenerationResult(
        report=report,
        created=True,
    )

def get_plant_report_chart_data(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
    granularity: str,
) -> list[dict]:
    """
    Prepara os dados de geração real x esperada para gráficos.

    granularity:
    - hour: um ponto por hora
    - day: um ponto por dia
    - month: um ponto por mês
    """

    from datetime import timedelta

    from app.services.generation_service import (
        get_generation_history,
    )
    from app.services.expected_generation_service import (
        get_expected_generation_for_period,
    )

    if period_end <= period_start:
        raise ValueError(
            "O fim do período deve ser posterior ao início."
        )

    if granularity not in {"hour", "day", "month"}:
        raise ValueError(
            "Granularidade inválida. Use: hour, day ou month."
        )

    generation_history = get_generation_history(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        period_start=period_start,
        period_end=period_end,
        granularity=granularity,
    )

    periods = []

    if granularity == "hour":
        current = period_start.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        while current < period_end:
            periods.append(current)
            current += timedelta(hours=1)

    elif granularity == "day":
        current = period_start.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        while current < period_end:
            periods.append(current)
            current += timedelta(days=1)

    else:
        current = period_start.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        while current < period_end:
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

    generation_by_period = {
        item["period"]: item["generation_kwh"]
        for item in generation_history
    }

    results = []

    for current_period in periods:

        if granularity == "hour":
            next_period = current_period + timedelta(hours=1)

        elif granularity == "day":
            next_period = current_period + timedelta(days=1)

        else:
            if current_period.month == 12:
                next_period = current_period.replace(
                    year=current_period.year + 1,
                    month=1,
                )
            else:
                next_period = current_period.replace(
                    month=current_period.month + 1,
                )

        segment_start = max(
            current_period,
            period_start,
        )

        segment_end = min(
            next_period,
            period_end,
        )

        if segment_end <= segment_start:
            continue

        expected = get_expected_generation_for_period(
            db=db,
            tenant_id=tenant_id,
            solar_plant_id=solar_plant_id,
            period_start=segment_start,
            period_end=segment_end,
        )

        results.append(
            {
                "period": current_period,
                "generation_kwh": generation_by_period.get(
                    current_period
                ),
                "expected_kwh": expected.expected_kwh,
            }
        )

    return results

@dataclass
class CustomerReportPlantData:
    solar_plant_id: int
    plant_name: str
    installed_power_kwp: Decimal | None
    actual_kwh: Decimal
    expected_kwh: Decimal
    performance_percent: Decimal | None
    coverage_percent: Decimal
    data_quality: str
    classification: str
    chart_data: list[dict]

@dataclass
class CustomerReportData:
    customer_id: int
    customer_name: str
    period_start: datetime
    period_end: datetime
    plants: list[CustomerReportPlantData]
    total_actual_kwh: Decimal
    total_expected_kwh: Decimal
    average_coverage_percent: Decimal
    overall_performance_percent: Decimal | None
    data_quality: str
    classification: str

def get_customer_report_data(
    db: Session,
    tenant_id: int,
    customer_id: int,
    period_start: datetime,
    period_end: datetime,
    granularity: str,
) -> CustomerReportData:
    from app.models.customer import Customer
    from app.models.solar_plant import SolarPlant

    if period_end <= period_start:
        raise ValueError(
            "O fim do período deve ser posterior ao início."
        )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
            Customer.is_active.is_(True),
        )
        .first()
    )

    if customer is None:
        raise ValueError(
            "Cliente não encontrado."
        )

    plants = (
        db.query(SolarPlant)
        .filter(
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.customer_id == customer_id,
            SolarPlant.is_active.is_(True),
        )
        .order_by(SolarPlant.name)
        .all()
    )

    plant_data = []

    total_actual_kwh = Decimal("0")
    total_expected_kwh = Decimal("0")

    coverage_values = []
    sufficient_performance_values = []

    for plant in plants:
        performance = calculate_plant_performance(
            db=db,
            tenant_id=tenant_id,
            solar_plant_id=plant.id,
            period_start=period_start,
            period_end=period_end,
        )

        chart_data = get_plant_report_chart_data(
            db=db,
            tenant_id=tenant_id,
            solar_plant_id=plant.id,
            period_start=period_start,
            period_end=period_end,
            granularity=granularity,
        )

        actual_kwh = Decimal(str(performance.actual_kwh))
        expected_kwh = Decimal(str(performance.expected_kwh))
        coverage_percent = Decimal(
            str(performance.coverage_percent)
        )

        total_actual_kwh += actual_kwh
        total_expected_kwh += expected_kwh

        coverage_values.append(coverage_percent)

        if performance.performance_percent is not None:
            sufficient_performance_values.append(
                Decimal(
                    str(performance.performance_percent)
                )
            )

        plant_data.append(
            CustomerReportPlantData(
                solar_plant_id=plant.id,
                plant_name=plant.name,
                installed_power_kwp=(
                    Decimal(str(plant.installed_power))
                    if plant.installed_power is not None
                    else None
                ),
                actual_kwh=actual_kwh,
                expected_kwh=expected_kwh,
                performance_percent=(
                    Decimal(
                        str(performance.performance_percent)
                    )
                    if performance.performance_percent is not None
                    else None
                ),
                coverage_percent=coverage_percent,
                data_quality=performance.data_quality,
                classification=performance.classification,
                chart_data=chart_data,
            )
        )

    if coverage_values:
        average_coverage_percent = (
            sum(coverage_values, Decimal("0"))
            / Decimal(len(coverage_values))
        )
    else:
        average_coverage_percent = Decimal("0")

    if total_expected_kwh > Decimal("0"):
        overall_performance_percent = (
            total_actual_kwh
            / total_expected_kwh
            * Decimal("100")
        )
    else:
        overall_performance_percent = None

    if average_coverage_percent <= Decimal("0"):
        data_quality = "NO_DATA"
    elif average_coverage_percent < Decimal("80"):
        data_quality = "INSUFFICIENT_DATA"
    else:
        data_quality = "SUFFICIENT_DATA"

    if data_quality != "SUFFICIENT_DATA":
        classification = "INSUFFICIENT_DATA"
    elif overall_performance_percent is None:
        classification = "NO_DATA"
    elif overall_performance_percent >= Decimal("105"):
        classification = "ABOVE_EXPECTED"
    elif overall_performance_percent >= Decimal("95"):
        classification = "WITHIN_EXPECTED"
    elif overall_performance_percent >= Decimal("85"):
        classification = "BELOW_EXPECTED"
    else:
        classification = "SIGNIFICANTLY_BELOW_EXPECTED"

    if sufficient_performance_values:
        # Mantemos a variável disponível para futuras
        # métricas consolidadas por usina.
        _ = sufficient_performance_values

    return CustomerReportData(
        customer_id=customer.id,
        customer_name=customer.name,
        period_start=period_start,
        period_end=period_end,
        plants=plant_data,
        total_actual_kwh=total_actual_kwh,
        total_expected_kwh=total_expected_kwh,
        average_coverage_percent=average_coverage_percent,
        overall_performance_percent=overall_performance_percent,
        data_quality=data_quality,
        classification=classification,
    )