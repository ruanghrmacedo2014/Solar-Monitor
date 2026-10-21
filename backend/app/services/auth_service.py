from sqlalchemy.orm import Session

from app.core.security.jwt import create_access_token
from app.core.security.password import verify_password
from app.services.user_service import get_user_by_email


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> str | None:
    user = get_user_by_email(
        db=db,
        email=email,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return create_access_token(user.id)