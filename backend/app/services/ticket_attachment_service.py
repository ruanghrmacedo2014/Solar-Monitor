from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.services.ticket_attachment_storage_service import (
    TicketAttachmentStorageService,
)
from app.services.ticket_attachment_validation_service import (
    TicketAttachmentValidationService,
)
from app.services.ticket_history_service import TicketHistoryService


class TicketAttachmentService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = TicketAttachmentStorageService()
        self.validation = TicketAttachmentValidationService()

    def create_attachment(
        self,
        tenant_id: int,
        ticket_id: int,
        uploaded_by_user_id: int,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> TicketAttachment:
        ticket = (
            self.db.query(Ticket)
            .filter(
                Ticket.id == ticket_id,
                Ticket.tenant_id == tenant_id,
            )
            .first()
        )

        if ticket is None:
            raise ValueError(
                "Ticket não encontrado nesta empresa."
            )

        file_size = len(content)

        extension = self.validation.validate(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
        )

        stored_filename = None
        storage_path = None

        try:
            stored_filename, storage_path = (
                self.storage.save_file(
                    tenant_id=tenant_id,
                    ticket_id=ticket_id,
                    file_extension=extension,
                    content=content,
                )
            )

            attachment = TicketAttachment(
                tenant_id=tenant_id,
                ticket_id=ticket_id,
                uploaded_by_user_id=uploaded_by_user_id,
                original_filename=filename,
                stored_filename=stored_filename,
                content_type=content_type,
                file_extension=extension,
                file_size=file_size,
                storage_path=storage_path,
            )

            self.db.add(attachment)
            self.db.commit()
            self.db.refresh(attachment)

            return attachment

        except Exception:
            self.db.rollback()

            if storage_path is not None:
                self.storage.delete_file(storage_path)

            raise

    def get_attachment(
        self,
        tenant_id: int,
        ticket_id: int,
        attachment_id: int,
    ) -> TicketAttachment | None:
        return (
            self.db.query(TicketAttachment)
            .filter(
                TicketAttachment.id == attachment_id,
                TicketAttachment.ticket_id == ticket_id,
                TicketAttachment.tenant_id == tenant_id,
            )
            .first()
        )

    def list_attachments(
        self,
        tenant_id: int,
        ticket_id: int,
    ) -> list[TicketAttachment]:
        return (
            self.db.query(TicketAttachment)
            .filter(
                TicketAttachment.tenant_id == tenant_id,
                TicketAttachment.ticket_id == ticket_id,
            )
            .order_by(TicketAttachment.created_at.desc())
            .all()
        )

    def delete_attachment(
        self,
        tenant_id: int,
        ticket_id: int,
        attachment_id: int,
        user_id: int,
    ) -> TicketAttachment | None:
        attachment = (
            self.db.query(TicketAttachment)
            .filter(
                TicketAttachment.id == attachment_id,
                TicketAttachment.ticket_id == ticket_id,
                TicketAttachment.tenant_id == tenant_id,
            )
            .first()
        )

        if attachment is None:
            return None

        storage_path = attachment.storage_path

        history_service = TicketHistoryService(self.db)

        try:
            self.storage.delete_file(storage_path)

            self.db.delete(attachment)

            history_service.create_history(
                tenant_id=tenant_id,
                ticket_id=ticket_id,
                user_id=user_id,
                action="TICKET_ATTACHMENT_REMOVED",
                old_value=(
                    f"attachment_id={attachment.id}; "
                    f"filename={attachment.original_filename}"
                ),
                new_value=None,
            )

            self.db.commit()

            return attachment

        except Exception:
            self.db.rollback()
        raise