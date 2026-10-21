from datetime import datetime

from sqlalchemy.orm import Session

from app.models.solar_plant import SolarPlant
from app.services.notification_service import NotificationService
from app.services.performance_service import (
    calculate_plant_performance,
)
from app.models.customer import Customer
from app.models.user_tenant import UserTenant
from sqlalchemy import select
from sqlalchemy.orm import Session

class PerformanceNotificationService:

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db=db)

    def check_plant_performance(
        self,
        tenant_id: int,
        solar_plant_id: int,
        period_start: datetime,
        period_end: datetime,
    ) -> None:
        try:
            performance = calculate_plant_performance(
                db=self.db,
                tenant_id=tenant_id,
                solar_plant_id=solar_plant_id,
                period_start=period_start,
                period_end=period_end,
            )
        except ValueError as exc:
            print(
                f"Performance não calculada | "
                f"planta={solar_plant_id} | "
                f"motivo={exc}"
            )
            return

        if performance.classification not in (
            "BELOW_EXPECTED",
            "SIGNIFICANTLY_BELOW_EXPECTED",
        ):
            return

        plant = self.db.get(
            SolarPlant,
            solar_plant_id,
        )

        if plant is None:
            return

        user_ids = self.notification_service.get_users_by_roles(
            tenant_id=tenant_id,
            roles=[
                "TENANT_ADMIN",
                "OPERATOR",
                "TECHNICIAN",
            ],
        )

        customer = self.db.get(
            Customer,
            plant.customer_id,
        )

        if customer is not None and customer.user_id is not None:
            customer_membership = self.db.scalar(
                select(UserTenant).where(
                    UserTenant.tenant_id == tenant_id,
                    UserTenant.user_id == customer.user_id,
                    UserTenant.role == "CUSTOMER",
                )
            )

            if customer_membership is not None:
                user_ids.append(customer.user_id)

        user_ids = list(set(user_ids))

        if not user_ids:
            print(
                f"Nenhum destinatário encontrado | "
                f"tenant={tenant_id}"
            )
            return

        severity = (
            "WARNING"
            if performance.classification == "BELOW_EXPECTED"
            else "CRITICAL"
        )

        self.notification_service.create_notification_for_users(
            tenant_id=tenant_id,
            user_ids=user_ids,
            category="PERFORMANCE",
            title=f"Baixa performance - {plant.name}",
            message=(
                f"A planta {plant.name} apresentou "
                f"{performance.performance_percent:.2f}% "
                f"da geração esperada no período."
            ),
            severity=severity,
            customer_id=plant.customer_id,
            solar_plant_id=plant.id,
        )