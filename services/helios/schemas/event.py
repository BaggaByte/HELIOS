from pydantic import BaseModel, UUID4, Field
from typing import Optional, Dict, Any
from datetime import datetime


class EventBase(BaseModel):
    action: str = Field(..., max_length=50)  # e.g. finding_created, evidence_added
    entity_type: str = Field(..., max_length=50)
    entity_id: Optional[UUID4] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = Field(None, max_length=45)


class EventCreate(EventBase):
    project_id: Optional[UUID4] = None
    actor_id: Optional[UUID4] = None


class EventResponse(EventBase):
    id: int
    project_id: Optional[UUID4] = None
    actor_id: Optional[UUID4] = None
    timestamp: datetime

    class Config:
        from_attributes = True
