from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.customer import Customer
from app.models.solar_plant import SolarPlant
from datetime import datetime, timezone


def create_solar_plant(
    db: Session,
    tenant_id: int,
    solarman_station_id: int,
    name: str,
    installed_power: float | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    plant_type: str | None = None,
    grid_interconnection_type: str | None = None,
    start_operating_at=None,
    owner_name: str | None = None,
    contact_phone: str | None = None,
) -> SolarPlant:
    solar_plant = SolarPlant(
        tenant_id=tenant_id,
        solarman_station_id=solarman_station_id,
        name=name.strip(),
        installed_power=installed_power,
        address=address.strip() if address else None,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        plant_type=plant_type,
        grid_interconnection_type=grid_interconnection_type,
        start_operating_at=start_operating_at,
        owner_name=owner_name.strip() if owner_name else None,
        contact_phone=contact_phone.strip() if contact_phone else None,
    )

    db.add(solar_plant)
    db.commit()
    db.refresh(solar_plant)

    return solar_plant

def get_solar_plants_by_tenant(
    db: Session,
    tenant_id: int,
) -> list[SolarPlant]:
    statement = (
        select(SolarPlant)
        .where(
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.is_active.is_(True),
        )
        .order_by(SolarPlant.name)
    )

    return list(db.scalars(statement).all())

def get_solar_plant_by_id(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
) -> SolarPlant | None:
    statement = (
        select(SolarPlant)
        .where(
            SolarPlant.id == solar_plant_id,
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.is_active.is_(True),
        )
    )

    return db.scalar(statement)

def link_solar_plant_to_customer(
    db: Session,
    tenant_id: int,
    solar_plant_id: int,
    customer_id: int,
) -> SolarPlant:
    solar_plant = get_solar_plant_by_id(
        db=db,
        tenant_id=tenant_id,
        solar_plant_id=solar_plant_id,
    )

    if solar_plant is None:
        raise ValueError("Planta solar não encontrada.")

    statement = (
        select(Customer)
        .where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
            Customer.is_active.is_(True),
        )
    )

    customer = db.scalar(statement)

    if customer is None:
        raise ValueError("Cliente não encontrado.")

    solar_plant.customer_id = customer.id

    db.commit()
    db.refresh(solar_plant)

    return solar_plant

def get_solar_plants_by_customer(
    db: Session,
    tenant_id: int,
    customer_id: int,
) -> list[SolarPlant]:
    statement = (
        select(SolarPlant)
        .where(
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.customer_id == customer_id,
            SolarPlant.is_active.is_(True),
        )
        .order_by(SolarPlant.name)
    )

    return list(db.scalars(statement).all())

def map_solarman_station_to_plant(
    tenant_id: int,
    station: dict,
) -> dict:
    start_operating_at = station.get("startOperatingTime")

    if start_operating_at is not None:
        start_operating_at = datetime.fromtimestamp(
            float(start_operating_at),
            tz=timezone.utc,
        )

    return {
        "tenant_id": tenant_id,
        "solarman_station_id": station["id"],
        "name": station["name"],
        "installed_power": station.get("installedCapacity"),
        "address": station.get("locationAddress"),
        "latitude": station.get("locationLat"),
        "longitude": station.get("locationLng"),
        "timezone": station.get("regionTimezone"),
        "plant_type": station.get("type"),
        "grid_interconnection_type": station.get(
            "gridInterconnectionType"
        ),
        "start_operating_at": start_operating_at,
        "owner_name": station.get("ownerName"),
        "contact_phone": station.get("contactPhone"),
        "source_provider": "SOLARMAN",
        "is_active": True,
    }

def upsert_solarman_station(
    db: Session,
    tenant_id: int,
    station: dict,
    commit: bool = True,
) -> SolarPlant:
    plant_data = map_solarman_station_to_plant(
        tenant_id=tenant_id,
        station=station,
    )

    plant = (
        db.query(SolarPlant)
        .filter(
            SolarPlant.tenant_id == tenant_id,
            SolarPlant.solarman_station_id
            == plant_data["solarman_station_id"],
        )
        .first()
    )

    if plant is None:
        plant = SolarPlant(**plant_data)
        db.add(plant)
    else:
        for field, value in plant_data.items():
            if field == "tenant_id":
                continue

            setattr(plant, field, value)

    if commit:
        db.commit()
        db.refresh(plant)

    return plant

