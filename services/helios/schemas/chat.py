from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ChatResponse(BaseModel):
    type: str  # "token", "error", "done"
    content: Optional[str] = None
    error: Optional[str] = None
