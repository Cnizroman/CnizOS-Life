import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def utcnow():
    return datetime.now(tz=timezone.utc)

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(32), default="note")  # note,idea,link,summary,draft,instruction,tech,bug,archive
    collection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)

class NoteTag(Base):
    __tablename__ = "note_tags"
    note_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(36), primary_key=True)

class ProjectNote(Base):
    __tablename__ = "project_notes"
    project_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    note_id: Mapped[str] = mapped_column(String(36), primary_key=True)
