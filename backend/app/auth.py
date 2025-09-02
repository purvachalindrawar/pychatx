from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import desc
from sqlalchemy.orm import Session
import uuid
import datetime as dt

from . import deps, schemas
from .database import get_db
from .security import hash_password, verify_password, create_access_token
from .utils_mail import send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------- Sign up ----------
@router.post("/signup", response_model=schemas.UserOut)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user.email.strip().lower()

    existing = db.query(deps.User).filter(deps.User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)

    new_user = deps.User(
        email=email,
        password=hashed_pw,
        display_name=user.display_name,
        email_verified=False,     # <- make sure column exists
        created_at=dt.datetime.utcnow(),
    )
    db.add(new_user)
    db.flush()  # get new_user.id without committing yet

    # create a single-use email verification token
    token = str(uuid.uuid4())
    ev = deps.EmailVerification(
        user_id=new_user.id,
        token=token,
        used=False,
        created_at=dt.datetime.utcnow(),
    )
    db.add(ev)
    db.commit()
    db.refresh(new_user)

    # send email (frontend preferred link + backend fallback is handled in utils_mail)
    await send_verification_email(email, token)

    return new_user


# ---------- Login ----------
@router.post("/login", response_model=schemas.Token)
def login(body: schemas.UserCreate, db: Session = Depends(get_db)):
    email = body.email.strip().lower()

    db_user = db.query(deps.User).filter(deps.User.email == email).first()
    if not db_user or not verify_password(body.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not getattr(db_user, "email_verified", False):
        # Encourage user to verify first; they can also call /auth/resend
        raise HTTPException(status_code=403, detail="Email not verified")

    # You can put user id/email in claims as you prefer
    token = create_access_token({"sub": str(db_user.id), "email": db_user.email, "type": "access"})
    return {"access_token": token, "token_type": "bearer"}


# ---------- Verify email ----------
@router.get("/verify")
async def verify_email(token: str = Query(..., min_length=30, max_length=60), db: Session = Depends(get_db)):
    # quick sanity check
    try:
        uuid.UUID(token)
    except Exception:
        raise HTTPException(status_code=400, detail="Bad token")

    ev = (
        db.query(deps.EmailVerification)
        .filter(deps.EmailVerification.token == token)
        .order_by(desc(deps.EmailVerification.created_at))
        .first()
    )
    if not ev:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user: deps.User = db.query(deps.User).filter(deps.User.id == ev.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Account missing")

    # idempotent behavior
    if getattr(user, "email_verified", False):
        return {"ok": True, "message": "Already verified."}

    # mark verified (even if ev.used somehow true, we still verify)
    user.email_verified = True
    ev.used = True
    ev.used_at = dt.datetime.utcnow()
    db.commit()

    return {"ok": True, "message": "Email verified. You may close this window."}


# ---------- Resend verification ----------
class ResendReq(BaseModel):
    email: EmailStr

@router.post("/resend")
async def resend_verification(body: ResendReq, db: Session = Depends(get_db)):
    email = body.email.strip().lower()

    user: deps.User = db.query(deps.User).filter(deps.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account with that email")

    if getattr(user, "email_verified", False):
        return {"ok": True, "message": "Already verified. Please log in."}

    token = str(uuid.uuid4())
    ev = deps.EmailVerification(
        user_id=user.id,
        token=token,
        used=False,
        created_at=dt.datetime.utcnow(),
    )
    db.add(ev)
    db.commit()

    await send_verification_email(email, token)
    return {"ok": True, "message": "Verification email re-sent."}
