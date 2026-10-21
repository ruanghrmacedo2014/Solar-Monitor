from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import require_tenant_roles
from app.core.permissions.roles import TenantRole
from app.schemas.tag import TagResponse
from app.schemas.ticket_tag import (
    TicketTagCreate,
    TicketTagResponse,
)
from app.services.ticket_tag_service import TicketTagService


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Tags"],
)


@router.post(
    "/{ticket_id}/tags",
    response_model=TicketTagResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_tag_to_ticket(
    ticket_id: int,
    data: TicketTagCreate,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
        )
    ),
    db: Session = Depends(get_db),
):
    service = TicketTagService(db)

    try:
        return service.add_tag_to_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            tag_id=data.tag_id,
        )
    except ValueError as exc:
        detail = str(exc)

        if "já está associada" in detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


@router.get(
    "/{ticket_id}/tags",
    response_model=list[TagResponse],
)
def list_ticket_tags(
    ticket_id: int,
    tenant_access=Depends(
        require_tenant_roles(
            TenantRole.TENANT_ADMIN,
            TenantRole.OPERATOR,
            TenantRole.TECHNICIAN,
            TenantRole.CUSTOMER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = TicketTagService(db)

    try:
        return service.list_ticket_tags(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete(
    "/{ticket_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_tag_from_ticket(
    ticket_id: int,
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
    service = TicketTagService(db)

    removed = service.remove_tag_from_ticket(
        tenant_id=tenant_access.tenant_id,
        ticket_id=ticket_id,
        tag_id=tag_id,
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag não está associada a este ticket.",
        )

    return None