from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(String(50), primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    cover_image = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transcripts = relationship("Transcript", back_populates="video", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="video", cascade="all, delete-orphan")
    chat_messages = relationship("VideoChatMessage", back_populates="video", cascade="all, delete-orphan")
    segments = relationship("VideoSegment", back_populates="video", cascade="all, delete-orphan")
    audio_dubs = relationship("AudioDub", back_populates="video", cascade="all, delete-orphan")
    qa_sessions = relationship("QASession", back_populates="video", cascade="all, delete-orphan")
