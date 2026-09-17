from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Type

from pydantic import BaseModel

from brain.security.permissions import PermissionLevel
from brain.state.context import CognitionContext


@dataclass
class Tool:
    name: str
    description: str
    permission: PermissionLevel
    input_model: Type[BaseModel]
    parameters: dict[str, Any]  # JSON Schema handed to the model
    execute: Callable[[BaseModel, CognitionContext], Awaitable[dict[str, Any]]]
