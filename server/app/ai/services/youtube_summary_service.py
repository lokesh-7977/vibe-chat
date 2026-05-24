from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from app.ai.services.youtube_transcript import fetch_youtube_transcript_text
from app.ai.prompts.summarization.youtube.prompt import build_youtube_summary_prompt
from app.repositories.content_summary_repository import ContentSummaryRepository
from app.ai.services.summary_cache_keys import youtube_cache_key
from sqlalchemy.orm import Session


class YouTubeSummaryService:
    def __init__(self, groq: object, *, db: Session | None = None, workspace_id: UUID | None = None) -> None:
        self.groq = groq
        self._db = db
        self._workspace_id = workspace_id

    async def stream_summary(self, *, url: str, user_prompt: str | None) -> AsyncGenerator[str, None]:
        prompt_key = ((user_prompt or "").strip() or "").lower()[:200]
        cache_key = youtube_cache_key(url)
        if self._db and self._workspace_id and cache_key:
            repo = ContentSummaryRepository(self._db)
            cached = repo.get(workspace_id=self._workspace_id, kind="youtube", key=cache_key, prompt=prompt_key)
            if cached and (cached.summary or "").strip():
                yield cached.summary.strip()
                return

        transcript = await fetch_youtube_transcript_text(url)
        prompt = build_youtube_summary_prompt(url=url, transcript=transcript, user_prompt=user_prompt)
        full = ""
        async for token in self.groq.stream_chat(messages=prompt.messages, temperature=0.0):
            full += token
            yield token

        if self._db and self._workspace_id and cache_key and full.strip():
            repo = ContentSummaryRepository(self._db)
            repo.upsert(workspace_id=self._workspace_id, kind="youtube", key=cache_key, prompt=prompt_key, summary=full.strip())
            self._db.commit()
