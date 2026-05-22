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
        """Translate text to a target language. Use when the user asks for translation."""
        return await _collect(
            translation.stream_translation(text=text, target_language=target_language, user_prompt=None)
        )

    @tool
    async def summarize_youtube(url: str) -> str:
        """Summarize a YouTube video from its URL. Use when the user provides a YouTube link."""
        return await _collect(yt_summary.stream_summary(url=url, user_prompt=None))

    @tool
    async def summarize_website(url: str) -> str:
        """Summarize a web page from its URL. Use when the user shares a website/article link."""
        return await _collect(web_summary.stream_summary(url=url, user_prompt=None))

    @tool
    async def summarize_audio(url: str) -> str:
        """Summarize an audio file from its URL. Use when the user shares an audio link (.mp3, .wav, etc.)."""
        return await _collect(audio_summary.stream_summary_from_url(url=url, user_prompt=None))

    @tool
    async def retrieve_context(question: str, channel_id: str) -> str:
        """Search the current channel for relevant information to answer a question. Use when the user asks a question that may be answered from channel history or uploaded documents."""
        sources, citations = await rag_service.retrieve(
            channel_id=UUID(channel_id),
            query=question,
        )
        if not sources:
            return "No relevant information found in the channel."
        lines: list[str] = [f"Found {len(sources)} relevant source(s):\n"]
        for i, s in enumerate(sources):
            lines.append(f"[{i+1}] ({s.source_type}) {s.content}")
        return "\n".join(lines)

    return [translate, summarize_youtube, summarize_website, summarize_audio, retrieve_context]
