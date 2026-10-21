from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationService:

    def __init__(self, db: Session):
        self.db = db

    def has_recent_notification(
        self,
        tenant_id: int,
        user_id: int,
        category: str,
        solar_plant_id: int | None = None,
        hours: int = 24,
    ) -> bool:
        from datetime import timedelta

        from sqlalchemy import select

        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(hours=hours)
        )

        statement = (
            select(Notification.id)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.category == category,
                Notification.created_at >= cutoff,
            )
        )

        if solar_plant_id is not None:
            statement = statement.where(
                Notification.solar_plant_id == solar_plant_id
            )

        return self.db.scalar(statement) is not None

    def create_notification(
        self,
        tenant_id: int,
        user_id: int,
        category: str,
        title: str,
        message: str,
        severity: str = "INFO",
        customer_id: int | None = None,
        solar_plant_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            customer_id=customer_id,
            solar_plant_id=solar_plant_id,
            category=category,
            title=title,
            message=message,
            severity=severity,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        return notification

    def get_users_by_roles(
        self,
        tenant_id: int,
        roles: list[str],
    ) -> list[int]:
        from sqlalchemy import select

        from app.models.user_tenant import UserTenant

        statement = (
            select(UserTenant.user_id)
            .where(
                UserTenant.tenant_id == tenant_id,
                UserTenant.role.in_(roles),
            )
        )

        return list(self.db.scalars(statement).all())

    def create_notification_for_users(
        self,
        tenant_id: int,
        user_ids: list[int],
        category: str,
        title: str,
        message: str,
        severity: str = "INFO",
        customer_id: int | None = None,
        solar_plant_id: int | None = None,
    ) -> list[Notification]:
        notifications = []

        for user_id in user_ids:
            if self.has_recent_notification(
                tenant_id=tenant_id,
                user_id=user_id,
                category=category,
                solar_plant_id=solar_plant_id,
                hours=24,
            ):
                continue

            notification = self.create_notification(
                tenant_id=tenant_id,
                user_id=user_id,
                category=category,
                title=title,
                message=message,
                severity=severity,
                customer_id=customer_id,
                solar_plant_id=solar_plant_id,
            )

            notifications.append(notification)

        return notifications

    def list_user_notifications(
        self,
        tenant_id: int,
        user_id: int,
        only_unread: bool = False,
    ) -> list[Notification]:
        from sqlalchemy import select

        statement = (
            select(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
            )
            .order_by(Notification.created_at.desc())
        )

        if only_unread:
            statement = statement.where(
                Notification.is_read.is_(False)
            )

        return list(self.db.scalars(statement).all())

    def mark_as_read(
        self,
        tenant_id: int,
        user_id: int,
        notification_id: int,
    ) -> Notification | None:
        from sqlalchemy import select

        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
        )

        notification = self.db.scalar(statement)

        if notification is None:
            return None

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(notification)

        return notification