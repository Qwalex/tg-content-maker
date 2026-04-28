from rq import Worker

from app.config import settings
from app.database import Base, engine
from app.services.queue_service import redis_conn


def main() -> None:
    if settings.auto_create_schema:
        Base.metadata.create_all(engine)
    worker = Worker(queues=["pipeline"], connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
