from dataclasses import dataclass, field
from typing import Literal

PluginType = Literal["web", "ios", "android", "desktop", "laptop", "voice", "camera", "robot"]
PluginStatus = Literal["online", "offline"]


@dataclass
class Plugin:
    id: str
    type: PluginType
    capabilities: list[str]  # e.g. ["chat.text", "ui.render"] or ["camera.capture", "filesystem.read"]
    version: str
    status: PluginStatus = "online"
