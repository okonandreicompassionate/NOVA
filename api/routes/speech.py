import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from models.speech import synthesize

from ..deps import authenticated_supabase

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str


@router.post("/brain/speak")
async def speak(body: SpeakRequest, auth: tuple = Depends(authenticated_supabase)):
    audio = await asyncio.to_thread(synthesize, body.text)
    return Response(content=audio, media_type="audio/mpeg")
