from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from ..db import conn_cursor
from ..security import hash_password, verify_password, make_access_token, make_refresh_token, decode_token
from ..emailer import send_verification_email
from ..rate_limit import rate_limit
from ..config import ISSUER

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupIn(BaseModel):
    email: EmailStr
    password: str
    display_name: str

@router.post("/signup")
async def signup(req: Request, data: SignupIn):
    rate_limit(req.client.host)
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT 1 FROM users WHERE email=%s", (data.email,))
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        pw = hash_password(data.password)
        await cur.execute(
            "INSERT INTO users(email,password_hash,display_name) VALUES(%s,%s,%s) RETURNING id",
            (data.email, pw, data.display_name)
        )
        user_id = (await cur.fetchone())[0]
        await cur.execute("INSERT INTO email_verifications(user_id) VALUES(%s) RETURNING token", (user_id,))
        token = (await cur.fetchone())[0]
        await conn.commit()
    try:
        await send_verification_email(data.email, str(token))
    except Exception:
        pass
    return {"ok": True, "message": "Check your email to verify your account."}

@router.get("/verify")
async def verify_email(token: str):
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT user_id, used FROM email_verifications WHERE token=%s", (token,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Invalid token")
        user_id, used = row
        if used:
            return {"ok": True, "message": "Already verified"}
        await cur.execute("UPDATE users SET email_verified=TRUE WHERE id=%s", (user_id,))
        await cur.execute("UPDATE email_verifications SET used=TRUE WHERE token=%s", (token,))
        await conn.commit()
    return {"ok": True, "message": "Email verified"}

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login(req: Request, data: LoginIn):
    rate_limit(req.client.host)
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT id,password_hash,email_verified FROM users WHERE email=%s", (data.email,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user_id, pw_hash, verified = row
        if not verify_password(data.password, pw_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verified:
            raise HTTPException(status_code=403, detail="Email not verified")
        access = make_access_token(str(user_id))
        refresh, jti = make_refresh_token(str(user_id))
        await cur.execute("INSERT INTO refresh_tokens(jti,user_id) VALUES(%s,%s)", (jti, user_id))
        await cur.execute("UPDATE users SET last_seen=NOW() WHERE id=%s", (user_id,))
        await conn.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

class RefreshIn(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(data: RefreshIn):
    from ..security import decode_token as _decode
    try:
        payload = _decode(data.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh")
    if payload.get("type") != "refresh" or payload.get("iss") != ISSUER:
        raise HTTPException(status_code=401, detail="Invalid refresh")
    jti = payload.get("jti")
    user_id = payload.get("sub")
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT rotated, revoked FROM refresh_tokens WHERE jti=%s", (jti,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Unknown refresh")
        rotated, revoked = row
        if rotated or revoked:
            await cur.execute("UPDATE refresh_tokens SET revoked=TRUE WHERE user_id=%s", (user_id,))
            await conn.commit()
            raise HTTPException(status_code=401, detail="Refresh reuse detected")
        await cur.execute("UPDATE refresh_tokens SET rotated=TRUE WHERE jti=%s", (jti,))
        access = make_access_token(str(user_id))
        new_refresh, new_jti = make_refresh_token(str(user_id))
        await cur.execute("INSERT INTO refresh_tokens(jti,user_id) VALUES(%s,%s)", (new_jti, user_id))
        await conn.commit()
    return {"access_token": access, "refresh_token": new_refresh}

@router.post("/logout")
async def logout(user_id: str):
    async with conn_cursor() as (conn, cur):
        await cur.execute("UPDATE refresh_tokens SET revoked=TRUE WHERE user_id=%s", (user_id,))
        await conn.commit()
    return {"ok": True}
