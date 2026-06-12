import logging
from app.db.database import AsyncSessionLocal
from app.models.domain import User
from sqlalchemy import update

logger = logging.getLogger(__name__)

# Simplified pricing table (Cost per 1M tokens in USD)
PRICING = {
    "gpt-4o": {"prompt": 5.0 / 1000000, "completion": 15.0 / 1000000},
    "gpt-3.5-turbo": {"prompt": 0.5 / 1000000, "completion": 1.5 / 1000000},
    "gemini-1.5-flash": {"prompt": 0.35 / 1000000, "completion": 1.05 / 1000000},
}

async def track_cost_background_task(user_id: int, model: str, prompt_tokens: int, completion_tokens: int):
    """
    Background task to calculate financial cost and update the database 
    without blocking the user's API response.
    """
    try:
        # Default to a very cheap model if not found in the pricing table
        model_pricing = PRICING.get(model, {"prompt": 0.1 / 1000000, "completion": 0.2 / 1000000})
        
        prompt_cost = prompt_tokens * model_pricing["prompt"]
        completion_cost = completion_tokens * model_pricing["completion"]
        total_run_cost = prompt_cost + completion_cost
        
        if total_run_cost <= 0:
            return

        # We MUST create a fresh database session here!
        # The session from the API route has already closed because the response was sent.
        async with AsyncSessionLocal() as session:
            # Execute an atomic update directly in PostgreSQL
            # (UPDATE users SET total_cost = total_cost + X WHERE id = Y)
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(total_cost=User.total_cost + total_run_cost)
            )
            await session.execute(stmt)
            await session.commit()
            
        logger.info(f"User {user_id} charged ${total_run_cost:.6f} for {model}")

    except Exception as e:
        logger.error(f"Failed to track cost for user {user_id}: {e}")
