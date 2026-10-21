from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from app.models.ticket_message import TicketMessageVisibility
from app.models.ticket import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    customer_id: int | None = None

    solar_plant_id: int | None = None

    solar_device_id: int | None = None

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=1,
    )

    priority: TicketPriority = TicketPriority.MEDIUM

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    subcategory: str = Field(
        min_length=1,
        max_length=100,
    )


class TicketUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    priority: TicketPriority | None = None

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    subcategory: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    status: TicketStatus | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    tenant_id: int

    customer_id: int | None
    solar_plant_id: int | None
    solar_device_id: int | None

    created_by_user_id: int
    owner_user_id: int | None

    title: str
    description: str

    status: TicketStatus
    priority: TicketPriority

    category: str
    subcategory: str

    is_active: bool

    claimed_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None

    created_at: datetime
    updated_at: datetime

class TicketMessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    visibility: TicketMessageVisibility = TicketMessageVisibility.PUBLIC

    mentioned_user_ids: list[int] = Field(
        default_factory=list,
        max_length=20,
    )

class TicketMessageUpdate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )


class TicketMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    ticket_id: int
    author_user_id: int
    content: str
    visibility: TicketMessageVisibility
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

class MentionableUserResponse(BaseModel):
    id: int
    name: str

class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    ticket_id: int
    uploaded_by_user_id: int
    original_filename: str
    content_type: str
    file_extension: str
    file_size: int
    created_at: datetime