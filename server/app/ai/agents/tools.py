from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from langchain_core.tools import tool

from app.ai.services.audio_summary_service import AudioSummaryService
from app.ai.services.rag_service import RagService
from app.ai.services.translation_service import TranslationService
from app.ai.services.website_summary_service import WebsiteSummaryService
from app.ai.services.youtube_summary_service import YouTubeSummaryService


async def _collect(stream: AsyncGenerator[str, None]) -> str:
    parts: list[str] = []
    async for token in stream:
        parts.append(token)
    return "".join(parts)


def create_react_tools(
    *,
    translation: TranslationService,
    yt_summary: YouTubeSummaryService,
    web_summary: WebsiteSummaryService,
    audio_summary: AudioSummaryService,
    rag_service: RagService,
) -> list:
    @tool
    async def translate(text: str, target_language: str) -> str:
        """Translate the given text to the target language. Output ONLY the translated text — no labels, notes, or extra commentary. Never add or alter meaning."""
        return await _collect(
            translation.stream_translation(text=text, target_language=target_language, user_prompt=None)
        )

    @tool
    async def summarize_youtube(url: str) -> str:
        """Summarize a YouTube video from its transcript. Only use for YouTube URLs. Never invent facts not in the transcript."""
        return await _collect(yt_summary.stream_summary(url=url, user_prompt="Main points only. <=150 words."))

    @tool
    async def summarize_website(url: str) -> str:
        """Summarize a website from its extracted content. Only use for direct website URLs. Never use prior knowledge about the site."""
        return await _collect(web_summary.stream_summary(url=url, user_prompt="<=150 words."))

    @tool
    async def summarize_audio(url: str) -> str:
        """Summarize an audio file from its transcript. Use for direct audio links. Never invent speakers or content."""
        return await _collect(audio_summary.stream_summary_from_url(url=url, user_prompt="Main points only. <=150 words."))

    @tool
    async def retrieve_context(question: str, channel_id: str) -> str:
        """Search channel history and uploaded documents for relevant information. Only answer from retrieved context; do not use outside knowledge."""
        sources, citations = await rag_service.retrieve(channel_id=UUID(channel_id), query=question)
        if not sources:
            return "No relevant information found in the channel."
        return await _collect(rag_service.stream_answer(question=question, sources=sources, citations=citations))

    return [translate, summarize_youtube, summarize_website, summarize_audio, retrieve_context]
