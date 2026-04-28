from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.config import settings
from app.models import (
    AuthState,
    Copier,
    CopierTarget,
    GlobalSettings,
    LogEntry,
    TelegramSession,
    TranslationJob,
)
from app.schemas import (
    CopierCreate,
    CopierOut,
    CopierPatch,
    GlobalSettingsOut,
    GlobalSettingsPatch,
    IngestSourceEvent,
    JobOut,
    LogOut,
    Session2FA,
    SessionCreate,
    SessionOut,
    TargetCreate,
    TargetOut,
)
from app.services.logging_service import log_event
from app.services.queue_service import pipeline_queue
from app.services.telegram_userbot import TelegramUserbotService, next_auth_state

app = FastAPI(title="Telegram AI Copier")
telegram = TelegramUserbotService()


@app.on_event("startup")
def startup() -> None:
    if settings.auto_create_schema:
        Base.metadata.create_all(engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    s = TelegramSession(owner_id=payload.owner_id, auth_state=AuthState.pending_qr)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@app.get("/api/sessions/{session_id}/qr")
async def get_qr(session_id: int, db: Session = Depends(get_db)):
    s = db.get(TelegramSession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    qr = await telegram.generate_qr(session_id)
    needs_2fa = await telegram.detect_2fa_required()
    s.auth_state = next_auth_state(needs_2fa)
    db.add(s)
    db.commit()
    log_event(db, "INFO", "auth.qr", "QR generated", {"session_id": session_id})
    return {"qr": qr, "auth_state": s.auth_state}


@app.get("/api/sessions/{session_id}/status")
def status(session_id: int, db: Session = Depends(get_db)):
    s = db.get(TelegramSession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return {"session_id": s.id, "auth_state": s.auth_state, "status": s.status}


@app.post("/api/sessions/{session_id}/2fa", response_model=SessionOut)
async def confirm_2fa(session_id: int, payload: Session2FA, db: Session = Depends(get_db)):
    s = db.get(TelegramSession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    if s.auth_state != AuthState.pending_2fa:
        raise HTTPException(409, "2FA not required in current state")
    ok = await telegram.verify_2fa(payload.password)
    if not ok:
        log_event(db, "WARNING", "auth.2fa", "Invalid 2FA password", {"session_id": session_id})
        raise HTTPException(401, "Invalid 2FA password")
    s.auth_state = AuthState.authorized
    db.add(s)
    db.commit()
    db.refresh(s)
    log_event(db, "INFO", "auth.2fa", "Session authorized", {"session_id": session_id})
    return s


@app.get("/api/settings/global", response_model=GlobalSettingsOut)
def get_global_settings(db: Session = Depends(get_db)):
    g = db.get(GlobalSettings, 1)
    if not g:
        g = GlobalSettings(id=1, ignore_images=False, ignore_videos=False)
        db.add(g)
        db.commit()
        db.refresh(g)
    return g


@app.patch("/api/settings/global", response_model=GlobalSettingsOut)
def patch_global_settings(payload: GlobalSettingsPatch, db: Session = Depends(get_db)):
    g = db.get(GlobalSettings, 1) or GlobalSettings(id=1)
    g.ignore_images = payload.ignore_images
    g.ignore_videos = payload.ignore_videos
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@app.post("/api/copiers", response_model=CopierOut)
def create_copier(payload: CopierCreate, db: Session = Depends(get_db)):
    s = db.get(TelegramSession, payload.session_id)
    if not s or s.auth_state != AuthState.authorized:
        raise HTTPException(400, "Session must be authorized")
    copier = Copier(**payload.model_dump())
    db.add(copier)
    db.commit()
    db.refresh(copier)
    return copier


@app.get("/api/copiers", response_model=list[CopierOut])
def list_copiers(db: Session = Depends(get_db)):
    return list(db.scalars(select(Copier).order_by(Copier.id.desc())).all())


@app.patch("/api/copiers/{copier_id}", response_model=CopierOut)
def patch_copier(copier_id: int, payload: CopierPatch, db: Session = Depends(get_db)):
    c = db.get(Copier, copier_id)
    if not c:
        raise HTTPException(404, "Copier not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@app.patch("/api/copiers/{copier_id}/group-settings", response_model=CopierOut)
def patch_group_settings(copier_id: int, payload: CopierPatch, db: Session = Depends(get_db)):
    return patch_copier(copier_id, payload, db)


@app.post("/api/copiers/{copier_id}/targets", response_model=TargetOut)
async def add_target(copier_id: int, payload: TargetCreate, db: Session = Depends(get_db)):
    c = db.get(Copier, copier_id)
    if not c:
        raise HTTPException(404, "Copier not found")
    if not await telegram.can_send_as_channel(payload.target_chat_id):
        raise HTTPException(400, "Target invalid: send-as-channel unavailable")
    t = CopierTarget(copier_id=copier_id, **payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@app.get("/api/logs", response_model=list[LogOut])
def get_logs(
    level: str | None = Query(default=None),
    component: str | None = Query(default=None),
    limit: int = Query(default=200),
    db: Session = Depends(get_db),
):
    q = select(LogEntry).order_by(LogEntry.id.desc()).limit(limit)
    if level:
        q = q.where(LogEntry.level == level)
    if component:
        q = q.where(LogEntry.component == component)
    return list(db.scalars(q).all())


@app.get("/api/jobs", response_model=list[JobOut])
def list_jobs(
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    q = select(TranslationJob).order_by(desc(TranslationJob.id)).limit(limit)
    if status:
        q = q.where(TranslationJob.status == status)
    return list(db.scalars(q).all())


@app.post("/api/internal/source-events")
def ingest_source_event(
    payload: IngestSourceEvent,
    db: Session = Depends(get_db),
    x_internal_token: str | None = Header(default=None),
):
    if not settings.internal_ingest_token or x_internal_token != settings.internal_ingest_token:
        raise HTTPException(401, "Unauthorized source ingestion")
    copier = db.get(Copier, payload.copier_id)
    if not copier:
        raise HTTPException(404, "Copier not found")
    job = pipeline_queue.enqueue(
        "app.tasks.process_source_event_task",
        kwargs={
            "copier_id": payload.copier_id,
            "source_message_id": payload.source_message_id,
            "source_text": payload.source_text,
            "media_type": payload.media_type,
            "is_edit": payload.is_edit,
            "source_created_at_iso": (payload.source_created_at or datetime.utcnow()).isoformat(),
        },
    )
    log_event(db, "INFO", "ingest.source", "Source event queued", {"copier_id": payload.copier_id, "rq_job_id": job.id})
    return {"queued": True, "rq_job_id": job.id}
