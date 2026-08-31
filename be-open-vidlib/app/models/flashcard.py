from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(10), nullable=False, default="en", index=True) # 'en', 'fr', 'bm', 'ff', 'wo'
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False) # list of string options
    correct_option = Column(Integer, nullable=False) # 0-indexed index of correct answer
    source = Column(String(255), nullable=True) # e.g. "[00:18] - 'quote...'"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="flashcards")
