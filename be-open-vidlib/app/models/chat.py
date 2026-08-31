from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class VideoChatMessage(Base):
    __tablename__ = "video_chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    is_relevant = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="chat_messages")
