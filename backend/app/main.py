import os
import socketio
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.sockets.handlers import sio
from app.api import auth, uploads, chat, calls
from app.config import settings  # use your config/settings if you have one

app = FastAPI(title="whatsap-backend")

print(f"DEBUG: DATABASE_URL used: {settings.DATABASE_URL}")


# Import models to ensure they are registered with Base
from app.models.base import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.call_log import CallLog
from app.db.session import engine

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(calls.router, prefix="/api", tags=["calls"])


@app.get("/")
async def root():
    return {"message": "whatsap backend — alive and vibing ✨"}

@app.get("/api/reset-db")
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Database reset successfully!"}


@app.get("/favicon.ico")
async def favicon():
    path = "static/favicon.ico"
    if os.path.exists(path):
        return FileResponse(path)
    return Response(status_code=204)


# ensure upload directory exists (use settings if available)
UPLOAD_DIR = getattr(settings, "UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# mount uploads for dev / static serving
# NOTE: serving user uploads directly from the webroot is fine for dev, but be careful in prod.
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


import json
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.db.session import get_db
from app.utils.security import decode_token
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

from app.sockets.connection_manager import manager

# CORS Configuration
# Allow all Vercel subdomains for this app
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://whatsap-replica-7ln1.vercel.app",
    "https://whatsap-replica-7ln1-git-main-sreejesh-m-ss-projects.vercel.app",
    "https://whatsap-replica-7ln1-i76rnspry-sreejesh-m-ss-projects.vercel.app"
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/chat/")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None), db: AsyncSession = Depends(get_db)):
    user_id = None
    try:
        if not token:
            await websocket.close(code=4003)
            return
            
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4003)
            return
            
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4003)
            return
            
        try:
            user_id = int(user_id)
        except ValueError:
            await websocket.close(code=4003)
            return

        await manager.connect(websocket, user_id)
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("action") == "send_message":
                receiver_id = message_data.get("receiver_id")
                content = message_data.get("content")
                
                if receiver_id and content:
                    try:
                        receiver_id = int(receiver_id)
                        print(f"DEBUG: Processing message from {user_id} to {receiver_id}")

                        # 1. Find or Create Conversation
                        # Check if conversation exists
                        query = select(Conversation).where(
                            or_(
                                and_(Conversation.user1_id == user_id, Conversation.user2_id == receiver_id),
                                and_(Conversation.user1_id == receiver_id, Conversation.user2_id == user_id)
                            )
                        )
                        result = await db.execute(query)
                        conversation = result.scalars().first()
                        
                        if not conversation:
                            conversation = Conversation(user1_id=user_id, user2_id=receiver_id)
                            db.add(conversation)
                            await db.commit()
                            await db.refresh(conversation)
                        
                        # 2. Save Message
                        new_message = Message(
                            conversation_id=conversation.id,
                            sender_id=user_id,
                            content=content,
                            type='text'
                        )
                        db.add(new_message)
                        await db.commit()
                        await db.refresh(new_message)
                        
                        # 3. Broadcast to Receiver
                        response = {
                            "type": "new_message",
                            "id": new_message.id,
                            "message": content,
                            "sender_id": user_id,
                            "timestamp": new_message.created_at.isoformat(),
                        }
                        await manager.send_personal_message(response, receiver_id)
                        
                        # 4. Echo back to Sender
                        await manager.send_personal_message({
                            "type": "message_sent",
                            "id": new_message.id,
                            "message": content,
                            "sender_id": user_id,
                            "timestamp": new_message.created_at.isoformat()
                        }, user_id)
                        print(f"DEBUG: Message sent successfully")

                    except Exception as e:
                        import traceback
                        print(f"ERROR processing message: {e}\n{traceback.format_exc()}")
                        await manager.send_personal_message({
                            "type": "error",
                            "message": f"Failed to send message: {str(e)}"
                        }, user_id)

            # WebRTC Signaling
            elif message_data.get("action") in ["call_offer", "call_answer", "ice_candidate", "call_end"]:
                receiver_id = message_data.get("receiver_id")
                if receiver_id:
                    # Forward the signaling message directly to the receiver
                    await manager.send_personal_message(message_data, receiver_id)

    except WebSocketDisconnect:
        if user_id:
            await manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        if user_id:
            await manager.disconnect(user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
