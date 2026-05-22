from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai import AIInteraction, AIRun


class AIInteractionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, interaction: AIInteraction) -> AIInteraction:
        self.db.add(interaction)
        return interaction

    def get_by_id(self, interaction_id) -> AIInteraction | None:
        return self.db.execute(
            select(AIInteraction).where(AIInteraction.id == interaction_id)
        ).scalar_one_or_none()

    def create_run(self, run: AIRun) -> AIRun:
        self.db.add(run)
        return run

