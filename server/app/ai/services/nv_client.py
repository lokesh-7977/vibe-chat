from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.ai.prompts.base import ChatMessage
from app.core.config import get_settings


class NvChatService:
    """
    NVIDIA Integrate (NVAPI) OpenAI-compatible Chat Completions client.

    Base URL default: https://integrate.api.nvidia.com/v1
    Endpoint: POST /chat/completions
    """

    def __init__(self, *, async_client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        if not settings.nvapi_api_key:
            raise RuntimeError("NVAPI_API_KEY is not configured")
        self._api_key = settings.nvapi_api_key
        self._base_url = self._normalize_base_url(settings.nvapi_base_url)
        self._model = settings.nvapi_chat_model
        self._async_client = async_client

    @staticmethod
    def _serialize_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for m in messages:
            base: dict[str, Any] = {"role": m.role}
            if m.content is not None:
                base["content"] = m.content
            if m.tool_call_id:
                base["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                base["tool_calls"] = m.tool_calls
            serialized.append(base)
        return serialized

    @staticmethod
    def _clamp_temperature(temp: float | None) -> float:
        if temp is None:
            return 0.2
        return max(0.0, min(1.0, float(temp)))

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"}

    @staticmethod
    def _first_choice(obj: dict[str, Any]) -> dict[str, Any]:
        choices = obj.get("choices")
        if not isinstance(choices, list) or not choices:
            detail = obj.get("error") or obj
            raise RuntimeError(f"NVIDIA chat response did not include choices: {str(detail)[:800]}")
        choice = choices[0]
        if not isinstance(choice, dict):
            raise RuntimeError(f"NVIDIA chat response choice was not an object: {str(choice)[:800]}")
        return choice

    @staticmethod
    def _optional_first_choice(obj: dict[str, Any]) -> dict[str, Any] | None:
        choices = obj.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        choice = choices[0]
        return choice if isinstance(choice, dict) else None

    @staticmethod
    def _normalize_base_url(value: str) -> str:
        """
        Accept either:
        - https://integrate.api.nvidia.com
        - https://integrate.api.nvidia.com/v1
        and normalize to the versioned base (…/v1).
        """
        base = (value or "").strip().rstrip("/")
        if base.endswith("/v1"):
            return base
        return f"{base}/v1"

    async def stream_chat(
        self,
        *,
        messages: list[ChatMessage],
        temperature: float | None = None,
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        temp = self._clamp_temperature(temperature)
        payload = {
            "model": model or self._model,
            "messages": self._serialize_messages(messages),
            "temperature": temp,
            "stream": True,
        }

        if not self._async_client:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                async for token in self._stream_with_client(client, payload):
                    yield token
            return

        async for token in self._stream_with_client(self._async_client, payload):
            yield token

    async def _stream_with_client(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        url = f"{self._base_url}/chat/completions"
        async with client.stream("POST", url, headers=self._headers(), json=payload) as resp:
            if resp.status_code >= 400:
                body = await resp.aread()
                raise RuntimeError(f"NVIDIA chat stream error {resp.status_code}: {body.decode(errors='replace')[:800]}")
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                data = line.strip()
                if data.startswith("data:"):
                    data = data.removeprefix("data:").strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choice = self._optional_first_choice(obj)
                if choice is None:
                    continue
                delta = (choice.get("delta") or {}).get("content")
                if delta:
                    yield str(delta)

    async def chat(
        self,
        *,
        messages: list[ChatMessage],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        temp = self._clamp_temperature(temperature)
        payload: dict[str, Any] = {
            "model": model or self._model,
            "messages": self._serialize_messages(messages),
            "temperature": temp,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        async def _call(client: httpx.AsyncClient) -> dict[str, Any]:
            url = f"{self._base_url}/chat/completions"
            resp = await client.post(url, headers=self._headers(), json=payload)
            if resp.status_code >= 400:
                raise RuntimeError(f"NVIDIA chat error {resp.status_code}: {resp.text[:800]}")
            resp.raise_for_status()
            obj = resp.json()
            choice = self._first_choice(obj)
            msg = choice.get("message", {}) or {}
            tool_calls = msg.get("tool_calls") or []
            return {
                "role": msg.get("role", "assistant"),
                "content": msg.get("content") or "",
                "tool_calls": tool_calls,
            }

        if self._async_client:
            return await _call(self._async_client)

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            return await _call(client)
