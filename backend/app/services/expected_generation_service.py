from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.solar_plant import SolarPlant
from app.models.solar_resource_snapshot import (
    SolarResourceSnapshot,
)
from app.services.performance_engine import (
    ExpectedGenerationResult,
    calculate_expected_generation,
)
from app.services.plant_performance_config_service import (
    get_effective_performance_config,
)


def prorate_monthly_expected_generation(
    monthly_expected_kwh: Decimal,
    period_start: datetime,
    period_end: datetime,
) -> Decimal:
    if period_end <= period_start:
        raise ValueError(
            "O fim do período deve ser posterior ao início."
        )

    if (
        period_start.year != period_end.year
        or period_start.month != period_end.month
    ):
        raise ValueError(
            "O período deve estar dentro do mesmo mês."
        )

    days_in_month = monthrange(
        period_start.year,
        period_start.month,
    )[1]

    period_days = (
        period_end - period_start
    ).total_seconds() / 86400

    return (
        monthly_expected_kwh
        * Decimal(str(period_days))
        / Decimal(str(days_in_month))
    )


def get_expected_generation_for_period(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    period_start: datetime,
    period_end: datetime,
) -> ExpectedGenerationResult:
    from calendar import monthrange

    if period_end <= period_start:
        raise ValueError(
            "O fim do período deve ser posterior ao início."
        )

    plant_statement = select(SolarPlant).where(
        SolarPlant.id == solar_plant_id,
        SolarPlant.tenant_id == tenant_id,
        SolarPlant.is_active.is_(True),
    )

    plant = db.scalar(plant_statement)

    if plant is None:
        raise ValueError(
            "Usina não encontrada ou inativa."
        )

    if plant.installed_power is None:
        raise ValueError(
            "A usina precisa possuir potência instalada."
        )

    config, source = get_effective_performance_config(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
    )

    if config is None:
        raise ValueError(
            "Não existe configuração de performance "
            "ativa para a usina."
        )

    if config.availability_target is None:
        raise ValueError(
            "A configuração de performance não possui "
            "meta de disponibilidade."
        )

    if config.degradation_rate is None:
        raise ValueError(
            "A configuração de performance não possui "
            "taxa de degradação."
        )

    performance_ratio = (
        config.performance_ratio
        if config.performance_ratio is not None
        else Decimal("1")
    )

    degradation_rate = Decimal(
        str(config.degradation_rate)
    )

    availability_target = Decimal(
        str(config.availability_target)
    )

    installed_power_kwp = Decimal(
        str(plant.installed_power)
    )

    total_expected_kwh = Decimal("0")

    current_period_start = period_start

    while current_period_start < period_end:
        month_start = datetime(
            current_period_start.year,
            current_period_start.month,
            1,
            tzinfo=current_period_start.tzinfo or timezone.utc,
        )

        days_in_month = monthrange(
            current_period_start.year,
            current_period_start.month,
        )[1]

        if current_period_start.month == 12:
            next_month_start = datetime(
                current_period_start.year + 1,
                1,
                1,
                tzinfo=current_period_start.tzinfo
                or timezone.utc,
            )
        else:
            next_month_start = datetime(
                current_period_start.year,
                current_period_start.month + 1,
                1,
                tzinfo=current_period_start.tzinfo
                or timezone.utc,
            )

        current_period_end = min(
            period_end,
            next_month_start,
        )

        snapshot_statement = select(
            SolarResourceSnapshot
        ).where(
            SolarResourceSnapshot.tenant_id == tenant_id,
            SolarResourceSnapshot.solar_plant_id
            == solar_plant_id,
            SolarResourceSnapshot.provider == "PVGIS",
            SolarResourceSnapshot.resource_type == "MONTHLY",
            SolarResourceSnapshot.period_start
            == month_start,
        )

        snapshot = db.scalar(snapshot_statement)

        if snapshot is None:
            raise ValueError(
                "Não existe snapshot de recurso solar "
                f"para {month_start.strftime('%Y-%m')}."
            )

        if snapshot.pv_output_kwh_kwp is None:
            raise ValueError(
                "O snapshot não possui produção "
                "fotovoltaica esperada."
            )

        monthly_pv_output_kwh_kwp = Decimal(
            str(snapshot.pv_output_kwh_kwp)
        )

        period_pv_output_kwh_kwp = (
            monthly_pv_output_kwh_kwp
        )

        if (
            current_period_start != month_start
            or current_period_end != next_month_start
        ):
            period_days = Decimal(
                str(
                    (
                        current_period_end
                        - current_period_start
                    ).total_seconds()
                    / 86400
                )
            )

            period_pv_output_kwh_kwp = (
                monthly_pv_output_kwh_kwp
                * period_days
                / Decimal(str(days_in_month))
            )

        years_since_start = Decimal("0")

        if plant.start_operating_at is not None:
            operating_start = plant.start_operating_at

            if operating_start.tzinfo is None:
                operating_start = operating_start.replace(
                    tzinfo=timezone.utc
                )

            elapsed_days = (
                current_period_start
                - operating_start
            ).days

            if elapsed_days > 0:
                years_since_start = (
                    Decimal(str(elapsed_days))
                    / Decimal("365.25")
                )

        monthly_expected = calculate_expected_generation(
            resource_pv_output_kwh_kwp=(
                period_pv_output_kwh_kwp
            ),
            installed_power_kwp=installed_power_kwp,
            performance_ratio=performance_ratio,
            availability_target=availability_target,
            degradation_rate=degradation_rate,
            years_since_start=years_since_start,
        )

        total_expected_kwh += monthly_expected.expected_kwh

        current_period_start = current_period_end

    return ExpectedGenerationResult(
        expected_kwh=total_expected_kwh,
        performance_ratio=performance_ratio,
        availability_target=availability_target,
        degradation_factor=Decimal("1"),
    )