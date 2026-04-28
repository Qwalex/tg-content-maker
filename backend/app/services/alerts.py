import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AlertRecord


async def send_alert(db: Session, text: str, severity: str = "error", payload: dict | None = None) -> None:
    status = "sent"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(settings.alert_webhook_url, json={"text": text})
    except Exception:  # noqa: BLE001
        status = "failed"
    db.add(AlertRecord(severity=severity, message=text, payload=payload, status=status))
    db.commit()
