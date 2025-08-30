from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from fastapi import HTTPException, status
from .settings import settings

ph = PasswordHasher()

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(hashed: str, plain: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except Exception:
        return False

def _create_jwt(sub: str, token_type: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_access_token(sub: str) -> str:
    return _create_jwt(sub, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES)

def create_refresh_token(sub: str) -> str:
    return _create_jwt(sub, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
