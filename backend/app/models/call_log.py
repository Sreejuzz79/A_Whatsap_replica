from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class CallLog(Base):
    __tablename__ = 'call_logs'
    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, nullable=False)
    receiver_id = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False) # 'missed', 'accepted', 'rejected'
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
