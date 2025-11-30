from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.models.base import Base

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, nullable=False)
    sender_id = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False, default='text')
    content = Column(Text, nullable=True)
    attachment_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered = Column(Boolean, default=False)
    read = Column(Boolean, default=False)