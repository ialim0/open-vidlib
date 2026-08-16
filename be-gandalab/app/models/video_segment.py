from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

try:
    from pgvector.sqlalchemy import Vector
    VectorType = Vector(1024)
except Exception:
    VectorType = JSON

class VideoSegment(Base):
    __tablename__ = "video_segments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    embedding = Column(VectorType, nullable=True)
    language = Column(String(10), default="en", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="segments")
    dubs = relationship("AudioDub", back_populates="segment", cascade="all, delete-orphan")
