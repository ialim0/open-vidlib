from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(10), nullable=False, default="en", index=True) # 'en', 'fr', 'bm', 'ff', 'wo'
    full_text = Column(Text, nullable=False)
    words = Column(JSON, nullable=True) # [{'word': str, 'start': float, 'end': float}]
    segments = Column(JSON, nullable=True) # [{'id': int, 'start': float, 'end': float, 'text': str}]
    embedding = Column(JSON, nullable=True) # Ready for vector embeddings / pgvector
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="transcripts")
