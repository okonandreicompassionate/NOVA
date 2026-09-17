from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

# The nervous system. Producers and consumers only ever touch this interface —
# V1's implementation is in-process, but swapping it for Supabase Realtime or
# a queue later (so events survive a brain restart, or reach a second brain
# instance) only touches this file.

EventType = str  # e.g. "conversation.created", "tool.executed", "task.completed"

Handler = Callable[["Event"], Awaitable[None]]


@dataclass
class Event:
    type: EventType
    user_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Handler]] = defaultdict(list)

    def on(self, event_type: EventType, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    async def emit(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            await handler(event)


event_bus = EventBus()
