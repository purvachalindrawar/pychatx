import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .settings import settings
from .db import Base, engine
from .models import User, Room, RoomMember  # noqa: F401
from .routers.users import router as users_router
from .routers.auth import router as auth_router
from .routers.rooms import router as rooms_router

app = FastAPI(title="PyChatX", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Auto-create only for SQLite (dev/tests). For Postgres/Neon, use Alembic.
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

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

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(rooms_router)

# Static demo page
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/web", StaticFiles(directory=STATIC_DIR, html=True), name="static")
