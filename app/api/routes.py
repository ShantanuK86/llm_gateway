from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse
from app.services.openai_client import call_openai, stream_openai
from app.services.gemini_client import call_gemini
from app.models.domain import User
from app.api.dependencies import get_current_user
from app.services.rate_limiter import check_rate_limit
from app.services.cost_tracker import track_cost_background_task
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

async def execute_with_retry(request: ChatCompletionRequest):
    max_retries = 2
    base_delay = 1.0 # seconds
    
    # Simple routing based on the model name prefix
    is_gemini_model = request.model.startswith("gemini")
    
    for attempt in range(max_retries + 1):
        try:
            if is_gemini_model:
                return await call_gemini(request, target_model=request.model)
            else:
                return await call_openai(request)
        except HTTPException as e:
            # Retry only on Rate Limits (429) or Server Errors (5xx)
            if e.status_code == 429 or e.status_code >= 500:
                if attempt < max_retries:
                    sleep_time = base_delay * (2 ** attempt) # Exponential backoff
                    logger.warning(f"Request failed with {e.status_code}. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                    continue
                else:
                    logger.error("Max retries reached.")
                    
                    # FALLBACK LOGIC
                    # If OpenAI completely fails after retries, fallback to Gemini
                    if not is_gemini_model:
                        logger.warning("Initiating fallback to Gemini-1.5-flash...")
                        try:
                            # Try the fallback model
                            return await call_gemini(request, target_model="gemini-1.5-flash")
                        except Exception as fallback_e:
                            logger.error(f"Fallback to Gemini also failed: {fallback_e}")
                            raise e # Raise original error if fallback fails
            
            # Client errors (4xx other than 429) should be raised immediately
            raise e

@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    logger.info(f"Processing request for user: {user.username}")
    
    # Enforce Rate Limiting (e.g., 5 requests per 60 seconds)
    await check_rate_limit(user.id, max_requests=5, window_seconds=60)
    
    if request.stream:
        # If the user requested streaming, we return a StreamingResponse
        # Note: We are only streaming OpenAI right now to keep the lesson focused.
        if request.model.startswith("gemini"):
            raise HTTPException(status_code=400, detail="Streaming for Gemini is not yet implemented in this phase.")
            
        return StreamingResponse(
            stream_openai(request), 
            media_type="text/event-stream"
        )
    else:
        # Standard synchronous-like waiting (with retries)
        response = await execute_with_retry(request)
        
        # Track cost in the background
        if response.usage:
            background_tasks.add_task(
                track_cost_background_task,
                user_id=user.id,
                model=response.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
            
        return response
