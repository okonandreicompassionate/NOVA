import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from brain import handle_input
from brain.types import BrainInput

from ..deps import authenticated_supabase

router = APIRouter()


class BrainInputRequest(BaseModel):
    plugin_id: str
    content: str
    conversation_id: str | None = None


@router.post("/brain/input")
async def brain_input(body: BrainInputRequest, auth: tuple = Depends(authenticated_supabase)):
    user_id, supabase = auth

    input = BrainInput(
        plugin_id=body.plugin_id,
        user_id=user_id,
        content=body.content,
        conversation_id=body.conversation_id,
    )

    async def event_stream():
        async for event in handle_input(input, supabase):
            payload = json.dumps({"type": event.type, **event.data})
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "Connection": "keep-alive"},
    )
