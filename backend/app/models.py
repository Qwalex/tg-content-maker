from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuthState(str, Enum):
    pending_qr = "pending_qr"
    pending_2fa = "pending_2fa"
    authorized = "authorized"
    expired = "expired"
    revoked = "revoked"


class TelegramSession(Base):
    __tablename__ = "telegram_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(100))
    telegram_user_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    auth_state: Mapped[AuthState] = mapped_column(SqlEnum(AuthState), default=AuthState.pending_qr)
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Copier(Base):
    __tablename__ = "copiers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("telegram_sessions.id"))
    name: Mapped[str] = mapped_column(String(200))
    source_chat_id: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_override_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ignore_images_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ignore_videos_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CopierTarget(Base):
    __tablename__ = "copier_targets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    copier_id: Mapped[int] = mapped_column(ForeignKey("copiers.id"))
    target_chat_id: Mapped[str] = mapped_column(String(200))
    language_code: Mapped[str] = mapped_column(String(20))
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    format_options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GlobalSettings(Base):
    __tablename__ = "global_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    ignore_images: Mapped[bool] = mapped_column(Boolean, default=False)
    ignore_videos: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    delivered = "delivered"
    failed = "failed"
    skipped = "skipped"


class MessageEvent(Base):
    __tablename__ = "message_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    copier_id: Mapped[int] = mapped_column(ForeignKey("copiers.id"), index=True)
    source_message_id: Mapped[str] = mapped_column(String(120), index=True)
    source_chat_id: Mapped[str] = mapped_column(String(200), index=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    source_created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TranslationJob(Base):
    __tablename__ = "translation_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("message_events.id"), index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("copier_targets.id"), index=True)
    status: Mapped[JobStatus] = mapped_column(SqlEnum(JobStatus), default=JobStatus.pending)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    openrouter_model: Mapped[str] = mapped_column(String(120))
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeliveryRecord(Base):
    __tablename__ = "delivery_records"
    __table_args__ = (UniqueConstraint("translation_job_id", name="uq_delivery_translation_job"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    translation_job_id: Mapped[int] = mapped_column(ForeignKey("translation_jobs.id"), index=True)
    source_message_id: Mapped[str] = mapped_column(String(120), index=True)
    target_chat_id: Mapped[str] = mapped_column(String(200), index=True)
    telegram_message_id: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="delivered")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LogEntry(Base):
    __tablename__ = "log_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(20))
    component: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    context_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AlertRecord(Base):
    __tablename__ = "alert_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(30), default="sent")
