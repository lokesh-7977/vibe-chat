from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, document_id) -> Document | None:
        return self.db.execute(
            select(Document).where(Document.id == document_id)
        ).scalar_one_or_none()

    def get_by_object_key(self, object_key: str) -> Document | None:
        return self.db.execute(
            select(Document).where(Document.object_key == object_key)
        ).scalar_one_or_none()

    def list_for_channel(self, channel_id, limit: int, offset: int) -> list[Document]:
        return list(
            self.db.execute(
                select(Document)
                .where(Document.channel_id == channel_id)
                .order_by(Document.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).scalars().all()
        )

    def create(self, document: Document) -> Document:
        self.db.add(document)
        return document
