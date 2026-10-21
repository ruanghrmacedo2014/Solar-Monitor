from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import (
    get_current_user,
    get_current_tenant,
)
from app.services.notification_service import NotificationService


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/")
def list_notifications(
    only_unread: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = NotificationService(db=db)

    notifications = service.list_user_notifications(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        only_unread=only_unread,
    )

    return notifications


@router.patch("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = NotificationService(db=db)

    notification = service.mark_as_read(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        notification_id=notification_id,
    )

    if notification is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Notificação não encontrada.",
        )

    return notification