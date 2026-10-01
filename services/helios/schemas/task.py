from datetime import datetime

from pydantic import UUID4, BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    status: str = Field(default="pending")  # pending, in_progress, completed, blocked
    priority: str = Field(default="medium")  # low, medium, high, critical
    due_date: datetime | None = None
    assigned_to: UUID4 | None = None


class TaskCreate(TaskBase):
    project_id: UUID4


class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    assigned_to: UUID4 | None = None
    completed_at: datetime | None = None


class TaskResponse(TaskBase):
    id: UUID4
    project_id: UUID4
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
