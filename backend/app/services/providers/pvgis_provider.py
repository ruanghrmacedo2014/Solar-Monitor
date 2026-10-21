from dataclasses import dataclass
from decimal import Decimal

import requests


PVGIS_BASE_URL = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"


@dataclass
class PVGISMonthlyResult:
    month: int
    expected_generation_kwh: Decimal
    solar_radiation_kwh_m2: Decimal
    peak_power_kw: Decimal

    @property
    def pv_output_kwh_kwp(self) -> Decimal:
        return (
            self.expected_generation_kwh
            / self.peak_power_kw
        )


def get_pvgis_monthly_output(
    latitude: Decimal,
    longitude: Decimal,
    peak_power_kw: Decimal,
) -> list[PVGISMonthlyResult]:
    params = {
        "lat": float(latitude),
        "lon": float(longitude),
        "peakpower": float(peak_power_kw),
        "loss": 14,
        "outputformat": "json",
    }

    response = requests.get(
        PVGIS_BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    monthly_data = data["outputs"]["monthly"]["fixed"]

    return [
        PVGISMonthlyResult(
            month=item["month"],
            expected_generation_kwh=Decimal(
                str(item["E_m"])
            ),
            solar_radiation_kwh_m2=Decimal(
                str(item["H(i)_m"])
            ),
            peak_power_kw=peak_power_kw,
        )
        for item in monthly_data
    ]