def sync_solarman_station_page(
    db: Session,
    tenant_id: int,
    stations: list[dict],
) -> list[SolarPlant]:
    plants = []

    for station in stations:
        plant = upsert_solarman_station(
            db=db,
            tenant_id=tenant_id,
            station=station,
            commit=False,
        )
        plants.append(plant)

    db.commit()

    return plants

def sync_all_solarman_stations(
    db: Session,
    tenant_id: int,
    page_size: int = 50,
) -> list[SolarPlant]:
    from app.services.providers.solarman_provider import SolarmanProvider

    provider = SolarmanProvider(db)

    first_page = provider.get_station_list(
        tenant_id=tenant_id,
        page=1,
        size=page_size,
    )

    total = first_page.get("total", 0)
    stations = first_page.get("stationList") or []

    plants = sync_solarman_station_page(
        db=db,
        tenant_id=tenant_id,
        stations=stations,
    )

    if not total:
        return plants

    total_pages = (total + page_size - 1) // page_size

    for page in range(2, total_pages + 1):
        result = provider.get_station_list(
            tenant_id=tenant_id,
            page=page,
            size=page_size,
        )

        stations = result.get("stationList") or []

        page_plants = sync_solarman_station_page(
            db=db,
            tenant_id=tenant_id,
            stations=stations,
        )

        plants.extend(page_plants)

    return plants

def sync_all_solarman_devices(
    db: Session,
    tenant_id: int,
    page_size: int = 50,
) -> dict:
    from app.services.providers.solarman_provider import SolarmanProvider
    from app.services.solar_device_service import sync_solarman_plant_devices

    provider = SolarmanProvider(db)

    first_page = provider.get_station_list(
        tenant_id=tenant_id,
        page=1,
        size=page_size,
    )

    total = first_page.get("total", 0)
    stations = first_page.get("stationList") or []

    total_devices = 0
    successful_stations = 0
    failed_stations = []

    def process_stations(stations: list[dict], start_number: int) -> None:
        nonlocal total_devices, successful_stations

        for index, station in enumerate(stations, start=start_number):
            station_id = station["id"]

            print(
                f"[{index}/{total}] "
                f"Sincronizando station {station_id}..."
            )

            try:
                plant = (
                    db.query(SolarPlant)
                    .filter(
                        SolarPlant.tenant_id == tenant_id,
                        SolarPlant.solarman_station_id == station_id,
                    )
                    .first()
                )

                if plant is None:
                    plant = upsert_solarman_station(
                        db=db,
                        tenant_id=tenant_id,
                        station=station,
                    )

                devices = sync_solarman_plant_devices(
                    db=db,
                    tenant_id=tenant_id,
                    solar_plant=plant,
                )

                total_devices += len(devices)
                successful_stations += 1

                if devices:
                    print(
                        f"[OK] Station {station_id}: "
                        f"{len(devices)} devices"
                    )
                else:
                    print(
                        f"[INFO] Station {station_id}: "
                        f"nenhum device encontrado"
                    )

            except Exception as exc:
                failed_stations.append(
                    {
                        "station_id": station_id,
                        "error": str(exc),
                    }
                )

                print(
                    f"[ERRO] Station {station_id}: {exc}"
                )

    process_stations(
        stations=stations,
        start_number=1,
    )

    if total:
        total_pages = (total + page_size - 1) // page_size

        for page in range(2, total_pages + 1):
            result = provider.get_station_list(
                tenant_id=tenant_id,
                page=page,
                size=page_size,
            )

            stations = result.get("stationList") or []

            process_stations(
                stations=stations,
                start_number=(page - 1) * page_size + 1,
            )

    print()
    print("========================================")
    print("Sincronização de devices concluída")
    print("========================================")
    print(f"Stations encontradas: {total}")
    print(f"Stations processadas: {successful_stations}")
    print(f"Stations com erro: {len(failed_stations)}")
    print(f"Devices sincronizados: {total_devices}")

    if failed_stations:
        print()
        print("Stations com erro:")

        for item in failed_stations:
            print(
                f"- {item['station_id']}: "
                f"{item['error']}"
            )

    return {
        "total_stations": total,
        "successful_stations": successful_stations,
        "failed_stations": failed_stations,
        "total_devices": total_devices,
    }