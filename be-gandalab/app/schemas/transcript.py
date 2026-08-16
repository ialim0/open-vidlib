from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float

class TranscriptSegment(BaseModel):
    id: Optional[int] = None
    start: float
    end: float
    text: str

class TranscriptBase(BaseModel):
    language: str = "en"
    full_text: str
    words: Optional[List[TranscriptWord]] = None
    segments: Optional[List[TranscriptSegment]] = None

class TranscriptCreate(TranscriptBase):
    video_id: str

class TranscriptResponse(TranscriptBase):
    id: int
    video_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WhisperTranscriptResponse(BaseModel):
    words: List[TranscriptWord] = []
    segments: List[Any] = []
    full_response: Optional[Any] = None
