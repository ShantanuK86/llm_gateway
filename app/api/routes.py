from fastapi import APIRouter
from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse
from app.services.openai_client import call_openai

router = APIRouter()

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    # For now, we assume all requests go to OpenAI.
    # In Phase 2, we'll add routing based on the 'model' field.
    return await call_openai(request)
