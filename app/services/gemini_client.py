import httpx
import time
import uuid
import logging
from fastapi import HTTPException
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse, Choice, ChatMessage, Usage
from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

async def call_gemini(request: ChatCompletionRequest, target_model: str = "gemini-2.5-flash-lite") -> ChatCompletionResponse:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured")

    # 1. Map OpenAI messages to Gemini format
    gemini_contents = []
    for msg in request.messages:
        # Gemini roles: "user" or "model". We map system prompts to user for simplicity here.
        role = "user" if msg.role in ["user", "system"] else "model"
        
        gemini_contents.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })

    # 2. Build the payload
    payload = {
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": request.temperature if request.temperature is not None else 1.0,
            "topP": request.top_p if request.top_p is not None else 1.0,
        }
    }
    
    if request.max_tokens:
        payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

    # 3. Make the API Call
    url = GEMINI_API_URL.format(model=target_model)
    url += f"?key={settings.GEMINI_API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30.0
            )
        except httpx.RequestError as e:
            logger.error(f"Gemini API request failed: {e}")
            raise HTTPException(status_code=503, detail="Error communicating with Gemini")

        if response.status_code != 200:
            logger.error(f"Gemini returned error: {response.status_code} {response.text}")
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise HTTPException(status_code=response.status_code, detail=detail)

        gemini_data = response.json()

        # 4. Map Gemini response back to OpenAI format
        try:
            candidates = gemini_data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates found in Gemini response")
                
            candidate = candidates[0]
            content_text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
            
            # Extract Token Usage
            usage_metadata = gemini_data.get("usageMetadata", {})
            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
            completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
            
            choice = Choice(
                index=0,
                message=ChatMessage(role="assistant", content=content_text),
                finish_reason="stop" 
            )

            response_obj = ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex}",
                created=int(time.time()),
                model=target_model,
                choices=[choice],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            )
            return response_obj

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            raise HTTPException(status_code=500, detail="Streaming not implemented for Gemini in this masterclass.")

async def get_embedding(text: str) -> list[float]:
    """
    Takes an English string and returns an array of 768 floating point numbers
    that mathematically represent the meaning of the text.
    """
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"
    
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text}]
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(gemini_url, json=payload, timeout=10.0)
        
        if response.status_code != 200:
            logger.error(f"Gemini Embedding failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
            
        data = response.json()
        return data["embedding"]["values"]
