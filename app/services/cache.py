import json
import hashlib
from app.core.redis import redis_client
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse

def generate_cache_key(request: ChatCompletionRequest) -> str:
    """
    Creates a unique SHA-256 hash based on the model and messages.
    If two users send the exact same messages to the same model, 
    the hash will be identical.
    """
    # Create a deterministic string representation of the request.
    # We only care about the model and the actual messages.
    # We ignore temperature/top_p to maximize cache hits.
    request_data = {
        "model": request.model,
        "messages": [{"role": m.role, "content": m.content} for m in request.messages]
    }
    
    # Sort keys to ensure deterministic JSON string
    json_str = json.dumps(request_data, sort_keys=True)
    
    # Generate SHA-256 hash
    request_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    return f"llm_cache:{request_hash}"

async def get_cached_response(request: ChatCompletionRequest):
    """
    Checks Redis for a previously cached response.
    Returns a ChatCompletionResponse object if found, otherwise None.
    """
    cache_key = generate_cache_key(request)
    cached_data = await redis_client.get(cache_key)
    
    if cached_data:
        # Convert the JSON string back into a Pydantic object
        return ChatCompletionResponse.model_validate_json(cached_data)
    
    return None

async def set_cached_response(request: ChatCompletionRequest, response: ChatCompletionResponse, ttl_seconds: int = 86400):
    """
    Saves a successful response to Redis with a Time-To-Live (TTL).
    Default TTL is 24 hours (86400 seconds).
    """
    cache_key = generate_cache_key(request)
    
    # Convert Pydantic model to JSON string
    response_json = response.model_dump_json()
    
    # Save to Redis with expiration
    await redis_client.setex(cache_key, ttl_seconds, response_json)
