from datetime import datetime

from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    current_power_w: float | None
    today_energy_kwh: float | None
    today_peak_power_w: float | None
    today_average_power_w: float | None

    plants_total: int
    plants_generating: int
    plants_online: int
    plants_offline: int

    devices_total: int
    devices_online: int
    devices_offline: int

    last_sync_at: datetime | None

class DashboardGenerationPointResponse(BaseModel):
    solar_plant_id: int
    measured_at: datetime
    power_w: float | None

class DashboardGenerationHourlyResponse(BaseModel):
    measured_at: datetime
    average_power_w: float | None
    peak_power_w: float | None
    minimum_power_w: float | None

class DashboardPlantProviderSummaryResponse(BaseModel):
    provider: str
    total: int
    generating: int
    online: int
    offline: int


class DashboardPlantResponse(BaseModel):
    id: int
    name: str
    source_provider: str
    status: str
    latest_power_w: float | None
    last_measured_at: datetime | None


class DashboardPlantsResponse(BaseModel):
    total: int
    generating: int
    online: int
    offline: int
    by_provider: list[DashboardPlantProviderSummaryResponse]
    plants: list[DashboardPlantResponse]

class DashboardDeviceProviderSummaryResponse(BaseModel):
    provider: str
    total: int
    online: int
    offline: int


class DashboardDeviceResponse(BaseModel):
    id: int
    solar_plant_id: int
    plant_name: str
    source_provider: str
    solarman_device_id: int | None
    device_sn: str | None
    device_type: str | None
    connect_status: str | None
    collection_time: datetime | None


class DashboardDevicesResponse(BaseModel):
    total: int
    online: int
    offline: int
    by_provider: list[DashboardDeviceProviderSummaryResponse]
    devices: list[DashboardDeviceResponse]

class DashboardSyncResponse(BaseModel):
    last_sync_at: datetime | None
    status: str | None

    started_at: datetime | None
    finished_at: datetime | None

    total_plants: int
    successful_plants: int
    failed_plants: int

    total_records_received: int
    total_records_saved: int

    failures: str | None

class DashboardGenerationDailyResponse(BaseModel):
    measured_at: datetime
    energy_kwh: float

class DashboardGenerationMonthlyResponse(BaseModel):
    measured_at: datetime
    energy_kwh: float

class DashboardGenerationYearlyResponse(BaseModel):
    measured_at: datetime
    energy_kwh: float