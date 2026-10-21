from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ExpectedGenerationResult:
    expected_kwh: Decimal
    performance_ratio: Decimal
    availability_target: Decimal
    degradation_factor: Decimal


def calculate_expected_generation(
    resource_pv_output_kwh_kwp: Decimal,
    installed_power_kwp: Decimal,
    performance_ratio: Decimal,
    availability_target: Decimal,
    degradation_rate: Decimal,
    years_since_start: Decimal = Decimal("0"),
) -> ExpectedGenerationResult:
    degradation_factor = (
        Decimal("1")
        - degradation_rate * years_since_start
    )

    if degradation_factor < Decimal("0"):
        degradation_factor = Decimal("0")

    expected_kwh = (
        resource_pv_output_kwh_kwp
        * installed_power_kwp
        * availability_target
        * degradation_factor
    )

    return ExpectedGenerationResult(
        expected_kwh=expected_kwh,
        performance_ratio=performance_ratio,
        availability_target=availability_target,
        degradation_factor=degradation_factor,
    )

@dataclass
class PerformanceComparisonResult:
    actual_kwh: Decimal
    expected_kwh: Decimal
    performance_percent: Decimal


def calculate_performance_percentage(
    actual_kwh: Decimal,
    expected_kwh: Decimal,
) -> PerformanceComparisonResult:
    if expected_kwh <= Decimal("0"):
        raise ValueError(
            "A geração esperada deve ser maior que zero."
        )

    performance_percent = (
        actual_kwh
        / expected_kwh
        * Decimal("100")
    )

    return PerformanceComparisonResult(
        actual_kwh=actual_kwh,
        expected_kwh=expected_kwh,
        performance_percent=performance_percent,
    )

def classify_performance(
    performance_percent: Decimal,
) -> str:
    if performance_percent >= Decimal("105"):
        return "ABOVE_EXPECTED"

    if performance_percent >= Decimal("95"):
        return "WITHIN_EXPECTED"

    if performance_percent >= Decimal("85"):
        return "BELOW_EXPECTED"

    return "SIGNIFICANTLY_BELOW_EXPECTED"

def classify_data_quality(
    coverage_percent: Decimal,
) -> str:
    if coverage_percent <= Decimal("0"):
        return "NO_DATA"

    if coverage_percent < Decimal("80"):
        return "INSUFFICIENT_DATA"

    return "SUFFICIENT_DATA"