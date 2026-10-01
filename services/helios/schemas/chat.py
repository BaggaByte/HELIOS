from datetime import datetime

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime | None = None


class ChatResponse(BaseModel):
    type: str  # "token", "error", "done"
    content: str | None = None
    error: str | None = None
