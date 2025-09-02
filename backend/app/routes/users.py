from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..deps import get_current_user_id
from ..db import conn_cursor

router = APIRouter(prefix="/users", tags=["Users"])

class ProfileUpdate(BaseModel):
    display_name: str

@router.get("/me")
async def me(user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (_, cur):
        await cur.execute("SELECT id,email,display_name,email_verified,last_seen,created_at FROM users WHERE id=%s", (user_id,))
        row = await cur.fetchone()
        return {
            "id": row[0], "email": row[1], "display_name": row[2],
            "email_verified": row[3],
            "last_seen": row[4].isoformat() if row[4] else None,
            "created_at": row[5].isoformat()
        }

@router.put("/me")
async def update_me(data: ProfileUpdate, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("UPDATE users SET display_name=%s WHERE id=%s", (data.display_name, user_id))
        await conn.commit()
    return {"ok": True}
