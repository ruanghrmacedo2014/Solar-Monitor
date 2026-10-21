from datetime import datetime, timezone

from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant
from app.services.performance_service import (
    calculate_plant_performance,
)


db = SessionLocal()

try:
    inicio = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    fim = datetime(
        2026,
        10,
        1,
        tzinfo=timezone.utc,
    )

    plantas = (
        db.query(SolarPlant)
        .filter(
            SolarPlant.tenant_id == 5,
            SolarPlant.is_active.is_(True),
        )
        .all()
    )

    encontrados = 0

    print(
        f"Total de plantas: {len(plantas)}"
    )

    for planta in plantas:
        try:
            resultado = calculate_plant_performance(
                db=db,
                tenant_id=5,
                solar_plant_id=planta.id,
                period_start=inicio,
                period_end=fim,
            )

            if resultado.data_quality == "SUFFICIENT_DATA":
                print(
                    f"PLANTA | "
                    f"id={planta.id} | "
                    f"nome={planta.name} | "
                    f"classificacao={resultado.classification} | "
                    f"performance={resultado.performance_percent} | "
                    f"cobertura={resultado.coverage_percent}"
                )
                print(
                    f"ALERTA ENCONTRADO | "
                    f"planta={planta.id} | "
                    f"nome={planta.name} | "
                    f"classificacao={resultado.classification} | "
                    f"performance={resultado.performance_percent} | "
                    f"cobertura={resultado.coverage_percent}"
                )

                encontrados += 1

                if encontrados >= 10:
                    break

        except ValueError:
            pass

    print(
        f"Total de alertas encontrados: {encontrados}"
    )

finally:
    db.close()