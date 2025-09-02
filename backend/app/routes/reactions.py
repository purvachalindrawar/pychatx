from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..deps import get_current_user_id
from ..db import conn_cursor

router = APIRouter(prefix="/reactions", tags=["Reactions"])

class ReactIn(BaseModel):
    message_id: str
    emoji: str

@router.post("/add")
async def add_reaction(data: ReactIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT room_id FROM messages WHERE id=%s AND deleted=FALSE", (data.message_id,))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Message not found")
        room_id = r[0]
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Not a member")
        try:
            await cur.execute("""
              INSERT INTO message_reactions(message_id,user_id,emoji)
              VALUES(%s,%s,%s)
            """, (data.message_id, user_id, data.emoji))
            await conn.commit()
        except Exception:
            pass
        await cur.execute("""
          SELECT emoji, COUNT(*) FROM message_reactions WHERE message_id=%s GROUP BY emoji
        """, (data.message_id,))
        rows = await cur.fetchall()
    return [{"emoji": x[0], "count": x[1]} for x in rows]

@router.post("/remove")
async def remove_reaction(data: ReactIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("DELETE FROM message_reactions WHERE message_id=%s AND user_id=%s AND emoji=%s",
                          (data.message_id, user_id, data.emoji))
        await conn.commit()
        await cur.execute("""
          SELECT emoji, COUNT(*) FROM message_reactions WHERE message_id=%s GROUP BY emoji
        """, (data.message_id,))
        rows = await cur.fetchall()
    return [{"emoji": x[0], "count": x[1]} for x in rows]
