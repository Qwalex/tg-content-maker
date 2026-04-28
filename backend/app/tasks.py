import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.services.pipeline import process_source_event


def process_source_event_task(
    copier_id: int,
    source_message_id: str,
    source_text: str,
    media_type: str | None = None,
    is_edit: bool = False,
    source_created_at_iso: str | None = None,
) -> None:
    source_created_at = datetime.fromisoformat(source_created_at_iso) if source_created_at_iso else None
    db = SessionLocal()
    try:
        asyncio.run(
            process_source_event(
                db=db,
                copier_id=copier_id,
                source_message_id=source_message_id,
                source_text=source_text,
                media_type=media_type,
                is_edit=is_edit,
                source_created_at=source_created_at,
            )
        )
    finally:
        db.close()
