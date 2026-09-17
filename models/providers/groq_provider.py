from __future__ import annotations

from typing import Any, AsyncIterator

from groq import AsyncGroq

from ..provider import (
    ChatMessage,
    DoneEvent,
    ModelProvider,
    StreamChatParams,
    StreamEvent,
    ToolCallEvent,
    ToolCallRequest,
    ToolDefinition,
    TokenEvent,
)


def _to_groq_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        if m.role == "assistant" and m.tool_calls:
            out.append(
                {
                    "role": "assistant",
                    "content": m.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": tc.arguments},
                        }
                        for tc in m.tool_calls
                    ],
                }
            )
        elif m.role == "tool":
            out.append({"role": "tool", "content": m.content, "tool_call_id": m.tool_call_id})
        else:
            out.append({"role": m.role, "content": m.content})
    return out


def _to_groq_tools(tools: list[ToolDefinition]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
        }
        for t in tools
    ]


class GroqProvider(ModelProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def stream_chat(self, params: StreamChatParams) -> AsyncIterator[StreamEvent]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=_to_groq_messages(params.messages),
            tools=_to_groq_tools(params.tools) if params.tools else None,
            stream=True,
        )

        # Groq streams tool-call arguments in fragments keyed by index —
        # accumulate until the stream ends, then emit one event per index.
        pending: dict[int, ToolCallRequest] = {}
        finish_reason = "stop"

        async for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            if choice is None:
                continue

            delta = choice.delta

            if delta and delta.content:
                yield TokenEvent(content=delta.content)

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    index = tc.index
                    existing = pending.get(index) or ToolCallRequest(id="", name="", arguments="")
                    if tc.id:
                        existing.id = tc.id
                    if tc.function and tc.function.name:
                        existing.name = tc.function.name
                    if tc.function and tc.function.arguments:
                        existing.arguments += tc.function.arguments
                    pending[index] = existing

            if choice.finish_reason:
                finish_reason = choice.finish_reason

        for call in pending.values():
            yield ToolCallEvent(tool_call=call)

        yield DoneEvent(finish_reason=finish_reason)
