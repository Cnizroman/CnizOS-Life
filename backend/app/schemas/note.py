from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(default="")
    type: Optional[str] = Field(default="note")
    collection: Optional[str] = None
    is_pinned: Optional[bool] = False
    is_favorite: Optional[bool] = False
    tag_ids: Optional[List[str]] = Field(default_factory=list)
    project_ids: Optional[List[str]] = Field(default_factory=list)

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    body: Optional[str] = None
    type: Optional[str] = None
    collection: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    tag_ids: Optional[List[str]] = None
    project_ids: Optional[List[str]] = None

class NoteOut(BaseModel):
    id: str
    title: str
    body: str
    type: str
    collection: Optional[str]
    is_pinned: bool
    is_favorite: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
