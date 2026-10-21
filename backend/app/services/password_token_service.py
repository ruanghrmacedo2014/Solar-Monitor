from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.orm import Session

from app.models.password_token import PasswordToken


PASSWORD_SETUP = "PASSWORD_SETUP"
PASSWORD_RESET = "PASSWORD_RESET"

TOKEN_EXPIRE_MINUTES = 30


def create_password_token(
    db: Session,
    user_id: int,
    token_type: str,
    expire_minutes: int = TOKEN_EXPIRE_MINUTES,
) -> str:
    token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=expire_minutes)
    )

    password_token = PasswordToken(
        user_id=user_id,
        token=token,
        token_type=token_type,
        expires_at=expires_at,
        used=False,
    )

    db.add(password_token)
    db.commit()
    db.refresh(password_token)

    return token


def get_valid_password_token(
    db: Session,
    token: str,
    token_type: str,
) -> PasswordToken | None:
    password_token = (
        db.query(PasswordToken)
        .filter(
            PasswordToken.token == token,
            PasswordToken.token_type == token_type,
            PasswordToken.used.is_(False),
        )
        .first()
    )

    if password_token is None:
        return None

    now = datetime.now(timezone.utc)

    if password_token.expires_at <= now:
        return None

    return password_token


def mark_password_token_as_used(
    db: Session,
    password_token: PasswordToken,
) -> None:
    password_token.used = True

    db.commit()

def generate_temporary_password() -> str:
    return secrets.token_urlsafe(32)