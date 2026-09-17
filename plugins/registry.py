from .types import Plugin

# In-memory for V1 — there is exactly one plugin. This becomes a real table
# (persisted across brain restarts, populated as devices connect/disconnect)
# the moment a second plugin — the laptop agent — needs to register itself.
_PLUGINS: dict[str, Plugin] = {
    "web": Plugin(id="web", type="web", capabilities=["chat.text", "ui.render"], version="0.1.0"),
}


def get_plugin(plugin_id: str) -> Plugin | None:
    return _PLUGINS.get(plugin_id)


def list_plugins() -> list[Plugin]:
    return list(_PLUGINS.values())
