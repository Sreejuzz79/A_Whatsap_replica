from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.call_log import CallLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/calls", tags=["calls"])

class CallCreate(BaseModel):
    receiver_id: int
    status: str = "missed" # 'missed', 'accepted', 'rejected'

class CallUpdate(BaseModel):
    status: str
    end_time: datetime | None = None

@router.post("/", response_model=dict)
async def create_call_log(call: CallCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_call = CallLog(
        caller_id=user.id,
        receiver_id=call.receiver_id,
        status=call.status
    )
    db.add(new_call)
    await db.commit()
    await db.refresh(new_call)
    return {"id": new_call.id, "status": new_call.status}

@router.patch("/{call_id}", response_model=dict)
async def update_call_log(call_id: int, call_update: CallUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CallLog).where(CallLog.id == call_id))
    call_log = result.scalars().first()
    
    if not call_log:
        raise HTTPException(status_code=404, detail="Call log not found")
        
    # Only caller or receiver can update? Usually caller updates 'missed' to 'accepted' if they connect?
    # Or receiver updates? Let's allow both for now, but in reality, whoever ends the call updates duration.
    
    call_log.status = call_update.status
    if call_update.end_time:
        call_log.end_time = call_update.end_time
        
    await db.commit()
    await db.refresh(call_log)
    return {"id": call_log.id, "status": call_log.status, "end_time": call_log.end_time}

@router.get("/", response_model=list)
async def get_call_history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(CallLog).where(
        or_(CallLog.caller_id == user.id, CallLog.receiver_id == user.id)
    ).order_by(desc(CallLog.created_at))
    
    result = await db.execute(query)
    calls = result.scalars().all()
    
    history = []
    for call in calls:
        other_user_id = call.receiver_id if call.caller_id == user.id else call.caller_id
        res = await db.execute(select(User).where(User.id == other_user_id))
        other_user = res.scalars().first()
        
        history.append({
            "id": call.id,
            "type": "outgoing" if call.caller_id == user.id else "incoming",
            "status": call.status,
            "start_time": call.start_time,
            "end_time": call.end_time,
            "other_user": {
                "id": other_user.id,
                "username": other_user.username,
                "full_name": other_user.full_name,
                "profile_picture": other_user.avatar
            } if other_user else None
        })
        
    return history
