from __future__ import annotations

from collections.abc import AsyncGenerator
import math
import re
from typing import Any
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.ai.prompts.base import ChatMessage
from app.ai.services.local_embeddings import HuggingFaceEmbeddingsService
from app.ai.services.web_extractor import fetch_page_extract
from app.ai.services.summary_cache_keys import normalize_website_url
from app.repositories.content_summary_repository import ContentSummaryRepository
from sqlalchemy.orm import Session


class WebsiteRagState(BaseModel):
    url: str = ""
    user_prompt: str | None = None
    corpus: str = ""
    chunks: list[str] = Field(default_factory=list)
    query_embedding: list[float] | None = None
    chunk_embeddings: list[list[float]] | None = None
    excerpts: list[str] = Field(default_factory=list)
    output: str | None = None


class WebsiteSummaryService:
    def __init__(
        self,
        groq: object,
        *,
        embeddings: HuggingFaceEmbeddingsService,
        db: Session | None = None,
        workspace_id: UUID | None = None,
    ) -> None:
        self.groq = groq
        self.embeddings = embeddings
        self._db = db
        self._workspace_id = workspace_id

    @staticmethod
    def _limit_words(text: str, max_words: int) -> str:
        words = (text or "").strip().split()
        if len(words) <= max_words:
            return (text or "").strip()
        return " ".join(words[:max_words]).rstrip(" ,;:-") + "..."

    @staticmethod
    def _clean_model_output(text: str) -> str:
        t = (text or "").strip()
        t = re.sub(r"^#+\s*", "", t)
        t = re.sub(r"^[-*\u2022]\s+", "", t, flags=re.MULTILINE)
        t = re.sub(r"\n{3,}", "\n\n", t).strip()
        return t

    @staticmethod
    def _looks_like_boilerplate(line: str) -> bool:
        l = (line or "").strip().lower()
        if not l:
            return True
        if l in {"home", "about", "services", "contact", "privacy policy", "terms", "login", "sign in", "sign up"}:
            return True
        if "cookie" in l or "copyright" in l:
            return True
        if l.startswith("©") or l.startswith("all rights reserved"):
            return True
        return False

    @staticmethod
    def _split_text(text: str, *, chunk_chars: int = 1600, overlap: int = 200) -> list[str]:
        t = (text or "").strip()
        if not t:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(t):
            end = min(len(t), start + chunk_chars)
            chunk = t[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(t):
                break
            start = max(0, end - overlap)
        return chunks

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        n = min(len(a), len(b))
        dot = 0.0
        na = 0.0
        nb = 0.0
        for i in range(n):
            x = float(a[i])
            y = float(b[i])
            dot += x * y
            na += x * x
            nb += y * y
        if na <= 0.0 or nb <= 0.0:
            return 0.0
        return dot / (math.sqrt(na) * math.sqrt(nb))

    def _build_rag_graph(self) -> Any:
        async def load_node(state: WebsiteRagState) -> dict[str, Any]:
            page = await fetch_page_extract(state.url)
            lines = [ln.strip() for ln in (page.text or "").splitlines()]
            lines = [ln for ln in lines if ln and len(ln) >= 20 and not self._looks_like_boilerplate(ln)]
            corpus = "\n".join(lines).strip()
            return {"corpus": corpus}

        async def split_node(state: WebsiteRagState) -> dict[str, Any]:
            if len(state.corpus) < 200:
                return {
                    "output": "Insufficient information extracted from the webpage (content may require JavaScript rendering)."
                }
            return {"chunks": self._split_text(state.corpus)}

        async def embed_node(state: WebsiteRagState) -> dict[str, Any]:
            if state.output or not state.chunks:
                return {}
            query = (state.user_prompt or "").strip() or "Summarize this website in <=150 words."
            return {
                "query_embedding": await self.embeddings.embed_query(query),
                "chunk_embeddings": await self.embeddings.embed_documents(state.chunks),
            }

        async def retrieve_node(state: WebsiteRagState) -> dict[str, Any]:
            if state.output:
                return {}
            if not state.chunks or not state.query_embedding or not state.chunk_embeddings:
                return {"output": "Insufficient information in provided excerpts."}
            scored = sorted(
                zip(state.chunks, state.chunk_embeddings, strict=False),
                key=lambda pair: self._cosine(state.query_embedding, pair[1]),
                reverse=True,
            )
            return {"excerpts": [chunk for (chunk, _embedding) in scored[:6]]}

        async def summarize_node(state: WebsiteRagState) -> dict[str, Any]:
            if state.output:
                return {}
            if not state.excerpts:
                return {"output": "Insufficient information in provided excerpts."}
            system = (
                "You are a careful website summarizer — zero hallucination.\n"
                "STRICT RULES:\n"
                "- Use ONLY the provided EXCERPTS. Do NOT use any outside knowledge about the website or topic.\n"
                "- Do NOT add, infer, or invent any facts not explicitly present in the excerpts.\n"
                "- If the EXCERPTS do not contain enough information, say exactly: \"Insufficient information in provided excerpts.\"\n"
                "- Output a single paragraph (no bullets, no headings).\n"
                "- Max length: 150 words.\n"
            )
            user = "Summarize this website based on the excerpts.\n\nURL: {url}\n\nEXCERPTS:\n{excerpts}".format(
                url=state.url,
                excerpts="\n\n---\n\n".join(state.excerpts),
            )
            messages = [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)]
            buffer = ""
            async for token in self.groq.stream_chat(messages=messages, temperature=0.0):
                buffer += token
            cleaned = self._clean_model_output(buffer)
            return {"output": self._limit_words(cleaned, 150)}

        graph = StateGraph(WebsiteRagState)
        graph.add_node("loader", load_node)
        graph.add_node("splitter", split_node)
        graph.add_node("embed_store", embed_node)
        graph.add_node("retriever", retrieve_node)
        graph.add_node("llm", summarize_node)
        graph.add_edge(START, "loader")
        graph.add_edge("loader", "splitter")
        graph.add_edge("splitter", "embed_store")
        graph.add_edge("embed_store", "retriever")
        graph.add_edge("retriever", "llm")
        graph.add_edge("llm", END)
        return graph.compile()

    async def stream_summary(self, *, url: str, user_prompt: str | None) -> AsyncGenerator[str, None]:
        prompt_key = ((user_prompt or "").strip() or "").lower()[:200]
        cache_key = normalize_website_url(url)
        if self._db and self._workspace_id and cache_key:
            repo = ContentSummaryRepository(self._db)
            cached = repo.get(workspace_id=self._workspace_id, kind="website", key=cache_key, prompt=prompt_key)
            if cached and (cached.summary or "").strip():
                yield cached.summary.strip()
                return

        graph = self._build_rag_graph()
        result = await graph.ainvoke(WebsiteRagState(url=url, user_prompt=user_prompt))
        output = (result.get("output", "") if isinstance(result, dict) else result.output) or ""
        final = output or "Insufficient information in provided excerpts."

        if self._db and self._workspace_id and cache_key and final.strip():
            repo = ContentSummaryRepository(self._db)
            repo.upsert(workspace_id=self._workspace_id, kind="website", key=cache_key, prompt=prompt_key, summary=final.strip())
            self._db.commit()

        yield final
