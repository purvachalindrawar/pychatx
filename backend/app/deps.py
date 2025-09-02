# app/deps.py
# Option B: keep ORM models in deps.py alongside your auth dependency.

from fastapi import Header, HTTPException
from .security import decode_token

# ---- SQLAlchemy imports ----
import uuid
import datetime as dt
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

# Prefer using your shared Base from database.py
try:
    from .database import Base  # must be the same Base used to create tables
except Exception:
    # Fallback (only used if your database.py doesn't expose Base)
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


# =======================
# Auth dependency (JWT)
# =======================
async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload["sub"]


# =======================
# ORM Models (kept here)
# =======================
def _utcnow():
    # timezone-aware UTC to fit timestamptz columns
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    # IMPORTANT: your DB uses password_hash (not "password")
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    email_verified = Column(Boolean, nullable=False, default=False)

    verifications = relationship(
        "EmailVerification",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_users_email_unique", "email", unique=True),
    )


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # store token as UUID to match your verify endpoint expectation
    token = Column(PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="verifications")


__all__ = ["get_current_user_id", "User", "EmailVerification", "Base"]
