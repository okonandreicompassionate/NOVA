from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from supabase import Client

from events.bus import Event, event_bus
from models.provider import ChatMessage, StreamChatParams, ToolCallEvent, ToolCallRequest, TokenEvent
from models.router import get_model_provider
from tools.registry import execute_tool, get_tool_definitions

from ..personality.identity import SYSTEM_PROMPT
from ..state.context import CognitionContext
from ..types import BrainEvent, BrainInput

MAX_TOOL_ROUNDS = 4


def _row_to_chat_message(row: dict[str, Any]) -> ChatMessage:
    tool_calls = None
    if row.get("tool_calls"):
        tool_calls = [ToolCallRequest(**tc) for tc in row["tool_calls"]]
    return ChatMessage(
        role=row["role"],
        content=row["content"] or "",
        tool_calls=tool_calls,
        tool_call_id=row.get("tool_call_id"),
    )


async def run(input: BrainInput, supabase: Client) -> AsyncIterator[BrainEvent]:
    """The cognitive loop: understand → remember → reason → act → observe → learn.

    This is the brain's only real entrypoint for a conversational turn. It
    does not know or care whether the caller is "web", "ios", or "laptop" —
    every plugin builds a BrainInput and funnels through here.
    """
    ctx = CognitionContext(
        user_id=input.user_id,
        plugin_id=input.plugin_id,
        conversation_id=input.conversation_id,
        supabase=supabase,
    )
    conversation_id = ctx.conversation_id

    # UNDERSTAND — establish which conversation this turn belongs to.
    if conversation_id is None:
        created = (
            ctx.supabase.table("conversations")
            .insert({"user_id": ctx.user_id, "title": input.content[:60]})
            .execute()
        )
        conversation_id = created.data[0]["id"]
        await event_bus.emit(
            Event(type="conversation.created", user_id=ctx.user_id, payload={"conversation_id": conversation_id})
        )
        yield BrainEvent(type="brain.conversation_started", data={"id": conversation_id})

    # REMEMBER — persist the new input, then load the full conversation.
    ctx.supabase.table("messages").insert(
        {"conversation_id": conversation_id, "role": "user", "content": input.content}
    ).execute()

    history = (
        ctx.supabase.table("messages")
        .select("role, content, tool_calls, tool_call_id")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    messages: list[ChatMessage] = [ChatMessage(role="system", content=SYSTEM_PROMPT)]
    messages.extend(_row_to_chat_message(row) for row in history.data)

    provider = get_model_provider()
    tool_defs = get_tool_definitions()

    # REASON → ACT → OBSERVE, repeated until the model stops calling tools.
    for _ in range(MAX_TOOL_ROUNDS):
        assistant_content = ""
        tool_calls: list[ToolCallRequest] = []

        try:
            async for event in provider.stream_chat(StreamChatParams(messages=messages, tools=tool_defs)):
                if isinstance(event, TokenEvent):
                    assistant_content += event.content
                    yield BrainEvent(type="brain.token", data={"content": event.content})
                elif isinstance(event, ToolCallEvent):
                    tool_calls.append(event.tool_call)
        except Exception as e:  # noqa: BLE001 — surface any provider failure as a brain error, not a 500
            yield BrainEvent(type="brain.error", data={"message": str(e)})
            return

        if not tool_calls:
            if assistant_content:
                ctx.supabase.table("messages").insert(
                    {"conversation_id": conversation_id, "role": "assistant", "content": assistant_content}
                ).execute()
            break

        ctx.supabase.table("messages").insert(
            {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": [tc.__dict__ for tc in tool_calls],
            }
        ).execute()
        messages.append(ChatMessage(role="assistant", content=assistant_content, tool_calls=tool_calls))

        # ACT — execute each requested tool under the security/permission gate.
        for call in tool_calls:
            yield BrainEvent(type="brain.tool_started", data={"name": call.name})

            try:
                args = json.loads(call.arguments) if call.arguments else {}
            except json.JSONDecodeError:
                args = {}

            result = await execute_tool(call.name, args, ctx, conversation_id, None)
            await event_bus.emit(
                Event(type="tool.executed", user_id=ctx.user_id, payload={"name": call.name, "status": result.status})
            )
            yield BrainEvent(type="brain.tool_finished", data={"name": call.name, "status": result.status})

            tool_result_content = json.dumps(result.output if result.status == "success" else {"error": result.error})
            ctx.supabase.table("messages").insert(
                {
                    "conversation_id": conversation_id,
                    "role": "tool",
                    "content": tool_result_content,
                    "tool_call_id": call.id,
                    "tool_name": call.name,
                }
            ).execute()
            messages.append(ChatMessage(role="tool", content=tool_result_content, tool_call_id=call.id))

    ctx.supabase.table("conversations").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversation_id).execute()
    yield BrainEvent(type="brain.done")
