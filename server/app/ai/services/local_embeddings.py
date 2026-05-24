from __future__ import annotations

import asyncio
from functools import cached_property

from sentence_transformers import SentenceTransformer

from app.ai.services.embeddings_utils import normalize_embedding_dim

TARGET_DIM = 1536


class HuggingFaceEmbeddingsService:
    model_name: str = "sentence-transformers/all-mpnet-base-v2"

    @cached_property
    def _model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    async def embed_query(self, text: str) -> list[float]:
        emb = await asyncio.to_thread(
            self._model.encode, text, normalize_embeddings=True
        )
        return normalize_embedding_dim(emb.tolist(), TARGET_DIM)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embs = await asyncio.to_thread(
            self._model.encode, texts, normalize_embeddings=True
        )
        return [normalize_embedding_dim(emb.tolist(), TARGET_DIM) for emb in embs]
