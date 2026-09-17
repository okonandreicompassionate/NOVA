from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Literal

# Model provider abstraction. Nothing outside models/ should import a provider
# SDK (e.g. "groq") directly — the brain talks only to this interface, so the
# underlying intelligence (Groq today, a local Ollama model later) can be
# swapped without touching cognition, tools, or any plugin.

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCallRequest:
    id: str
    name: str
    arguments: str  # raw JSON string, as returned by the model


@dataclass
class ChatMessage:
    role: Role
    content: str
    tool_calls: list[ToolCallRequest] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema


@dataclass
class TokenEvent:
    content: str


@dataclass
class ToolCallEvent:
    tool_call: ToolCallRequest


@dataclass
class DoneEvent:
    finish_reason: str


StreamEvent = TokenEvent | ToolCallEvent | DoneEvent


@dataclass
class StreamChatParams:
    messages: list[ChatMessage]
    tools: list[ToolDefinition] = field(default_factory=list)


class ModelProvider(ABC):
    name: str

    @abstractmethod
    def stream_chat(self, params: StreamChatParams) -> AsyncIterator[StreamEvent]:
        ...
