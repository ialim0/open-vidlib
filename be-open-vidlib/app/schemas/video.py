from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.transcript import TranscriptResponse, TranscriptWord
from app.schemas.flashcard import FlashcardResponse

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    url: str
    cover_image: Optional[str] = None
    duration_seconds: Optional[int] = None

class VideoCreate(VideoBase):
    id: str
    slug: Optional[str] = None

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    cover_image: Optional[str] = None
    duration_seconds: Optional[int] = None

class VideoListItemResponse(VideoBase):
    id: str
    slug: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VideoDetailResponse(VideoListItemResponse):
    transcripts: List[TranscriptResponse] = []
    flashcards: List[FlashcardResponse] = []
    transcript: Optional[str] = None
    transcript_words: Optional[List[TranscriptWord]] = None
    flashcards_by_lang: Optional[Dict[str, List[FlashcardResponse]]] = None

    model_config = ConfigDict(from_attributes=True)
