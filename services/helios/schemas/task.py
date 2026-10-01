from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending")  # pending, in_progress, completed, blocked
    priority: str = Field(default="medium")  # low, medium, high, critical
    due_date: Optional[datetime] = None
    assigned_to: Optional[UUID4] = None


class TaskCreate(TaskBase):
    project_id: UUID4


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[UUID4] = None
    completed_at: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: UUID4
    project_id: UUID4
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
