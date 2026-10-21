from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.api.database import SessionLocal
from app.models.solar_plant import SolarPlant
from app.services.performance_notification_service import (
    PerformanceNotificationService,
)


def run_daily_performance_notification_check() -> None:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        period_start = (
            now - timedelta(days=1)
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        period_end = period_start + timedelta(days=1)

        plants = db.scalars(
            select(SolarPlant)
            .where(
                SolarPlant.is_active.is_(True),
            )
        ).all()

        service = PerformanceNotificationService(db=db)

        for plant in plants:
            try:
                service.check_plant_performance(
                    tenant_id=plant.tenant_id,
                    solar_plant_id=plant.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            except Exception as exc:
                db.rollback()

                print(
                    f"Erro na verificação de performance | "
                    f"tenant={plant.tenant_id} | "
                    f"planta={plant.id} | "
                    f"erro={exc}"
                )

        print(
            "Verificação diária de performance concluída | "
            f"período={period_start.isoformat()} "
            f"até {period_end.isoformat()}"
        )

    finally:
        db.close()