from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.content_summary import ContentSummary


class ContentSummaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, *, workspace_id, kind: str, key: str, prompt: str) -> ContentSummary | None:
        stmt = select(ContentSummary).where(
            ContentSummary.workspace_id == workspace_id,
            ContentSummary.kind == kind,
            ContentSummary.key == key,
            ContentSummary.prompt == prompt,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(self, *, workspace_id, kind: str, key: str, prompt: str, summary: str) -> ContentSummary:
        existing = self.get(workspace_id=workspace_id, kind=kind, key=key, prompt=prompt)
        if existing:
            existing.summary = summary
            self.db.add(existing)
            return existing
        row = ContentSummary(workspace_id=workspace_id, kind=kind, key=key, prompt=prompt, summary=summary)
        self.db.add(row)
        return row

