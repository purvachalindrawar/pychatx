from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from ..deps import get_current_user_id
from ..db import conn_cursor

router = APIRouter(prefix="/receipts", tags=["Receipts"])

class ReceiptIn(BaseModel):
    message_ids: List[str]

@router.post("/delivered")
async def delivered(data: ReceiptIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        for mid in data.message_ids:
            await cur.execute("""
              INSERT INTO message_receipts(message_id, user_id, delivered_at)
              VALUES(%s,%s,NOW())
              ON CONFLICT (message_id, user_id) DO UPDATE SET delivered_at=EXCLUDED.delivered_at
            """, (mid, user_id))
        await conn.commit()
    return {"ok": True}

@router.post("/read")
async def read(data: ReceiptIn, user_id: str = Depends(get_current_user_id)):
    async with conn_cursor() as (conn, cur):
        for mid in data.message_ids:
            await cur.execute("""
              INSERT INTO message_receipts(message_id, user_id, read_at)
              VALUES(%s,%s,NOW())
              ON CONFLICT (message_id, user_id) DO UPDATE SET read_at=EXCLUDED.read_at
            """, (mid, user_id))
        await conn.commit()
    return {"ok": True}
