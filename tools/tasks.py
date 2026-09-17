from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from brain.security.permissions import PermissionLevel
from brain.state.context import CognitionContext

from .types import Tool

Status = Literal["open", "in_progress", "done", "cancelled"]


class CreateTaskInput(BaseModel):
    title: str
    project_name: str | None = None


async def _create_task(input: CreateTaskInput, ctx: CognitionContext) -> dict:
    project_id = None
    if input.project_name:
        found = (
            ctx.supabase.table("projects")
            .select("id")
            .eq("user_id", ctx.user_id)
            .ilike("name", input.project_name)
            .maybe_single()
            .execute()
        )
        project_id = found.data["id"] if found.data else None

    result = (
        ctx.supabase.table("tasks")
        .insert({"user_id": ctx.user_id, "title": input.title, "project_id": project_id})
        .execute()
    )
    return {"id": result.data[0]["id"]}


create_task = Tool(
    name="create_task",
    description="Create a to-do item for the user, optionally linked to a project by name.",
    permission=PermissionLevel.LOW_RISK_WRITE,
    input_model=CreateTaskInput,
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "project_name": {
                "type": "string",
                "description": "Name of an existing project to link this task to.",
            },
        },
        "required": ["title"],
    },
    execute=_create_task,
)


class ListTasksInput(BaseModel):
    status: Status | None = None


async def _list_tasks(input: ListTasksInput, ctx: CognitionContext) -> dict:
    query = (
        ctx.supabase.table("tasks")
        .select("id, title, status")
        .eq("user_id", ctx.user_id)
        .order("created_at", desc=True)
    )
    if input.status:
        query = query.eq("status", input.status)
    result = query.execute()
    return {"tasks": result.data}


list_tasks = Tool(
    name="list_tasks",
    description="List the user's tasks, optionally filtered by status.",
    permission=PermissionLevel.READ,
    input_model=ListTasksInput,
    parameters={
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["open", "in_progress", "done", "cancelled"]}
        },
    },
    execute=_list_tasks,
)


class CompleteTaskInput(BaseModel):
    title: str


async def _complete_task(input: CompleteTaskInput, ctx: CognitionContext) -> dict:
    result = (
        ctx.supabase.table("tasks")
        .update({"status": "done", "completed_at": datetime.now(timezone.utc).isoformat()})
        .eq("user_id", ctx.user_id)
        .ilike("title", input.title)
        .execute()
    )
    return {"updated": len(result.data) > 0}


complete_task = Tool(
    name="complete_task",
    description="Mark a task as done by matching its title.",
    permission=PermissionLevel.LOW_RISK_WRITE,
    input_model=CompleteTaskInput,
    parameters={"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
    execute=_complete_task,
)
