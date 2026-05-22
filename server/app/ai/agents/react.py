from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from app.ai.agents.tools import create_react_tools
from app.ai.prompts.base import ChatMessage
from app.ai.services.groq_client import GroqChatService
from app.ai.services.rag_service import RagService
from app.ai.services.streaming_service import sse, StreamingCollector
from app.ai.services.translation_service import TranslationService
from app.ai.services.website_summary_service import WebsiteSummaryService
from app.ai.services.youtube_summary_service import YouTubeSummaryService
from app.ai.services.audio_summary_service import AudioSummaryService


REACT_SYSTEM_PROMPT = """You are VibeChat AI, a helpful assistant for a team chat application.

You have access to tools that can:
- translate(text, target_language) — Translate text to another language
- summarize_youtube(url) — Summarize a YouTube video
- summarize_website(url) — Summarize a web page
- summarize_audio(url) — Summarize an audio file
- retrieve_context(question, channel_id) — Search channel history and documents

When a user asks a question, think about which tool(s) to call. You can call multiple tools if needed.
After receiving tool results, synthesize them into a clear, helpful response.

If you cannot answer from the available tools, say so politely."""


class AgentState(BaseModel):
    messages: list = Field(default_factory=list)


def _to_chat_messages(messages: list) -> list[ChatMessage]:
    result: list[ChatMessage] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append(ChatMessage(role="user", content=msg.content))
        elif isinstance(msg, AIMessage):
            m = ChatMessage(role="assistant", content=msg.content or "")
            if msg.tool_calls:
                m.tool_calls = [
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": {"name": tc["name"], "arguments": str(tc["args"])},
                    }
                    for tc in msg.tool_calls
                ]
            result.append(m)
        elif isinstance(msg, ToolMessage):
            result.append(
                ChatMessage(role="tool", content=msg.content, tool_call_id=msg.tool_call_id)
            )
    return result


def _from_chat_response(response: dict) -> AIMessage:
    content = response.get("content", "") or ""
    tool_calls_raw = response.get("tool_calls", [])
    tool_calls = []
    for tc in tool_calls_raw:
        tool_calls.append({
            "name": tc["function"]["name"],
            "args": tc["function"]["arguments"],
            "id": tc["id"],
            "type": "tool_call",
        })
    return AIMessage(content=content, tool_calls=tool_calls)


def build_react_agent(
    *,
    groq: GroqChatService,
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
    for t in tools:
        schema = t.get_input_schema().model_json_schema()
        tool_schemas.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": schema,
            },
        })

    async def call_model(state: AgentState) -> dict[str, list]:
        messages = list(state.messages)
        if not messages or (isinstance(messages[0], HumanMessage) and messages[0].content != REACT_SYSTEM_PROMPT):
            messages = [HumanMessage(content=REACT_SYSTEM_PROMPT), *messages]

        chat_messages = _to_chat_messages(messages)
        response = await groq.chat(messages=chat_messages, tools=tool_schemas, temperature=0.2)
        ai_msg = _from_chat_response(response)
        return {"messages": [ai_msg]}

    def should_continue(state: AgentState) -> str:
        messages = state.messages
        if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "tools"
        return "end"

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "agent")
    return workflow.compile()


async def run_react_agent_stream(
    *,
    groq: GroqChatService,
    translation: TranslationService,
    yt_summary: YouTubeSummaryService,
    web_summary: WebsiteSummaryService,
    audio_summary: AudioSummaryService,
    rag_service: RagService,
    user_input: str,
    channel_id: UUID,
    collector: StreamingCollector,
) -> AsyncGenerator[bytes, None]:
    compiled = build_react_agent(
        groq=groq,
        translation=translation,
        yt_summary=yt_summary,
        web_summary=web_summary,
        audio_summary=audio_summary,
        rag_service=rag_service,
    )

    inputs = AgentState(messages=[HumanMessage(content=user_input)])
    final_text: str | None = None

    async for event in compiled.astream(inputs, stream_mode="updates"):
        for node_name, updates in event.items():
            if node_name == "agent":
                msgs = updates.get("messages", [])
                if msgs and isinstance(msgs[-1], AIMessage):
                    last = msgs[-1]
                    if last.tool_calls:
                        names = [tc["name"] for tc in last.tool_calls]
                        yield sse("agent_action", {"tool_calls": names})
                    elif last.content:
                        final_text = last.content
            elif node_name == "tools":
                msgs = updates.get("messages", [])
                for m in msgs:
                    if isinstance(m, ToolMessage):
                        yield sse("agent_observation", {"tool_call_id": m.tool_call_id})

    if final_text:
        for token in final_text.split(" "):
            collector.add_token(token + " ")
            yield sse("token", {"content": token + " "})
            await asyncio.sleep(0)
