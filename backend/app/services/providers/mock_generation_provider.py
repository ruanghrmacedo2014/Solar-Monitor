from datetime import datetime, timedelta

from app.services.providers.generation_provider import GenerationProvider


class MockGenerationProvider(GenerationProvider):
    """Provider temporário para simular dados de geração solar."""

    def get_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        records = []

        current = start_at
        energy_total = 1000.0

        while current <= end_at:
            hour = current.hour

            if 6 <= hour <= 18:
                power_w = max(
                    0,
                    5000 * (1 - abs(12 - hour) / 7),
                )
            else:
                power_w = 0

            energy_today_kwh = power_w / 1000
            energy_total += energy_today_kwh

            records.append(
                {
                    "tenant_id": tenant_id,
                    "solar_plant_id": solar_plant_id,
                    "measured_at": current,
                    "power_w": round(power_w, 3),
                    "energy_today_kwh": round(energy_today_kwh, 3),
                    "energy_total_kwh": round(energy_total, 3),
                    "voltage_v": 220.0 if power_w > 0 else 0.0,
                    "current_a": round(power_w / 220, 3) if power_w > 0 else 0.0,
                    "frequency_hz": 60.0 if power_w > 0 else 0.0,
                }
            )

            current += timedelta(hours=1)

        return records