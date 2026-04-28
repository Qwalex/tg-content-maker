from sqlalchemy.orm import Session

from app.models import LogEntry


def log_event(db: Session, level: str, component: str, message: str, context: dict | None = None) -> None:
    db.add(LogEntry(level=level, component=component, message=message, context_json=context))
    db.commit()
