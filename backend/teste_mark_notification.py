from app.api.database import SessionLocal
from app.services.notification_service import NotificationService


db = SessionLocal()

try:
    service = NotificationService(db=db)

    notification = service.mark_as_read(
        tenant_id=5,
        user_id=5,
        notification_id=3,
    )

    if notification is None:
        print("NOTIFICAÇÃO NÃO ENCONTRADA")
    else:
        print("NOTIFICAÇÃO MARCADA COMO LIDA")
        print("ID:", notification.id)
        print("USER:", notification.user_id)
        print("IS_READ:", notification.is_read)
        print("READ_AT:", notification.read_at)

finally:
    db.close()