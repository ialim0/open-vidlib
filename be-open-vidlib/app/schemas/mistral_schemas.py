from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone

# 1. Ingestion Schemas
class CaptionItem(BaseModel):
    text: str
    start: float
    end: float

class IngestRequest(BaseModel):
    captions: List[CaptionItem]
    language: str = "en"

class IngestResponse(BaseModel):
    video_id: str
    chunks_created: int
    message: str

# 2. Semantic Search Schemas
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SentenceItem(BaseModel):
    text: str
    start: float
    end: float

class SearchResultItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str
    start_time: float
    end_time: float
    similarity: float
    sentences: Optional[List[SentenceItem]] = None

class SearchResponse(BaseModel):
    video_id: str
    query: str
    results: List[SearchResultItem]

# 3. RAG Q&A Schemas
class RAGQuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default-session"

class RAGAnswerResponse(BaseModel):
    answer: str
    sources: List[SearchResultItem]
    question: str
    video_id: str

# 4. Dubbing Schemas
class DubbingRequest(BaseModel):
    language: str # ISO code e.g. "fr", "es", "de", "wo"
    voice_gender: str = "female" # "female", "male"

class DubbedSegmentItem(BaseModel):
    segment_id: Optional[int] = None
    audio_url: str
    start: float
    end: float
    translated_text: Optional[str] = None

class DubbedTrackResponse(BaseModel):
    video_id: str
    language: str
    voice: str
    status: str
    segments: List[DubbedSegmentItem] = []

# 5. Agent Router Unified Schemas
class AgentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"

class AgentChatResponse(BaseModel):
    type: str # "search" | "qa" | "dubbing" | "chat"
    content: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    sources: Optional[List[SearchResultItem]] = None
    results: Optional[List[SearchResultItem]] = None
    status: Optional[str] = None
    language: Optional[str] = None
    voice_gender: Optional[str] = None
    dub_track: Optional[DubbedTrackResponse] = None
    session_id: Optional[str] = None
    mode: str = "loop"
    tool_call_count: int = 0
    steps: Optional[int] = None
    verified: Optional[bool] = None
    degraded: Optional[bool] = None
    trajectory_id: Optional[str] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
