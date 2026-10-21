from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant
from app.models.generation_record import GenerationRecord
from app.services.providers.solarman_provider import SolarmanProvider
from sqlalchemy import exists


db = SessionLocal()
provider = SolarmanProvider(db)

plants = (
    db.query(SolarPlant)
    .filter(
        SolarPlant.tenant_id == 5,
        SolarPlant.is_active.is_(True),
        SolarPlant.source_provider == "SOLARMAN",
        ~exists().where(
            (GenerationRecord.solar_plant_id == SolarPlant.id)
            & (GenerationRecord.tenant_id == 5)
        ),
    )
    .order_by(SolarPlant.id)
    .all()
)

print("Plantas sem geração no banco:", len(plants))
print()

com_dados = []
sem_dados = []
falhas = []

for plant in plants:
    try:
        result = provider.get_station_history(
            tenant_id=5,
            station_id=plant.solarman_station_id,
            start_time="2026-09-28",
            end_time="2026-09-28",
            time_type=1,
        )

        total = result.get("total") or 0

        if total > 0:
            com_dados.append(
                (
                    plant.id,
                    plant.solarman_station_id,
                    plant.name,
                    total,
                )
            )
        else:
            sem_dados.append(
                (
                    plant.id,
                    plant.solarman_station_id,
                    plant.name,
                )
            )

    except Exception as exc:
        falhas.append(
            (
                plant.id,
                plant.solarman_station_id,
                plant.name,
                str(exc),
            )
        )

print("COM DADOS EM 28/09:", len(com_dados))

for item in com_dados:
    print(
        "Planta=",
        item[0],
        "| Station=",
        item[1],
        "| Total=",
        item[3],
        "| Nome=",
        item[2],
    )

print()
print("SEM DADOS EM 28/09:", len(sem_dados))

for item in sem_dados:
    print(
        "Planta=",
        item[0],
        "| Station=",
        item[1],
        "| Nome=",
        item[2],
    )

print()
print("FALHAS NA CONSULTA:", len(falhas))

for item in falhas:
    print(
        "Planta=",
        item[0],
        "| Station=",
        item[1],
        "| Nome=",
        item[2],
        "| Erro=",
        item[3],
    )

db.close()