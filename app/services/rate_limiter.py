import time
from fastapi import HTTPException
from app.core.redis import redis_client

async def check_rate_limit(user_id: int, max_requests: int = 10, window_seconds: int = 60):
    """
    A simple Fixed Window rate limiting algorithm using Redis.
    Limits a user to `max_requests` per `window_seconds`.
    """
    current_time = int(time.time())
    # Divide current unix time by window size to group requests into "buckets"
    window_key = current_time // window_seconds
    
    # Create a Redis key unique to the user AND the current time window
    redis_key = f"rate_limit:user:{user_id}:window:{window_key}"
    
    # INCR is an atomic operation in Redis. It increases the count by 1.
    request_count = await redis_client.incr(redis_key)
    
    # If this is the very first request in this window, set an expiration
    # (TTL) on the key so it automatically deletes itself from Redis, preventing memory leaks.
    if request_count == 1:
        await redis_client.expire(redis_key, window_seconds * 2)
        
    if request_count > max_requests:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per minute allowed."
        )
