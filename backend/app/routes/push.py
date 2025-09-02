from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..deps import get_current_user_id
from ..db import conn_cursor

router = APIRouter(prefix="/push", tags=["Push"])

class SubIn(BaseModel):
    endpoint: str
    keys: dict  # {p256dh, auth}

@router.post("/subscribe")
async def subscribe(data: SubIn, user_id: str = Depends(get_current_user_id)):
    p256dh = data.keys.get("p256dh")
    auth = data.keys.get("auth")
    async with conn_cursor() as (conn, cur):
        await cur.execute("""
          INSERT INTO push_subscriptions(user_id, endpoint, p256dh, auth)
          VALUES(%s,%s,%s,%s)
          ON CONFLICT (endpoint) DO UPDATE SET user_id=EXCLUDED.user_id, p256dh=EXCLUDED.p256dh, auth=EXCLUDED.auth
        """, (user_id, data.endpoint, p256dh, auth))
        await conn.commit()
    return {"ok": True}

@router.post("/unsubscribe")
async def unsubscribe(data: SubIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        await cur.execute("DELETE FROM push_subscriptions WHERE endpoint=%s AND user_id=%s",
                          (data.endpoint, user_id))
        await conn.commit()
    return {"ok": True}
