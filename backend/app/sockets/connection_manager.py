import json
from datetime import datetime
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.models.user import User
from app.db.session import AsyncSessionLocal

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await self.broadcast_status(user_id, "online")

    async def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            await self.update_last_seen(user_id)
            await self.broadcast_status(user_id, "offline")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

    async def broadcast_status(self, user_id: int, status: str):
        # In a real app, we'd only broadcast to contacts. 
        # For now, broadcasting to all active connections is simpler but less scalable.
        # To improve, we should fetch contacts of user_id and only send to them.
        message = {
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "last_seen": datetime.utcnow().isoformat() if status == "offline" else None
        }
        for connection in self.active_connections.values():
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

    async def update_last_seen(self, user_id: int):
        async with AsyncSessionLocal() as db:
            try:
                stmt = update(User).where(User.id == user_id).values(last_seen=datetime.utcnow())
                await db.execute(stmt)
                await db.commit()
            except Exception as e:
                print(f"Error updating last_seen: {e}")

manager = ConnectionManager()
