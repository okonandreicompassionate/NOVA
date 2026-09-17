import os

from .provider import ModelProvider
from .providers.groq_provider import GroqProvider

# V1 has exactly one real provider. This function is the seam: adding a local
# model later (e.g. an OllamaProvider) means adding a branch here and setting
# AI_PROVIDER=local — no change to the cognitive loop, the API, or any plugin.


def get_model_provider() -> ModelProvider:
    provider = os.environ.get("AI_PROVIDER", "groq")

    if provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        return GroqProvider(api_key=api_key, model=model)

    raise RuntimeError(f"Unknown AI_PROVIDER: {provider}")
