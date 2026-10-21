from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.services.generation_service import (
    GenerationBatchSyncResult,
    GenerationService,
)


SYNC_WINDOW_HOURS = 48


def sync_tenant_generation(
    db: Session,
    tenant_id: int,
    window_hours: int = SYNC_WINDOW_HOURS,
) -> GenerationBatchSyncResult:
    """
    Sincroniza a geração recente de todas as plantas Solarman
    ativas de um tenant.
    """

    if window_hours <= 0:
        raise ValueError(
            "A janela de sincronização deve ser maior que zero."
        )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=window_hours)

    service = GenerationService(db=db)

    return service.sync_solarman_tenant_generation(
        tenant_id=tenant_id,
        start_time=start_time.strftime("%Y-%m-%d"),
        end_time=end_time.strftime("%Y-%m-%d"),
    )