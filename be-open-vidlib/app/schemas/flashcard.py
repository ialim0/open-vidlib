from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FlashcardBase(BaseModel):
    language: str = "en"
    question: str
    options: List[str]
    correct_option: int
    source: Optional[str] = None

class FlashcardCreate(FlashcardBase):
    video_id: str

class FlashcardResponse(FlashcardBase):
    id: int
    video_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FlashcardGenerateRequest(BaseModel):
    language: str = "en"
    count: int = 5
