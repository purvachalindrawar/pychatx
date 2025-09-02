from fastapi import APIRouter, Depends, HTTPException
from ..deps import get_current_user_id
from ..db import conn_cursor

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/messages")
async def search_messages(room_id: str, q: str, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (_, cur):
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Not a member")
        await cur.execute("""
          SELECT id,user_id,content,created_at
          FROM messages
          WHERE room_id=%s AND deleted=FALSE AND content ILIKE '%%' || %s || '%%'
          ORDER BY created_at DESC LIMIT 100
        """, (room_id, q))
        rows = await cur.fetchall()
    return [
        {"id": r[0], "user_id": r[1], "content": r[2], "created_at": r[3].isoformat()}
        for r in rows
    ]
