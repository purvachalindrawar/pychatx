import os
from dotenv import load_dotenv

load_dotenv()

def _bool(name: str, default: str = "false") -> bool:
    return (os.getenv(name, default) or "").strip().lower() in ("1", "true", "yes", "on")

# -------- Database --------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing in environment (.env)")

# -------- JWT --------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
ACCESS_MIN = int(os.getenv("ACCESS_MIN", os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")))
REFRESH_DAYS = int(os.getenv("REFRESH_DAYS", os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14")))
ISSUER = os.getenv("ISSUER", "pychatx")

# -------- SMTP --------
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS") or os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM") or (f"PyChatX <{SMTP_USER}>" if SMTP_USER else "")

# -------- CORS / Frontend origin --------
# APP_ORIGIN is the single allowed origin used by CORS (and defaults to localhost:5173)
APP_ORIGIN = (
    os.getenv("APP_ORIGIN")
    or os.getenv("FRONTEND_URL")
    or (
        (os.getenv("FRONTEND_BASE_URL") or "http://localhost")
        + (f":{os.getenv('FRONTEND_PORT')}" if os.getenv("FRONTEND_PORT") else ":5173")
    )
)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()] or [APP_ORIGIN]

# FRONTEND_BASE_URL is used when composing links in emails (e.g., /invite/<code>)
# Default it to APP_ORIGIN so both stay in sync unless you override it explicitly.
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", APP_ORIGIN)

# -------- Optional (uploads / push / observability) --------
# Feature flags (so missing S3/Push config doesn't crash the app)
UPLOADS_ENABLED = _bool("UPLOADS_ENABLED", "false")
PUSH_ENABLED    = _bool("PUSH_ENABLED", "false")

# S3 / R2 (only used if UPLOADS_ENABLED=true)
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_REGION = os.getenv("S3_REGION", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PRESIGN_EXPIRE = int(os.getenv("S3_PRESIGN_EXPIRE", "3600"))
S3_PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL", "")

# Web Push (only used if PUSH_ENABLED=true)
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "")

# Observability
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENV = os.getenv("SENTRY_ENV", "dev")
