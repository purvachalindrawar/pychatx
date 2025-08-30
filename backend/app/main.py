import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Base, engine
# Import the model class once so the table is registered
from .models.user import User  # noqa: F401
from .routers.users import router as users_router

app = FastAPI(title="PyChatX", version="0.2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # we'll tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Create tables in SQLite (temporary). We'll switch to Alembic soon.
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
            await ws.send_text(data)  # simple echo
    except WebSocketDisconnect:
        pass


# 1) Include API routers FIRST so they are not shadowed by static files
app.include_router(users_router)

# 2) Mount static demo page at /web (not at "/") to avoid POST 405 conflicts
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/web", StaticFiles(directory=STATIC_DIR, html=True), name="static")
