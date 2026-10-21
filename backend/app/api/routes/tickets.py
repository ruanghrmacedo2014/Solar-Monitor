from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.dependencies import (
    get_current_tenant,
    get_current_user,
    require_tenant_roles,
)
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketMessageUpdate,
    TicketResponse,
    TicketUpdate,
    MentionableUserResponse,
)
from app.models.user_tenant import UserTenant
from app.services.ticket_service import TicketService
from app.services.ticket_message_service import TicketMessageService
from fastapi import File, UploadFile
from app.schemas.ticket import TicketAttachmentResponse
from app.services.ticket_attachment_service import (
    TicketAttachmentService,
)
from pathlib import Path
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    try:
        return service.create_ticket(
            tenant_id=tenant_access.tenant_id,
            created_by_user_id=current_user.id,
            data=data,
            is_customer=is_customer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

@router.get(
    "",
    response_model=list[TicketResponse],
)
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    return service.list_tickets(
        tenant_id=tenant_access.tenant_id,
        user_id=current_user.id,
        is_customer=is_customer,
    )

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    ticket = service.get_ticket(
        tenant_id=tenant_access.tenant_id,
        ticket_id=ticket_id,
        user_id=current_user.id,
        is_customer=is_customer,
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    return ticket

@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    try:
        ticket = service.update_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            data=data,
            user_id=current_user.id,
            is_customer=is_customer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    return ticket

@router.post(
    "/{ticket_id}/claim",
    response_model=TicketResponse,
)
def claim_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
        )
    ),
):
    service = TicketService(db)

    try:
        ticket = service.claim_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    return ticket

@router.post(
    "/{ticket_id}/unclaim",
    response_model=TicketResponse,
)
def unclaim_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
        )
    ),
):
    service = TicketService(db)

    try:
        ticket = service.unclaim_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    return ticket

@router.post(
    "/{ticket_id}/reassign",
    response_model=TicketResponse,
)
def reassign_ticket(
    ticket_id: int,
    new_owner_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(
        require_tenant_roles(
            "TENANT_ADMIN",
            "OPERATOR",
            "TECHNICIAN",
        )
    ),
):
    service = TicketService(db)

    try:
        ticket = service.reassign_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            current_user_id=current_user.id,
            new_owner_user_id=new_owner_user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    return ticket

@router.get(
    "/{ticket_id}/mentionable-users",
    response_model=list[MentionableUserResponse],
)
def list_mentionable_users(
    ticket_id: int,
    q: str = "",
    db: Session = Depends(get_db),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketService(db)

    try:
        ticket = service.get_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=tenant_access.user_id,
            is_customer=tenant_access.role == "CUSTOMER",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    query = q.strip()

    if len(query) < 2:
        return []

    mentionable_query = (
        db.query(User)
        .join(
            UserTenant,
            UserTenant.user_id == User.id,
        )
        .filter(
            UserTenant.tenant_id == tenant_access.tenant_id,
            User.is_active.is_(True),
            UserTenant.is_active.is_(True),
            User.name.ilike(f"%{query}%"),
        )
    )

    if tenant_access.role == "CUSTOMER":
        mentionable_query = mentionable_query.filter(
            UserTenant.role != "CUSTOMER",
        )

    users = (
        mentionable_query
        .order_by(User.name.asc())
        .limit(10)
        .all()
    )

    return users

@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_message(
    ticket_id: int,
    data: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketMessageService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    try:
        return service.create_message(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            author_user_id=current_user.id,
            data=data,
            is_customer=is_customer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.get(
    "/{ticket_id}/messages",
    response_model=list[TicketMessageResponse],
)
def list_ticket_messages(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketMessageService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    try:
        return service.list_messages(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=current_user.id,
            is_customer=is_customer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

@router.patch(
    "/{ticket_id}/messages/{message_id}",
    response_model=TicketMessageResponse,
)
def update_ticket_message(
    ticket_id: int,
    message_id: int,
    data: TicketMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketMessageService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    try:
        message = service.update_message(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            message_id=message_id,
            user_id=current_user.id,
            data=data,
            is_customer=is_customer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensagem não encontrada.",
        )

    return message

@router.delete(
    "/{ticket_id}/messages/{message_id}",
    response_model=TicketMessageResponse,
)
def delete_ticket_message(
    ticket_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketMessageService(db)

    is_customer = tenant_access.role == "CUSTOMER"

    try:
        message = service.delete_message(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            message_id=message_id,
            user_id=current_user.id,
            is_customer=is_customer,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensagem não encontrada.",
        )

    return message

@router.post(
    "/{ticket_id}/attachments",
    response_model=TicketAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_ticket_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant_access=Depends(get_current_tenant),
):
    service = TicketAttachmentService(db)

    if tenant_access.role == "CUSTOMER":
        try:
            ticket_service = TicketService(db)

            ticket = ticket_service.get_ticket(
                tenant_id=tenant_access.tenant_id,
                ticket_id=ticket_id,
                user_id=tenant_access.user_id,
                is_customer=True,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            )

        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket não encontrado.",
            )

        if ticket.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cliente não pode adicionar anexo a este ticket.",
            )

    try:
        content = file.file.read()

        attachment = service.create_attachment(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            uploaded_by_user_id=tenant_access.user_id,
            filename=file.filename or "arquivo",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )

        return attachment

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.get(
    "/{ticket_id}/attachments/{attachment_id}/download",
)
def download_ticket_attachment(
    ticket_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    tenant_access=Depends(get_current_tenant),
):
    attachment_service = TicketAttachmentService(db)

    attachment = attachment_service.get_attachment(
        tenant_id=tenant_access.tenant_id,
        ticket_id=ticket_id,
        attachment_id=attachment_id,
    )

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado.",
        )

    ticket_service = TicketService(db)

    try:
        ticket = ticket_service.get_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=tenant_access.user_id,
            is_customer=tenant_access.role == "CUSTOMER",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    file_path = Path(attachment.storage_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico do anexo não encontrado.",
        )

    return FileResponse(
        path=file_path,
        media_type=attachment.content_type,
        filename=attachment.original_filename,
    )

@router.get(
    "/{ticket_id}/attachments",
    response_model=list[TicketAttachmentResponse],
)
def list_ticket_attachments(
    ticket_id: int,
    db: Session = Depends(get_db),
    tenant_access=Depends(get_current_tenant),
):
    ticket_service = TicketService(db)

    try:
        ticket = ticket_service.get_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=tenant_access.user_id,
            is_customer=tenant_access.role == "CUSTOMER",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    attachment_service = TicketAttachmentService(db)

    return attachment_service.list_attachments(
        tenant_id=tenant_access.tenant_id,
        ticket_id=ticket_id,
    )

@router.delete(
    "/{ticket_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_attachment(
    ticket_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    tenant_access=Depends(get_current_tenant),
):
    ticket_service = TicketService(db)

    try:
        ticket = ticket_service.get_ticket(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            user_id=tenant_access.user_id,
            is_customer=tenant_access.role == "CUSTOMER",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket não encontrado.",
        )

    if tenant_access.role == "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente não pode remover anexos.",
        )

    attachment_service = TicketAttachmentService(db)

    try:
        attachment = attachment_service.delete_attachment(
            tenant_id=tenant_access.tenant_id,
            ticket_id=ticket_id,
            attachment_id=attachment_id,
            user_id=tenant_access.user_id,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível remover o anexo.",
        )

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado.",
        )

    return None