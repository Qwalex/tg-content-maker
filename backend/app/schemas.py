from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from app.models import AuthState, JobStatus


class SessionCreate(BaseModel):
    owner_id: str


class Session2FA(BaseModel):
    password: str = Field(min_length=1)


class SessionOut(BaseModel):
    id: int
    owner_id: str
    telegram_user_id: str | None
    auth_state: AuthState
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CopierCreate(BaseModel):
    session_id: int
    name: str
    source_chat_id: str
    is_active: bool = True


class CopierPatch(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    source_override_enabled: bool | None = None
    ignore_images_override: bool | None = None
    ignore_videos_override: bool | None = None


class TargetCreate(BaseModel):
    target_chat_id: str
    language_code: str
    system_prompt: str | None = None
    user_prompt: str | None = None
    format_options: dict[str, Any] | None = None


class GlobalSettingsPatch(BaseModel):
    ignore_images: bool
    ignore_videos: bool


class LogOut(BaseModel):
    id: int
    level: str
    component: str
    message: str
    context_json: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class CopierOut(BaseModel):
    id: int
    session_id: int
    name: str
    source_chat_id: str
    is_active: bool
    source_override_enabled: bool
    ignore_images_override: bool | None
    ignore_videos_override: bool | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TargetOut(BaseModel):
    id: int
    copier_id: int
    target_chat_id: str
    language_code: str
    system_prompt: str | None
    user_prompt: str | None
    format_options: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class GlobalSettingsOut(BaseModel):
    id: int
    ignore_images: bool
    ignore_videos: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class IngestSourceEvent(BaseModel):
    copier_id: int
    source_message_id: str
    source_text: str = ""
    media_type: str | None = None
    is_edit: bool = False
    source_created_at: datetime | None = None


class JobOut(BaseModel):
    id: int
    event_id: int
    target_id: int
    status: JobStatus
    retry_count: int
    openrouter_model: str
    error: str | None
    updated_at: datetime

    class Config:
        from_attributes = True
