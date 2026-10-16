import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def utcnow():
    return datetime.now(tz=timezone.utc)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    push_subscription: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class IntegrationSettings(Base):
    __tablename__ = "integration_settings"
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    zoro_enabled: Mapped[bool] = mapped_column(default=True)
    zoro_token_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bridge_auto_connect: Mapped[bool] = mapped_column(default=True)
    theme: Mapped[str] = mapped_column(String(32), default="dark")
    accent: Mapped[str] = mapped_column(String(32), default="#4ADE80")
    density: Mapped[str] = mapped_column(String(32), default="comfortable")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
