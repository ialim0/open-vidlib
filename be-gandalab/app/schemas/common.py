from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
