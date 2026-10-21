from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.password import hash_password
from app.models.user import User
from app.services.email_service import send_email
from app.services.password_token_service import (
    PASSWORD_SETUP,
    create_password_token,
    get_valid_password_token,
    mark_password_token_as_used,
)


def send_password_setup_email(
    db: Session,
    user: User,
) -> None:
    token = create_password_token(
        db=db,
        user_id=user.id,
        token_type=PASSWORD_SETUP,
    )

    setup_url = (
        f"{settings.frontend_url}/create-password"
        f"?token={token}"
    )

    send_email(
        to_email=user.email,
        subject="Crie sua senha - Solar Monitor",
        body=(
            f"Olá, {user.name}!\n\n"
            "Seu acesso ao Solar Monitor foi criado.\n\n"
            "Para definir sua senha, acesse o link abaixo:\n\n"
            f"{setup_url}\n\n"
            "Este link é temporário e pode ser usado uma única vez.\n\n"
            "Se você não esperava este e-mail, ignore esta mensagem.\n\n"
            "Equipe Solar Monitor"
        ),
    )


def create_password_from_setup_token(
    db: Session,
    token: str,
    password: str,
) -> User | None:
    if len(password) < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    password_token = get_valid_password_token(
        db=db,
        token=token,
        token_type=PASSWORD_SETUP,
    )

    if password_token is None:
        return None

    user = db.get(User, password_token.user_id)

    if user is None:
        return None

    user.password_hash = hash_password(password)

    mark_password_token_as_used(
        db=db,
        password_token=password_token,
    )

    db.commit()
    db.refresh(user)

    return user