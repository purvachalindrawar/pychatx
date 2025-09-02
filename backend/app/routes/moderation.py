from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..db import conn_cursor
from ..auth import require_user
from ..utils import now_utc

router = APIRouter(prefix="/mod", tags=["moderation"])

class TargetIn(BaseModel):
    room_id: str
    target_user_id: str
    reason: Optional[str] = None
    minutes: Optional[int] = None  # for mute until

async def _role(cur, room_id: str, user_id: str) -> str:
    await cur.execute("SELECT role FROM room_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
    r = cur.fetchone()
    return r[0] if r else None

def _role_ok(actor: str, target: str) -> bool:
    order = {"guest":0,"member":1,"mod":2,"admin":3,"owner":4}
    return order.get(actor,0) > order.get(target,0)

@router.post("/mute")
async def mute(body: TargetIn, user=Depends(require_user)):
    async with conn_cursor() as cur:
        actor = await _role(cur, body.room_id, user["id"])
        if actor not in ("mod","admin","owner"):
            raise HTTPException(403, "Insufficient role")
        target = await _role(cur, body.room_id, body.target_user_id)
        if not target:
            raise HTTPException(404, "Target not a member")
        if not _role_ok(actor, target):
            raise HTTPException(403, "Cannot moderate same/higher role")
        until = None
        if body.minutes and body.minutes > 0:
            await cur.execute("SELECT now() + (%s || ' minutes')::interval", (str(body.minutes),))
            until = cur.fetchone()[0]
        await cur.execute("""
          INSERT INTO room_mutes(room_id,target_user_id,actor_user_id,reason,until)
          VALUES(%s,%s,%s,%s,%s)
          ON CONFLICT (room_id,target_user_id) DO UPDATE
          SET reason=EXCLUDED.reason, until=EXCLUDED.until, actor_user_id=EXCLUDED.actor_user_id
        """, (body.room_id, body.target_user_id, user["id"], body.reason, until))
    return {"ok": True, "until": until}

@router.post("/unmute")
async def unmute(body: TargetIn, user=Depends(require_user)):
    async with conn_cursor() as cur:
        actor = await _role(cur, body.room_id, user["id"])
        if actor not in ("mod","admin","owner"):
            raise HTTPException(403, "Insufficient role")
        await cur.execute("DELETE FROM room_mutes WHERE room_id=%s AND target_user_id=%s", (body.room_id, body.target_user_id))
    return {"ok": True}

@router.post("/ban")
async def ban(body: TargetIn, user=Depends(require_user)):
    async with conn_cursor() as cur:
        actor = await _role(cur, body.room_id, user["id"])
        if actor not in ("mod","admin","owner"):
            raise HTTPException(403, "Insufficient role")
        target = await _role(cur, body.room_id, body.target_user_id)
        if target and not _role_ok(actor, target):
            raise HTTPException(403, "Cannot ban same/higher role")
        await cur.execute("""
          INSERT INTO room_bans(room_id,target_user_id,actor_user_id,reason)
          VALUES(%s,%s,%s,%s)
          ON CONFLICT (room_id,target_user_id) DO NOTHING
        """, (body.room_id, body.target_user_id, user["id"], body.reason))
        # also remove from members if present
        await cur.execute("DELETE FROM room_members WHERE room_id=%s AND user_id=%s", (body.room_id, body.target_user_id))
    return {"ok": True}

@router.post("/unban")
async def unban(body: TargetIn, user=Depends(require_user)):
    async with conn_cursor() as cur:
        actor = await _role(cur, body.room_id, user["id"])
        if actor not in ("mod","admin","owner"):
            raise HTTPException(403, "Insufficient role")
        await cur.execute("DELETE FROM room_bans WHERE room_id=%s AND target_user_id=%s", (body.room_id, body.target_user_id))
    return {"ok": True}
