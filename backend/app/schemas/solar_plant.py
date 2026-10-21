from datetime import datetime

from pydantic import BaseModel


class SolarPlantCreate(BaseModel):
    solarman_station_id: int
    name: str

    installed_power: float | None = None

    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None

    plant_type: str | None = None
    grid_interconnection_type: str | None = None

    start_operating_at: datetime | None = None

    owner_name: str | None = None
    contact_phone: str | None = None

class SolarPlantResponse(BaseModel):
    id: int
    tenant_id: int
    customer_id: int | None

    solarman_station_id: int
    name: str

    installed_power: float | None

    address: str | None
    latitude: float | None
    longitude: float | None
    timezone: str | None

    plant_type: str | None
    grid_interconnection_type: str | None

    start_operating_at: datetime | None

    owner_name: str | None
    contact_phone: str | None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class SolarPlantCustomerLink(BaseModel):
    customer_id: int

class SolarDeviceResponse(BaseModel):
    id: int
    solar_plant_id: int

    solarman_device_id: int
    device_sn: str | None
    device_type: str | None
    connect_status: int | None
    collection_time: datetime | None

    model_config = {
        "from_attributes": True
    }