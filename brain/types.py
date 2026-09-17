from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# The standardized protocol every plugin speaks to the brain. A web request,
# an iPhone push, a voice transcript, and a future robot's sensor event all
# become one of these before the brain ever sees them.


@dataclass
class BrainInput:
    plugin_id: str
    user_id: str
    content: str
    conversation_id: str | None = None


BrainEventType = Literal[
    "brain.conversation_started",
    "brain.token",
    "brain.tool_started",
    "brain.tool_finished",
    "brain.error",
    "brain.done",
]


@dataclass
class BrainEvent:
    type: BrainEventType
    data: dict[str, Any] = field(default_factory=dict)
