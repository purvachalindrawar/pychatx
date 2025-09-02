import secrets
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..db import conn_cursor
from ..deps import get_current_user_id

router = APIRouter(prefix="/rooms", tags=["Rooms"])

class RoomCreate(BaseModel):
    name: str
    is_private: bool = False

@router.post("")
async def create_room(data: RoomCreate, user_id: str = Depends(get_current_user_id)):
    invite = secrets.token_urlsafe(8)
    async with conn_cursor() as (conn, cur):
        await cur.execute(
            "INSERT INTO rooms(name,is_private,invite_code,created_by) VALUES(%s,%s,%s,%s) RETURNING id",
            (data.name, data.is_private, invite, user_id)
        )
        room_id = (await cur.fetchone())[0]
        await cur.execute("INSERT INTO room_members(room_id,user_id,role) VALUES(%s,%s,'owner')", (room_id, user_id))
        await conn.commit()
    return {"id": room_id, "invite_code": invite}

@router.post("/join")
async def join_room(invite_code: str, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("SELECT id FROM rooms WHERE invite_code=%s", (invite_code,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Invalid invite")
        room_id = row[0]
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        if not await cur.fetchone():
            await cur.execute("INSERT INTO room_members(room_id,user_id,role) VALUES(%s,%s,'member')", (room_id, user_id))
            await conn.commit()
    return {"ok": True, "room_id": room_id}

@router.get("")
async def my_rooms(user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (_, cur):
        await cur.execute("""
            SELECT r.id, r.name, r.is_private, r.invite_code, r.created_at
            FROM rooms r
            JOIN room_members m ON r.id=m.room_id
            WHERE m.user_id=%s
            ORDER BY r.created_at DESC
        """, (user_id,))
        rows = await cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "is_private": r[2], "invite_code": r[3], "created_at": r[4].isoformat()}
        for r in rows
    ]
