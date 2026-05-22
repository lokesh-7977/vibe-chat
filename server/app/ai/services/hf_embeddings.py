from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


def normalize_embedding_dim(vec: list[float], target_dim: int) -> list[float]:
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0] * (target_dim - len(vec))


@dataclass
class HfEmbeddingsService:
    """
    Uses Hugging Face Inference API for feature-extraction embeddings.
    This avoids bundling large local embedding models in the server image.
    """

    async_client: httpx.AsyncClient

    async def _embed_one(self, text: str) -> list[float]:
        settings = get_settings()
        if not settings.hf_api_token:
            raise RuntimeError("HF_API_TOKEN is not configured")

        url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.hf_embeddings_model}"
        headers = {"Authorization": f"Bearer {settings.hf_api_token}"}
        resp = await self.async_client.post(url, headers=headers, json={"inputs": text})
        resp.raise_for_status()
        data = resp.json()

        # HF may return nested lists (token embeddings). Pool by mean if needed.
        if data and isinstance(data[0], list):
            # mean-pool across tokens
            token_vectors = data
            dim = len(token_vectors[0])
            pooled = [0.0] * dim
            for tv in token_vectors:
                for i, v in enumerate(tv):
                    pooled[i] += float(v)
            return [v / max(1, len(token_vectors)) for v in pooled]

        return [float(x) for x in data]

    async def embed_query(self, text: str) -> list[float]:
        return await self._embed_one(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.gather(*(self._embed_one(t) for t in texts))
