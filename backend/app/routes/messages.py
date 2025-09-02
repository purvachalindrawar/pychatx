from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from ..db import conn_cursor
from ..deps import get_current_user_id

router = APIRouter(prefix="/messages", tags=["Messages"])

class MsgCreate(BaseModel):
    room_id: str
    content: str = ""
    parent_id: Optional[str] = None
    mentions: List[str] = []

@router.post("")
async def post_message(data: MsgCreate, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (data.room_id, user_id))
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Not a member")
        if data.parent_id:
            await cur.execute("SELECT room_id FROM messages WHERE id=%s", (data.parent_id,))
            pr = await cur.fetchone()
            if not pr or pr[0] != data.room_id:
                raise HTTPException(status_code=400, detail="Invalid parent")
        await cur.execute("""
            INSERT INTO messages(room_id,user_id,content,parent_id)
            VALUES(%s,%s,%s,%s) RETURNING id, created_at
        """, (data.room_id, user_id, data.content, data.parent_id))
        row = await cur.fetchone()
        mid = row[0]
        for m in set(data.mentions):
            await cur.execute("""
              INSERT INTO message_mentions(message_id,mentioned_user_id)
              VALUES(%s,%s) ON CONFLICT DO NOTHING
            """, (mid, m))
        await conn.commit()
    return {"id": mid, "created_at": row[1].isoformat()}

@router.get("")
async def list_messages(room_id: str, cursor: Optional[str] = None, limit: int = Query(50, le=200),
                        thread_of: Optional[str] = None,
                        user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (_, cur):
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Not a member")

        base = """
            SELECT id,user_id,content,edited,deleted,created_at,updated_at,parent_id,
                   attachment_key,attachment_name,attachment_type,attachment_size
            FROM messages
            WHERE room_id=%s
        """
        params = [room_id]
        if thread_of:
            base += " AND parent_id=%s"
            params.append(thread_of)
        if cursor:
            base += " AND created_at < %s"
            params.append(cursor)
        base += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        await cur.execute(base, tuple(params))
        rows = await cur.fetchall()
    return [
        {
            "id": r[0], "user_id": r[1], "content": r[2], "edited": r[3], "deleted": r[4],
            "created_at": r[5].isoformat(), "updated_at": r[6].isoformat() if r[6] else None,
            "parent_id": r[7],
            "attachment": None if not r[8] else {
                "key": r[8], "name": r[9], "type": r[10], "size": r[11]
            }
        } for r in rows
    ]
