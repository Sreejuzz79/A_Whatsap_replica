from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from pydantic import BaseModel

router = APIRouter(prefix="")

class ProfileUpdate(BaseModel):
    full_name: str | None = None
    about: str | None = None
    profile_picture: str | None = None

from sqlalchemy import select, or_, and_, func
from app.models.conversation import Conversation
from app.models.message import Message

@router.get("/contacts/")
async def get_contacts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Find all conversations where the user is a participant
    query = select(Conversation).where(
        or_(Conversation.user1_id == user.id, Conversation.user2_id == user.id)
    )
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    contacts = []
    for conv in conversations:
        # Determine the "other" user
        other_user_id = conv.user2_id if conv.user1_id == user.id else conv.user1_id
        # Fetch the other user's details
        res = await db.execute(select(User).where(User.id == other_user_id))
        other_user = res.scalars().first()
        
        # Calculate unread count
        unread_query = select(func.count(Message.id)).where(
            and_(
                Message.conversation_id == conv.id,
                Message.sender_id != user.id,
                Message.read == False
            )
        )
        unread_res = await db.execute(unread_query)
        unread_count = unread_res.scalar()
        
        if other_user:
            contacts.append({
                "id": conv.id,
                "contact_user": {
                    "id": other_user.id,
                    "username": other_user.username,
                    "full_name": other_user.full_name,
                    "about": other_user.about,
                    "profile_picture": other_user.avatar
                },
                "unread_count": unread_count
            })
            
    return contacts

from app.sockets.connection_manager import manager

@router.post("/messages/{contact_id}/read/")
async def mark_messages_read(contact_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Find conversation
    query = select(Conversation).where(
        or_(
            and_(Conversation.user1_id == user.id, Conversation.user2_id == contact_id),
            and_(Conversation.user1_id == contact_id, Conversation.user2_id == user.id)
        )
    )
    result = await db.execute(query)
    conversation = result.scalars().first()
    
    if not conversation:
        return {"status": "success", "updated": 0}
        
    # Update messages
    # We want to mark messages sent BY contact_id TO user AS read
    stmt = select(Message).where(
        and_(
            Message.conversation_id == conversation.id,
            Message.sender_id == contact_id,
            Message.read == False
        )
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    if not messages:
        return {"status": "success", "updated": 0}

    for msg in messages:
        msg.read = True
        
    await db.commit()

    # Broadcast read receipt to the sender (contact_id)
    # They need to know that 'user' read their messages
    await manager.send_personal_message({
        "type": "messages_read",
        "conversation_id": conversation.id,
        "reader_id": user.id,
        "message_ids": [m.id for m in messages]
    }, contact_id)

    return {"status": "success", "updated": len(messages)}

@router.get("/messages/{contact_id}/")
async def get_messages(contact_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Find the conversation between these two users
    # We need to check both combinations: (user, contact) and (contact, user)
    query = select(Conversation).where(
        or_(
            and_(Conversation.user1_id == user.id, Conversation.user2_id == contact_id),
            and_(Conversation.user1_id == contact_id, Conversation.user2_id == user.id)
        )
    )
    result = await db.execute(query)
    conversation = result.scalars().first()
    
    if not conversation:
        return []
        
    # Fetch messages for this conversation
    msg_query = select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
    msg_result = await db.execute(msg_query)
    messages = msg_result.scalars().all()
    
    # Format for frontend
    formatted_messages = []
    for msg in messages:
        # We need the sender's username. For MVP, we can infer it or fetch it.
        # Let's fetch it for now to be safe, or optimize later.
        sender_res = await db.execute(select(User).where(User.id == msg.sender_id))
        sender = sender_res.scalars().first()
        
        formatted_messages.append({
            "id": msg.id,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
            "sender_id": msg.sender_id,
            "sender_username": sender.username if sender else "Unknown",
            "delivered": msg.delivered,
            "read": msg.read
        })
        
    return formatted_messages

@router.get("/search/")
async def search_users(q: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not q:
        return []
        
    # Search by username or full_name, excluding the current user
    query = select(User).where(
        and_(
            User.id != user.id,
            or_(
                User.username.ilike(f"%{q}%"),
                User.full_name.ilike(f"%{q}%")
            )
        )
    )
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [{
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "profile_picture": u.avatar,
        "about": u.about
    } for u in users]

@router.patch("/profile/")
async def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    print(f"DEBUG: update_profile called with: {data}")
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.about is not None:
        user.about = data.about
    if data.profile_picture is not None:
        print(f"DEBUG: Updating profile_picture. Length: {len(data.profile_picture)}")
        user.avatar = data.profile_picture
    
    print(f"DEBUG: Committing changes for user {user.id}")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "about": user.about,
        "profile_picture": user.avatar
    }






