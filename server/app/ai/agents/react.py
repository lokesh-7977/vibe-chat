from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from app.ai.agents.tools import create_react_tools
from app.ai.prompts.base import ChatMessage
from app.ai.services.audio_summary_service import AudioSummaryService
from app.ai.services.rag_service import RagService
from app.ai.services.streaming_service import StreamingCollector, sse
from app.ai.services.translation_service import TranslationService
from app.ai.services.website_summary_service import WebsiteSummaryService
from app.ai.services.youtube_summary_service import YouTubeSummaryService


REACT_SYSTEM_PROMPT = """You are VibeChat AI, a grounded assistant. You must solve every request by calling exactly one available tool.

GROUNDING RULES (strict — never violate these):
1. TRANSLATION: Translate ONLY the source text. Do NOT add, remove, embellish, or alter meaning. Output ONLY the translated text — no labels, notes, or commentary.
2. SUMMARIZATION: Summarize ONLY the content provided by the tool (transcript/page text/context). Do NOT use outside knowledge. Do NOT invent details, names, numbers, or facts.
3. RAG: Answer ONLY from the retrieved context. If the context lacks the answer, say you don't know. Never guess.
4. TOOL RESULT IS FINAL: After a tool runs, its result is the final answer. Do not add commentary, notes, or extra text.
5. UNCERTAINTY: If you're unsure whether a tool applies, call retrieve_context.

TOOL SELECTION:
- Translation request -> translate(text, target_language)
- Normal website URL -> summarize_website(url)
- YouTube URL -> summarize_youtube(url)
- Audio URL -> summarize_audio(url)
- Question about channel content/documents -> retrieve_context(question, channel_id)
- Default (no tool matches) -> retrieve_context(question, channel_id)
"""


class WorkflowInput(BaseModel):
    user_input: str = ""
    channel_id: UUID | None = None
    target_language: str | None = None


class AgentState(BaseModel):
    messages: list = Field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 2


_FUNCTION_CALL_RE = re.compile(r"<function=(\w+)>(.*?)(?:</function>|$)", re.DOTALL)


def _to_chat_messages(messages: list) -> list[ChatMessage]:
    result: list[ChatMessage] = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            result.append(ChatMessage(role="system", content=str(msg.content)))
        elif isinstance(msg, HumanMessage):
            result.append(ChatMessage(role="user", content=str(msg.content)))
        elif isinstance(msg, AIMessage):
            has_tool_calls = bool(msg.tool_calls)
            chat_msg = ChatMessage(role="assistant", content=None if has_tool_calls else str(msg.content or ""))
            if has_tool_calls:
                chat_msg.tool_calls = [
                    {
                        "id": tc.get("id") or f"call_{index}",
                        "type": "function",
                        "function": {
                            "name": tc.get("name") or "unknown",
                            "arguments": json.dumps(tc.get("args") or {}, default=str),
                        },
                    }
                    for index, tc in enumerate(msg.tool_calls)
                ]
            result.append(chat_msg)
        elif isinstance(msg, ToolMessage):
            result.append(ChatMessage(role="tool", content=str(msg.content), tool_call_id=msg.tool_call_id))
    return result


def _from_chat_response(response: dict[str, Any], *, tools_passed: bool) -> AIMessage:
    content = response.get("content", "") or ""
    tool_calls = []
    for tool_call in response.get("tool_calls", []) or []:
        function = tool_call.get("function", {}) or {}
        args_raw = function.get("arguments") or "{}"
        if isinstance(args_raw, str):
            try:
                args = json.loads(args_raw)
            except json.JSONDecodeError:
                args = {}
        else:
            args = args_raw
        tool_calls.append(
            {
                "name": function.get("name") or "unknown",
                "args": args,
                "id": tool_call.get("id") or f"call_{len(tool_calls)}",
                "type": "tool_call",
            }
        )

    if not tool_calls and tools_passed:
        for match in _FUNCTION_CALL_RE.finditer(content):
            try:
                args = json.loads(match.group(2))
            except json.JSONDecodeError:
                continue
            tool_calls.append(
                {
                    "name": match.group(1),
                    "args": args,
                    "id": f"fc_{len(tool_calls)}",
                    "type": "tool_call",
                }
            )

    return AIMessage(content=content if not tool_calls else "", tool_calls=tool_calls)


