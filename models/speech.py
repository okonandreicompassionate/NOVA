import os

from groq import Groq

# A dedicated speech provider, separate from the chat ModelProvider — NOVA's
# "voice" and its "reasoning" are different capabilities that happen to both
# be served by Groq today. Swapping the voice model later (or moving it local)
# only touches this file.

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
_MODEL = "canopylabs/orpheus-v1-english"
_DEFAULT_VOICE = os.environ.get("SPEECH_VOICE", "tara")


def synthesize(text: str, voice: str | None = None) -> bytes:
    response = _client.audio.speech.create(
        input=text,
        model=_MODEL,
        voice=voice or _DEFAULT_VOICE,
        response_format="mp3",
    )
    return response.read()
