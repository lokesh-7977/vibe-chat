from __future__ import annotations

import asyncio
from functools import cached_property

import httpx

from app.ai.services.embeddings_utils import normalize_embedding_dim
from app.core.config import get_settings

TARGET_DIM = 1536


class ApiEmbeddingsService:
    @cached_property
    def _api_key(self) -> str:
        settings = get_settings()
        key = settings.embedding_api_key or settings.nvapi_api_key
        if not key:
            raise RuntimeError(
                "No embedding API key configured. Set EMBEDDING_API_KEY or NVAPI_API_KEY."
            )
        return key

    @cached_property
    def _api_url(self) -> str:
        settings = get_settings()
        url = settings.embedding_api_url
        if url:
            return url.rstrip("/")
        base = settings.nvapi_base_url.rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/embeddings"
        return f"{base}/v1/embeddings"

    @cached_property
    def _model(self) -> str:
        return get_settings().embedding_model

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {
            "model": self._model,
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(self._api_url, headers=self._headers(), json=payload)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Embedding API error {resp.status_code}: {resp.text[:500]}"
                )
            resp.raise_for_status()
            data = resp.json()
            return [e["embedding"] for e in sorted(data["data"], key=lambda x: x.get("index", 0))]

    async def embed_query(self, text: str) -> list[float]:
        embs = await self._embed([text])
        return normalize_embedding_dim(embs[0], TARGET_DIM) if embs else []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        results: list[list[float]] = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embs = await self._embed(batch)
            results.extend(embs)
            if i + batch_size < len(texts):
                await asyncio.sleep(0.05)
        return [normalize_embedding_dim(emb, TARGET_DIM) for emb in results]
