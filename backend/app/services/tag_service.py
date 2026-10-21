from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


class TagService:
    def __init__(self, db: Session):
        self.db = db

    def create_tag(
        self,
        tenant_id: int,
        data: TagCreate,
    ) -> Tag:
        existing_tag = (
            self.db.query(Tag)
            .filter(
                Tag.tenant_id == tenant_id,
                Tag.name == data.name,
            )
            .first()
        )

        if existing_tag is not None:
            raise ValueError(
                "Já existe uma tag com este nome nesta empresa."
            )

        tag = Tag(
            tenant_id=tenant_id,
            name=data.name,
            color=data.color,
            description=data.description,
            is_active=True,
        )

        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)

        return tag

    def get_tag(
        self,
        tenant_id: int,
        tag_id: int,
    ) -> Tag | None:
        return (
            self.db.query(Tag)
            .filter(
                Tag.id == tag_id,
                Tag.tenant_id == tenant_id,
            )
            .first()
        )

    def list_tags(
        self,
        tenant_id: int,
        include_inactive: bool = False,
    ) -> list[Tag]:
        query = (
            self.db.query(Tag)
            .filter(Tag.tenant_id == tenant_id)
        )

        if not include_inactive:
            query = query.filter(Tag.is_active.is_(True))

        return (
            query
            .order_by(Tag.name.asc())
            .all()
        )

    def update_tag(
        self,
        tenant_id: int,
        tag_id: int,
        data: TagUpdate,
    ) -> Tag | None:
        tag = self.get_tag(
            tenant_id=tenant_id,
            tag_id=tag_id,
        )

        if tag is None:
            return None

        if data.name is not None and data.name != tag.name:
            existing_tag = (
                self.db.query(Tag)
                .filter(
                    Tag.tenant_id == tenant_id,
                    Tag.name == data.name,
                    Tag.id != tag_id,
                )
                .first()
            )

            if existing_tag is not None:
                raise ValueError(
                    "Já existe uma tag com este nome nesta empresa."
                )

            tag.name = data.name

        if data.color is not None:
            tag.color = data.color

        if data.description is not None:
            tag.description = data.description

        if data.is_active is not None:
            tag.is_active = data.is_active

        self.db.commit()
        self.db.refresh(tag)

        return tag