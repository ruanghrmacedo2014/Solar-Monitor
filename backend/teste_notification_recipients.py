from app.api.database import SessionLocal
from app.services.notification_service import NotificationService


db = SessionLocal()

try:
    service = NotificationService(db=db)

    user_ids = service.get_users_by_roles(
        tenant_id=5,
        roles=[
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
        ],
    )

    notifications = service.create_notification_for_users(
        tenant_id=5,
        user_ids=user_ids,
        category="PERFORMANCE",
        title="Teste de alerta de performance",
        message="Esta é uma notificação de teste enviada para os usuários responsáveis pela operação.",
        severity="WARNING",
    )

    print("NOTIFICAÇÕES CRIADAS:")

    for notification in notifications:
        print(
            f"ID={notification.id} | "
            f"USER={notification.user_id} | "
            f"CATEGORY={notification.category} | "
            f"IS_READ={notification.is_read}"
        )

finally:
    db.close()