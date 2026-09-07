import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.core.database import init_db
from app.realtime.interview_events import interview_socket

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Role-Based AI Interviewer", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api")
app.add_api_websocket_route("/ws/interviews/{session_id}", interview_socket)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