async def _stream_text(text: str, collector: StreamingCollector) -> AsyncGenerator[bytes, None]:
    cleaned = _FUNCTION_CALL_RE.sub("", text or "").strip()
    cleaned = re.sub(r"<\|python_tag\|>.*?(\n|$)", "", cleaned).strip()
    if not cleaned:
        return
    for token in cleaned.split(" "):
        chunk = token + " "
        collector.add_token(chunk)
        yield sse("token", {"content": chunk})
        await asyncio.sleep(0)


def build_react_agent(
    *,
    llm: Any,
    translation: TranslationService,
    yt_summary: YouTubeSummaryService,
    web_summary: WebsiteSummaryService,
    audio_summary: AudioSummaryService,
    rag_service: RagService,
) -> Any:
    tools = create_react_tools(
        translation=translation,
        yt_summary=yt_summary,
        web_summary=web_summary,
        audio_summary=audio_summary,
        rag_service=rag_service,
    )
    tool_node = ToolNode(tools)
    tool_schemas = []
    for tool_item in tools:
        schema = tool_item.get_input_schema().model_json_schema()
        parameters = {key: value for key, value in schema.items() if key in ("type", "properties", "required")}
        tool_schemas.append(
            {
                "type": "function",
                "function": {
                    "name": tool_item.name or tool_item.__class__.__name__,
                    "description": tool_item.description or "",
                    "parameters": parameters,
                },
            }
        )

    async def call_model(state: AgentState) -> dict[str, Any]:
        messages = [SystemMessage(content=REACT_SYSTEM_PROMPT), *state.messages]
        response = await llm.chat(messages=_to_chat_messages(messages), tools=tool_schemas, temperature=0.0)
        return {"messages": [_from_chat_response(response, tools_passed=True)], "iterations": state.iterations + 1}

    def should_continue(state: AgentState) -> str:
        if state.iterations >= state.max_iterations:
            return "end"
        last = state.messages[-1] if state.messages else None
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "end"

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", END)
    return workflow.compile()


async def run_react_agent_stream(
    *,
    llm: Any,
    translation: TranslationService,
    yt_summary: YouTubeSummaryService,
    web_summary: WebsiteSummaryService,
    audio_summary: AudioSummaryService,
    rag_service: RagService,
    user_input: str,
    channel_id: UUID,
    target_language: str | None,
    collector: StreamingCollector,
) -> AsyncGenerator[bytes, None]:
    compiled = build_react_agent(
        llm=llm,
        translation=translation,
        yt_summary=yt_summary,
        web_summary=web_summary,
        audio_summary=audio_summary,
        rag_service=rag_service,
    )
    parts = [user_input]
    if target_language:
        parts.insert(0, f"Target language: {target_language}")
    parts.append(f"channel_id: {channel_id}")
    input_text = "\n\n".join(parts)
    final_text: str | None = None

    async for event in compiled.astream(AgentState(messages=[HumanMessage(content=input_text)]), stream_mode="updates"):
        for node_name, updates in event.items():
            messages = updates.get("messages", [])
            if node_name == "agent" and messages and isinstance(messages[-1], AIMessage):
                last = messages[-1]
                if last.tool_calls:
                    yield sse("agent_action", {"tool_calls": [tc["name"] for tc in last.tool_calls]})
                elif last.content:
                    final_text = str(last.content)
            elif node_name == "tools":
                for message in messages:
                    if isinstance(message, ToolMessage):
                        yield sse("agent_observation", {"tool_call_id": message.tool_call_id})
                        content = str(message.content or "")
                        final_text = content
                        async for chunk in _stream_text(content, collector):
                            yield chunk
                        return

    if final_text:
        async for chunk in _stream_text(final_text, collector):
            yield chunk
