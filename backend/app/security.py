import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from .config import JWT_SECRET, JWT_ALGO, ACCESS_MIN, REFRESH_DAYS, ISSUER

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def make_access_token(sub: str) -> str:
    payload = {
        "iss": ISSUER,
        "sub": sub,
        "type": "access",
        "exp": now_utc() + timedelta(minutes=ACCESS_MIN),
        "iat": now_utc(),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def make_refresh_token(sub: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    payload = {
        "iss": ISSUER,
        "sub": sub,
        "type": "refresh",
        "exp": now_utc() + timedelta(days=REFRESH_DAYS),
        "iat": now_utc(),
        "jti": jti,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO), jti

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO], options={"verify_aud": False})
