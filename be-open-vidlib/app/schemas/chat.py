from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class VideoChatRequest(BaseModel):
    session_id: str = "default-session"
    message: str
    language: Optional[str] = "en"

class VideoChatResponse(BaseModel):
    answer: str
    is_relevant: bool = True
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessageItem(BaseModel):
    role: str
    content: str
    timestamp: datetime

class ConversationHistoryResponse(BaseModel):
    video_id: str
    session_id: str
    messages: List[ChatMessageItem]
