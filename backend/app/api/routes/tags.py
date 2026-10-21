from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.core.permissions.roles import TenantRole
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import TagService


router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tag(
    data: TagCreate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = TagService(db)

    try:
        return service.create_tag(
            tenant_id=tenant_access.tenant_id,
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[TagResponse],
)
def list_tags(
    include_inactive: bool = False,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = TagService(db)

    return service.list_tags(
        tenant_id=tenant_access.tenant_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
)
def get_tag(
    tag_id: int,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = TagService(db)

    tag = service.get_tag(
        tenant_id=tenant_access.tenant_id,
        tag_id=tag_id,
    )

    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag não encontrada.",
        )

    return tag


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = TagService(db)

    try:
        tag = service.update_tag(
            tenant_id=tenant_access.tenant_id,
            tag_id=tag_id,
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag não encontrada.",
        )

    return tag