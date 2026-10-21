from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.tenant import TenantSelect
from app.api.routes.tenants import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserTenantResponse,
    CreatePasswordRequest,
)
from app.services.user_tenant_service import get_user_tenants_with_details
from app.services.auth_service import authenticate_user
from app.services.user_tenant_service import (
    get_user_tenants_with_details,
    user_has_tenant_access,
)
from app.core.security.jwt import create_access_token
from app.api.dependencies import (
    get_current_tenant,
    get_current_user,
)
from app.models.user import User
from app.services.password_setup_service import (
    create_password_from_setup_token,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    access_token = authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
    )

    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos.",
        )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "global_role": current_user.global_role,
    }

@router.get(
    "/me/tenants",
    response_model=list[UserTenantResponse],
)
def get_my_tenants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    associations = get_user_tenants_with_details(
        db=db,
        user_id=current_user.id,
    )

    return [
        {
            "tenant_id": association.tenant_id,
            "tenant_name": association.name,
            "role": association.role.value,
        }
        for association in associations
    ]

@router.post("/select-tenant")
def select_tenant(
    tenant_data: TenantSelect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    association = user_has_tenant_access(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_data.tenant_id,
    )

    if association is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário não possui acesso a esta empresa.",
        )

    tenant_access_token = create_access_token(
        user_id=current_user.id,
        tenant_id=association.tenant_id,
        role=association.role.value,
    )

    return {
        "access_token": tenant_access_token,
        "token_type": "bearer",
        "tenant_id": association.tenant_id,
        "role": association.role.value,
    }

@router.get("/me/tenant")
def get_current_tenant_info(
    tenant_access=Depends(get_current_tenant),
):
    return {
        "tenant_id": tenant_access.tenant_id,
        "role": tenant_access.role.value,
        "is_active": tenant_access.is_active,
    }

@router.post("/create-password")
def create_password(
    password_data: CreatePasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        user = create_password_from_setup_token(
            db=db,
            token=password_data.token,
            password=password_data.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Token inválido ou expirado.",
        )

    return {
        "message": "Senha criada com sucesso.",
    }