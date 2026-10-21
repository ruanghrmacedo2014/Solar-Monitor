from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security.password import hash_password
from app.models.user import User


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
) -> User:
    user = User(
        name=name,
        email=email.strip().lower(),
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    statement = select(User).where(
        User.email == email.strip().lower()
    )

    return db.scalar(statement)

def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    statement = select(User).where(
        User.id == user_id
    )

    return db.scalar(statement)