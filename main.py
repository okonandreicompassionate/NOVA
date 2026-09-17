from dotenv import load_dotenv

load_dotenv()  # must run before any module reads os.environ (storage, models) is imported

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from api.routes.brain import router as brain_router  # noqa: E402

app = FastAPI(title="NOVA Brain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Authorization", "Content-Type", "X-Brain-Plugin-Secret"],
)

app.include_router(brain_router)


@app.get("/health")
async def health():
    return {"status": "online"}
