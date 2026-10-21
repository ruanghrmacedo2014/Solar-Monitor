from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_access_token(
    user_id: int,
    tenant_id: int | None = None,
    role: str | None = None,
    platform_context: bool = False,
) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    if tenant_id is not None:
        payload["tenant_id"] = tenant_id

    if role is not None:
        payload["role"] = role

    if platform_context:
        payload["platform_context"] = True

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    user_id = payload.get("sub")

    if user_id is None:
        raise ValueError("Token não contém o usuário.")

    return {
        "user_id": int(user_id),
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role"),
        "platform_context": payload.get("platform_context", False),
    }