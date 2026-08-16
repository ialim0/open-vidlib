from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class AudioDub(Base):
    __tablename__ = "audio_dubs"
    __table_args__ = (
        UniqueConstraint("video_id", "segment_id", "language", name="uq_video_segment_language"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(String(50), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_id = Column(Integer, ForeignKey("video_segments.id", ondelete="CASCADE"), nullable=True, index=True)
    language = Column(String(10), nullable=False, index=True)
    audio_path = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    voice_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="audio_dubs")
    segment = relationship("VideoSegment", back_populates="dubs")
