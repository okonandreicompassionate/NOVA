import os

from groq import Groq

# Browser-native speech recognition (what the mic button used before this)
# is free but genuinely unreliable — no domain awareness, poor handling of
# accents/background noise. Whisper via Groq is dramatically more accurate
# for the same "hold a button, talk" interaction, and needs no special
# model-terms acceptance (unlike the Orpheus voice model).

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
_MODEL = "whisper-large-v3-turbo"


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    result = _client.audio.transcriptions.create(
        model=_MODEL,
        file=(filename, audio_bytes),
        response_format="json",
    )
    return result.text.strip()
