from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.core.security.jwt import decode_access_token
from app.services.user_service import get_user_by_id
from app.services.user_tenant_service import user_has_tenant_access
from app.core.permissions.roles import CUSTOMER_CREATE_ROLES
from app.models.user import GlobalRole
from types import SimpleNamespace

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        token_data = decode_access_token(
            credentials.credentials
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    user = get_user_by_id(
        db=db,
        user_id=token_data["user_id"],
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo.",
        )

    return user

def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        token_data = decode_access_token(
            credentials.credentials
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    tenant_id = token_data.get("tenant_id")

    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nenhuma empresa foi selecionada.",
        )

    user = get_user_by_id(
        db=db,
        user_id=token_data["user_id"],
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inválido ou inativo.",
        )

    if (
        user.global_role == GlobalRole.PLATFORM_ADMIN
        and token_data.get("platform_context") is True
    ):
        return SimpleNamespace(
            tenant_id=tenant_id,
            role=GlobalRole.PLATFORM_ADMIN,
            is_active=True,
            is_platform_admin=True,
        )

    association = user_has_tenant_access(
        db=db,
        user_id=user.id,
        tenant_id=tenant_id,
    )

    if association is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não possui acesso a esta empresa.",
        )

    return association

def require_tenant_roles(*allowed_roles):
    def role_checker(
        tenant_access=Depends(get_current_tenant),
    ):
        if getattr(
            tenant_access,
            "is_platform_admin",
            False,
        ):
            return tenant_access

        if tenant_access.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não possui permissão para esta operação.",
            )

        return tenant_access

    return role_checker

def require_platform_admin(
    current_user=Depends(get_current_user),
):
    if current_user.global_role != GlobalRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao administrador da plataforma.",
        )

    return current_user