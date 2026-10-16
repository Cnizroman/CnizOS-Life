import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def utcnow():
    return datetime.now(tz=timezone.utc)

class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="Default")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    device_type: Mapped[str] = mapped_column(String(32), default="desktop")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    layout_id: Mapped[str] = mapped_column(String(36), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
