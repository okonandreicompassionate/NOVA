import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from models.speech import synthesize
from models.transcription import transcribe

from ..deps import authenticated_supabase

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str


@router.post("/brain/speak")
async def speak(body: SpeakRequest, auth: tuple = Depends(authenticated_supabase)):
    audio = await asyncio.to_thread(synthesize, body.text)
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/brain/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...), auth: tuple = Depends(authenticated_supabase)
):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio")
    text = await asyncio.to_thread(transcribe, audio_bytes, audio.filename or "audio.webm")
    return {"text": text}
