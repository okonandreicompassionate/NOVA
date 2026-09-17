from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import ValidationError

from brain.security.permissions import requires_confirmation
from brain.state.context import CognitionContext
from models.provider import ToolDefinition

from .memory import create_memory, search_memory
from .projects import create_project, get_project, list_projects
from .tasks import complete_task, create_task, list_tasks
from .types import Tool

_TOOLS: list[Tool] = [
    search_memory,
    create_memory,
    list_projects,
    get_project,
    create_project,
    list_tasks,
    create_task,
    complete_task,
]

_BY_NAME = {t.name: t for t in _TOOLS}


def get_tool_definitions() -> list[ToolDefinition]:
    return [ToolDefinition(name=t.name, description=t.description, parameters=t.parameters) for t in _TOOLS]


ExecutionStatus = Literal["success", "denied", "error"]


@dataclass
class ToolExecutionResult:
    status: ExecutionStatus
    output: dict[str, Any] | None = None
    error: str | None = None


async def execute_tool(
    name: str,
    raw_input: dict[str, Any],
    ctx: CognitionContext,
    conversation_id: str | None = None,
    message_id: str | None = None,
) -> ToolExecutionResult:
    tool = _BY_NAME.get(name)
    if tool is None:
        return ToolExecutionResult(status="error", error=f"Unknown tool: {name}")

    # V1 ships no high-risk/dangerous tools, but the gate is real: a tool
    # registered without a confirmation flow wired up fails closed instead of
    # silently executing.
    if requires_confirmation(tool.permission):
        reason = "This action requires user confirmation, which is not yet wired up."
        await _log_tool_call(ctx, tool.name, tool.permission, raw_input, None, "denied", conversation_id, message_id, reason)
        return ToolExecutionResult(status="denied", error=reason)

    try:
        parsed = tool.input_model(**raw_input)
    except ValidationError as e:
        error = f"Invalid arguments: {e}"
        await _log_tool_call(ctx, tool.name, tool.permission, raw_input, None, "error", conversation_id, message_id, error)
        return ToolExecutionResult(status="error", error=error)

    try:
        output = await tool.execute(parsed, ctx)
        await _log_tool_call(ctx, tool.name, tool.permission, parsed.model_dump(), output, "success", conversation_id, message_id)
        return ToolExecutionResult(status="success", output=output)
    except Exception as e:  # noqa: BLE001 — tool execution is arbitrary; surface it as a tool error, not a 500
        error = str(e)
        await _log_tool_call(ctx, tool.name, tool.permission, parsed.model_dump(), None, "error", conversation_id, message_id, error)
        return ToolExecutionResult(status="error", error=error)


async def _log_tool_call(
    ctx: CognitionContext,
    tool_name: str,
    permission: str,
    input_data: dict[str, Any],
    output: dict[str, Any] | None,
    status: str,
    conversation_id: str | None,
    message_id: str | None,
    error: str | None = None,
) -> None:
    ctx.supabase.table("tool_calls").insert(
        {
            "user_id": ctx.user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "tool_name": tool_name,
            "permission_level": permission,
            "input": input_data,
            "output": output,
            "status": status,
            "error": error,
        }
    ).execute()
