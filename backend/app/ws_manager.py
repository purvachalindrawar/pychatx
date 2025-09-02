from typing import Dict, Set
from fastapi import WebSocket

class WSManager:
    def __init__(self):
        self.rooms_sockets: Dict[str, Set[WebSocket]] = {}
        self.rooms_users: Dict[str, Set[str]] = {}

    async def connect(self, room_id: str, user_id: str, ws: WebSocket):
        await ws.accept()
        self.rooms_sockets.setdefault(room_id, set()).add(ws)
        self.rooms_users.setdefault(room_id, set()).add(user_id)

    def disconnect(self, room_id: str, user_id: str, ws: WebSocket):
        if room_id in self.rooms_sockets and ws in self.rooms_sockets[room_id]:
            self.rooms_sockets[room_id].remove(ws)
            if not self.rooms_sockets[room_id]:
                del self.rooms_sockets[room_id]
        if room_id in self.rooms_users and user_id in self.rooms_users[room_id]:
            self.rooms_users[room_id].remove(user_id)
            if not self.rooms_users[room_id]:
                del self.rooms_users[room_id]

    async def broadcast(self, room_id: str, message: dict):
        for ws in list(self.rooms_sockets.get(room_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def is_user_online_in_room(self, room_id: str, user_id: str) -> bool:
        return user_id in self.rooms_users.get(room_id, set())

manager = WSManager()
