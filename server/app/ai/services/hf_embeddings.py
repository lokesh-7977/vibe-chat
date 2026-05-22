from __future__ import annotations

import asyncio
import warnings
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, SecretStr

from app.core.config import get_settings


def normalize_embedding_dim(vec: list[float], target_dim: int) -> list[float]:
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0] * (target_dim - len(vec))


class HfEmbeddingsService(BaseModel):
    """
    Uses LangChain Community's Hugging Face Inference API embeddings.

    A small HTTP fallback is kept so the service still works if LangChain's
    community integration changes while the server is running in production.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async_client: httpx.AsyncClient | None = Field(default=None, exclude=True)
    api_token: str | None = Field(default=None, exclude=True)
    model_name: str | None = None

    _langchain_embeddings: Any = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        settings = get_settings()
        self.api_token = self.api_token or settings.hf_api_token
        self.model_name = self.model_name or settings.hf_embeddings_model
        if not self.api_token:
            return

        try:
            from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r"The class `HuggingFaceInferenceAPIEmbeddings` was deprecated.*",
                )
                self._langchain_embeddings = HuggingFaceInferenceAPIEmbeddings(
                    api_key=SecretStr(self.api_token),
                    model_name=self.model_name,
                )
        except Exception:
            self._langchain_embeddings = None

    async def _embed_one(self, text: str) -> list[float]:
        if not self.api_token:
            raise RuntimeError("HF_API_TOKEN is not configured")

        if self._langchain_embeddings is not None:
            vector = await self._langchain_embeddings.aembed_query(text)
            return [float(x) for x in vector]

        if self.async_client is None:
            raise RuntimeError("HTTP client is required for Hugging Face embedding fallback")

        url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
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
        if not texts:
            return []
        if self._langchain_embeddings is not None:
            vectors = await self._langchain_embeddings.aembed_documents(texts)
            return [[float(x) for x in vector] for vector in vectors]
        return await asyncio.gather(*(self._embed_one(t) for t in texts))
