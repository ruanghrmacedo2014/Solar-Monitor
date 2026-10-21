from datetime import datetime

from pydantic import BaseModel


class GenerationResponse(BaseModel):
    id: int
    solar_plant_id: int
    measured_at: datetime
    synced_at: datetime

    power_w: float | None
    energy_today_kwh: float | None
    energy_total_kwh: float | None
    voltage_v: float | None
    current_a: float | None
    frequency_hz: float | None

    model_config = {
        "from_attributes": True
    }

class GenerationSummaryResponse(BaseModel):
    solar_plant_id: int
    start_at: datetime
    end_at: datetime
    records: int
    peak_power_w: float | None
    average_power_w: float | None
    first_measured_at: datetime | None
    last_measured_at: datetime | None