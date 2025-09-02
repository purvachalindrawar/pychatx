from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..ws_manager import manager
from ..db import conn_cursor

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket, room_id: str = Query(...), user_id: str = Query(...)):
    async with conn_cursor() as (_, cur):
        await cur.execute("SELECT 1 FROM room_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        if not await cur.fetchone():
            await ws.close(code=1008)
            return
    await manager.connect(room_id, user_id, ws)
    await manager.broadcast(room_id, {"type": "presence", "user_id": user_id, "event": "join"})
    try:
        while True:
            data = await ws.receive_json()
            t = data.get("type")
            if t == "typing":
                await manager.broadcast(room_id, {"type": "typing", "user_id": user_id, "state": data.get("state", True)})
            elif t == "delivered":
                mids = data.get("message_ids", [])
                async with conn_cursor() as (conn, cur):
                    for mid in mids:
                        await cur.execute("""
                          INSERT INTO message_receipts(message_id,user_id,delivered_at)
                          VALUES(%s,%s,NOW())
                          ON CONFLICT (message_id,user_id) DO UPDATE SET delivered_at=EXCLUDED.delivered_at
                        """, (mid, user_id))
                    await conn.commit()
            elif t == "read":
                mids = data.get("message_ids", [])
                async with conn_cursor() as (conn, cur):
                    for mid in mids:
                        await cur.execute("""
                          INSERT INTO message_receipts(message_id,user_id,read_at)
                          VALUES(%s,%s,NOW())
                          ON CONFLICT (message_id,user_id) DO UPDATE SET read_at=EXCLUDED.read_at
                        """, (mid, user_id))
                    await conn.commit()
            elif t == "reaction":
                mid, emoji, action = data.get("message_id"), data.get("emoji"), data.get("action","add")
                async with conn_cursor() as (conn, cur):
                    if action == "remove":
                        await cur.execute("DELETE FROM message_reactions WHERE message_id=%s AND user_id=%s AND emoji=%s",
                                          (mid, user_id, emoji))
                    else:
                        try:
                            await cur.execute("INSERT INTO message_reactions(message_id,user_id,emoji) VALUES(%s,%s,%s)",
                                              (mid, user_id, emoji))
                        except Exception:
                            pass
                    await conn.commit()
                await manager.broadcast(room_id, {"type":"reaction", "message_id": mid, "emoji": emoji, "user_id": user_id, "action": action})
            elif t == "message":
                content = data.get("content", "").strip()
                if content:
                    async with conn_cursor() as (conn, cur):
                        await cur.execute("""
                          INSERT INTO messages(room_id,user_id,content)
                          VALUES(%s,%s,%s) RETURNING id, created_at
                        """, (room_id, user_id, content))
                        row = await cur.fetchone()
                        await conn.commit()
                    await manager.broadcast(room_id, {
                        "type": "message",
                        "id": row[0], "room_id": room_id, "user_id": user_id,
                        "content": content, "created_at": row[1].isoformat()
                    })
            elif t == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.broadcast(room_id, {"type": "presence", "user_id": user_id, "event": "leave"})
        manager.disconnect(room_id, user_id, ws)
        async with conn_cursor() as (conn, cur):
            await cur.execute("UPDATE users SET last_seen=NOW() WHERE id=%s", (user_id,))
            await conn.commit()
