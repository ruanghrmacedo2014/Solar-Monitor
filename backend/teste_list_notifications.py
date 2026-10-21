from app.api.database import SessionLocal
from app.services.notification_service import NotificationService


db = SessionLocal()

try:
    service = NotificationService(db=db)

    notifications = service.list_user_notifications(
        tenant_id=5,
        user_id=5,
    )

    print("NOTIFICAÇÕES DO USUÁRIO 5:")

    for notification in notifications:
        print(
            f"ID={notification.id} | "
            f"CATEGORY={notification.category} | "
            f"TITLE={notification.title} | "
            f"IS_READ={notification.is_read}"
        )

finally:
    db.close()