from typing import Literal

from pydantic import BaseModel, Field

from brain.security.permissions import PermissionLevel
from brain.state.context import CognitionContext

from .types import Tool

Category = Literal["preference", "project", "decision", "fact", "event", "goal"]


class CreateMemoryInput(BaseModel):
    content: str
    category: Category = "fact"


async def _create_memory(input: CreateMemoryInput, ctx: CognitionContext) -> dict:
    result = (
        ctx.supabase.table("memories")
        .insert({"user_id": ctx.user_id, "content": input.content, "category": input.category})
        .execute()
    )
    return {"id": result.data[0]["id"]}


create_memory = Tool(
    name="create_memory",
    description="Store a durable fact, preference, decision, or event about the user for later recall.",
    permission=PermissionLevel.LOW_RISK_WRITE,
    input_model=CreateMemoryInput,
    parameters={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The fact to remember, written plainly."},
            "category": {
                "type": "string",
                "enum": ["preference", "project", "decision", "fact", "event", "goal"],
            },
        },
        "required": ["content"],
    },
    execute=_create_memory,
)


class SearchMemoryInput(BaseModel):
    query: str
    limit: int = Field(default=5, gt=0, le=20)


async def _search_memory(input: SearchMemoryInput, ctx: CognitionContext) -> dict:
    result = (
        ctx.supabase.table("memories")
        .select("id, content, category, created_at")
        .eq("user_id", ctx.user_id)
        .ilike("content", f"%{input.query}%")
        .order("created_at", desc=True)
        .limit(input.limit)
        .execute()
    )
    return {"results": result.data}


search_memory = Tool(
    name="search_memory",
    description="Search previously stored memories by keyword.",
    permission=PermissionLevel.READ,
    input_model=SearchMemoryInput,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keyword or phrase to search memories for."},
            "limit": {"type": "number", "description": "Max results (default 5)."},
        },
        "required": ["query"],
    },
    execute=_search_memory,
)
