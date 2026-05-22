from __future__ import annotations

import math
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any
from uuid import UUID
import asyncio
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.services.groq_client import GroqChatService
from app.ai.services.hf_embeddings import HfEmbeddingsService, normalize_embedding_dim
from app.ai.types import SourceDocument
from app.core.config import get_settings
from app.db.models.activity import Activity
from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.db.models.embedding import ActivityEmbedding, DocumentEmbedding
from app.repositories.activity_repository import ActivityRepository
from app.repositories.document_repository import DocumentRepository
from app.storage.r2_download import download_document_bytes
from app.utils.text_extractors import extract_text_from_document_bytes, chunk_text
from app.ai.services.web_extractor import fetch_readable_text
from app.ai.services.youtube_transcript import fetch_youtube_transcript_text


@dataclass(frozen=True)
class RetrievedSource:
    kind: str
    id: str
    snippet: str
    url: str | None = None


class RagService:
    def __init__(self, db: Session, *, embeddings: HfEmbeddingsService, groq: GroqChatService) -> None:
        self.db = db
        self.embeddings = embeddings
        self.groq = groq
        self.activity_repo = ActivityRepository(db)
        self.document_repo = DocumentRepository(db)

    async def _ensure_activity_embeddings(self, *, activities: list[Activity]) -> None:
        settings = get_settings()
        model_name = f"hf::{settings.hf_embeddings_model}::padded1536"
        to_embed: list[Activity] = []
        for a in activities:
            if not a.content:
                continue
            if a.embedding is None:
                to_embed.append(a)
        if not to_embed:
            return

        # If a message is a link, embed extracted content instead of the raw URL.
        texts: list[str] = []
        extracted_links = 0
        for a in to_embed:
            content = a.content or ""
            url_match = re.search(r"https?://\\S+", content)
            if url_match and extracted_links < 5:
                url = url_match.group(0)
                try:
                    if "youtube.com" in url or "youtu.be" in url:
                        extracted = await fetch_youtube_transcript_text(url)
                        texts.append(extracted)
                        extracted_links += 1
                    else:
                        extracted = await fetch_readable_text(url)
                        texts.append(extracted)
                        extracted_links += 1
                    continue
                except Exception:
                    pass
            texts.append(content)

        vectors = await self.embeddings.embed_documents(texts)
        for activity, vec in zip(to_embed, vectors, strict=False):
            padded = normalize_embedding_dim(vec, 1536)
            self.db.add(
                ActivityEmbedding(
                    activity_id=activity.id,
                    workspace_id=activity.workspace_id,
                    channel_id=activity.channel_id,
                    embedding=padded,
                    embedding_model=model_name,
                )
            )

    async def _ensure_document_embeddings_for_channel(self, *, channel_id: UUID) -> None:
        settings = get_settings()
        model_name = f"hf::{settings.hf_embeddings_model}::padded1536"

        docs = self.db.execute(
            select(Document).where(Document.channel_id == channel_id).order_by(Document.created_at.desc())
        ).scalars().all()
        for doc in docs:
            if doc.status != "uploaded":
                continue

            existing_chunks = list(
                self.db.execute(
                    select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index.asc())
                ).scalars().all()
            )
            if not existing_chunks:
                # Best effort ingest now.
                try:
                    content_bytes = await asyncio.to_thread(download_document_bytes, doc.file_url)
                    text = await asyncio.to_thread(
                        extract_text_from_document_bytes,
                        content_bytes,
                        mime_type=doc.mime_type,
                    )
                except Exception:
                    continue

                chunks = await asyncio.to_thread(chunk_text, text)
                for idx, chunk in enumerate(chunks):
                    self.db.add(
                        DocumentChunk(
                            document_id=doc.id,
                            workspace_id=doc.workspace_id,
                            channel_id=doc.channel_id,
                            chunk_index=idx,
                            content=chunk,
                            token_count=None,
                            meta_data={"file_name": doc.file_name, "file_url": doc.file_url},
                        )
                    )
                self.db.flush()
                existing_chunks = list(
                    self.db.execute(
                        select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index.asc())
                    ).scalars().all()
                )

            # Embed missing chunks.
            missing = [c for c in existing_chunks if c.embedding is None]
            if not missing:
                continue

            vectors = await self.embeddings.embed_documents([c.content for c in missing])
            for chunk, vec in zip(missing, vectors, strict=False):
                padded = normalize_embedding_dim(vec, 1536)
                self.db.add(
                    DocumentEmbedding(
                        document_chunk_id=chunk.id,
                        embedding=padded,
                        embedding_model=model_name,
                    )
                )

    async def retrieve(
        self,
        *,
        channel_id: UUID,
        query: str,
    ) -> tuple[list[SourceDocument], list[RetrievedSource]]:
        settings = get_settings()
        query_vec = normalize_embedding_dim(await self.embeddings.embed_query(query), 1536)

        # Ensure embeddings exist for recent messages and documents.
        recent_activities = self.activity_repo.list_for_channel(channel_id, limit=settings.rag_max_sources_per_type, offset=0)
        await self._ensure_activity_embeddings(activities=recent_activities)
        await self._ensure_document_embeddings_for_channel(channel_id=channel_id)

        # Commit any newly created vectors.
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

        # Similarity search: activity_embeddings and document_embeddings.
        activity_rows = list(
            self.db.execute(
                select(ActivityEmbedding, Activity)
                .join(Activity, Activity.id == ActivityEmbedding.activity_id)
                .where(ActivityEmbedding.channel_id == channel_id)
                .order_by(ActivityEmbedding.embedding.cosine_distance(query_vec))
                .limit(settings.rag_top_k)
            ).all()
        )

        doc_rows = list(
            self.db.execute(
                select(DocumentEmbedding, DocumentChunk)
                .join(DocumentChunk, DocumentChunk.id == DocumentEmbedding.document_chunk_id)
                .where(DocumentChunk.channel_id == channel_id)
                .order_by(DocumentEmbedding.embedding.cosine_distance(query_vec))
                .limit(max(1, math.ceil(settings.rag_top_k / 2)))
            ).all()
        )

        sources: list[SourceDocument] = []
        citations: list[RetrievedSource] = []

        for emb, activity in activity_rows:
            if not activity.content:
                continue
            sources.append(
                SourceDocument(
                    source_type="channel_message",
                    source_id=str(activity.id),
                    title=None,
                    url=None,
                    content=activity.content,
                    meta={"created_at": activity.created_at.isoformat()},
                )
            )
            citations.append(
                RetrievedSource(kind="channel_message", id=str(activity.id), snippet=activity.content[:240])
            )

        for emb, chunk in doc_rows:
            sources.append(
                SourceDocument(
                    source_type="document_chunk",
                    source_id=str(chunk.id),
                    title=chunk.meta_data.get("file_name") if chunk.meta_data else None,
                    url=chunk.meta_data.get("file_url") if chunk.meta_data else None,
                    content=chunk.content,
                    meta={"chunk_index": chunk.chunk_index},
                )
            )
            citations.append(
                RetrievedSource(
                    kind="document_chunk",
                    id=str(chunk.id),
                    snippet=chunk.content[:240],
                    url=(chunk.meta_data.get("file_url") if chunk.meta_data else None),
                )
            )

        return sources, citations

    async def stream_answer(
        self,
        *,
        question: str,
        sources: list[SourceDocument],
        citations: list[RetrievedSource],
    ) -> AsyncGenerator[str, None]:
        context = "\n\n".join(
            f"[{i+1}] ({s.source_type}) {s.content}"
            for i, s in enumerate(sources)
        )
        sources_text = "\n".join(
            f"[{i+1}] {c.kind}:{c.id}{(' ' + c.url) if c.url else ''}"
            for i, c in enumerate(citations)
        )
        system = (
            "You answer using ONLY the provided context. If the answer is not in context, say you don't know. "
            "At the end, include a 'Sources:' section listing the source ids used."
        )
        user = (
            f"Question:\n{question}\n\n"
            f"Context:\n{context}\n\n"
            f"Allowed sources:\n{sources_text}\n\n"
            "Return the answer followed by:\n\nSources:\n- <source>\n- <source>\n"
        )

        async for token in self.groq.stream_chat(system=system, user=user):
            yield token
