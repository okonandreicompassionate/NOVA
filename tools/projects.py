from pydantic import BaseModel

from brain.security.permissions import PermissionLevel
from brain.state.context import CognitionContext

from .types import Tool


class ListProjectsInput(BaseModel):
    pass


async def _list_projects(input: ListProjectsInput, ctx: CognitionContext) -> dict:
    result = (
        ctx.supabase.table("projects")
        .select("id, name, description, status")
        .eq("user_id", ctx.user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return {"projects": result.data}


list_projects = Tool(
    name="list_projects",
    description="List the user's tracked projects.",
    permission=PermissionLevel.READ,
    input_model=ListProjectsInput,
    parameters={"type": "object", "properties": {}},
    execute=_list_projects,
)


class GetProjectInput(BaseModel):
    name: str


async def _get_project(input: GetProjectInput, ctx: CognitionContext) -> dict:
    result = (
        ctx.supabase.table("projects")
        .select("id, name, description, status")
        .eq("user_id", ctx.user_id)
        .ilike("name", input.name)
        .maybe_single()
        .execute()
    )
    return {"project": result.data}


get_project = Tool(
    name="get_project",
    description="Get details for a single project by name.",
    permission=PermissionLevel.READ,
    input_model=GetProjectInput,
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Project name (case-insensitive)."}},
        "required": ["name"],
    },
    execute=_get_project,
)


class CreateProjectInput(BaseModel):
    name: str
    description: str | None = None


async def _create_project(input: CreateProjectInput, ctx: CognitionContext) -> dict:
    result = (
        ctx.supabase.table("projects")
        .insert({"user_id": ctx.user_id, "name": input.name, "description": input.description})
        .execute()
    )
    return {"id": result.data[0]["id"]}


create_project = Tool(
    name="create_project",
    description="Register a new project the user is working on.",
    permission=PermissionLevel.LOW_RISK_WRITE,
    input_model=CreateProjectInput,
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string"}, "description": {"type": "string"}},
        "required": ["name"],
    },
    execute=_create_project,
)
