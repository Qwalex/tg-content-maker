from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Copier, CopierTarget, DeliveryRecord, GlobalSettings, JobStatus, MessageEvent, TranslationJob
from app.services.alerts import send_alert
from app.services.logging_service import log_event
from app.services.openrouter import OpenRouterService
from app.services.telegram_userbot import TelegramUserbotService


async def process_source_event(
    db: Session,
    copier_id: int,
    source_message_id: str,
    source_text: str,
    media_type: str | None,
    is_edit: bool,
    source_created_at: datetime | None,
) -> None:
    copier = db.get(Copier, copier_id)
    if not copier or not copier.is_active:
        return

    if is_edit and source_created_at is None:
        original_event = db.scalar(
            select(MessageEvent)
            .where(
                MessageEvent.copier_id == copier_id,
                MessageEvent.source_message_id == source_message_id,
            )
            .order_by(MessageEvent.id.asc())
            .limit(1)
        )
        source_created_at = original_event.source_created_at if original_event else datetime.utcnow()
    source_created_at = source_created_at or datetime.utcnow()
    global_settings = db.get(GlobalSettings, 1) or GlobalSettings(id=1, ignore_images=False, ignore_videos=False)
    db.add(global_settings)
    db.commit()

    ignore_images = copier.ignore_images_override if copier.source_override_enabled else global_settings.ignore_images
    ignore_videos = copier.ignore_videos_override if copier.source_override_enabled else global_settings.ignore_videos
    if (media_type == "image" and ignore_images) or (media_type == "video" and ignore_videos):
        log_event(
            db,
            "INFO",
            "pipeline.filter",
            "Message skipped by media filter",
            {"copier_id": copier_id, "source_message_id": source_message_id, "media_type": media_type},
        )
        return

    if is_edit and datetime.utcnow() > source_created_at + timedelta(minutes=settings.edit_window_minutes):
        log_event(
            db,
            "INFO",
            "pipeline.edit",
            "Edit ignored out of sync window",
            {"copier_id": copier_id, "source_message_id": source_message_id},
        )
        return

    event = MessageEvent(
        copier_id=copier_id,
        source_message_id=source_message_id,
        source_chat_id=copier.source_chat_id,
        source_text=source_text,
        media_meta={"type": media_type} if media_type else None,
        is_edit=is_edit,
        source_created_at=source_created_at,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    targets = list(db.scalars(select(CopierTarget).where(CopierTarget.copier_id == copier_id)).all())
    openrouter = OpenRouterService()
    telegram = TelegramUserbotService()

    for target in targets:
        send_as = await telegram.can_send_as_channel(target.target_chat_id)
        if not send_as:
            log_event(db, "ERROR", "pipeline.target", "send-as-channel unavailable", {"target_chat_id": target.target_chat_id})
            await send_alert(db, f"send-as-channel unavailable: {target.target_chat_id}", payload={"copier_id": copier_id})
            continue

        job = TranslationJob(
            event_id=event.id,
            target_id=target.id,
            status=JobStatus.processing,
            openrouter_model=settings.openrouter_default_model,
            retry_count=0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            transformed_text, request_payload = await openrouter.transform_text(
                source_text, target.language_code, target.system_prompt, target.user_prompt
            )
            job.request_payload = request_payload
            previous = db.scalar(
                select(DeliveryRecord)
                .where(
                    DeliveryRecord.source_message_id == source_message_id,
                    DeliveryRecord.target_chat_id == target.target_chat_id,
                )
                .order_by(DeliveryRecord.id.desc())
                .limit(1)
            )
            if is_edit and previous:
                telegram_message_id = await telegram.edit(target.target_chat_id, previous.telegram_message_id, transformed_text)
            else:
                telegram_message_id = await telegram.publish(target.target_chat_id, transformed_text)

            job.status = JobStatus.delivered
            job.response_payload = {"text": transformed_text}
            db.add(job)
            db.commit()

            existing_delivery = db.scalar(
                select(DeliveryRecord).where(DeliveryRecord.translation_job_id == job.id).limit(1)
            )
            if not existing_delivery:
                delivery = DeliveryRecord(
                    translation_job_id=job.id,
                    source_message_id=source_message_id,
                    target_chat_id=target.target_chat_id,
                    telegram_message_id=telegram_message_id,
                    status="delivered",
                )
                db.add(delivery)
                db.commit()
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.failed
            job.error = str(exc)
            job.retry_count += 1
            db.add(job)
            db.commit()
            log_event(db, "ERROR", "pipeline.job", "Target processing failed", {"job_id": job.id, "error": str(exc)})
            await send_alert(db, f"Pipeline error job={job.id}: {exc}", payload={"job_id": job.id})
