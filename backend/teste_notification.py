from app.api.database import SessionLocal
from app.services.notification_service import NotificationService


db = SessionLocal()

try:
    service = NotificationService(db=db)

    notification = service.create_notification(
        tenant_id=5,
        user_id=8,
        category="SYSTEM",
        title="Teste de notificação",
        message="Esta é uma notificação de teste do Solar Monitor.",
        severity="INFO",
    )

    print("NOTIFICAÇÃO CRIADA")
    print("ID:", notification.id)
    print("TENANT:", notification.tenant_id)
    print("USER:", notification.user_id)
    print("CATEGORY:", notification.category)
    print("TITLE:", notification.title)
    print("IS_READ:", notification.is_read)

finally:
    db.close()