import os

from dotenv import load_dotenv

load_dotenv()  # must run before any module reads os.environ (storage, models) is imported

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.routes.brain import router as brain_router  # noqa: E402
from api.routes.speech import router as speech_router  # noqa: E402

app = FastAPI(title="NOVA Brain")

# Comma-separated list — e.g. "http://localhost:3000,https://nova-web.vercel.app"
web_origins = [o.strip() for o in os.environ.get("WEB_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=web_origins,
    allow_methods=["POST"],
    allow_headers=["Authorization", "Content-Type", "X-Brain-Plugin-Secret"],
)

app.include_router(brain_router)
app.include_router(speech_router)


@app.get("/health")
async def health():
    return {"status": "online"}
