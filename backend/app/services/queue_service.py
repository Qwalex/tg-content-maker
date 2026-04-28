from redis import Redis
from rq import Queue

from app.config import settings

redis_conn = Redis.from_url(settings.redis_url)
pipeline_queue = Queue("pipeline", connection=redis_conn, default_timeout=300)
