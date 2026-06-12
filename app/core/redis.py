import redis.asyncio as redis
from app.core.config import settings

# Create an async connection pool to Redis
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
