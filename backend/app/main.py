import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .settings import settings
from .db import Base, engine
from .models import User  # noqa: F401  (import to register model)
from .routers.users import router as users_router

app = FastAPI(title="PyChatX", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # For SQLite (dev/tests) we still auto-create tables to keep things easy
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    # For Postgres we rely on Alembic migrations. No auto-create here.

@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_text(data)
    except WebSocketDisconnect:
        pass

# Include API routes first
app.include_router(users_router)

# Mount static demo at /web
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/web", StaticFiles(directory=STATIC_DIR, html=True), name="static")
