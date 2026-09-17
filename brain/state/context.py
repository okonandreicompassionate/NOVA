from dataclasses import dataclass

from supabase import Client


@dataclass
class CognitionContext:
    """Everything the cognitive loop needs to know about who's asking and how.

    This is per-request state — "what am I doing, for whom, via which plugin"
    — not a persistent state machine. Durable state (conversations, memories,
    tasks) already lives in Postgres; this just carries a request through the
    loop.
    """

    user_id: str
    plugin_id: str
    conversation_id: str | None
    supabase: Client
