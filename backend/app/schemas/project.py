from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(default="other")
    status: Optional[str] = Field(default="idea")
    priority: Optional[str] = Field(default="medium")
    links: Optional[List[Any]] = Field(default_factory=list)
    local_path: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    started_at: Optional[str] = None
    deadline: Optional[str] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    links: Optional[List[Any]] = None
    local_path: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    deadline: Optional[str] = None

class ProjectOut(BaseModel):
    id: str
    title: str
    slug: str
    description: Optional[str]
    category: str
    status: str
    priority: str
    links: List[Any]
    local_path: Optional[str]
    github_url: Optional[str]
    demo_url: Optional[str]
    started_at: Optional[datetime | str] = None
    deadline: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
