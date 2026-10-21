from datetime import datetime, timezone


def map_solarman_aggregate_item(
    tenant_id: int,
    solar_plant_id: int,
    item: dict,
    granularity: str,
) -> dict:
    year = item.get("year")
    month = item.get("month")

    if year is None:
        raise ValueError(
            "Registro SolarMan sem year."
        )

    if granularity == "MONTH":
        if month is None:
            raise ValueError(
                "Registro mensal SolarMan sem month."
            )

        period_start = datetime(
            int(year),
            int(month),
            1,
            tzinfo=timezone.utc,
        )

    elif granularity == "YEAR":
        period_start = datetime(
            int(year),
            1,
            1,
            tzinfo=timezone.utc,
        )

    else:
        raise ValueError(
            f"Granularidade não suportada: {granularity}"
        )

    generation_value = item.get("generationValue")

    if generation_value is None:
        generation_value = 0

    return {
        "tenant_id": tenant_id,
        "solar_plant_id": solar_plant_id,
        "period_start": period_start,
        "granularity": granularity,
        "generation_kwh": generation_value,
        "raw_data": item,
    }