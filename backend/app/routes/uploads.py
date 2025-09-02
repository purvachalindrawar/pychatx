from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..deps import get_current_user_id
from ..db import conn_cursor
from ..storage import make_key, presign_put, presign_get, public_url

router = APIRouter(prefix="/uploads", tags=["Uploads"])

class PresignIn(BaseModel):
    room_id: str
    filename: str
    content_type: str

@router.post("/presign")
async def presign(data: PresignIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (_, cur):
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (data.room_id, user_id))
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Not a member")
    key = make_key(data.room_id, data.filename)
    put_url = presign_put(key, data.content_type)
    return {"key": key, "put_url": put_url}

class AttachIn(BaseModel):
    room_id: str
    key: str
    filename: str
    content_type: str
    size: int

@router.post("/attach")
async def attach(data: AttachIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (data.room_id, user_id))
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Not a member")
        await cur.execute("""
            INSERT INTO messages(room_id,user_id,content,attachment_key,attachment_name,attachment_type,attachment_size)
            VALUES(%s,%s,'',%s,%s,%s,%s) RETURNING id, created_at
        """, (data.room_id, user_id, data.key, data.filename, data.content_type, data.size))
        row = await cur.fetchone()
        await conn.commit()
    return {
        "id": row[0], "room_id": data.room_id, "created_at": row[1].isoformat(),
        "attachment": {
            "key": data.key, "name": data.filename, "type": data.content_type,
            "size": data.size, "get_url": public_url(data.key) or presign_get(data.key)
        }
    }
