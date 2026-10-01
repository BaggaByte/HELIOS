from datetime import datetime
from typing import Any

from pydantic import UUID4, BaseModel, Field


class EventBase(BaseModel):
    action: str = Field(..., max_length=50)  # e.g. finding_created, evidence_added
    entity_type: str = Field(..., max_length=50)
    entity_id: UUID4 | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = Field(None, max_length=45)


class EventCreate(EventBase):
    project_id: UUID4 | None = None
    actor_id: UUID4 | None = None


class EventResponse(EventBase):
    id: int
    project_id: UUID4 | None = None
    actor_id: UUID4 | None = None
    timestamp: datetime

    class Config:
        from_attributes = True
