from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.user import User
from ..schemas.auth import SignUpIn, LoginIn, TokenPairOut, TokenOut, MeOut
from ..security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=True)

COOKIE_COMMON = {
    "httponly": True,
    "samesite": "lax",
    "secure": False,  # True in production with HTTPS
    "path": "/",
}

@router.post("/signup", response_model=MeOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpIn, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenPairOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.password_hash or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)

    # set http-only cookies
    response.set_cookie("access_token", access, **COOKIE_COMMON)
    response.set_cookie("refresh_token", refresh, **COOKIE_COMMON)

    # and return both tokens in the body so Swagger can copy/paste
    return TokenPairOut(access_token=access, refresh_token=refresh)

@router.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh/bearer", response_model=TokenOut)
def refresh_bearer(creds: HTTPAuthorizationCredentials = Security(bearer)):
    """
    Send Authorization: Bearer <refresh_token>
    Returns new access token.
    """
    refresh_token = creds.credentials
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token")

    access = create_access_token(payload["sub"])
    return TokenOut(access_token=access)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}
