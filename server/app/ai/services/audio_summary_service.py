from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqAudioService, GroqChatService
from app.ai.services.url_fetcher import fetch_bytes_from_url


class AudioSummaryService:
    def __init__(self, groq_audio: GroqAudioService, groq_chat: GroqChatService) -> None:
        self.groq_audio = groq_audio
        self.groq_chat = groq_chat

    async def stream_summary_from_url(self, *, url: str) -> AsyncGenerator[str, None]:
        audio_bytes, content_type = await fetch_bytes_from_url(url)
        transcript = await self.groq_audio.transcribe(audio_bytes=audio_bytes, content_type=content_type)
        system = "You are a concise assistant. Summarize the audio transcript with key points and action items if any."
        user = f"Summarize this transcript:\n\nURL: {url}\n\nTranscript:\n{transcript}"
        async for token in self.groq_chat.stream_chat(system=system, user=user):
            yield token

