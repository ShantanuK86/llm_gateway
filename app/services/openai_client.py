import httpx
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse
from app.core.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def call_openai(request: ChatCompletionRequest) -> ChatCompletionResponse:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Filter out None values to avoid OpenAI API validation errors
    payload = request.model_dump(exclude_none=True)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload,
                timeout=30.0
            )
        except httpx.RequestError as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise HTTPException(status_code=503, detail="Error communicating with OpenAI")
            
        if response.status_code != 200:
            logger.error(f"OpenAI returned error: {response.status_code} {response.text}")
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise HTTPException(status_code=response.status_code, detail=detail)
            
        data = response.json()
        return ChatCompletionResponse(**data)

async def stream_openai(request: ChatCompletionRequest):
    """
    Generator function that connects to OpenAI and streams the chunks back.
    In FastAPI, generators are used with StreamingResponse to keep the connection open.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    payload = request.model_dump(exclude_none=True)
    
    async with httpx.AsyncClient() as client:
        # client.stream keeps the socket open so we can read data as it arrives
        async with client.stream("POST", OPENAI_API_URL, headers=headers, json=payload, timeout=30.0) as response:
            if response.status_code != 200:
                await response.aread()
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            # Iterate over the lines as they are received
            async for line in response.aiter_lines():
                if line:
                    # In SSE, events are separated by double newlines
                    yield f"{line}\n\n"
