from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.api.database import SessionLocal
from app.models.tenant_integration import (
    IntegrationProvider,
    TenantIntegration,
)
from app.services.generation_service import GenerationService


def run_daily_generation_sync() -> None:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        start_time = now - timedelta(days=1)
        end_time = now

        tenant_ids = db.scalars(
            select(TenantIntegration.tenant_id)
            .where(
                TenantIntegration.provider == IntegrationProvider.SOLARMAN,
                TenantIntegration.is_active.is_(True),
            )
            .distinct()
        ).all()

        for tenant_id in tenant_ids:
            try:
                service = GenerationService(db=db)

                result = service.sync_solarman_tenant_generation(
                    tenant_id=tenant_id,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                )

                print(
                    f"Sync diário tenant={tenant_id} | "
                    f"sucesso={result.successful_plants} | "
                    f"falhas={result.failed_plants} | "
                    f"registros={result.total_records_saved}"
                )

            except Exception as exc:
                db.rollback()

                print(
                    f"Erro no sync diário tenant={tenant_id}: {exc}"
                )

    finally:
        db.close()