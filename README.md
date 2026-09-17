# NOVA Brain

The actual intelligence. Independently runnable — stop every plugin (web, future phone, future
laptop agent) and this keeps existing. Plugins are terminals into this; this is not a terminal
into anything.

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - `SUPABASE_URL` / `SUPABASE_ANON_KEY` — same Supabase project as the web plugin (Project Settings → API)
   - `GROQ_API_KEY` — from [console.groq.com](https://console.groq.com)
   - `BRAIN_PLUGIN_SECRET` — any random string; must match the web plugin's `.env.local` exactly
2. `.venv` is already set up. Activate it or call its Python directly:
   ```bash
   .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
   ```
3. Check `http://localhost:8000/health` → `{"status": "online"}`.

## Architecture

- `brain/` — the actual cognition. `brain/cognition/loop.py` is the one real entrypoint
  (`handle_input`) every plugin calls into; nothing else in this codebase should be called
  directly from `api/`. `brain/personality/` holds NOVA's identity (one copy, every plugin gets
  the same voice). `brain/security/` is the permission gate between deciding and acting.
- `models/` — the `ModelProvider` abstraction. `models/router.py` picks a provider from
  `AI_PROVIDER`; today that's Groq. Adding a local model later (Ollama) means adding
  `models/providers/ollama.py` and flipping the env var — nothing in `brain/` changes.
- `tools/` — the capability catalog (memory, projects, tasks). Each tool declares its own
  permission level and pydantic input schema; `tools/registry.py` validates and audit-logs every
  call before it runs.
- `plugins/` — the plugin protocol. V1 has exactly one plugin (`web`), hardcoded in
  `plugins/registry.py`. This becomes a real, persisted registry the moment a second plugin
  (laptop agent) needs to register itself across restarts.
- `events/` — the nervous system. In-process for V1; swappable for Supabase Realtime or a queue
  later without touching producers or consumers.
- `storage/` — Supabase access. Always scoped to the calling user's own JWT — this service never
  holds a service-role key, so Postgres RLS enforces the same per-user isolation it always has.
- `api/` — the HTTP surface. `POST /brain/input` is the only real endpoint: it authenticates the
  caller (shared plugin secret + the user's own Supabase session), then streams `brain.*` events
  back over SSE.

## Security model

Every request needs two things: the `X-Brain-Plugin-Secret` header (proves the caller is an
authorized plugin, not a random client) and a `Bearer` token in `Authorization` (the user's own
Supabase JWT, verified against Supabase Auth on every request — never just decoded and trusted).
The brain builds its Supabase client from that JWT, so it can never see or touch more than the
user it's currently acting for.
"# NOVA" 
