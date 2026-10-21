from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.core.permissions.roles import USER_CREATE_ROLES
from app.models.user_tenant import UserTenant
from app.schemas.user import UserCreate
from app.services.user_service import create_user


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/")
def create_user_endpoint(
    user_data: UserCreate,
    tenant_access: UserTenant = Depends(
        require_tenant_roles(*USER_CREATE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    user = create_user(
        db=db,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
    )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active,
        "global_role": user.global_role,
    }