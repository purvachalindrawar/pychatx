from typing import Optional
from fastapi import Depends, Cookie, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .db import get_db
from .models.user import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)

def get_current_user(
    db: Session = Depends(get_db),
    creds: Optional[HTTPAuthorizationCredentials] = Security(bearer),
    access_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
):
    """
    Read JWT from Authorization: Bearer <token> or 'access_token' cookie.
    """
    token: Optional[str] = None
    if creds:
        token = creds.credentials
    elif access_cookie:
        token = access_cookie

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
