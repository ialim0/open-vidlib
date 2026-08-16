from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class QASession(Base):
    __tablename__ = "qa_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    messages = Column(JSON, default=list) # List of {"role": str, "content": str, "timestamp": str}
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="qa_sessions")
