from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import time
import logging

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from .db import init_pool, close_pool, conn_cursor
from .config import (
    APP_ORIGIN,
    CORS_ORIGINS,
    SENTRY_DSN,
    SENTRY_ENV,
    UPLOADS_ENABLED,
    PUSH_ENABLED,
)
from .security_headers import SecurityHeadersMiddleware

# Core routers (always on)
from .routes import auth, users, rooms, messages, search
from .routes import websocket as ws_routes
from .routes import reactions, receipts

# Optional router (only if you created routes/invites.py)
try:
    from .routes import invites
    HAS_INVITES = True
except Exception:
    HAS_INVITES = False

if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, environment=SENTRY_ENV, integrations=[FastApiIntegration()])

REQ_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQ_LAT = Histogram("http_request_latency_seconds", "Latency", ["method", "path"])

log = logging.getLogger(__name__)

app = FastAPI(title="PyChatX Backend")

from fastapi.responses import JSONResponse, Response

@app.get("/")
async def root():
    return JSONResponse({"name": "PyChatX Backend", "status": "ok"})

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

# Security headers + CORS
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or [APP_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus middleware
@app.middleware("http")
async def metrics_mw(request, call_next):
    start = time.time()
    resp = await call_next(request)
    dur = time.time() - start
    REQ_COUNT.labels(request.method, request.url.path, str(resp.status_code)).inc()
    REQ_LAT.labels(request.method, request.url.path).observe(dur)
    return resp

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Startup / Shutdown
@app.on_event("startup")
async def startup():
    await init_pool()
    sql_path = Path(__file__).with_name("sql").joinpath("bootstrap.sql")
    if sql_path.exists():
        sql = sql_path.read_text(encoding="utf-8")
        async with conn_cursor() as (conn, cur):
            await cur.execute(sql)
            await conn.commit()

@app.on_event("shutdown")
async def shutdown():
    await close_pool()

@app.get("/health")
async def health():
    return {"ok": True}

# Routers (core)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rooms.router)
app.include_router(messages.router)
app.include_router(search.router)
app.include_router(reactions.router)
app.include_router(receipts.router)
app.include_router(ws_routes.router)

# Router (invites) if present
if HAS_INVITES:
    app.include_router(invites.router, prefix="/invites", tags=["invites"])

# Optional routers (guarded by flags to avoid import-time failures)
if UPLOADS_ENABLED:
    from .routes import uploads
    app.include_router(uploads.router)
else:
    log.info("Uploads disabled (set UPLOADS_ENABLED=true to enable).")

if PUSH_ENABLED:
    from .routes import push
    app.include_router(push.router)
else:
    log.info("Push disabled (set PUSH_ENABLED=true to enable).")
