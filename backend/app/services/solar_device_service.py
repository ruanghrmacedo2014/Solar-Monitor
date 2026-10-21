from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.models.solar_device import SolarDevice
from app.models.solar_plant import SolarPlant


def map_solarman_device_to_model(
    tenant_id: int,
    solar_plant_id: int,
    device: dict,
) -> dict:
    collection_time = device.get("collectionTime")

    if collection_time is not None:
        collection_time = datetime.fromtimestamp(
            float(collection_time),
            tz=timezone.utc,
        )

    return {
        "tenant_id": tenant_id,
        "solar_plant_id": solar_plant_id,
        "solarman_device_id": device["deviceId"],
        "device_sn": device.get("deviceSn"),
        "device_type": device.get("deviceType"),
        "connect_status": device.get("connectStatus"),
        "collection_time": collection_time,
    }


def upsert_solarman_device(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    device: dict,
    commit: bool = True,
) -> SolarDevice:
    device_data = map_solarman_device_to_model(
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
        device=device,
    )

    solar_device = (
        db.query(SolarDevice)
        .filter(
            SolarDevice.tenant_id == tenant_id,
            SolarDevice.solarman_device_id
            == device_data["solarman_device_id"],
        )
        .first()
    )

    if solar_device is None:
        solar_device = SolarDevice(**device_data)
        db.add(solar_device)
    else:
        for field, value in device_data.items():
            if field in {"tenant_id", "solar_plant_id"}:
                continue

            setattr(solar_device, field, value)

    if commit:
        db.commit()
        db.refresh(solar_device)

    return solar_device

def sync_solarman_station_devices(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    devices: list[dict],
) -> list[SolarDevice]:
    solar_devices = []

    for device in devices:
        solar_device = upsert_solarman_device(
            db=db,
            tenant_id=tenant_id,
            solar_plant_id=solar_plant_id,
            device=device,
            commit=False,
        )

        solar_devices.append(solar_device)

    db.commit()

    return solar_devices

def sync_solarman_plant_devices(
    db: Session,
    tenant_id: int,
    solar_plant: SolarPlant,
) -> list[SolarDevice]:
    from app.services.providers.solarman_provider import SolarmanProvider

    provider = SolarmanProvider(db)

    result = provider.get_station_devices(
        tenant_id=tenant_id,
        station_id=solar_plant.solarman_station_id,
        page=1,
        size=50,
    )

    devices = result.get("deviceListItems") or []

    return sync_solarman_station_devices(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant.id,
        devices=devices,
    )

def get_solar_devices_by_plant(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
) -> list[SolarDevice]:
    return (
        db.query(SolarDevice)
        .filter(
            SolarDevice.tenant_id == tenant_id,
            SolarDevice.solar_plant_id == solar_plant_id,
        )
        .order_by(SolarDevice.id)
        .all()
    )