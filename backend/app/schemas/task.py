from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    status: Optional[str] = Field(default="todo")
    priority: Optional[str] = Field(default="medium")
    project_id: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    recurrence_rule: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    completed_at: Optional[datetime] = None

class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    project_id: Optional[str]
    category: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    recurrence_rule: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
